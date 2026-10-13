from __future__ import annotations
import asyncio,subprocess,io,wave
from pathlib import Path
from config import config

VOICE_MAP={'en':'en-IN-NeerjaNeural','ta':'ta-IN-PallaviNeural','hi':'hi-IN-SwaraNeural',
 'te':'te-IN-ShrutiNeural','ml':'ml-IN-SobhanaNeural','kn':'kn-IN-SapnaNeural','tanglish':'en-IN-NeerjaNeural'}

class StreamingTTS:
    async def stream(self,text: str,language: str='en'):
        if config.VOICE_TTS_ENGINE=='piper' and config.PIPER_MODEL_PATH:
            process=await asyncio.create_subprocess_exec(config.PIPER_EXECUTABLE,'--model',config.PIPER_MODEL_PATH,
                '--output-raw',stdin=asyncio.subprocess.PIPE,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.DEVNULL)
            audio,_=await process.communicate(text.encode('utf-8'))
            if process.returncode==0 and audio:
                output=io.BytesIO()
                with wave.open(output,'wb') as wav:
                    wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(config.PIPER_SAMPLE_RATE);wav.writeframes(audio)
                yield output.getvalue(),'audio/wav';return
        import edge_tts
        voice=VOICE_MAP.get(language,VOICE_MAP['en'])
        communicate=edge_tts.Communicate(text,voice)
        async for chunk in communicate.stream():
            if chunk['type']=='audio' and chunk.get('data'):yield chunk['data'],'audio/mpeg'
