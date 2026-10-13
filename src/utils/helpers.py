import hashlib

def generate_message_id(session_id: str, timestamp: float) -> str:
    data = f"{session_id}:{timestamp}"
    return hashlib.md5(data.encode()).hexdigest()

def truncate_text(text: str, max_length: int = 100) -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."
