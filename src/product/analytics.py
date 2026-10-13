from __future__ import annotations
from src.database.db_manager import DatabaseManager


class ProductAnalytics:
    """Privacy-conscious local operational analytics. No external telemetry is sent."""
    def __init__(self, db: DatabaseManager | None = None):
        self.db = db or DatabaseManager()

    def summary(self) -> dict:
        with self.db.get_connection() as conn:
            sessions = int(conn.execute("SELECT COUNT(*) FROM chat_sessions").fetchone()[0] or 0)
            user_messages = int(conn.execute("SELECT COUNT(*) FROM messages WHERE role='user'").fetchone()[0] or 0)
            bot_messages = int(conn.execute("SELECT COUNT(*) FROM messages WHERE role='bot'").fetchone()[0] or 0)
            avg_conf = conn.execute("SELECT AVG(confidence) FROM messages WHERE role='bot'").fetchone()[0]
            feedback = conn.execute("SELECT COUNT(*), SUM(CASE WHEN rating=1 THEN 1 ELSE 0 END), SUM(CASE WHEN rating=-1 THEN 1 ELSE 0 END) FROM feedback").fetchone()
        total_fb, positive, negative = [int(x or 0) for x in feedback]
        return {
            "sessions": sessions,
            "user_messages": user_messages,
            "bot_messages": bot_messages,
            "average_confidence": round(float(avg_conf or 0.0), 4),
            "feedback_total": total_fb,
            "feedback_positive": positive,
            "feedback_negative": negative,
            "positive_feedback_rate": round(positive / total_fb, 4) if total_fb else None,
        }
