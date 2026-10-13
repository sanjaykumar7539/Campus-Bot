from __future__ import annotations
from datetime import datetime, timedelta, timezone
from uuid import uuid4
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from config import config

ROLES={'student','faculty','hostel_manager','admin'}
ROLE_PERMISSIONS={'student':{'chat:use'},'faculty':{'chat:use','notices:internal'},
 'hostel_manager':{'chat:use','hostel:manage'},'admin':{'*'}}
hasher=PasswordHasher(); bearer=HTTPBearer(auto_error=False)

def hash_password(password): return hasher.hash(password)
def verify_password(password,digest):
    try:return hasher.verify(digest,password)
    except VerifyMismatchError:return False
def create_token(user_id,role):
    now=datetime.now(timezone.utc);jti=str(uuid4())
    payload={'sub':str(user_id),'role':role,'jti':jti,'iat':now,'exp':now+timedelta(minutes=config.JWT_EXPIRE_MINUTES)}
    return jwt.encode(payload,config.JWT_SECRET,algorithm='HS256')
def decode_token(token):
    try:
        payload=jwt.decode(token,config.JWT_SECRET,algorithms=['HS256'])
        from src.database.db_manager import DatabaseManager
        db=DatabaseManager();mark='%s' if db.is_postgres else '?'
        with db.get_connection() as c:
            if c.execute(f'SELECT 1 FROM revoked_tokens WHERE jti={mark}',(payload['jti'],)).fetchone():
                raise HTTPException(401,'Access token has been revoked')
        return payload
    except jwt.PyJWTError:raise HTTPException(401,'Invalid or expired access token',headers={'WWW-Authenticate':'Bearer'})
def get_current_user(credentials:HTTPAuthorizationCredentials|None=Depends(bearer)):
    if not credentials:raise HTTPException(401,'Authentication required',headers={'WWW-Authenticate':'Bearer'})
    return decode_token(credentials.credentials)
def require_roles(*roles):
    def dependency(user=Depends(get_current_user)):
        if user.get('role') not in roles:raise HTTPException(403,'Insufficient role permission')
        return user
    return dependency
