"""Modular monolith entrypoint: no external services or build step required at runtime."""
from pathlib import Path
from urllib.parse import urlparse
import os
import secrets
from fastapi import FastAPI,Request,HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from .config import Settings,ROOT
from .database import Database
from .seed import seed
from .analytics import AnalyticsRuntime
from .routers import auth,editorial,inquiries,media,public,builder,analytics

class BodyLimitMiddleware:
    """Bound request buffering, including requests without Content-Length."""
    def __init__(self,app,limit=9*1024*1024):
        self.app,self.limit=app,limit

    async def __call__(self,scope,receive,send):
        if scope['type']!='http' or scope['method'] not in ('POST','PATCH','PUT','DELETE'):
            return await self.app(scope,receive,send)
        chunks=[]
        size=0
        while True:
            event=await receive()
            if event['type']=='http.disconnect':
                return
            chunk=event.get('body',b'')
            size+=len(chunk)
            if size>self.limit:
                return await JSONResponse({'detail':'Die Anfrage ist zu groß.'},status_code=413)(scope,receive,send)
            chunks.append(chunk)
            if not event.get('more_body',False):
                break
        sent=False
        async def buffered_receive():
            nonlocal sent
            if not sent:
                sent=True
                return {'type':'http.request','body':b''.join(chunks),'more_body':False}
            return await receive()
        await self.app(scope,buffered_receive,send)

def create_app(settings: Settings|None=None):
    settings=settings or Settings.from_env()
    db=Database(settings.data_dir)
    db.init()
    if settings.demo_content:
        seed(db)
    if not db.one('SELECT id FROM users LIMIT 1'):
        keyfile=db.data_dir/'.setup-key'
        try:
            descriptor=os.open(keyfile,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
            with os.fdopen(descriptor,'w') as f:
                f.write(secrets.token_urlsafe(32))
        except FileExistsError:
            pass
    app=FastAPI(title='Form Studio CMS',version='0.4.0',docs_url=None,redoc_url=None,openapi_url=None)
    app.state.db=db
    app.state.settings=settings
    app.state.analytics=AnalyticsRuntime()
    host=urlparse(settings.origin).hostname
    app.add_middleware(TrustedHostMiddleware,allowed_hosts=[host,'127.0.0.1','localhost'])
    app.add_middleware(BodyLimitMiddleware)

    @app.middleware('http')
    async def security_headers(request: Request,call_next):
        if request.method not in ('GET','HEAD','OPTIONS'):
            origin=request.headers.get('origin','')
            if origin!=settings.origin:
                return JSONResponse({'detail':'Die Anfrage stammt nicht von der konfigurierten Website.'},status_code=403)
        response=await call_next(request)
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['Referrer-Policy']='same-origin'
        response.headers['X-Frame-Options']='SAMEORIGIN'
        response.headers['Permissions-Policy']='camera=(), microphone=(), geolocation=()'
        response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'self'; object-src 'none'; base-uri 'self'; form-action 'self'"
        if request.url.path.startswith(('/admin','/api')):
            response.headers['Cache-Control']='no-store'
            response.headers['X-Robots-Tag']='noindex, nofollow'
        if settings.secure_cookies:
            response.headers['Strict-Transport-Security']='max-age=31536000'
        return response

    @app.get('/api/health')
    def health():
        return {'status':'ok','version':'0.4.0'}

    app.include_router(auth.router)
    app.include_router(editorial.router)
    app.include_router(inquiries.router)
    app.include_router(media.router)
    app.include_router(builder.router)
    app.include_router(analytics.router)
    app.mount('/static',StaticFiles(directory=ROOT/'static'),name='static')
    app.include_router(public.router)

    @app.exception_handler(StarletteHTTPException)
    async def exception(request: Request,exc: HTTPException):
        if exc.status_code==404 and not request.url.path.startswith('/api'):
            ctx=public.context(request)
            ctx.update(title='Seite nicht gefunden',description='',canonical=request.url.path)
            return public.templates.TemplateResponse(request,'404.html',ctx,status_code=404)
        return JSONResponse({'detail':exc.detail},status_code=exc.status_code,headers=exc.headers)
    return app
