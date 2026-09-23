"""Stateless draft rendering and shared block presets, always authenticated."""
import json
import uuid
from fastapi import APIRouter,Request,Depends,HTTPException
from ..security import current_user,roles
from ..models import ContentInput,ReusableInput
from ..content import checked
from ..database import now,encode
from ..catalog import catalog
from .public import render_page,detail,render_article,render_campaign

router=APIRouter(prefix='/api/admin')

@router.get('/catalog')
def get_catalog(user=Depends(current_user)):
    return catalog()

@router.post('/preview')
def preview(body:ContentInput,request:Request,user=Depends(current_user)):
    """Validate and render, but never save, audit, publish or change a revision."""
    data=checked(body.kind,body.data)
    if body.kind=='page':
        response=render_page(request,data,True)
    elif body.kind in ('service','project'):
        response=detail(request,body.kind,data['slug'],data,True)
    elif body.kind=='article':
        response=render_article(request,data,True)
    elif body.kind=='campaign':
        response=render_campaign(request,data)
    else:
        raise HTTPException(422,'Globale Einstellungen haben keine eigenständige Seitenvorschau.')
    return {'html':response.body.decode('utf-8')}

@router.get('/block-presets')
def presets(request:Request,user=Depends(current_user)):
    rows=request.app.state.db.all('SELECT * FROM block_presets ORDER BY created_at DESC,id')
    return [dict(r,block=json.loads(r['block'])) for r in rows]

@router.post('/block-presets')
def save_preset(body:ReusableInput,request:Request,user=Depends(roles('admin','editor'))):
    db=request.app.state.db
    identity=uuid.uuid4().hex
    with db.connect(write=True) as con:
        if con.execute('SELECT count(*) FROM block_presets').fetchone()[0]>=100:
            raise HTTPException(409,'Die Bibliothek enthält bereits 100 Vorlagen. Bitte nicht mehr benötigte Vorlagen entfernen.')
        con.execute('INSERT INTO block_presets VALUES(?,?,?,?,?)',(identity,body.name,encode(body.block.model_dump()),user['id'],now()))
        db.audit(con,user['id'],'preset_created',identity)
    return {'id':identity,'name':body.name,'block':body.block.model_dump(),'created_by':user['id']}

@router.delete('/block-presets/{identity}')
def delete_preset(identity:str,request:Request,user=Depends(roles('admin','editor'))):
    db=request.app.state.db
    with db.connect(write=True) as con:
        row=con.execute('SELECT created_by FROM block_presets WHERE id=?',(identity,)).fetchone()
        if not row:
            raise HTTPException(404,'Vorlage nicht gefunden.')
        if user['role']!='admin' and row['created_by']!=user['id']:
            raise HTTPException(403,'Nur eigene Vorlagen können entfernt werden.')
        con.execute('DELETE FROM block_presets WHERE id=?',(identity,))
        db.audit(con,user['id'],'preset_deleted',identity)
    return {'ok':True}
