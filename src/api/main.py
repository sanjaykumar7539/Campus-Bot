from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .routes import router
from .auth_routes import router as auth_router
from .voice_routes import router as voice_router
from .middleware import setup_middleware
from .exceptions import GroundingError, ModelLoadError, grounding_exception_handler, model_exception_handler
from config import config

app = FastAPI(
    title=f"{config.PRODUCT_NAME} — {config.INSTITUTE_SHORT_NAME}",
    description="College assistant that answers from source-linked verified Q&A data and directs unsupported questions to admissions.",
    version=config.PRODUCT_VERSION
)

setup_middleware(app)
app.add_exception_handler(GroundingError, grounding_exception_handler)
app.add_exception_handler(ModelLoadError, model_exception_handler)
app.include_router(router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(voice_router, prefix="/api/v1")

# Prefer React production build when available; fall back to classic frontend/
_REACT_DIST = Path(config.BASE_DIR) / "frontend-react" / "dist"
_CLASSIC = Path(config.BASE_DIR) / "frontend"
FRONTEND_DIR = _REACT_DIST if (_REACT_DIST / "index.html").exists() else _CLASSIC
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")
# Vite assets live under /assets — also serve from the same dist root
if FRONTEND_DIR == _REACT_DIST:
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR / "assets")), name="react-assets")


@app.get("/", include_in_schema=False)
async def frontend_home():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/api", tags=["system"])
async def api_info():
    return {
        "message": f"Welcome to {config.INSTITUTE_NAME} AI Chatbot API",
        "docs": "/docs",
        "version": config.PRODUCT_VERSION,
        "product": config.PRODUCT_NAME,
        "edition": config.PRODUCT_EDITION,
        "features": ["Verified Institute Q&A", "Official Answer Sources", "Admissions Contact Fallback", "SSE Streaming", "Website Auto-Monitor", "Voice Input"]
    }
