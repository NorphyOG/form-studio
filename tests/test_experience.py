"""v0.3 contracts: drafts, dynamic modules, bounded queries and opt-in statistics."""
import json
import uuid
from datetime import date, timedelta
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from app.catalog import make_block
from app.collections import active_campaign, news_list
from app.content import create_content, public_items
from app.analytics import AnalyticsRuntime
from conftest import action as transition

def action(client,row,name,**kwargs):
    if name != "save":return transition(client,row,name,**kwargs)
    response=client.patch("/api/admin/content/"+row["id"],json={"expected_revision":row["revision"],**kwargs})
    assert response.status_code==200,response.text
    return response.json()


def create(admin, kind, **data):
    result=admin.post('/api/admin/content',json={'kind':kind,'data':dict(title='Test '+kind,slug='test-'+kind,**data)})
    assert result.status_code==200,result.text
    return result.json()


def optin(admin):
    row=admin.get('/api/admin/content?kind=settings').json()[0]
    row=action(admin,row,'save',data={**row['data'],'analytics_enabled':True})
    action(admin,row,'publish')


def event(client, **kwargs):
    return client.post('/api/analytics/event',json=dict(event='pageview',path='/',token='a'*32,consent=True,**kwargs))


@pytest.fixture
def guest(app):
    with TestClient(app,headers={'Origin':'http://testserver'}) as client:
        yield client


def test_article_draft_publish_and_search(admin,guest):
    row=create(admin,'article',body='Only draft text.',author='Redaktion',category='Test',blocks=[make_block('tabs',id='topics')])
    assert guest.get('/news/test-article').status_code==404
    assert 'href="/news/test-article"' not in guest.get('/news?q=Test+article').text
    assert admin.post('/api/admin/preview',json={'kind':'article','data':row['data']}).status_code==200
    row=action(admin,row,'publish')
    live=guest.get('/news/test-article')
    assert live.status_code==200 and 'data-tabs' in live.text and 'Only draft text.' in live.text
    assert 'Test article' in guest.get('/news?category=Test').text
    assert '/news/test-article' in guest.get('/feed.xml').text
    row=action(admin,row,'save',data={**row['data'],'body':'Secret unreviewed update.'})
    assert 'Secret unreviewed update.' not in guest.get('/news/test-article').text
    assert 'Secret unreviewed update.' in admin.get('/admin/preview/'+row['id']).text


def test_article_moderation_and_published_date_are_independent(admin,account,guest):
    editor=account('editor');moderator=account('moderator')
    row=create(editor,'article',published_on='2099-01-01')
    assert editor.post('/api/admin/content/'+row['id']+'/publish',json={'expected_revision':row['revision']}).status_code==403
    row=action(editor,row,'submit');action(moderator,row,'publish')
    assert guest.get('/news/test-article').status_code==200  # Editorial display date, not a scheduling promise.


@pytest.mark.parametrize('bad',['2026-02-30','20260923','2026-9-3','hello'])
def test_article_rejects_invalid_dates(admin,bad):
    r=admin.post('/api/admin/content',json={'kind':'article','data':{'title':'Bad date','slug':'bad','published_on':bad}})
    assert r.status_code==422


def test_campaign_is_central_and_disappears_when_unpublished(admin,guest):
    campaign=create(admin,'campaign',sponsor='Example partner',link_url='https://example.com',body='Original public message')
    page=create(admin,'page',blocks=[make_block('advert',id='sponsor',campaign=campaign['id'])]);action(admin,page,'publish')
    assert 'data-campaign' not in guest.get('/p/test-page').text
    campaign=action(admin,campaign,'publish')
    html=guest.get('/p/test-page').text
    assert 'ANZEIGE' in html and 'Original public message' in html and 'sponsored noopener noreferrer' in html
    campaign=action(admin,campaign,'save',data={**campaign['data'],'body':'New partner message'})
    assert 'New partner message' not in guest.get('/p/test-page').text
    campaign=action(admin,campaign,'publish')
    assert 'New partner message' in guest.get('/p/test-page').text
    action(admin,campaign,'unpublish')
    assert 'data-campaign' not in guest.get('/p/test-page').text


@pytest.mark.parametrize('url',['javascript:alert(1)','//evil.test','data:text/html,x','/\\evil.test','https://good.test\nX: bad'])
def test_ads_reject_active_or_ambiguous_links(admin,url):
    r=admin.post('/api/admin/content',json={'kind':'campaign','data':{'title':'Invalid ad','slug':'bad-ad','link_url':url}})
    assert r.status_code==422


