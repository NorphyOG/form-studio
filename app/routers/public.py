"""Server-rendered public pages. Read only relevant content and media per request."""
import json
from html import escape
from urllib.parse import urlencode
from fastapi import APIRouter, Request, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse, PlainTextResponse, Response
from fastapi.templating import Jinja2Templates
from ..config import ROOT
from ..security import current_user
from ..content import public_items, public_entry, record
from ..collections import news_list, active_campaign, media_for

router = APIRouter()
templates = Jinja2Templates(directory=str(ROOT/'templates'))


def context(request):
    db = request.app.state.db
    settings = public_entry(db, 'settings', 'site') or dict(brand='FORM / STUDIO', tagline='Independent digital studio', accent='blue', location='Design. Technologie. Wirkung.', email='')
    home = public_entry(db, 'page', 'home') or {}
    labels = {'bento': 'Leistungen', 'projects': 'Arbeiten', 'process': 'Studio'}
    navigation, seen = [], set()
    for block in home.get('blocks', []):
        kind = block['type']
        if block.get('enabled', True) and kind in labels and kind not in seen:
            navigation.append(dict(label=labels[kind], href='/#'+block['id']))
            seen.add(kind)
    nav_rows = db.all("SELECT published_slug,json_extract(published,'$.title') title,json_extract(published,'$.navigation_label') label "
                      "FROM content WHERE kind='page' AND published IS NOT NULL AND archived=0 AND json_extract(published,'$.in_navigation')=1 "
                      "AND published_slug!='home' ORDER BY json_extract(published,'$.order'),id LIMIT 24")
    navigation.extend(dict(label=r['label'] or r['title'], href='/p/'+r['published_slug']) for r in nav_rows)
    if settings.get('news_in_navigation', True):
        navigation.append(dict(label='Journal', href='/news'))
    return dict(request=request, site=settings, navigation=navigation, services=[], projects=[],
                media={}, preview=False, news_by_block={}, campaigns_by_block={},
                origin=request.app.state.settings.origin)


def block_context(request, ctx, entry):
    db = request.app.state.db
    blocks = [b for b in entry.get('blocks', []) if b.get('enabled', True)]
    if any(b['type'] == 'bento' for b in blocks):
        ctx['services'] = public_items(db, 'service', limit=7)
    if any(b['type'] == 'projects' for b in blocks):
        ctx['projects'] = public_items(db, 'project', limit=24)
    for block in blocks:
        if block['type'] == 'news':
            ctx['news_by_block'][block['id']] = news_list(db, block.get('limit', 6), category=block.get('category', ''))['items']
        elif block['type'] == 'advert':
            ctx['campaigns_by_block'][block['id']] = active_campaign(db, block.get('campaign', ''))
    ctx['media'] = media_for(db, entry, ctx['services'], ctx['projects'],
                             list(ctx['news_by_block'].values()), list(ctx['campaigns_by_block'].values()))


def render_page(request, page, preview=False):
    ctx = context(request)
    works = next((b['id'] for b in page.get('blocks', []) if b['type'] == 'projects' and b.get('enabled', True)), None)
    ctx['works_anchor'] = '#'+works if works else '/kontakt'
    block_context(request, ctx, page)
    ctx.update(page=page, preview=preview, title=page['title'], description=page.get('description', ''),
               canonical='/' if page['slug'] == 'home' else '/p/'+page['slug'])
    return templates.TemplateResponse(request, 'page.html', ctx)


@router.get('/', response_class=HTMLResponse)
def home(request: Request):
    page = public_entry(request.app.state.db, 'page', 'home')
    if not page:
        return templates.TemplateResponse(request, 'unpublished.html', context(request), status_code=503)
    return render_page(request, page)


@router.get('/p/{slug}', response_class=HTMLResponse)
def page(slug: str, request: Request):
    entry = public_entry(request.app.state.db, 'page', slug)
    if not entry:
        raise HTTPException(404, 'Diese Seite ist noch nicht veröffentlicht.')
    return render_page(request, entry)


