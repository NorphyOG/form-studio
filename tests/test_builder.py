"""v0.2 contracts: catalogue, stateless preview, presets, migration, safe content."""
from copy import deepcopy
from typing import get_args
import json
from pathlib import Path
import pytest
from app.catalog import catalog,make_block
from app.models import BlockType,Page,Block,BlockItem,Art,SiteSettings
from app.config import ROOT
from app.database import Database,now,encode
from pydantic import ValidationError
from conftest import action


def payload(blocks=None):
    return {'kind':'page','data':{'title':'Testseite','slug':'baukasten-test','blocks':blocks or []}}


def test_catalog_is_complete_and_private(client,admin):
    # client is the same session in these fixtures; create unauthenticated endpoint check separately.
    result=admin.get('/api/admin/catalog')
    assert result.status_code==200
    c=result.json()
    assert {x['type'] for x in c['modules']}==set(get_args(BlockType))
    assert len(c['modules'])==20 and len(c['templates'])==8
    assert {x['id'] for x in c['assets']}==set(get_args(Art))
    for spec in c['modules']:
        assert (ROOT/'templates'/'blocks'/(spec['type']+'.html')).is_file()
        assert Block.model_validate(spec['defaults']).type==spec['type']
        assert len(spec['description'])>15
    assert c['limits']=={'blocks':30,'items':20,'presets':100}


@pytest.mark.parametrize('path',['/api/admin/catalog','/api/admin/block-presets'])
def test_builder_reads_require_auth(client,path):
    assert client.get(path).status_code==401


def test_stateless_preview_auth_and_csrf(client,admin):
    assert admin.post('/api/admin/preview',json=payload(),headers={'X-CSRF-Token':'no'}).status_code==403
    assert admin.post('/api/admin/preview',json=payload(),headers={'Origin':'https://wrong.test'}).status_code==403


def test_stateless_preview_no_session(client):
    assert client.post('/api/admin/preview',json=payload()).status_code==401


@pytest.mark.parametrize('kind',get_args(BlockType))
def test_every_module_renders_live_and_preview(admin,kind):
    block=make_block(kind)
    block['id']='sample-'+kind
    body=payload([block])
    response=admin.post('/api/admin/preview',json=body)
    assert response.status_code==200,response.text
    assert 'data-module="'+kind+'"' in response.json()['html']
    created=admin.post('/api/admin/content',json=body)
    assert created.status_code==200,created.text
    action(admin,created.json(),'publish')
    public=admin.get('/p/baukasten-test')
    assert public.status_code==200
    if kind == 'advert':
        assert 'data-block-id="sample-advert"' not in public.text  # Unassigned ads do not create a public gap.
    else:
        assert 'data-block-id="sample-'+kind+'"' in public.text


@pytest.mark.parametrize('template',catalog()['templates'],ids=lambda x:x['id'])
def test_templates_validate_and_render(admin,template):
    blocks=deepcopy(template['blocks'])
    for i,block in enumerate(blocks):block['id']=f'template-{i}'
    response=admin.post('/api/admin/preview',json=payload(blocks))
    assert response.status_code==200,response.text
    assert response.json()['html'].count('data-module=')==len(blocks)


def test_preview_does_not_save_publish_or_audit(admin,app):
    db=app.state.db
    before={name:db.all('SELECT * FROM '+name) for name in ('content','revisions','audit','inquiries')}
    body=payload([make_block('text',title='NUR IN DER SOFORTVORSCHAU')])
    for _ in range(3):
        r=admin.post('/api/admin/preview',json=body)
        assert r.status_code==200 and 'NUR IN DER SOFORTVORSCHAU' in r.json()['html']
    assert admin.get('/p/baukasten-test').status_code==404
    after={name:db.all('SELECT * FROM '+name) for name in before}
    assert before==after


def test_preview_escapes_text_and_rejects_settings(admin):
    r=admin.post('/api/admin/preview',json=payload([make_block('quote',text='<img src=x onerror=alert(1)>')]))
    assert r.status_code==200
    assert '<img src=x onerror=' not in r.json()['html']
    assert '&lt;img src=x' in r.json()['html']
    r=admin.post('/api/admin/preview',json={'kind':'settings','data':{'title':'Site','slug':'site'}})
    assert r.status_code==422


@pytest.mark.parametrize('value',['javascript:alert(1)','data:text/html,abc','//evil.test','http://plain.test','https://user:pass@evil.test','/\\evil.test','/%2f%2fevil.test','#bad anchor','ftp://evil.test','https://good.test/\nscript'])
def test_unsafe_links_rejected(value):
    with pytest.raises(ValidationError):Block(id='x',type='contact',link_url=value)
    with pytest.raises(ValidationError):BlockItem(title='X',link_url=value)


@pytest.mark.parametrize('value',['','/kontakt','/p/geschichte','#kontakt','https://example.test/angebot?a=1&b=2','https://example.test/%20foto'])
def test_safe_links_supported(value):
    assert Block(id='x',type='media',link_url=value).link_url==value


@pytest.mark.parametrize('bad',[{'type':'html'},{'columns':7},{'theme':'script'},{'animation':'forever'},{'unknown':True},{'image':'/etc/passwd'},{'id':'x" onclick="y'}])
def test_invalid_module_contract_rejected(bad):
    with pytest.raises(ValidationError):Block.model_validate({'id':'x','type':'text',**bad})


