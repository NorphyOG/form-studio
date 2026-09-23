"""Server-side sessions, CSRF validation, role checks and rate-limit helpers."""
import hashlib
import secrets
from fastapi import Request, HTTPException
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
from .database import now

HASHER = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=2)
DUMMY_HASH = HASHER.hash(secrets.token_urlsafe(32))
COOKIE = 'studio_session'

def digest(token):
    return hashlib.sha256(token.encode()).hexdigest()

def verify_password(stored, password):
    try:
        return HASHER.verify(stored or DUMMY_HASH, password)
    except (VerifyMismatchError, VerificationError):
        return False

def check_rate(request, category, limit=15, seconds=600):
    # Never trust a client-supplied X-Forwarded-For header here.
    address = request.client.host if request.client else 'unknown'
    if not request.app.state.db.rate(digest(category+':'+address), limit, seconds):
        raise HTTPException(429, 'Zu viele Versuche. Bitte später erneut versuchen.', headers={'Retry-After': str(seconds)})

def current_user(request: Request):
    token = request.cookies.get(COOKIE, '')
    if not token:
        raise HTTPException(401, 'Bitte zuerst anmelden.')
    row = request.app.state.db.one(
        'SELECT u.id,u.name,u.email,u.role,s.csrf,s.expires FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token_hash=? AND u.active=1 AND s.expires>?',
        (digest(token), now()))
    if not row:
        raise HTTPException(401, 'Die Sitzung ist abgelaufen. Bitte erneut anmelden.')
    if request.method not in ('GET', 'HEAD', 'OPTIONS'):
        if not secrets.compare_digest(request.headers.get('X-CSRF-Token', ''), row['csrf']):
            raise HTTPException(403, 'Ungültiger Sicherheitstoken. Bitte neu anmelden.')
    return row

def roles(*allowed):
    def dependency(request: Request):
        user = current_user(request)
        if user['role'] not in allowed:
            raise HTTPException(403, 'Für diese Aktion fehlt die Berechtigung.')
        return user
    return dependency

def make_session(request, response, user_id):
    token = secrets.token_urlsafe(40)
    csrf = secrets.token_urlsafe(32)
    expiry = now()+8*3600
    with request.app.state.db.connect(write=True) as con:
        con.execute('DELETE FROM sessions WHERE expires<?', (now(),))
        con.execute('INSERT INTO sessions VALUES(?,?,?,?)', (digest(token), user_id, csrf, expiry))
    response.set_cookie(COOKIE, token, httponly=True, secure=request.app.state.settings.secure_cookies,
                        samesite='strict', max_age=8*3600, path='/')
    return csrf
