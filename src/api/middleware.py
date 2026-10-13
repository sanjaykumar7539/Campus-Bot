import time
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from config import config


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()
        response = await call_next(request)
        response.headers['X-Process-Time'] = f'{time.perf_counter() - start_time:.4f}'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'camera=(), geolocation=(), microphone=(self)'
        response.headers['Content-Security-Policy'] = "default-src 'self'; img-src 'self' data: https://tile.openstreetmap.org; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; connect-src 'self'"
        response.headers['Cross-Origin-Opener-Policy'] = 'same-origin'
        if config.APP_ENV == 'production':
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response


def setup_cors(app):
    # Frontend and API are same-origin in normal use; credentials are unnecessary.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=(config.CORS_ORIGINS or ['http://127.0.0.1:%s' % config.PORT, 'http://localhost:%s' % config.PORT]), allow_credentials=False,
        allow_methods=['GET', 'POST'], allow_headers=['Content-Type', 'Authorization', 'X-Admin-Key'],
    )


def setup_middleware(app):
    setup_cors(app)
    app.add_middleware(LoggingMiddleware)
