from fastapi import Request
from fastapi.responses import JSONResponse

class GroundingError(Exception):
    pass

class ModelLoadError(Exception):
    pass

async def grounding_exception_handler(request: Request, exc: GroundingError):
    return JSONResponse(status_code=422, content={"detail": str(exc), "type": "grounding_error"})

async def model_exception_handler(request: Request, exc: ModelLoadError):
    return JSONResponse(status_code=503, content={"detail": str(exc), "type": "model_error"})
