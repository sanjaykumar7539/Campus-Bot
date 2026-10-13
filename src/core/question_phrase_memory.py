"""Local, minimized memory of high-confidence institute question phrasing."""
import re
from functools import lru_cache

from src.database.db_manager import DatabaseManager


_EMAIL = re.compile(r'\b[\w.+-]+@[\w.-]+\.[a-z]{2,}\b', re.IGNORECASE)
_URL = re.compile(r'\b(?:https?://|www\.)\S+', re.IGNORECASE)
_LONG_NUMBER = re.compile(r'\d{5,}')
_PHONE = re.compile(r'(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)(?!\w)')


def normalize_learnable_phrase(question: str) -> str | None:
    """Minimize and reject likely personal/contact data before persistence."""
    value = ' '.join(re.sub(r'[^\w]+', ' ', question.casefold(), flags=re.UNICODE).split())
    if not value or len(value) > 180 or len(value.split()) < 2:
        return None
    if any(pattern.search(question) for pattern in (_EMAIL, _URL, _LONG_NUMBER, _PHONE)):
        return None
    return value


class QuestionPhraseMemory:
    """Persist only anonymized question wording mapped to an approved fact ID."""

    def __init__(self, db: DatabaseManager | None = None):
        self.db = db or DatabaseManager()

    def get_fact_id(self, normalized_question: str) -> str | None:
        marker = '%s' if self.db.is_postgres else '?'
        with self.db.get_connection() as connection:
            row = connection.execute(
                f'SELECT fact_id FROM learned_question_phrases WHERE normalized_question = {marker}',
                (normalized_question,),
            ).fetchone()
        return str(row[0]) if row else None

    def remember(self, question: str, fact_id: str) -> bool:
        normalized = normalize_learnable_phrase(question)
        if normalized is None or not fact_id:
            return False
        marker = '%s' if self.db.is_postgres else '?'
        with self.db.get_connection() as connection:
            existing = connection.execute(
                f'SELECT fact_id FROM learned_question_phrases WHERE normalized_question = {marker}',
                (normalized,),
            ).fetchone()
            if existing and existing[0] != fact_id:
                return False
            connection.execute(
                f'''
                INSERT INTO learned_question_phrases (normalized_question, fact_id)
                VALUES ({marker}, {marker})
                ON CONFLICT (normalized_question) DO UPDATE SET
                    usage_count = learned_question_phrases.usage_count + 1,
                    last_seen_at = CURRENT_TIMESTAMP
                ''',
                (normalized, fact_id),
            )
        return True


@lru_cache(maxsize=1)
def get_question_phrase_memory() -> QuestionPhraseMemory:
    return QuestionPhraseMemory()
