from fastapi import APIRouter, Request, Response, Depends, HTTPException
import secrets
import sqlite3
from ..models import Credentials, SetupInput, UserInput, UserState
from ..security import HASHER, verify_password, current_user, roles, make_session, COOKIE, digest, check_rate
from ..database import now

router = APIRouter(prefix='/api')

@router.get('/setup-status')
def setup_status(request: Request):
    return {'setup_required': not bool(request.app.state.db.one('SELECT id FROM users LIMIT 1'))}

@router.post('/setup')
def setup(body: SetupInput, request: Request, response: Response):
    check_rate(request,'setup',8,600)
    db = request.app.state.db
    keyfile = db.data_dir / '.setup-key'
    key = keyfile.read_text().strip() if keyfile.exists() else ''
    if not key or not secrets.compare_digest(body.setup_key,key):
        raise HTTPException(403,'Der Einrichtungscode ist ungültig. Er steht im lokalen Startfenster.')
    password_hash = HASHER.hash(body.password)
    with db.connect(write=True) as con:
        if con.execute('SELECT 1 FROM users LIMIT 1').fetchone():
            raise HTTPException(409,'Die Ersteinrichtung ist bereits abgeschlossen.')
        cursor = con.execute('INSERT INTO users(name,email,password_hash,role,created_at) VALUES(?,?,?,?,?)',
            (body.name,body.email,password_hash,'admin',now()))
        uid = cursor.lastrowid
        db.audit(con,uid,'setup','users')
    keyfile.unlink(missing_ok=True)
    make_session(request,response,uid)
    return {'ok':True}

@router.post('/login')
def login(body: Credentials, request: Request, response: Response):
    check_rate(request,'login',15,600)
    db = request.app.state.db
    user = db.one('SELECT * FROM users WHERE email=? AND active=1',(body.email.lower(),))
    valid = verify_password(user['password_hash'] if user else None,body.password)
    if not user or not valid:
        raise HTTPException(401,'E-Mail-Adresse oder Passwort ist nicht korrekt.')
    # Rotate rather than reusing an existing session identifier.
    old = request.cookies.get(COOKIE)
    if old:
        with db.connect(write=True) as con:
            con.execute('DELETE FROM sessions WHERE token_hash=?',(digest(old),))
    csrf = make_session(request,response,user['id'])
    return {'ok':True,'csrf':csrf}

@router.get('/admin/session')
def session(user=Depends(current_user)):
    return user

@router.post('/admin/logout')
def logout(request: Request, response: Response, user=Depends(current_user)):
    with request.app.state.db.connect(write=True) as con:
        con.execute('DELETE FROM sessions WHERE token_hash=?',(digest(request.cookies.get(COOKIE,'')),))
    response.delete_cookie(COOKIE,path='/')
    return {'ok':True}

@router.get('/admin/users')
def users(request: Request, user=Depends(roles('admin'))):
    return request.app.state.db.all('SELECT id,name,email,role,active,created_at FROM users ORDER BY id')

@router.post('/admin/users')
def create_user(body: UserInput,request: Request,user=Depends(roles('admin'))):
    db = request.app.state.db
    hashed = HASHER.hash(body.password)
    try:
        with db.connect(write=True) as con:
            cursor = con.execute('INSERT INTO users(name,email,password_hash,role,created_at) VALUES(?,?,?,?,?)',
                (body.name,body.email,hashed,body.role,now()))
            db.audit(con,user['id'],'user_created',str(cursor.lastrowid))
    except sqlite3.IntegrityError as exc:
        raise HTTPException(409,'Diese E-Mail-Adresse existiert bereits.') from exc
    return {'ok':True}

@router.patch('/admin/users/{identity}')
def change_user(identity: int,body: UserState,request: Request,user=Depends(roles('admin'))):
    if identity == user['id']:
        raise HTTPException(409,'Das eigene aktive Konto kann hier nicht deaktiviert werden.')
    db = request.app.state.db
    with db.connect(write=True) as con:
        if not con.execute('SELECT 1 FROM users WHERE id=?',(identity,)).fetchone():
            raise HTTPException(404,'Konto nicht gefunden.')
        con.execute('UPDATE users SET active=? WHERE id=?',(int(body.active),identity))
        if not body.active:
            con.execute('DELETE FROM sessions WHERE user_id=?',(identity,))
        db.audit(con,user['id'],'user_activated' if body.active else 'user_deactivated',str(identity))
    return {'ok':True}
