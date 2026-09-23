from fastapi import APIRouter,Request,Depends,HTTPException,Query
import uuid
from ..models import Inquiry,InquiryStatus
from ..security import roles,check_rate
from ..database import now

router=APIRouter()

@router.post('/api/inquiries',status_code=201)
def send(body: Inquiry,request: Request):
    check_rate(request,'inquiry',6,3600)
    if body.website:
        # Return the same shape without accepting the spam submission.
        return {'ok':True}
    db=request.app.state.db
    with db.connect(write=True) as con:
        con.execute('INSERT INTO inquiries(id,name,email,service,message,created_at) VALUES(?,?,?,?,?,?)',
            (uuid.uuid4().hex,body.name,body.email,body.service,body.message,now()))
    return {'ok':True}

@router.get('/api/admin/inquiries')
def listing(request: Request,limit:int=Query(100,ge=1,le=100),offset:int=Query(0,ge=0,le=1000000),user=Depends(roles('admin','moderator'))):
    return request.app.state.db.all('SELECT * FROM inquiries ORDER BY created_at DESC,id LIMIT ? OFFSET ?',(limit,offset))

@router.patch('/api/admin/inquiries/{identity}')
def update(identity: str,body: InquiryStatus,request: Request,user=Depends(roles('admin','moderator'))):
    db=request.app.state.db
    with db.connect(write=True) as con:
        if not con.execute('SELECT 1 FROM inquiries WHERE id=?',(identity,)).fetchone():
            raise HTTPException(404,'Anfrage nicht gefunden.')
        con.execute('UPDATE inquiries SET status=? WHERE id=?',(body.status,identity))
        db.audit(con,user['id'],'inquiry_'+body.status,identity)
    return {'ok':True}

@router.delete('/api/admin/inquiries/{identity}')
def delete(identity: str,request: Request,user=Depends(roles('admin'))):
    db=request.app.state.db
    with db.connect(write=True) as con:
        con.execute('DELETE FROM inquiries WHERE id=?',(identity,))
        db.audit(con,user['id'],'inquiry_deleted',identity)
    return {'ok':True}
