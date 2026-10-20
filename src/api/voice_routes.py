from __future__ import annotations
import asyncio,json
from fastapi import APIRouter,WebSocket,WebSocketDisconnect
from config import config
from src.security.auth import decode_token
from src.security.prompt_security import PromptSecurity
from src.voice.audio_processing import VoiceActivityDetector
from src.voice.session import VoiceSession
from src.voice.stt_engine import FasterWhisperSTT
from src.voice.tts_engine import StreamingTTS
from src.api import routes as chat_routes
from src.api.rate_limiter import SlidingWindowRateLimiter
from src.utils.translator import resolve_language
from src.utils.answer_presentation import display_answer

router=APIRouter();vad=VoiceActivityDetector(config.VOICE_VAD_THRESHOLD,config.VOICE_MIN_RMS_ENERGY)
stt=FasterWhisperSTT();tts=StreamingTTS();prompt_security=PromptSecurity()
voice_limiter=SlidingWindowRateLimiter(config.CHAT_RATE_LIMIT,config.CHAT_RATE_WINDOW_SECONDS)

async def send(ws,event,**data):await ws.send_json({'event':event,**data})

def authorize(token):
    if not config.AUTH_REQUIRED:return None
    if not token:raise ValueError('Authentication required')
    user=decode_token(token)
    if user.get('role') not in {'student','faculty','hostel_manager','admin'}:raise ValueError('Role not allowed')
    return user

def answer_question(text,language,session_id):
    if not prompt_security.assess(text)['safe']:raise ValueError('Voice request conflicts with CampusMind security rules')
    resolved=resolve_language(text,language)
    result=chat_routes.rag_chain.invoke(
        query=text,
        context_fact_id=chat_routes.session_manager.get_topic(session_id),
    )
    if not result['is_grounded'] and result.get('reason') != 'Specific detail not verified':
        result['answer']=chat_routes.fallback_handler.handle(text,result.get('reason',''))
    result['answer'],resolved=display_answer(result,resolved)
    chat_routes.session_manager.add_message(session_id,'user',text)
    chat_routes.session_manager.add_message(session_id,'bot',result['answer'])
    chat_routes.session_manager.set_topic(session_id,result.get('fact_id'))
    message_id=chat_routes.chat_logger.log(session_id=session_id,user_id=None,query=text,answer=result['answer'],
        sources=result.get('sources',[]),confidence=result.get('confidence',0.0))
    visuals=[]
    return {**result,'sources':[],'language':resolved,'message_id':message_id,'visuals':visuals}

@router.websocket('/voice/stream')
async def voice_stream(ws:WebSocket):
    if not config.VOICE_STREAMING_ENABLED:
        await ws.close(code=1008,reason='Voice streaming disabled');return
    client_ip=ws.client.host if ws.client else 'unknown'
    if not voice_limiter.check('voice:'+client_ip)[0]:
        await ws.close(code=1008,reason='Voice rate limit exceeded');return
    await ws.accept();session=None
    try:
        config_msg=await ws.receive_json()
        if config_msg.get('type')!='start':raise ValueError('First message must be start configuration')
        authorize(config_msg.get('token'))
        sample_rate=int(config_msg.get('sample_rate',16000))
        if sample_rate!=16000:raise ValueError('Only 16000 Hz mono PCM is supported')
        session=VoiceSession(sample_rate,config_msg.get('language','auto'),config_msg.get('session_id','voice'))
        await send(ws,'ready',sample_rate=sample_rate,format='pcm_s16le',stt=config.VOICE_STT_MODEL)
        while True:
            message=await ws.receive()
            if message.get('bytes') is not None:
                session.append(message['bytes'])
                if session.should_partial() and vad.contains_speech(bytes(session.buffer),sample_rate):
                    session.mark_partial()
                    partial=await asyncio.to_thread(stt.transcribe,bytes(session.buffer),session.language)
                    if partial['text']:await send(ws,'partial_transcript',text=partial['text'],language=partial['language'])
            elif message.get('text'):
                command=json.loads(message['text'])
                if command.get('type')=='stop':break
        if session.duration<config.VOICE_MIN_UTTERANCE_SECONDS or not vad.contains_speech(bytes(session.buffer),sample_rate):
            await send(ws,'no_speech',detail='No clear speech detected.');return
        await send(ws,'status',stage='transcribing')
        transcript=await asyncio.to_thread(stt.transcribe,bytes(session.buffer),session.language)
        if not transcript['text']:await send(ws,'no_speech',detail='Speech could not be transcribed.');return
        await send(ws,'final_transcript',**transcript)
        await send(ws,'status',stage='retrieving_and_generating')
        result=await asyncio.to_thread(answer_question,transcript['text'],session.language,session.session_id)
        for i in range(0,len(result['answer']),48):await send(ws,'answer_chunk',text=result['answer'][i:i+48])
        await send(ws,'answer_complete',answer=result['answer'],sources=result.get('sources',[]),
            confidence=result.get('confidence',0),is_grounded=result.get('is_grounded',False),language=result['language'],
            message_id=result['message_id'],visuals=result.get('visuals',[]))
        if config.VOICE_TTS_ENABLED:
            first=True;mime='audio/mpeg'
            try:
                async for audio,mime in tts.stream(result['answer'],result['language']):
                    if first:await send(ws,'audio_start',mime_type=mime);first=False
                    await ws.send_bytes(audio)
                if not first:await send(ws,'audio_end',mime_type=mime)
            except Exception as exc:await send(ws,'tts_unavailable',detail=str(exc))
        await send(ws,'done')
    except WebSocketDisconnect:return
    except ValueError as exc:
        await send(ws,'error',detail=str(exc))
        await ws.close(code=1008)
    except Exception:
        await send(ws,'error',detail='Voice processing failed safely. Text chat remains available.')
        await ws.close(code=1011)
