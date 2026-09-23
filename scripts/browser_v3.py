#!/usr/bin/env python3
"""Real UI and FastAPI, isolated transport; NOT a deployed-host E2E.

This environment blocks host navigation. HTML is loaded with set_content and
requests are fulfilled through a TestClient. A TEST-ONLY adapter lets postMessage
work with about:blank's opaque ('null') origin; the shipped production source still
requires the same origin and exact parent/frame. Cookies, deployment CSP and native
cross-document navigation must additionally be checked on the target host.
"""
import argparse,json,os,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright,expect
from app.main import create_app
from app.config import Settings
from app.catalog import catalog,make_block
from app.content import create_content

BASE='http://127.0.0.1:8765'
PASSWORD='Browser-test-only-local-2026!'
def adapted(html):return html.replace('<head>','<head><base href="'+BASE+'/">',1)


def run(output):
 output.mkdir(parents=True,exist_ok=True);checks=[];errors=[]
 def passed(text):checks.append(text);print('PASS',text,flush=True)
 with tempfile.TemporaryDirectory(prefix='studio-v3-browser-') as d,sync_playwright() as pw:
  app=create_app(Settings(Path(d),origin=BASE))
  client=TestClient(app,base_url=BASE,headers={'Origin':BASE})
  browser=pw.chromium.launch(headless=True,executable_path=os.getenv('CHROMIUM_EXECUTABLE','/usr/bin/chromium'),args=['--no-sandbox'])
  def new_page(path='/',width=1440,height=1000,reduced=False,transport=client):
   context=browser.new_context(viewport={'width':width,'height':height},reduced_motion='reduce' if reduced else 'no-preference')
   page=context.new_page();page.set_default_timeout(10000)
   def route(r):
    req=r.request
    try:
     headers={k:v for k,v in req.headers.items() if k.lower() not in ('host','content-length','cookie','origin')};headers['Origin']=BASE
     response=transport.request(req.method,req.url.removeprefix(BASE),content=req.post_data_buffer,headers=headers)
     hs=dict(response.headers)
     for k in ('content-length','content-encoding'):hs.pop(k,None)
     hs['access-control-allow-origin']='null';hs['access-control-allow-credentials']='true'
     body=response.content
     if any(file in req.url for file in ('/static/js/admin/editor.js','/static/js/preview-bridge.js')):
      # Test-only target-origin adapter; leave source/origin checks untouched.
      body=response.text.replace(', location.origin)', ", '*')").encode()
     if '/api/admin/preview' in req.url and response.status_code==200:
      value=response.json();value['html']=adapted(value['html']);body=json.dumps(value).encode()
     r.fulfill(status=response.status_code,headers=hs,body=body)
    except Exception as exc:errors.append('Transport '+str(exc));r.abort()
   page.route(BASE+'/**',route)
   page.on('pageerror',lambda exc:(errors.append(str(exc)),print('JS ERROR',str(exc),flush=True)))
   page.on('dialog',lambda dialog:dialog.accept())
   page.set_content(adapted(transport.get(path).text),wait_until='networkidle')
   return page
  page=new_page();page.wait_for_timeout(1900)
  assert page.locator('.service-card').count()==7
  assert page.locator('.news-card').count()==3
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
  page.screenshot(path=str(output/'website-hero.png'));page.screenshot(path=str(output/'website-desktop.png'),full_page=True)
  passed('Startseite: sieben Kacheln, drei echte Demo-Beiträge, kein Überlauf')
  for key in ('brand','web','print','motion'):
   card=page.locator('.service-card[data-art='+key+']');before=card.evaluate('(el)=>getComputedStyle(el).backgroundColor')
   card.hover();page.wait_for_timeout(250)
   assert card.evaluate('(el)=>getComputedStyle(el).backgroundColor')!=before
   assert card.evaluate('(el)=>getComputedStyle(el).transform')!='none'
   page.mouse.move(0,0);page.wait_for_timeout(250)
  passed('Vier Hover-Kontrastwechsel mit perspektivischer Bewegung')
  # Frames from implemented UI, no synthetic design mockup.
  frames=[]
  for x in range(12):
   if x==0:page.locator('.service-card[data-art=brand]').hover()
   if x==5:page.locator('.service-card[data-art=web]').hover()
   if x==9:page.mouse.move(5,5)
   page.wait_for_timeout(90);frames.append(page.screenshot())
  from PIL import Image
  from io import BytesIO
  images=[Image.open(BytesIO(x)).convert('RGB').resize((1008,700)) for x in frames]
  images[0].save(output/'motion-preview.gif',save_all=True,append_images=images[1:],duration=150,loop=0)
  page.locator('.replay-intro').evaluate('(el)=>el.click()');page.wait_for_function('!!document.querySelector(".signature-curtain")')
  a=page.locator('.signature-curtain').bounding_box();page.wait_for_timeout(500);b=page.locator('.signature-curtain').bounding_box()
  assert a and b and b['width']<a['width'];page.locator('.signature-skip').click()
  passed('Signature-Intro bleibt abspielbar und überspringbar')
  page.close()
  play=new_page('/p/spielraum')
  play.wait_for_timeout(800);play.screenshot(path=str(output/'spielraum.png'),full_page=True)
  tabs=play.locator('[role=tab]');tabs.nth(1).click()
  expect(tabs.nth(1)).to_have_attribute('aria-selected','true')
  tabs.nth(1).press('ArrowRight');expect(tabs.nth(2)).to_have_attribute('aria-selected','true')
  passed('Themen-Tabs per Maus und Pfeiltaste, ARIA-Zustand aktualisiert')
  slider=play.locator('[data-comparison] input[type=range]')
  slider.fill('80');slider.dispatch_event('input')
  assert '80' in slider.get_attribute('aria-valuetext')
  assert '80' in play.locator('[data-comparison]').evaluate('(el)=>el.style.getPropertyValue("--split")')
  passed('Bildvergleich aktualisiert sichtbare Teilung und zugänglichen Wert')
  assert 'ANZEIGE' in play.locator('[data-campaign]').inner_text()
  assert play.locator('.creator-credit a').get_attribute('href')=='https://github.com/NorphyOG'
  play.locator('.creator-credit').screenshot(path=str(output/'erstellerhinweis.png'))
  passed('Partnerfläche und fixer Erstellerhinweis sind öffentlich sichtbar')
  # Replay a repeat module when re-entering; use real observer/WAAPI.
  play.evaluate('scrollTo(0,0)');play.wait_for_timeout(850)
  play.evaluate('scrollTo(0,document.body.scrollHeight)');play.wait_for_timeout(550)
  play.evaluate('scrollTo(0,0)');play.wait_for_timeout(100)
  assert play.locator('[data-animation=repeat]').first.evaluate('(el)=>el.getAnimations({subtree:true}).length')>0
  passed('Wiederkehrende Bühne animiert beim erneuten Betreten des Sichtbereichs')
  play.close()
  mobile=new_page('/',width=390,height=844,reduced=True)
  assert mobile.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
  assert mobile.locator('.signature-curtain').count()==0
  mobile.locator('.menu-toggle').click();expect(mobile.locator('.menu-toggle')).to_have_attribute('aria-expanded','true')
  mobile.locator('.menu-toggle').click();mobile.screenshot(path=str(output/'website-mobile.png'),full_page=True)
  passed('Mobile Navigation und reduzierte Bewegung bei 390 px');mobile.close()
  news=new_page('/news');news.screenshot(path=str(output/'journal.png'));assert news.locator('.news-card').count()==3;news.close()
  article=new_page('/news/design-als-system');assert 'BEISPIELBEITRAG' in article.locator('.article-prose').inner_text();article.screenshot(path=str(output/'beitrag.png'),full_page=True);article.close()
  passed('Journal und modulare Beitragsdetailseite werden gerendert')
  # Admin via actual setup form.
  admin=new_page('/admin',width=1560,height=1000)
  admin.wait_for_selector('#auth-form [name=setup_key]')
  admin.locator('[name=setup_key]').fill((app.state.db.data_dir/'.setup-key').read_text())
  admin.locator('[name=name]').fill('Studio Redaktion');admin.locator('[name=email]').fill('studio@example.test');admin.locator('[name=password]').fill(PASSWORD)
  admin.locator('[data-help=password]').click();expect(admin.locator('.help-dialog')).to_be_visible();admin.keyboard.press('Escape')
  assert admin.locator('[name=password]').input_value()==PASSWORD
  admin.locator('#auth-form button[type=submit]').click();admin.wait_for_selector('#view h1')
  passed('Echtes Setup, Hilfedialog ohne Eingabeverlust, authentifizierter Admin')
  admin.screenshot(path=str(output/'admin-dashboard.png'))
  admin.evaluate("location.hash='pages'");admin.wait_for_selector('[data-edit]')
  home=next(x for x in client.get('/api/admin/content?kind=page').json() if x['data']['slug']=='home')
  admin.locator('[data-edit="'+home['id']+'"]').click();admin.wait_for_selector('.block-editor')
  admin.wait_for_function('!!document.querySelector("iframe")?.contentDocument?.querySelector(".hero-heading")')
  first=admin.locator('.block-editor').first
  first.locator('[data-bfield=title]').fill('IDEEN.\nWEITER GEDACHT.')
  admin.wait_for_timeout(1000)
  iframe=admin.frame_locator('iframe');expect(iframe.locator('.hero-heading')).to_have_text('IDEEN. WEITER GEDACHT.')
  assert client.get('/api/admin/content/'+home['id']).json()['revision']==home['revision']
  # Marker in frame proves that subsequent edits patch rather than reload the document.
  admin.locator('iframe').evaluate('(el)=>el.contentWindow.__testKeep=42')
  first.locator('[data-bfield=title]').fill('IDEEN.\nIN BEWEGUNG.')
  admin.wait_for_timeout(1000);expect(iframe.locator('.hero-heading')).to_have_text('IDEEN. IN BEWEGUNG.')
  assert admin.locator('iframe').evaluate('(el)=>el.contentWindow.__testKeep')==42
  passed('Live-Vorschau patcht ungespeicherte Eingaben ohne iframe-Neuladen oder Datenbankrevision')
  first.locator('button[data-help=block_title]').click();admin.screenshot(path=str(output/'admin-infohilfe.png'));admin.keyboard.press('Escape')
  assert first.locator('[data-bfield=title]').input_value()=='IDEEN.\nIN BEWEGUNG.'
  admin.locator('[data-device="390"]').click();assert admin.locator('iframe').evaluate('(el)=>el.contentWindow.innerWidth')==390
  admin.locator('[data-device="1200"]').click();admin.wait_for_timeout(300);admin.screenshot(path=str(output/'seiteneditor.png'))
  passed('Ausführliche Fragezeichen-Hilfe erhält Eingaben; echte Mobilvorschau')
  admin.locator('#preview-pause').click();first.locator('[data-bfield=title]').fill('PAUSIERTE ÄNDERUNG')
  admin.wait_for_timeout(900);expect(iframe.locator('.hero-heading')).to_have_text('IDEEN. IN BEWEGUNG.')
  admin.locator('#preview-pause').click();admin.wait_for_timeout(1000);expect(iframe.locator('.hero-heading')).to_have_text('PAUSIERTE ÄNDERUNG')
  passed('Live-Vorschau pausiert und übernimmt beim Fortsetzen die Änderungen')
  admin.locator('[data-open-library]').first.click();expect(admin.locator('.library-card')).to_have_count(20)
  admin.screenshot(path=str(output/'modulkatalog.png'))
  admin.locator('#library-search').fill('Themen');admin.locator('[data-insert=tabs]').click()
  expect(admin.locator('.block-editor')).to_have_count(7)
  admin.locator('[data-undo]').click();expect(admin.locator('.block-editor')).to_have_count(6)
  admin.locator('[data-redo]').click();expect(admin.locator('.block-editor')).to_have_count(7)
  passed('20 Module durchsuchen, Themen einfügen, Undo und Redo')
  admin.wait_for_timeout(1100)
  iframe.locator('[data-module=tabs] h2').click();admin.wait_for_timeout(300)
  assert 'Themen' in admin.locator('.block-editor[open] > summary').inner_text()
  admin.locator('#preview-mode').click();admin.wait_for_timeout(200)
  iframe.locator('[role=tab]').nth(1).click();expect(iframe.locator('[role=tab]').nth(1)).to_have_attribute('aria-selected','true')
  admin.locator('#preview-play').click()
  assert iframe.locator('[data-module=tabs]').evaluate('(el)=>el.getAnimations({subtree:true}).length')>0
  passed('Vorschau-Auswahl, Testmodus mit echten Tabs und Animation erneut abspielen')
  admin.locator('#save-button').click();admin.wait_for_function('document.querySelector("#save-status").textContent.startsWith("Gespeichert")')
  assert client.get('/api/admin/content/'+home['id']).json()['revision']==home['revision']+1
  assert 'PAUSIERTE ÄNDERUNG' not in client.get('/').text
  passed('Speichern erzeugt Entwurfsrevision und verändert nicht die öffentliche Startseite')
  admin.locator('.close-editor').click();admin.evaluate("location.hash='articles'");admin.wait_for_selector('#new-item')
  admin.locator('#new-item').click();admin.wait_for_selector('#record-form')
  admin.locator('#record-form [name=title]').fill('Unser erster eigener Beitrag')
  admin.locator('#record-form [name=slug]').fill('browser-beitrag')
  admin.locator('#record-form [name=description]').fill('Dieser Beitrag wurde im Browser-Testformular erstellt.')
  admin.locator('#record-form [name=body]').fill('Inhalt aus dem tatsächlichen Editor. Kein generierter Statistikdatensatz.')
  admin.locator('#pick-cover').click();expect(admin.locator('.picker-dialog')).to_be_visible();admin.keyboard.press('Escape')
  admin.locator('#save-button').click();admin.wait_for_function('document.querySelector("#save-status").textContent.startsWith("Gespeichert")')
  assert client.get('/api/admin/content-index?kind=article&q=Unser+erster').json()['total']==1
  assert client.get('/news/browser-beitrag').status_code==404
  passed('Beitrag über UI anlegen, Mediathek öffnen, sicher als Entwurf speichern')
  admin.screenshot(path=str(output/'beitragseditor.png'))
  admin.locator('.close-editor').click();admin.evaluate("location.hash='library'");admin.wait_for_selector('[data-start-template]')
  expect(admin.locator('[data-start-template]')).to_have_count(8)
  admin.screenshot(path=str(output/'vorlagen.png'),full_page=True)
  admin.locator('[data-start-template=product]').click();admin.wait_for_selector('.block-editor');expect(admin.locator('.block-editor')).to_have_count(5)
  ids=admin.locator('[data-bfield=id]').evaluate_all('(xs)=>xs.map(x=>x.value)');assert len(ids)==len(set(ids))
  admin.set_viewport_size({'width':390,'height':844});admin.wait_for_timeout(300)
  assert admin.locator('#modal').evaluate('(el)=>el.scrollWidth<=el.clientWidth+1')
  admin.screenshot(path=str(output/'admin-mobile.png'));admin.locator('.close-editor').click();admin.set_viewport_size({'width':1560,'height':1000})
  passed('Acht Vorlagen, fünf eindeutige Produktmodule und mobiler Editor ohne Überlauf')
  admin.evaluate("location.hash='help'");admin.wait_for_selector('#help-search')
  admin.locator('#help-search').fill('Werbe');admin.wait_for_timeout(200);assert admin.locator('.handbook-topic').count()>0
  admin.locator('.handbook-topic[data-help]').first.click();admin.screenshot(path=str(output/'hilfe-handbuch.png'));admin.keyboard.press('Escape')
  passed('Durchsuchbares Handbuch mit ausführlicher Werbeplatz-Hilfe')
  admin.evaluate("location.hash='analytics'");admin.wait_for_selector('.analytics-chart');admin.screenshot(path=str(output/'admin-analyse.png'))
  assert 'ausgeschaltet' in admin.locator('#view').inner_text().lower() or 'deaktiviert' in admin.locator('#view').inner_text().lower()
  passed('Analyse zeigt deaktivierten Zustand und echte Nullwerte statt Beispieldaten')
  admin.close()
  # Every module, 3 sizes × 3 themes; campaign assigned so no missing public block.
  ad=next(x for x in client.get('/api/admin/content?kind=campaign').json())
  for theme in ('paper','blue','dark'):
   blocks=[make_block(m['type'],id='check-'+m['type'],theme=theme) for m in catalog()['modules']]
   next(b for b in blocks if b['type']=='advert')['campaign']=ad['id']
   create_content(app.state.db,'page',dict(title='Layoutprüfung '+theme,slug='layout-'+theme,blocks=blocks),publish=True)
   for width in (1440,768,390):
    check=new_page('/p/layout-'+theme,width=width,height=1000,reduced=True)
    assert check.locator('[data-block-id]').count()==20
    assert check.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),(theme,width,check.evaluate('document.documentElement.scrollWidth'))
    if theme=='paper' and width==1440:check.screenshot(path=str(output/'module-showcase.png'),full_page=True)
    check.close()
  passed('20 Module × drei Farbschemata × drei Bildschirmbreiten ohne horizontalen Seitenüberlauf')
  setting=client.get('/api/admin/content?kind=settings').json()[0]
  client.headers['X-CSRF-Token']=client.get('/api/admin/session').json()['csrf']
  saved=client.patch('/api/admin/content/'+setting['id'],json={'data':{**setting['data'],'analytics_enabled':True},'expected_revision':setting['revision']})
  assert saved.status_code==200,saved.text
  assert client.post('/api/admin/content/'+setting['id']+'/publish',json={'expected_revision':saved.json()['revision']}).status_code==200
  guest=TestClient(app,base_url=BASE,headers={'Origin':BASE})
  consent=new_page('/p/spielraum',transport=guest)
  assert app.state.db.all('SELECT * FROM metrics_daily')==[]
  expect(consent.locator('.privacy-panel')).to_be_visible()
  consent.locator('[data-consent=accepted]').click();consent.wait_for_timeout(450)
  assert client.get('/api/admin/analytics').json()['pageviews']==1
  consent.locator('[data-campaign]').scroll_into_view_if_needed();consent.wait_for_timeout(1300)
  assert client.get('/api/admin/analytics').json()['ad_impressions']==1
  consent.locator('.privacy-settings').click();consent.locator('[data-consent=denied]').click();consent.wait_for_timeout(300)
  assert app.state.analytics.active()==0
  consent.close();guest.close()
  passed('Gastbrowser: keine Zählung vor Zustimmung, ein Aufruf und eine Sichtung danach, Widerruf beendet aktive Messung')
  assert not errors,errors
  passed('Keine JavaScript-Exceptions oder Testtransportfehler im gesamten geprüften Ablauf')
  browser.close();client.close()
 (output/'browser-results.json').write_text(json.dumps({'passed':len(checks),'checks':checks,'errors':errors,'transport':'TestClient + set_content + test-only opaque-origin postMessage adapter; NOT deployment E2E'},indent=2,ensure_ascii=False))
 print('TOTAL',len(checks),flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=Path('docs/qa-v3'));args=p.parse_args();run(args.output)
