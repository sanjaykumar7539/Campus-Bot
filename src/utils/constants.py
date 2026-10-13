from enum import Enum

class MessageRole(str, Enum):
    USER = "user"
    BOT = "bot"
    SYSTEM = "system"

class DocumentType(str, Enum):
    PDF = "pdf"
    HTML = "html"
    TEXT = "text"

class FeedbackRating(int, Enum):
    THUMBS_UP = 1
    THUMBS_DOWN = -1