@router.get('/leistungen/{slug}', response_class=HTMLResponse)
def service(slug: str, request: Request):
    return detail(request, 'service', slug)


@router.get('/arbeiten/{slug}', response_class=HTMLResponse)
def project(slug: str, request: Request):
    return detail(request, 'project', slug)


def detail(request, kind, slug, data=None, preview=False):
    entry = data or public_entry(request.app.state.db, kind, slug)
    if not entry:
        raise HTTPException(404, 'Dieser Inhalt ist noch nicht veröffentlicht.')
    ctx = context(request)
    ctx.update(entry=entry, kind=kind, preview=preview, title=entry['title'], description=entry['description'],
               media=media_for(request.app.state.db, entry), canonical=('/leistungen/' if kind == 'service' else '/arbeiten/')+slug)
    return templates.TemplateResponse(request, 'detail.html', ctx)


@router.get('/leistungen', response_class=HTMLResponse)
@router.get('/arbeiten', response_class=HTMLResponse)
def collection_archive(request: Request, page: int = Query(1, ge=1, le=100000)):
    kind = 'service' if request.url.path == '/leistungen' else 'project'
    db = request.app.state.db
    total = db.one("SELECT count(*) n FROM content WHERE kind=? AND published IS NOT NULL AND archived=0", (kind,))['n']
    rows = db.all("SELECT published_slug,json_extract(published,'$.title') title,json_extract(published,'$.description') description,json_extract(published,'$.image') image,json_extract(published,'$.art') art FROM content WHERE kind=? AND published IS NOT NULL AND archived=0 ORDER BY json_extract(published,'$.order'),id LIMIT 12 OFFSET ?", (kind,(page-1)*12))
    ctx = context(request)
    ctx.update(title='Leistungen' if kind=='service' else 'Arbeiten', description='Alle veröffentlichten Inhalte entdecken.', canonical=request.url.path+('?page='+str(page) if page>1 else ''), archive_items=rows, archive_path=request.url.path, media=media_for(db,rows), page_number=page,
               previous=request.url.path+'?page='+str(page-1) if page>1 else '', next=request.url.path+'?page='+str(page+1) if page*12<total else '')
    return templates.TemplateResponse(request, 'collection-index.html', ctx)


@router.get('/news', response_class=HTMLResponse)
def news(request: Request, page: int = Query(1, ge=1, le=100000), category: str = Query('', max_length=50), q: str = Query('', max_length=80)):
    db = request.app.state.db
    listing = news_list(db, offset=(page-1)*12, category=category, query=q)
    ctx = context(request)
    ctx.update(title='Journal', description='Neuigkeiten, Perspektiven und Einblicke.', canonical='/news'+('?page='+str(page) if page>1 else ''),
               listing=listing, page_number=page, category=category, query=q,
               previous='/news?'+urlencode(dict(page=page-1, category=category, q=q)) if page > 1 else '',
               next='/news?'+urlencode(dict(page=page+1, category=category, q=q)) if page*12 < listing['total'] else '',
               media=media_for(db, listing['items']))
    return templates.TemplateResponse(request, 'news-index.html', ctx)


def render_article(request, entry, preview=False):
    ctx = context(request)
    block_context(request, ctx, entry)
    ctx.update(entry=entry, page=entry, title=entry['title'], description=entry.get('description', ''),
               canonical='/news/'+entry['slug'], preview=preview, article_context=True, og_type='article',
               reading_minutes=max(1, round(len(entry.get('body', '').split())/200)))
    return templates.TemplateResponse(request, 'article.html', ctx)


@router.get('/news/{slug}', response_class=HTMLResponse)
def article(slug: str, request: Request):
    entry = public_entry(request.app.state.db, 'article', slug)
    if not entry:
        raise HTTPException(404, 'Dieser Beitrag ist noch nicht veröffentlicht.')
    return render_article(request, entry)


