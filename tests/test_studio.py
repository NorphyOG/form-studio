from io import BytesIO
from PIL import Image
import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.config import Settings
from conftest import PASSWORD,create_service,action

@pytest.mark.parametrize('path',['/','/kontakt','/leistungen/web','/arbeiten/mono','/p/datenschutz','/admin','/static/js/admin/main.js','/sitemap.xml','/robots.txt'])
def test_public_routes(client,path):
    assert client.get(path).status_code==200

def test_404_is_designed_html(client):
    r=client.get('/missing-route')
    assert r.status_code==404
    assert 'text/html' in r.headers['content-type']

def test_bootstrap_requires_secret(client,app):
    assert client.get('/api/setup-status').json()['setup_required']
    r=client.post('/api/setup',json=dict(setup_key='wrong-secret-code-value',name='Admin',email='a@example.test',password=PASSWORD))
    assert r.status_code==403
    assert app.state.db.one('SELECT count(*) n FROM users')['n']==0

def test_setup_one_time_and_cookie(admin,app):
    assert not (app.state.db.data_dir/'.setup-key').exists()
    assert not admin.get('/api/setup-status').json()['setup_required']
    r=admin.post('/api/login',json={'email':'admin@example.test','password':PASSWORD})
    assert r.status_code==200
    assert 'HttpOnly' in r.headers['set-cookie']
    assert 'SameSite=strict' in r.headers['set-cookie']
    r=admin.post('/api/setup',json=dict(setup_key='wrong-secret-code-value',name='Admin',email='a@example.test',password=PASSWORD))
    assert r.status_code==403

def test_admin_requires_session(client):
    assert client.get('/api/admin/content').status_code==401

def test_invalid_login(admin):
    assert admin.post('/api/login',json={'email':'admin@example.test','password':'wrong'}).status_code==401

def test_csrf_and_origin(admin):
    row=create_service(admin)
    payload={'expected_revision':row['revision']}
    assert admin.post(f"/api/admin/content/{row['id']}/publish",json=payload,headers={'X-CSRF-Token':'wrong'}).status_code==403
    assert admin.post(f"/api/admin/content/{row['id']}/publish",json=payload,headers={'Origin':'https://evil.example'}).status_code==403

def test_session_rotates_and_logout_revokes(admin,app):
    old=admin.cookies.get('studio_session')
    r=admin.post('/api/login',json={'email':'admin@example.test','password':PASSWORD})
    assert old!=admin.cookies.get('studio_session')
    stale=TestClient(app,headers={'Origin':'http://testserver'})
    stale.cookies.set('studio_session',old)
    assert stale.get('/api/admin/content').status_code==401
    admin.headers['X-CSRF-Token']=admin.get('/api/admin/session').json()['csrf']
    assert admin.post('/api/admin/logout').status_code==200
    assert admin.get('/api/admin/content').status_code==401

def test_editor_role(admin,account):
    editor=account('editor')
    row=create_service(editor)
    assert editor.post(f"/api/admin/content/{row['id']}/publish",json={'expected_revision':row['revision']}).status_code==403
    for path in ['users','inquiries','audit']:
        assert editor.get('/api/admin/'+path).status_code==403
    settings=next(x for x in editor.get('/api/admin/content').json() if x['kind']=='settings')
    assert editor.patch('/api/admin/content/'+settings['id'],json={'data':settings['data'],'expected_revision':settings['revision']}).status_code==403
    pending=action(editor,row,'submit')
    assert pending['state']=='pending'

def test_moderator_role(admin,account):
    moderator=account('moderator')
    row=create_service(admin)
    assert moderator.post('/api/admin/content',json={'kind':'service','data':row['data']}).status_code==403
    assert moderator.patch('/api/admin/content/'+row['id'],json={'data':row['data'],'expected_revision':row['revision']}).status_code==403
    assert moderator.post(f"/api/admin/content/{row['id']}/publish",json={'expected_revision':row['revision']}).status_code==409
    row=action(admin,row,'submit')
    row=action(moderator,row,'publish')
    assert row['live']['title']=='Private Idee'

def test_draft_private_then_published(admin,app):
    row=create_service(admin)
    anonymous=TestClient(app)
    assert anonymous.get('/leistungen/private-idee').status_code==404
    assert anonymous.get('/admin/preview/'+row['id']).status_code==401
    assert admin.get('/admin/preview/'+row['id']).status_code==200
    row=action(admin,row,'publish')
    assert anonymous.get('/leistungen/private-idee').status_code==200
    assert 'private-idee' in anonymous.get('/sitemap.xml').text

def test_live_snapshot_and_slug_survive_draft_edits(admin):
    row=action(admin,create_service(admin),'publish')
    data={**row['data'],'title':'Noch geheim','slug':'neue-adresse'}
    updated=admin.patch('/api/admin/content/'+row['id'],json={'data':data,'expected_revision':row['revision']}).json()
    assert updated['state']=='draft'
    assert 'Private Idee' in admin.get('/leistungen/private-idee').text
    assert 'Noch geheim' not in admin.get('/leistungen/private-idee').text
    assert 'Noch geheim' in admin.get('/admin/preview/'+row['id']).text
    assert admin.get('/leistungen/neue-adresse').status_code==404
    action(admin,updated,'publish')
    assert admin.get('/leistungen/neue-adresse').status_code==200
    assert admin.get('/leistungen/private-idee').status_code==404

