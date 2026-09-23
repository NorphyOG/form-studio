from fastapi import APIRouter,Request,Depends,UploadFile,File,Form,HTTPException,Query
from fastapi.responses import FileResponse
from PIL import Image,ImageOps,UnidentifiedImageError
from io import BytesIO
import uuid
import warnings
from ..security import current_user,roles
from ..database import now

router=APIRouter()
MAX_BYTES=8*1024*1024
MAX_PIXELS=20_000_000

@router.get('/api/admin/media')
def listing(request: Request,limit:int=Query(80,ge=1,le=100),offset:int=Query(0,ge=0,le=1000000),q:str=Query('',max_length=80),user=Depends(current_user)):
    return request.app.state.db.all('SELECT * FROM media WHERE instr(lower(alt),lower(?))>0 ORDER BY created_at DESC,id LIMIT ? OFFSET ?',(q,limit,offset))

@router.post('/api/admin/media',status_code=201)
async def upload(request: Request,file: UploadFile=File(...),alt: str=Form(...),user=Depends(roles('admin','editor'))):
    if not 3 <= len(alt.strip()) <= 200:
        raise HTTPException(422,'Bitte einen Alternativtext mit 3–200 Zeichen eingeben.')
    raw=await file.read(MAX_BYTES+1)
    await file.close()
    if len(raw)>MAX_BYTES:
        raise HTTPException(413,'Bilder dürfen höchstens 8 MB groß sein.')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error',Image.DecompressionBombWarning)
            source=Image.open(BytesIO(raw))
            if source.format not in ('PNG','JPEG','WEBP') or source.width*source.height>MAX_PIXELS:
                raise ValueError('Nur PNG, JPEG oder WebP bis 20 Megapixel erlaubt.')
            source.load()
            image=ImageOps.exif_transpose(source).convert('RGB')
            image.thumbnail((2400,2400))
    except (UnidentifiedImageError,OSError,ValueError,Image.DecompressionBombError,Image.DecompressionBombWarning) as exc:
        raise HTTPException(422,'Ungültiges Bild. Erlaubt: JPG, PNG und WebP bis 20 Megapixel.') from exc
    identity=uuid.uuid4().hex
    filename=identity+'.webp'
    db=request.app.state.db
    path=db.media_dir/filename
    image.save(path,'WEBP',quality=88)  # Re-encoding strips metadata and rejects active formats.
    try:
        with db.connect(write=True) as con:
            con.execute('INSERT INTO media VALUES(?,?,?,?,?,?)',(identity,filename,alt.strip(),image.width,image.height,now()))
            db.audit(con,user['id'],'media_uploaded',identity)
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return {'id':identity,'filename':filename,'alt':alt,'width':image.width,'height':image.height}

@router.get('/media/{identity}')
def serve(identity: str,request: Request):
    db=request.app.state.db
    row=db.one('SELECT filename FROM media WHERE id=?',(identity,))
    if not row:
        raise HTTPException(404,'Bild nicht gefunden.')
    return FileResponse(db.media_dir/row['filename'],media_type='image/webp',headers={'Cache-Control':'public,max-age=86400'})

@router.get('/api/admin/media/{identity}')
def media_entry(identity:str,request:Request,user=Depends(current_user)):
    row=request.app.state.db.one('SELECT * FROM media WHERE id=?',(identity,))
    if not row:
        raise HTTPException(404,'Bild nicht gefunden.')
    return row
