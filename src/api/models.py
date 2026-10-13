from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


class ChatRequest(BaseModel):
    session_id: str = Field(..., min_length=3, max_length=128)
    message: str = Field(..., min_length=1, max_length=1000)
    user_id: Optional[str] = Field(None, max_length=128)
    language: Optional[str] = Field(None, description='auto, en, ta, tanglish, hi, te, ml or kn')


class SourceDocument(BaseModel):
    document: str
    page: str
    relevance_score: float


class ChatResponse(BaseModel):
    session_id: str
    message_id: int
    answer: str
    sources: List[SourceDocument]
    confidence: float
    is_grounded: bool
    quick_replies: List[str] = Field(default_factory=list)
    language: str = 'en'
    visuals: List[Dict[str, Any]] = Field(default_factory=list)


class FeedbackRequest(BaseModel):
    message_id: int = Field(..., gt=0)
    rating: int = Field(..., description='1 thumbs up, -1 thumbs down')
    comment: Optional[str] = Field(None, max_length=1000)


class HealthResponse(BaseModel):
    status: str
    vector_db_status: str
    model_status: str
    model_loaded: bool
