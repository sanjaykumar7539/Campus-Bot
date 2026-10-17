from fastapi import APIRouter, HTTPException, Header, Request, Response, Depends
from fastapi.responses import StreamingResponse
import asyncio
import json
from .models import ChatRequest, ChatResponse, FeedbackRequest, HealthResponse
from src.core.rag_chain import RAGChain
from src.chatbot.session_manager import SessionManager
from src.chatbot.fallback_handler import FallbackHandler
from src.database.chat_logs import ChatLogger
from src.database.feedback import FeedbackLogger
from src.utils.translator import resolve_language
from src.utils.validators import validate_query
from src.core.readiness import check_readiness
from src.product.product_info import get_product_info, get_product_status
from src.product.analytics import ProductAnalytics
from src.voice.voice_config import get_voice_languages
from src.utils.logger import get_logger
from config import config
from src.api.rate_limiter import SlidingWindowRateLimiter
from src.core.traffic_guard import TrafficGuard
from src.security.prompt_security import PromptSecurity
from src.security.auth import decode_token, require_roles

router = APIRouter()
logger = get_logger('routes')
rag_chain = RAGChain()
session_manager = SessionManager()
fallback_handler = FallbackHandler()
chat_logger = ChatLogger()
feedback_logger = FeedbackLogger()
chat_rate_limiter = SlidingWindowRateLimiter(config.CHAT_RATE_LIMIT, config.CHAT_RATE_WINDOW_SECONDS)
traffic_guard = TrafficGuard(config.LLM_MAX_CONCURRENT, config.LLM_MAX_QUEUE, config.LLM_QUEUE_TIMEOUT_SECONDS)
prompt_security = PromptSecurity()

@router.post('/chat/stream')
async def chat_stream(payload: ChatRequest, http_request: Request):
    """SSE stream with immediate progress, answer chunks, and final metadata."""
    async def events():
        def event(name, data):
            return f'event: {name}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n'
        yield event('status', {'stage': 'accepted'})
        yield event('status', {'stage': 'retrieving_and_generating'})
        try:
            api_response = await asyncio.to_thread(lambda: asyncio.run(chat(payload, http_request, Response())))
            body = api_response.model_dump() if hasattr(api_response, 'model_dump') else api_response.dict()
            words = body['answer'].split(' ')
            # Fewer, larger events reduce browser renders and make completed
            # answers appear noticeably faster on slower phones.
            chunk_size = 12
            for index in range(0, len(words), chunk_size):
                yield event('token', {'text': ' '.join(words[index:index + chunk_size]) + (' ' if index + chunk_size < len(words) else '')})
                await asyncio.sleep(0)
            for visual in body.get('visuals', []):
                yield event('visual', visual)
            yield event('complete', body)
        except HTTPException as exc:
            yield event('error', {'status': exc.status_code, 'detail': exc.detail})
        except Exception:
            logger.exception('Streaming chat failed')
            yield event('error', {'status': 500, 'detail': 'Unable to process the request.'})
    return StreamingResponse(events(), media_type='text/event-stream', headers={
        'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no', 'Connection': 'keep-alive'})