def render_campaign(request, entry):
    ctx = context(request)
    ctx.update(entry=entry, title=entry['title'], description=entry['description'], preview=True,
               canonical='/news', media=media_for(request.app.state.db, entry))
    return templates.TemplateResponse(request, 'campaign-preview.html', ctx)


@router.get('/kontakt', response_class=HTMLResponse)
def contact(request: Request):
    ctx = context(request)
    ctx.update(title='Projekt anfragen', description='Erzähl uns von deinem Vorhaben.', canonical='/kontakt',
               services=public_items(request.app.state.db, 'service', limit=100))
    return templates.TemplateResponse(request, 'contact.html', ctx)


@router.get('/admin/preview/{identity}', response_class=HTMLResponse)
def preview(identity: str, request: Request, user=Depends(current_user)):
    row = record(request.app.state.db.one('SELECT * FROM content WHERE id=? AND archived=0', (identity,)))
    if row['kind'] == 'page':
        return render_page(request, row['data'], True)
    if row['kind'] in ('service', 'project'):
        return detail(request, row['kind'], row['data']['slug'], row['data'], True)
    if row['kind'] == 'article':
        return render_article(request, row['data'], True)
    if row['kind'] == 'campaign':
        return render_campaign(request, row['data'])
    raise HTTPException(404, 'Für diesen Inhalt gibt es keine Seitenvorschau.')


@router.get('/admin', response_class=HTMLResponse)
@router.get('/admin/{path:path}', response_class=HTMLResponse)
def admin(request: Request, path: str = ''):
    return templates.TemplateResponse(request, 'admin.html', {})


@router.get('/feed.xml')
def feed(request: Request):
    entries = news_list(request.app.state.db, limit=50)['items']
    origin = request.app.state.settings.origin
    xml = '<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>Journal</title><link>'+escape(origin+'/news')+'</link><description>Neuigkeiten</description>'
    for item in entries:
        link = origin+'/news/'+item['slug']
        xml += '<item><title>'+escape(item['title'])+'</title><link>'+escape(link)+'</link><guid>'+escape(link)+'</guid><description>'+escape(item['description'])+'</description></item>'
    return Response(xml+'</channel></rss>', media_type='application/rss+xml')


@router.get('/sitemap.xml')
def sitemap(request: Request, page: int = Query(1, ge=1, le=100000)):
    db = request.app.state.db
    rows = db.all("SELECT kind,published_slug FROM content WHERE published IS NOT NULL AND archived=0 "
                  "AND kind IN ('page','service','project','article') ORDER BY kind,published_slug LIMIT 1000 OFFSET ?", ((page-1)*1000,))
    total = db.one("SELECT count(*) n FROM content WHERE published IS NOT NULL AND archived=0 AND kind IN ('page','service','project','article')")['n']
    base = request.app.state.settings.origin
    if total > 1000 and 'page' not in request.query_params:
        xml = '<?xml version="1.0" encoding="UTF-8"?><sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        xml += ''.join('<sitemap><loc>'+escape(base+'/sitemap.xml?page='+str(i))+'</loc></sitemap>' for i in range(1, (total+999)//1000+1))
        return Response(xml+'</sitemapindex>', media_type='application/xml')
    prefixes = {'page': '/p/', 'service': '/leistungen/', 'project': '/arbeiten/', 'article': '/news/'}
    paths = ['/kontakt', '/news', '/leistungen', '/arbeiten'] if page == 1 else []
    paths += ['/' if r['kind'] == 'page' and r['published_slug'] == 'home' else prefixes[r['kind']]+r['published_slug'] for r in rows]
    xml = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    xml += ''.join('<url><loc>'+escape(base+p)+'</loc></url>' for p in paths)
    return Response(xml+'</urlset>', media_type='application/xml')


@router.get('/robots.txt', response_class=PlainTextResponse)
def robots(request: Request):
    return 'User-agent: *\nDisallow: /admin\nDisallow: /api/\nSitemap: '+request.app.state.settings.origin+'/sitemap.xml\n'
