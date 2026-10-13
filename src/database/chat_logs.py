import json
from typing import Dict, List, Optional
from .db_manager import DatabaseManager
from src.security.crypto import FieldCipher


class ChatLogger:
    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or DatabaseManager()
        self.cipher = FieldCipher()

    def ensure_session(self, session_id: str, user_id: str | None = None):
        with self.db.get_connection() as conn:
            if self.db.is_postgres:
                conn.execute('INSERT INTO chat_sessions (session_id,user_id) VALUES (%s,%s) ON CONFLICT (session_id) DO NOTHING',(session_id,user_id))
            else:
                conn.execute('INSERT OR IGNORE INTO chat_sessions (session_id, user_id) VALUES (?, ?)',(session_id,user_id))
            if user_id:
                q='UPDATE chat_sessions SET user_id = COALESCE(user_id, %s) WHERE session_id = %s' if self.db.is_postgres else 'UPDATE chat_sessions SET user_id = COALESCE(user_id, ?) WHERE session_id = ?'
                conn.execute(q,(user_id,session_id))

    def log(self, session_id: str, user_id: str, query: str, answer: str, sources: List[Dict], confidence: float) -> int:
        self.ensure_session(session_id, user_id)
        with self.db.get_connection() as conn:
            mark='%s' if self.db.is_postgres else '?'
            conn.execute(
                f'INSERT INTO messages (session_id, role, content, confidence) VALUES ({mark}, {mark}, {mark}, {mark})',
                (session_id, 'user', self.cipher.encrypt(query), confidence),
            )
            sources_json = json.dumps(sources, ensure_ascii=False) if sources else None
            returning=' RETURNING id' if self.db.is_postgres else ''
            cursor = conn.execute(
                f'INSERT INTO messages (session_id, role, content, sources, confidence) VALUES ({mark}, {mark}, {mark}, {mark}, {mark}){returning}',
                (session_id, 'bot', self.cipher.encrypt(answer), sources_json, confidence),
            )
            return int(cursor.fetchone()[0] if self.db.is_postgres else cursor.lastrowid)

    def get_session_logs(self, session_id: str) -> List[Dict]:
        with self.db.get_connection() as conn:
            q='SELECT * FROM messages WHERE session_id = %s ORDER BY id' if self.db.is_postgres else 'SELECT * FROM messages WHERE session_id = ? ORDER BY id'
            cursor=conn.execute(q,(session_id,)); rows=cursor.fetchall()
            if self.db.is_postgres:
                names=[d.name for d in cursor.description]; result=[dict(zip(names,row)) for row in rows]
            else:
                result=[dict(row) for row in rows]
            for item in result:item['content']=self.cipher.decrypt(item.get('content'))
            return result
