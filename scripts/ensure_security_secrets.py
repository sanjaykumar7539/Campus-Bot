"""Create persistent local security secrets once; never prints secret values."""
from pathlib import Path
import secrets

ROOT=Path(__file__).resolve().parents[1];env=ROOT/'.env';text=env.read_text(encoding='utf-8') if env.exists() else ''
updates={}
values={line.split('=',1)[0]:line.split('=',1)[1] for line in text.splitlines() if '=' in line and not line.lstrip().startswith('#')}
if len(values.get('JWT_SECRET','').strip())<32:updates['JWT_SECRET']=secrets.token_urlsafe(48)
if not values.get('FIELD_ENCRYPTION_KEY','').strip():
    from cryptography.fernet import Fernet
    updates['FIELD_ENCRYPTION_KEY']=Fernet.generate_key().decode()
if updates:
    lines=text.splitlines()
    for key,value in updates.items():
        replaced=False
        for i,line in enumerate(lines):
            if line.startswith(key+'='):lines[i]=key+'='+value;replaced=True;break
        if not replaced:lines.append(key+'='+value)
    env.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('Security secrets initialized securely in .env.')
else:print('Security secrets already configured.')
