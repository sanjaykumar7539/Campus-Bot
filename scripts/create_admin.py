"""Interactively create the first admin without storing a plaintext password."""
from pathlib import Path
import getpass,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.security.user_service import UserService

users=UserService();username=input('Admin username: ').strip();password=getpass.getpass('Admin password (10+ characters): ')
if len(password)<10:raise SystemExit('Password is too short.')
if users.find(username):raise SystemExit('Username already exists.')
uid=users.create(username,password,'admin');print(f'Admin created securely (id={uid}).')
