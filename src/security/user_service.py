from __future__ import annotations
import json
from datetime import datetime, timedelta, timezone
from src.database.db_manager import DatabaseManager
from .auth import hash_password, verify_password, create_token
from config import config

class UserService:
    def __init__(self,db=None):self.db=db or DatabaseManager()
    @property
    def mark(self):return '%s' if self.db.is_postgres else '?'
    def _row(self,cursor,row):
        if not row:return None
        names=[d.name if hasattr(d,'name') else d[0] for d in cursor.description];return dict(zip(names,row))
    def audit(self,actor,action,target='',details=None):
        m=self.mark
        with self.db.get_connection() as c:c.execute(f'INSERT INTO security_audit_log(actor_user_id,action,target,details) VALUES ({m},{m},{m},{m})',(actor,action,target,json.dumps(details or {})))
    def create(self,username,password,role='student'):
        m=self.mark; returning=' RETURNING id' if self.db.is_postgres else ''
        with self.db.get_connection() as c:
            cur=c.execute(f'INSERT INTO users(username,password_hash,role) VALUES ({m},{m},{m}){returning}',(username.lower(),hash_password(password),role))
            uid=cur.fetchone()[0] if self.db.is_postgres else cur.lastrowid
        self.audit(uid,'user.created',username,{'role':role});return int(uid)
    def find(self,username):
        m=self.mark
        with self.db.get_connection() as c:
            cur=c.execute(f'SELECT * FROM users WHERE username={m}',(username.lower(),));return self._row(cur,cur.fetchone())
    def authenticate(self,username,password):
        user=self.find(username)
        if not user or not user['is_active']:return None
        locked=user.get('locked_until')
        if locked:
            if isinstance(locked,str):locked=datetime.fromisoformat(locked.replace('Z','+00:00'))
            if locked.tzinfo is None:locked=locked.replace(tzinfo=timezone.utc)
            if locked>datetime.now(timezone.utc):return None
        m=self.mark
        if not verify_password(password,user['password_hash']):
            failures=int(user.get('failed_attempts') or 0)+1
            until=datetime.now(timezone.utc)+timedelta(minutes=config.LOGIN_LOCKOUT_MINUTES) if failures>=config.LOGIN_MAX_FAILURES else None
            with self.db.get_connection() as c:c.execute(f'UPDATE users SET failed_attempts={m},locked_until={m} WHERE id={m}',(failures,until,user['id']))
            self.audit(user['id'],'login.failed',username,{'locked':bool(until)});return None
        with self.db.get_connection() as c:c.execute(f'UPDATE users SET failed_attempts=0,locked_until=NULL WHERE id={m}',(user['id'],))
        self.audit(user['id'],'login.success',username);return {'access_token':create_token(user['id'],user['role']),'token_type':'bearer','role':user['role']}