@router.post('/chat', response_model=ChatResponse)
async def chat(payload: ChatRequest, http_request: Request, response: Response):
    if config.AUTH_REQUIRED:
        authorization=http_request.headers.get('authorization','')
        if not authorization.lower().startswith('bearer '):
            raise HTTPException(401,'Authentication required',headers={'WWW-Authenticate':'Bearer'})
        identity=decode_token(authorization.split(' ',1)[1])
        if identity.get('role') not in {'student','faculty','hostel_manager','admin'}:
            raise HTTPException(403,'Role is not allowed to use chat')
    client_ip = http_request.client.host if http_request.client else 'unknown'
    ip_allowed, ip_retry = chat_rate_limiter.check(f'ip:{client_ip}')
    session_allowed, session_retry = chat_rate_limiter.check(f'session:{payload.session_id}')
    if not ip_allowed or not session_allowed:
        retry_after = max(ip_retry, session_retry)
        raise HTTPException(status_code=429, detail='Too many chat requests. Please try again shortly.',
                            headers={'Retry-After': str(retry_after)})
    valid, reason = validate_query(payload.message)
    if not valid:
        raise HTTPException(status_code=400, detail=reason)
    risk=prompt_security.assess(payload.message)
    if not risk['safe']:
        logger.warning('Blocked high-risk prompt for session %s',payload.session_id)
        raise HTTPException(status_code=400,detail='This request conflicts with CampusMind security rules.')
    language = resolve_language(payload.message, payload.language)
    response.headers['X-CampusMind-Cache'] = 'VERIFIED_DATA'
    try:
        result = rag_chain.invoke(
            query=payload.message,
            context_fact_id=session_manager.get_topic(payload.session_id),
        )
    except (FileNotFoundError, ValueError) as exc:
        logger.exception('Verified institute answer data is unavailable')
        raise HTTPException(status_code=503, detail='Verified institute answer data is unavailable.') from exc

    if not result['is_grounded']:
        result['answer'] = fallback_handler.handle(payload.message, result.get('reason', ''))

    message_id = chat_logger.log(
        session_id=payload.session_id, user_id=payload.user_id, query=payload.message,
        answer=result['answer'], sources=result['sources'], confidence=result['confidence'],
    )
    session_manager.add_message(payload.session_id, 'user', payload.message)
    session_manager.add_message(payload.session_id, 'bot', result['answer'])
    session_manager.set_topic(payload.session_id, result.get('fact_id'))
    return ChatResponse(
        session_id=payload.session_id, message_id=message_id, answer=result['answer'],
        sources=[], confidence=result['confidence'], is_grounded=result['is_grounded'],
        quick_replies=[], language=language, visuals=[],
    )


@router.get('/system/traffic')
async def traffic_status():
    snapshot = await traffic_guard.snapshot()
    return {
        'active_inference': snapshot.active,
        'queued_requests': snapshot.waiting,
        'max_concurrent_inference': snapshot.max_concurrent,
        'max_queue': snapshot.max_waiting,
    }


@router.post('/feedback')
async def submit_feedback(request: FeedbackRequest):
    if request.rating not in {-1, 1}:
        raise HTTPException(status_code=400, detail='rating must be 1 or -1')
    try:
        feedback_logger.save(request.message_id, request.rating, request.comment)
        return {'status': 'success', 'message': 'Feedback recorded'}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get('/health', response_model=HealthResponse)
async def health_check():
    readiness = check_readiness()
    vector_status = 'present' if readiness['vector_db_present'] else 'missing'
    if readiness['vector_db_present'] and not readiness['manifest_present']:
        vector_status = 'present (legacy/unverified; rebuild recommended)'
    return HealthResponse(
        status='healthy', vector_db_status=vector_status,
        model_status='present' if readiness['model_present'] else 'missing',
        model_loaded=False,
    )


@router.get('/ready')
async def ready_check():
    state = check_readiness()
    return {'status': 'ready' if state['ready_for_full_chat'] else 'setup_required', **state}


@router.get('/history/{session_id}')
async def get_chat_history(session_id: str):
    return {'session_id': session_id, 'messages': session_manager.get_messages(session_id)}


@router.get('/product')
async def product_info():
    return get_product_info()


@router.get('/product/status')
async def product_status():
    return get_product_status()


@router.get('/admin/analytics')
async def admin_analytics(request: Request, x_admin_key: str | None = Header(default=None)):
    if not config.ADMIN_API_KEY:
        raise HTTPException(status_code=404, detail='Admin analytics endpoint is disabled')
    if x_admin_key != config.ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail='Invalid admin key')
    if config.AUTH_REQUIRED:
        authorization = request.headers.get('authorization', '')
        if not authorization.lower().startswith('bearer '):
            raise HTTPException(401, 'Authentication required', headers={'WWW-Authenticate': 'Bearer'})
        if decode_token(authorization.split(' ', 1)[1]).get('role') != 'admin':
            raise HTTPException(403, 'Insufficient role permission')
    return ProductAnalytics().summary()


@router.get('/voice/languages')
async def voice_languages():
    return {'languages': get_voice_languages(), 'engine': 'browser-web-speech'}
