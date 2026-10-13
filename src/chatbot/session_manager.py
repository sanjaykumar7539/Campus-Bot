import uuid
from typing import Dict, List
from collections import defaultdict
from config import config
from .context_window import ContextWindow


class SessionManager:
    def __init__(self, max_history: int | None = None):
        self.sessions: Dict[str, List[Dict]] = defaultdict(list)
        self.session_topics: Dict[str, str] = {}
        self.max_history = max_history or config.MAX_SESSION_MESSAGES
        self.context_window = ContextWindow(max_messages=min(self.max_history, 8))

    def create_session(self) -> str:
        return str(uuid.uuid4())

    def add_message(self, session_id: str, role: str, content: str):
        if role not in {'user', 'bot'}:
            raise ValueError('role must be user or bot')
        self.sessions[session_id].append({'role': role, 'content': content})
        if len(self.sessions[session_id]) > self.max_history:
            self.sessions[session_id] = self.sessions[session_id][-self.max_history:]

    def get_history(self, session_id: str) -> str:
        return self.context_window.build_context(self.sessions.get(session_id, []))

    def get_messages(self, session_id: str) -> List[Dict]:
        return list(self.sessions.get(session_id, []))

    def set_topic(self, session_id: str, fact_id: str | None):
        if fact_id:
            self.session_topics[session_id] = fact_id

    def get_topic(self, session_id: str) -> str | None:
        return self.session_topics.get(session_id)

    def clear_session(self, session_id: str):
        self.sessions.pop(session_id, None)
        self.session_topics.pop(session_id, None)
