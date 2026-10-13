# CampusMind Security Architecture

CampusMind uses defense in depth; it does not claim that any software is 100%
secure.

## Implemented controls

- HS256 JWT access tokens with short configurable expiry and persistent logout
  revocation.
- Argon2id password hashing; plaintext passwords are never stored.
- Student, faculty, hostel-manager and admin roles. Public registration can
  create only a student. Only an authenticated admin can create elevated users.
- Login failure tracking, temporary account lockout and auth endpoint limiting.
- Fernet authenticated encryption for stored chat messages and feedback
  comments. The encryption key is excluded from source control.
- Prompt-injection risk blocking before retrieval/generation.
- Per-IP and per-session chat rate limiting.
- Grounding, source verification and low-confidence escalation.
- Admin analytics requires an admin JWT and, when configured, `X-Admin-Key`.
- CSP, HSTS in production, anti-sniffing, clickjacking, referrer, permissions
  and cross-origin isolation headers.
- Restricted CORS and parameterized database operations.
- Security audit records for user creation, login failures/success and logout.

## First secure setup

1. Run `START_CAMPUSMIND.bat`; persistent JWT and Fernet keys are generated
   locally without printing them.
2. Run `.venv\Scripts\python.exe scripts\create_admin.py` once.
3. Change `AUTH_REQUIRED=true` in `.env` when every chat user must sign in.
4. Deploy only behind HTTPS and protect `.env`, database files and backups with
   operating-system access controls.

Rotating `FIELD_ENCRYPTION_KEY` without migrating old encrypted records makes
those records unreadable. Back up the key securely before rotation.
