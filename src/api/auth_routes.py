from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from src.security.auth import get_current_user, require_roles, ROLES
from datetime import datetime, timezone
from src.security.user_service import UserService
from src.api.rate_limiter import SlidingWindowRateLimiter
from config import config

router=APIRouter(prefix='/auth',tags=['authentication']);users=UserService()
auth_limiter=SlidingWindowRateLimiter(config.LOGIN_MAX_FAILURES*2,60)
class RegisterRequest(BaseModel):
    username:str=Field(min_length=3,max_length=128,pattern=r'^[A-Za-z0-9_.@-]+$')
    password:str=Field(min_length=10,max_length=256)
class LoginRequest(BaseModel):
    username:str;password:str
class ManagedUserRequest(RegisterRequest):
    role:str

@router.post('/register',status_code=201)
def register(payload:RegisterRequest,request:Request):
    if not auth_limiter.check('register:'+request.client.host if request.client else 'register:unknown')[0]:raise HTTPException(429,'Too many registration attempts')
    if users.find(payload.username):raise HTTPException(409,'Username already exists')
    try:uid=users.create(payload.username,payload.password,'student')
    except Exception:raise HTTPException(409,'Username already exists')
    return {'id':uid,'username':payload.username.lower(),'role':'student'}

@router.post('/login')
def login(payload:LoginRequest,request:Request):
    if not auth_limiter.check('login:'+request.client.host if request.client else 'login:unknown')[0]:raise HTTPException(429,'Too many login attempts')
    result=users.authenticate(payload.username,payload.password)
    if not result:raise HTTPException(401,'Invalid credentials or account temporarily locked')
    return result

@router.get('/me')
def me(user=Depends(get_current_user)):return {'user_id':user['sub'],'role':user['role']}

@router.post('/logout')
def logout(user=Depends(get_current_user)):
    m=users.mark
    with users.db.get_connection() as c:
        c.execute(f'INSERT INTO revoked_tokens(jti,expires_at) VALUES ({m},{m}) ON CONFLICT (jti) DO NOTHING' if users.db.is_postgres else f'INSERT OR IGNORE INTO revoked_tokens(jti,expires_at) VALUES ({m},{m})',(user['jti'],datetime.fromtimestamp(user['exp'],timezone.utc)))
    users.audit(int(user['sub']),'logout','token',{'jti':user['jti']})
    return {'status':'logged_out'}

@router.post('/users',status_code=201)
def create_managed_user(payload:ManagedUserRequest,admin=Depends(require_roles('admin'))):
    if payload.role not in ROLES:raise HTTPException(400,'Invalid role')
    uid=users.create(payload.username,payload.password,payload.role)
    users.audit(int(admin['sub']),'admin.user_created',payload.username,{'role':payload.role})
    return {'id':uid,'username':payload.username.lower(),'role':payload.role}
