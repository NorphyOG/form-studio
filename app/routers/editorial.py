from fastapi import APIRouter, Request, Depends, HTTPException, Query
from ..security import current_user,roles
from ..models import ContentInput,ContentUpdate,Action
from ..content import list_content,create_content,mutate_content,record,content_index

router=APIRouter(prefix='/api/admin')

@router.get('/content')
def listing(request: Request,kind: str|None=None,limit:int=Query(100,ge=1,le=100),offset:int=Query(0,ge=0,le=1000000),state:str|None=None,user=Depends(current_user)):
    return list_content(request.app.state.db,kind,limit,offset,state)

@router.get('/content-index')
def index(request:Request,kind:str|None=None,state:str|None=None,q:str=Query('',max_length=80),
          limit:int=Query(24,ge=1,le=100),offset:int=Query(0,ge=0,le=1000000),user=Depends(current_user)):
    return content_index(request.app.state.db,kind,state,q,limit,offset)

@router.get('/content/{identity}')
def get_content(identity:str,request:Request,user=Depends(current_user)):
    return record(request.app.state.db.one('SELECT * FROM content WHERE id=? AND archived=0',(identity,)))

@router.post('/content')
def create(body: ContentInput,request: Request,user=Depends(roles('admin','editor'))):
    if body.kind=='settings' and user['role']!='admin':
        raise HTTPException(403,'Globale Einstellungen sind Administratoren vorbehalten.')
    return create_content(request.app.state.db,body.kind,body.data,user['id'])

@router.patch('/content/{identity}')
def update(identity: str,body: ContentUpdate,request: Request,user=Depends(roles('admin','editor'))):
    db=request.app.state.db
    row=record(db.one('SELECT * FROM content WHERE id=? AND archived=0',(identity,)))
    if row['kind']=='settings' and user['role']!='admin':
        raise HTTPException(403,'Globale Einstellungen sind Administratoren vorbehalten.')
    return mutate_content(db,identity,'save',body.expected_revision,user['id'],data=body.data)

@router.get('/content/{identity}/history')
def history(identity: str,request: Request,user=Depends(current_user)):
    rows=request.app.state.db.all('SELECT r.revision,r.action,r.created_at,u.name FROM revisions r LEFT JOIN users u ON u.id=r.user_id WHERE content_id=? ORDER BY revision DESC LIMIT 100',(identity,))
    return rows

@router.post('/content/{identity}/restore/{revision}')
def restore(identity: str,revision: int,body: Action,request: Request,user=Depends(roles('admin','editor'))):
    db=request.app.state.db
    row=record(db.one('SELECT * FROM content WHERE id=?',(identity,)))
    if row['kind']=='settings' and user['role']!='admin':
        raise HTTPException(403,'Keine Berechtigung.')
    return mutate_content(db,identity,'restore',body.expected_revision,user['id'],restore_revision=revision)

@router.post('/content/{identity}/{action}')
def transition(identity: str,action: str,body: Action,request: Request,user=Depends(current_user)):
    permissions={'submit':('admin','editor'),'publish':('admin','moderator'),'reject':('admin','moderator'),
        'unpublish':('admin','moderator'),'archive':('admin',)}
    if action not in permissions:
        raise HTTPException(404,'Unbekannte Aktion.')
    if user['role'] not in permissions[action]:
        raise HTTPException(403,'Für diesen Redaktionsschritt fehlt die Berechtigung.')
    db=request.app.state.db
    row=record(db.one('SELECT * FROM content WHERE id=?',(identity,)))
    if row['kind']=='settings' and user['role']!='admin':
        raise HTTPException(403,'Globale Einstellungen sind Administratoren vorbehalten.')
    if user['role']=='moderator' and action=='publish' and row['state']!='pending':
        raise HTTPException(409,'Moderatoren können nur eingereichte Inhalte freigeben.')
    return mutate_content(db,identity,action,body.expected_revision,user['id'],note=body.note)

@router.get('/overview')
def overview(request: Request,user=Depends(current_user)):
    db=request.app.state.db
    counts=db.one("SELECT count(published) published,coalesce(sum(state IN ('draft','rejected')),0) drafts,"
                  "coalesce(sum(state='pending'),0) pending FROM content WHERE archived=0")
    return {**counts,'new_inquiries':db.one("SELECT count(*) n FROM inquiries WHERE status='new'")['n'],
            'recent':content_index(db,limit=6)['items']}

@router.get('/audit')
def audit(request: Request,user=Depends(roles('admin'))):
    return request.app.state.db.all('SELECT a.id,a.action,a.target,a.created_at,u.name FROM audit a LEFT JOIN users u ON u.id=a.user_id ORDER BY a.id DESC LIMIT 100')