def test_conflicting_save_returns_409(admin):
    row=create_service(admin)
    payload={'data':{**row['data'],'title':'Update'},'expected_revision':row['revision']}
    assert admin.patch('/api/admin/content/'+row['id'],json=payload).status_code==200
    assert admin.patch('/api/admin/content/'+row['id'],json=payload).status_code==409

def test_rejection_requires_reason(admin):
    row=action(admin,create_service(admin),'submit')
    url=f"/api/admin/content/{row['id']}/reject"
    assert admin.post(url,json={'expected_revision':row['revision']}).status_code==422
    rejected=action(admin,row,'reject',note='Bitte Beispiel ergänzen.')
    assert rejected['state']=='rejected' and rejected['note']=='Bitte Beispiel ergänzen.'

def test_restore_preserves_live_version(admin):
    row=create_service(admin)
    row=admin.patch('/api/admin/content/'+row['id'],json={'data':{**row['data'],'title':'Live Version'},'expected_revision':row['revision']}).json()
    row=action(admin,row,'publish')
    restored=admin.post(f"/api/admin/content/{row['id']}/restore/1",json={'expected_revision':row['revision']}).json()
    assert restored['data']['title']=='Private Idee'
    assert restored['live']['title']=='Live Version'
    assert restored['revision']==4
    assert len(admin.get(f"/api/admin/content/{row['id']}/history").json())==4

def test_unpublish_and_archive(admin):
    row=action(admin,create_service(admin),'publish')
    row=action(admin,row,'unpublish')
    assert admin.get('/leistungen/private-idee').status_code==404
    row=action(admin,row,'archive')
    assert row['archived']==1
    assert row['id'] not in [x['id'] for x in admin.get('/api/admin/content').json()]
    assert len(admin.get(f"/api/admin/content/{row['id']}/history").json())==4

def test_protected_home_and_settings(admin):
    for row in admin.get('/api/admin/content').json():
        if row['data']['slug'] in ('home','site'):
            assert admin.post(f"/api/admin/content/{row['id']}/archive",json={'expected_revision':row['revision']}).status_code==409

def test_navigation_uses_only_published_pages(admin):
    row=admin.post('/api/admin/content',json={'kind':'page','data':{'title':'Unsere Geschichte','slug':'geschichte','in_navigation':True,'navigation_label':'Geschichte','blocks':[{'id':'story','type':'text','title':'Geschichte','text':'Der Anfang.'}]}}).json()
    assert '/p/geschichte' not in admin.get('/').text
    row=action(admin,row,'publish')
    assert '/p/geschichte' in admin.get('/').text
    assert admin.get('/p/geschichte').status_code==200

def test_disabled_module_and_new_service(admin):
    home=next(x for x in admin.get('/api/admin/content').json() if x['data']['slug']=='home')
    for block in home['data']['blocks']:
        if block['type']=='faq':block['enabled']=False
    home=admin.patch('/api/admin/content/'+home['id'],json={'data':home['data'],'expected_revision':home['revision']}).json()
    action(admin,home,'publish')
    assert 'Noch eine Frage?' not in admin.get('/').text
    action(admin,create_service(admin,title='Achte Disziplin',slug='extra-service'),'publish')
    assert 'Achte Disziplin' in admin.get('/').text

def test_inquiries_workflow(admin,account,app):
    body={'name':'Demo Person','email':'person@example.test','message':'Das ist eine konkrete Anfrage.','privacy':True}
    assert admin.post('/api/inquiries',json=body).status_code==201
    row=admin.get('/api/admin/inquiries').json()[0]
    moderator=account('moderator')
    assert moderator.patch('/api/admin/inquiries/'+row['id'],json={'status':'in_progress'}).status_code==200
    assert moderator.delete('/api/admin/inquiries/'+row['id']).status_code==403
    assert admin.delete('/api/admin/inquiries/'+row['id']).status_code==200
    assert admin.get('/api/admin/inquiries').json()==[]

def test_inquiry_honeypot_privacy_and_rate(client,app):
    body={'name':'Demo Person','email':'person@example.test','message':'Das ist eine konkrete Anfrage.','privacy':True}
    assert client.post('/api/inquiries',json={**body,'privacy':False}).status_code==422
    assert client.post('/api/inquiries',json={**body,'website':'spam'}).status_code==201
    assert app.state.db.one('SELECT count(*) n FROM inquiries')['n']==0
    for _ in range(5):assert client.post('/api/inquiries',json=body).status_code==201
    assert client.post('/api/inquiries',json=body).status_code==429