def test_module_and_item_bounds():
    blocks=[{'id':f'b{i}','type':'text'} for i in range(31)]
    with pytest.raises(ValidationError):Page(title='Too many',slug='too-many',blocks=blocks)
    with pytest.raises(ValidationError):Block(id='x',type='features',items=[{'title':'X'}]*21)
    with pytest.raises(ValidationError):Page(title='Duplicate',slug='dup',blocks=[blocks[0],blocks[0]])


def test_legacy_block_defaults_and_single_h1(admin):
    body=payload([{'id':'a','type':'bento','title':'Erste Idee'},{'id':'b','type':'bento','title':'Zweite Idee'}])
    html=admin.post('/api/admin/preview',json=body).json()['html']
    assert html.count('<h1 ')==1 and '<h2 class="hero-heading">Zweite Idee</h2>' in html
    assert 'theme-paper spacing-normal width-wide align-left columns-3' in html


def test_public_works_link_targets_actual_module_id(admin):
    blocks=[make_block('bento',id='hero'),make_block('projects',id='meine-arbeit')]
    html=admin.post('/api/admin/preview',json=payload(blocks)).json()['html']
    assert 'href="#meine-arbeit"' in html
    blocks[1]['enabled']=False
    html=admin.post('/api/admin/preview',json=payload(blocks)).json()['html']
    assert 'Arbeiten entdecken' not in html and 'Projekt besprechen' in html


def test_design_options_and_custom_link_render(admin):
    b=make_block('media',theme='dark',spacing='compact',width='narrow',align='center',columns=4,animation='none',link_label='Kontakt',link_url='/kontakt')
    html=admin.post('/api/admin/preview',json=payload([b])).json()['html']
    assert 'theme-dark spacing-compact width-narrow align-center columns-4' in html
    assert 'data-animation="none"' in html and 'href="/kontakt"' in html


def test_presets_roles_ownership_copy_and_deletion(admin,account):
    editor=account('editor');moderator=account('moderator')
    data={'name':'Mein Baustein','block':make_block('features')}
    assert moderator.post('/api/admin/block-presets',json=data).status_code==403
    r=editor.post('/api/admin/block-presets',json=data);assert r.status_code==200,r.text
    own=r.json();saved=admin.post('/api/admin/block-presets',json={**data,'name':'Team Basis'}).json()
    assert len(moderator.get('/api/admin/block-presets').json())==2
    assert editor.delete('/api/admin/block-presets/'+saved['id']).status_code==403
    assert moderator.delete('/api/admin/block-presets/'+own['id']).status_code==403
    block=deepcopy(own['block']);block['id']='independent';block['title']='Unabhängige Kopie'
    row=editor.post('/api/admin/content',json=payload([block])).json()
    assert editor.get('/api/admin/block-presets').json()[0]['block']['title']!='Unabhängige Kopie'
    assert editor.delete('/api/admin/block-presets/'+own['id']).status_code==200
    assert next(x for x in admin.get('/api/admin/content').json() if x['id']==row['id'])['data']['blocks'][0]['title']=='Unabhängige Kopie'
    assert admin.delete('/api/admin/block-presets/'+saved['id']).status_code==200
    assert admin.delete('/api/admin/block-presets/'+saved['id']).status_code==404


def test_presets_cap_and_csrf(admin,app):
    user=admin.get('/api/admin/session').json()
    block=make_block('text')
    with app.state.db.connect(write=True) as con:
        for i in range(100):con.execute('INSERT INTO block_presets VALUES(?,?,?,?,?)',(str(i),'Vorlage',encode(block),user['id'],now()))
    data={'name':'Noch eine','block':block}
    assert admin.post('/api/admin/block-presets',json=data).status_code==409
    assert admin.delete('/api/admin/block-presets/0',headers={'X-CSRF-Token':'bad'}).status_code==403


def test_v1_upgrade_preserves_content_and_is_idempotent(app):
    db=app.state.db
    before=db.all('SELECT * FROM content')
    with db.connect(write=True) as con:
        con.execute('DROP TABLE block_presets');con.execute('PRAGMA user_version=1')
    db.init();db.init()
    assert db.all('SELECT * FROM content')==before
    assert db.all('SELECT * FROM block_presets')==[]
    with db.connect() as con:assert con.execute('PRAGMA user_version').fetchone()[0]==3


def test_backup_contains_reusable_presets(admin,app,tmp_path):
    from scripts.backup import backup
    from scripts.restore_backup import restore
    row=admin.post('/api/admin/block-presets',json={'name':'Backup Block','block':make_block('media')}).json()
    archive=backup(app.state.db.data_dir,tmp_path/'backups')
    target=tmp_path/'restored'
    restore(archive,target)
    db=Database(target);db.init()
    assert db.one('SELECT name FROM block_presets WHERE id=?',(row['id'],))['name']=='Backup Block'
    assert db.all('SELECT * FROM sessions')==[]


def test_assets_are_bundled_svg_and_no_active_code(client):
    for asset in catalog()['assets']:
        r=client.get('/static/assets/'+asset['id']+'.svg')
        assert r.status_code==200 and 'image/svg+xml' in r.headers['content-type']
        assert '<svg' in r.text and '<title>' in r.text
        assert '<script' not in r.text and 'onload=' not in r.text


def test_animation_settings_default_and_validation():
    assert SiteSettings(title='Site',slug='site').motion=='signature'
    assert SiteSettings(title='Site',slug='site').intro=='session'
    with pytest.raises(ValidationError):SiteSettings(title='Site',slug='site',motion='broken')


def test_contact_rejects_invisible_extra_items():
    with pytest.raises(ValidationError):
        Block(id='contact',type='contact',items=[{'title':'Note'}]*3)
