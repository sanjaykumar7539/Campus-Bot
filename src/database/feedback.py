from .db_manager import DatabaseManager
from src.security.crypto import FieldCipher


class FeedbackLogger:
    def __init__(self, db: DatabaseManager | None = None):
        self.db = db or DatabaseManager()
        self.cipher = FieldCipher()

    def save(self, message_id: int, rating: int, comment: str = None):
        if rating not in {-1, 1}:
            raise ValueError('rating must be 1 or -1')
        with self.db.get_connection() as conn:
            mark='%s' if self.db.is_postgres else '?'
            exists = conn.execute(f"SELECT 1 FROM messages WHERE id = {mark} AND role = 'bot'", (message_id,)).fetchone()
            if not exists:
                raise ValueError('Bot message not found')
            conn.execute(f'INSERT INTO feedback (message_id, rating, comment) VALUES ({mark}, {mark}, {mark})', (message_id, rating, self.cipher.encrypt(comment)))

    def get_stats(self) -> dict:
        with self.db.get_connection() as conn:
            row = conn.execute('''SELECT COUNT(*) total,
                SUM(CASE WHEN rating = 1 THEN 1 ELSE 0 END) positive,
                SUM(CASE WHEN rating = -1 THEN 1 ELSE 0 END) negative FROM feedback''').fetchone()
            data = dict(row) if row else {}
            return {k: int(data.get(k) or 0) for k in ('total', 'positive', 'negative')}