def test_media_reencoded_and_bad_input_rejected(admin):
    out=BytesIO();Image.new('RGB',(150,80)).save(out,'PNG')
    r=admin.post('/api/admin/media',files={'file':('photo.png',out.getvalue(),'image/png')},data={'alt':'Ein Testmotiv'})
    assert r.status_code==201,r.text
    image=admin.get('/media/'+r.json()['id'])
    assert image.headers['content-type']=='image/webp'
    assert Image.open(BytesIO(image.content)).size==(150,80)
    assert admin.post('/api/admin/media',files={'file':('evil.svg',b'<svg onload="alert(1)"></svg>','image/svg+xml')},data={'alt':'Ungültiges SVG'}).status_code==422

def test_media_byte_limit(admin):
    r=admin.post('/api/admin/media',files={'file':('large.png',b'x'*(8*1024*1024+1),'image/png')},data={'alt':'Zu großes Bild'})
    assert r.status_code==413

def test_request_body_limit(admin):
    assert admin.post('/api/inquiries',content=b'x'*(9*1024*1024+1)).status_code==413

def test_xss_escaped_and_slug_validated(admin):
    row=create_service(admin,title='<script>alert(1)</script>')
    action(admin,row,'publish')
    html=admin.get('/leistungen/private-idee').text
    assert '<script>alert(1)</script>' not in html
    assert '&lt;script&gt;' in html
    assert admin.post('/api/admin/content',json={'kind':'service','data':{'title':'Unsafe','slug':'../escape'}}).status_code==422

def test_duplicate_slug_and_block_ids(admin):
    create_service(admin)
    assert admin.post('/api/admin/content',json={'kind':'service','data':{'title':'Duplicate','slug':'private-idee'}}).status_code==409
    assert admin.post('/api/admin/content',json={'kind':'page','data':{'title':'Duplicate modules','slug':'duplicate','blocks':[{'id':'x','type':'text'},{'id':'x','type':'faq'}]}}).status_code==422

def test_deactivation_revokes_sessions(admin,account):
    editor=account('editor')
    user=editor.get('/api/admin/session').json()
    assert admin.patch('/api/admin/users/'+str(user['id']),json={'active':False}).status_code==200
    assert editor.get('/api/admin/session').status_code==401
    own=admin.get('/api/admin/session').json()
    assert admin.patch('/api/admin/users/'+str(own['id']),json={'active':False}).status_code==409

def test_security_headers(client,admin):
    r=client.get('/')
    assert "script-src 'self'" in r.headers['content-security-policy']
    assert r.headers['x-content-type-options']=='nosniff'
    r=admin.get('/api/admin/content')
    assert r.headers['cache-control']=='no-store'
    assert r.headers['x-robots-tag']=='noindex, nofollow'

def test_persistence_after_application_restart(admin,app):
    row=action(admin,create_service(admin),'publish')
    other=create_app(Settings(app.state.db.data_dir,origin='http://testserver'))
    with TestClient(other) as c:
        assert c.get('/leistungen/private-idee').status_code==200
        assert not c.get('/api/setup-status').json()['setup_required']
        assert other.state.db.one('SELECT revision FROM content WHERE id=?',(row['id'],))['revision']==2

def test_backup_and_restore(admin,app,tmp_path):
    from scripts.backup import backup
    from scripts.restore_backup import restore
    import sqlite3
    row=action(admin,create_service(admin),'publish')
    out=BytesIO();Image.new('RGB',(30,20)).save(out,'PNG')
    image=admin.post('/api/admin/media',files={'file':('photo.png',out.getvalue(),'image/png')},data={'alt':'Backup Testmotiv'}).json()
    zip_path=backup(app.state.db.data_dir,tmp_path/'backups')
    destination=tmp_path/'restored'
    restore(zip_path,destination)
    with sqlite3.connect(destination/'studio.sqlite3') as db:
        assert db.execute('SELECT revision FROM content WHERE id=?',(row['id'],)).fetchone()[0]==2
        assert db.execute('SELECT count(*) FROM sessions').fetchone()[0]==0
    assert (destination/'media'/image['filename']).is_file()
    with pytest.raises(ValueError):restore(zip_path,destination)

def test_backup_rejects_path_traversal(tmp_path):
    from scripts.restore_backup import restore
    import zipfile
    archive=tmp_path/'evil.zip'
    with zipfile.ZipFile(archive,'w') as z:
        z.writestr('studio.sqlite3',b'not-a-database')
        z.writestr('../escaped.txt','not allowed')
    with pytest.raises(ValueError):restore(archive,tmp_path/'restored')
    assert not (tmp_path/'escaped.txt').exists()

def test_local_launcher_check(tmp_path):
    import os,subprocess,sys
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    r=subprocess.run([sys.executable,str(root/'start.py'),'--no-bootstrap','--no-browser','--check'],capture_output=True,text=True,env={**os.environ,'DATA_DIR':str(tmp_path/'launcher'),'SITE_ORIGIN':'http://127.0.0.1:8000'},timeout=15)
    assert r.returncode==0,r.stdout+r.stderr
    assert (tmp_path/'launcher'/'studio.sqlite3').is_file()