def test_campaign_schedule_and_invalid_range(admin,app):
    row=create(admin,'campaign',link_url='/kontakt',starts_on='2030-01-01',ends_on='2030-01-31');action(admin,row,'publish')
    for day, expected in [('2029-12-31',False),('2030-01-01',True),('2030-01-31',True),('2030-02-01',False)]:
        with patch('app.collections.utc_day',return_value=day):
            assert bool(active_campaign(app.state.db,row['id'])) is expected
    result=admin.post('/api/admin/content',json={'kind':'campaign','data':{'title':'Invalid dates','slug':'invalid-dates','link_url':'/kontakt','starts_on':'2030-01-31','ends_on':'2030-01-01'}})
    assert result.status_code==422


def test_comparison_enforces_two_items(admin):
    block=make_block('comparison');block['items'].append(block['items'][0])
    r=admin.post('/api/admin/preview',json={'kind':'page','data':{'title':'Comparison','slug':'compare','blocks':[block]}})
    assert r.status_code==422


def test_news_read_model_and_admin_index_are_projected_and_paged(admin,app):
    for i in range(33):
        create_content(app.state.db,'article',dict(title=f'Bulk {i:03}',slug=f'bulk-{i}',category='Bulk',body='LONG PRIVATE BODY '*200,published_on='2026-01-01'),publish=True)
    a=news_list(app.state.db,limit=12,category='Bulk');b=news_list(app.state.db,limit=12,offset=12,category='Bulk')
    assert a['total']==33 and len(a['items'])==12 and len(b['items'])==12
    assert not {x['id'] for x in a['items']} & {x['id'] for x in b['items']}
    assert 'body' not in a['items'][0] and 'blocks' not in a['items'][0]
    response=admin.get('/api/admin/content-index?kind=article&limit=5&q=Bulk')
    data=response.json();assert data['total']==33 and len(data['items'])==5
    assert 'body' not in data['items'][0]['data']
    full=admin.get('/api/admin/content/'+data['items'][0]['id']).json()
    assert full['data']['body'].startswith('LONG PRIVATE BODY')
    assert admin.get('/api/admin/content-index?limit=1000').status_code==422
    assert admin.get('/api/admin/content-index?q=%27%20OR%201=1%20--').json()['total']==0


def test_analytics_disabled_and_consent_required(admin,app,guest):
    assert 'privacy-panel' not in guest.get('/').text
    assert event(guest).json()=={'recorded':False}
    assert app.state.db.all('SELECT * FROM metrics_daily')==[]
    optin(admin)
    assert 'privacy-panel' in guest.get('/').text
    assert guest.post('/api/analytics/event',json={'event':'pageview','path':'/','token':'a'*32,'consent':False}).status_code==422
    assert guest.post('/api/analytics/event',json={'event':'pageview','path':'/','token':'a'*32}).status_code==422


@pytest.mark.parametrize('headers',[{'DNT':'1'},{'Sec-GPC':'1'}])
def test_privacy_signals_do_not_count(admin,guest,headers):
    optin(admin);guest.headers.update(headers)
    assert event(guest).json()=={'recorded':False}
    assert admin.get('/api/admin/analytics').json()['pageviews']==0


def test_admin_activity_excluded_and_guest_deduplicated(admin,guest,app):
    optin(admin)
    assert event(admin).json()=={'recorded':False}
    assert event(guest).json()=={'recorded':True}
    assert event(guest).json()=={'recorded':False}
    report=admin.get('/api/admin/analytics?days=7').json()
    assert report['pageviews']==1 and report['active_tabs']==1 and len(report['series'])==7
    rows=app.state.db.all('SELECT * FROM metrics_daily')
    assert set(rows[0])=={'day','event','resource','count'}
    assert rows[0]['resource']=='/' and 'a'*32 not in json.dumps(rows)


def test_analytics_unknown_path_csrf_and_permissions(admin,guest,account):
    optin(admin)
    assert guest.post('/api/analytics/event',json={'event':'pageview','path':'/not-published','token':'a'*32,'consent':True}).status_code==422
    guest.headers['Origin']='https://evil.example'
    assert event(guest).status_code==403
    assert account('editor').get('/api/admin/analytics').status_code==403
    mod=account('moderator');assert mod.get('/api/admin/analytics').status_code==200
    assert mod.delete('/api/admin/analytics').status_code==403
    assert admin.get('/api/admin/analytics?days=1000').status_code==422


def test_campaign_analytics_and_deletion(admin,guest,app):
    optin(admin)
    row=create(admin,'campaign',link_url='/kontakt');row=action(admin,row,'publish')
    for name in ['ad_impression','ad_click']:
        r=guest.post('/api/analytics/event',json={'event':name,'path':'/','token':'b'*32,'resource':row['id'],'consent':True})
        assert r.json()['recorded']
        assert not guest.post('/api/analytics/event',json={'event':name,'path':'/','token':'b'*32,'resource':row['id'],'consent':True}).json()['recorded']
    report=admin.get('/api/admin/analytics').json();assert report['campaigns'][0]['impressions']==1 and report['campaigns'][0]['clicks']==1
    action(admin,row,'unpublish')
    assert not guest.post('/api/analytics/event',json={'event':'ad_click','path':'/','token':'c'*32,'resource':row['id'],'consent':True}).json()['recorded']
    assert admin.delete('/api/admin/analytics').status_code==200
    assert app.state.db.all('SELECT * FROM metrics_daily')==[] and app.state.analytics.active()==0


def test_analytics_expiry_and_memory_bounds():
    runtime=AnalyticsRuntime()
    with patch('app.analytics.time.monotonic',return_value=100):
        assert runtime.accept('a','/','pageview','ip','/')
        assert runtime.active()==1
    with patch('app.analytics.time.monotonic',return_value=191):
        assert runtime.active()==0
        assert not runtime.accept('b','/','heartbeat','ip','/')
        assert 'a' not in runtime.tabs
    runtime.clear()
    for i in range(5005):
        runtime.accept(str(i),'/','heartbeat','ip'+str(i),'/')
    assert len(runtime.tabs)==5000
    runtime.clear();assert len(runtime.tabs)==len(runtime.rates)==0


def test_rate_limited_statistics_and_retention(admin,guest,app):
    optin(admin)
    runtime=app.state.analytics
    for i in range(180):runtime.accept(str(i),'/','heartbeat','one-ip','/')
    assert not runtime.accept('over','/','pageview','one-ip','/')
    with app.state.db.connect(write=True) as con:
        con.execute('INSERT INTO metrics_daily VALUES(?,?,?,?)',((date.today()-timedelta(days=100)).isoformat(),'pageview','/',5))
    event(guest)
    assert all(x['day']>=(date.today()-timedelta(days=89)).isoformat() for x in app.state.db.all('SELECT day FROM metrics_daily'))


def test_migrate_v2_keeps_contents_and_presets(app):
    db=app.state.db;before=db.all('SELECT * FROM content')
    with db.connect(write=True) as con:con.execute('DROP TABLE metrics_daily');con.execute('PRAGMA user_version=2')
    db.init();db.init()
    assert db.all('SELECT * FROM content')==before
    assert db.all('SELECT * FROM metrics_daily')==[]
    with db.connect() as con:assert con.execute('PRAGMA user_version').fetchone()[0]==3


@pytest.mark.parametrize('path',['/','/news','/news/design-als-system','/p/spielraum','/p/datenschutz','/kontakt','/leistungen','/arbeiten','/not-found'])
def test_creator_attribution_is_public_and_outside_editable_data(guest,path):
    response=guest.get(path)
    assert 'https://github.com/NorphyOG' in response.text and 'creator-credit' in response.text


def test_indexes_exist_and_single_detail_uses_index(app):
    with app.state.db.connect() as con:
        plan=con.execute("EXPLAIN QUERY PLAN SELECT published FROM content WHERE kind='article' AND published_slug='foo' AND published IS NOT NULL").fetchall()
    assert 'INDEX' in ' '.join(str(tuple(p)) for p in plan)


def test_ad_totals_include_campaigns_beyond_top_twenty(admin,app):
    today=date.today().isoformat()
    with app.state.db.connect(write=True) as con:
        for i in range(25):con.execute('INSERT INTO metrics_daily VALUES(?,?,?,?)',(today,'ad_impression',str(i),1))
    result=admin.get('/api/admin/analytics').json()
    assert result['ad_impressions']==25 and len(result['campaigns'])==20


def test_article_with_bento_has_one_main_heading(admin,guest):
    import re
    row=create(admin,'article',blocks=[make_block('bento',id='nested-bento')]);action(admin,row,'publish')
    text=guest.get('/news/test-article').text
    assert len(re.findall(r'<h1(?:\s|>)',text))==1
    assert 'property="og:type" content="article"' in text
