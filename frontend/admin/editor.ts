import {pickMedia,setMediaSelect} from './pickers.js';
import {api,json} from './api.js';
import {escape as e,field,textarea,select,check,modal,toast,errorMessage,badge,kindName,date,publicPath} from './ui.js';
import {helpButton} from './help.js';
import {getCatalog} from './catalog.js';
import {PageBuilder} from './builder.js';
import {assetUrl} from './asset-url.js';
import type {ContentData,Kind,Media,RecordItem,Revision,User} from './types.js';

const designOptions:[string,string,string][]=[
 ['studio','Studio','Klar · modular'],['noir','Noir','Dunkel · kontrastreich'],
 ['editorial','Editorial','Typografisch · klassisch'],['atelier','Atelier','Warm · weich'],
 ['aurora','Aurora','Kühl · räumlich'],['brutalist','Brutalist','Laut · kantig'],
 ['minimal','Minimal','Ruhig · reduziert'],['garden','Garden','Organisch · natürlich'],
 ['sunset','Sunset','Lebendig · farbig'],['terminal','Terminal','Digital · präzise']
];

function defaultData(kind:Kind):ContentData{
 const base={title:'',slug:'',description:'',order:0};
 if(kind==='campaign')return {...base,sponsor:'',body:'',image:'',art:'rings',link_label:'Mehr erfahren',link_url:'/kontakt',starts_on:'',ends_on:''};
 if(kind==='article')return {...base,art:'print',body:'',tags:[],image:'',category:'Studio',author:'Redaktion',published_on:new Date().toISOString().slice(0,10),featured:false,blocks:[]};
 return kind==='page'?{...base,blocks:[],in_navigation:false,navigation_label:''}:{...base,art:'web',body:'',tags:[],image:'',...(kind==='project'?{category:'Digital',client:'',year:String(new Date().getFullYear()),demo:true}:{})};
}
export async function openEditor(record:RecordItem|null,kind:Kind,user:User,refresh:()=>void,initial?:Partial<ContentData>):Promise<void>{
 let current=record;
 const data:ContentData={...structuredClone(record?.data||defaultData(kind)),...initial};
 if(kind==='article'&&!record)data.author=user.name;
 const hasBlocks=kind==='page'||kind==='article';
 const [media,catalog]=await Promise.all([api<Media[]>('/api/admin/media'),getCatalog()]);
 // Ensure older referenced uploads stay selected even outside the first library page.
 const referenced=new Set<string>();const walk=(value:unknown):void=>{if(Array.isArray(value))value.forEach(walk);else if(value&&typeof value==='object'){const o=value as Record<string,unknown>;if(typeof o.image==='string'&&o.image)referenced.add(o.image);Object.values(o).forEach(v=>{if(typeof v==='object')walk(v);});}};walk(data);
 await Promise.all(Array.from(referenced).filter(id=>!media.some(m=>m.id===id)).map(async id=>{try{media.push(await api<Media>('/api/admin/media/'+id));}catch{/* Missing references use the standard illustration. */}}));
 const canEdit=user.role!=='moderator';
 const assetOptions:[string,string][]=catalog.assets.map(a=>[a.id,a.name]);
 const mediaOptions:[string,string][]=[['','Standardgrafik verwenden'],...media.map(m=>[m.id,m.alt] as [string,string])];
 const basic=`<div class="field-grid">${field(kind==='settings'?'Interner Titel':'Titel','title',data.title,'text','required minlength="2" maxlength="120"')}${field('URL-Kennung','slug',data.slug,'text',`required pattern="[a-z0-9][a-z0-9-]{0,63}" ${kind==='settings'||data.slug==='home'?'readonly':''}`)}</div>${textarea('Kurzbeschreibung / Suchmaschinen','description',data.description,2,'maxlength="500"')}`;
 const designSelector=kind==='settings'?`<section class="design-chooser" aria-label="Designpakete"><div class="design-chooser-heading"><span class="eyebrow">DESIGNPAKETE</span><h3>Ein Inhalt. Zehn Looks.</h3><p>Wähle eine Oberfläche für die gesamte öffentliche Website. Seiten, Beiträge und Funktionen bleiben erhalten.</p></div>${select('Designpaket','design',data.design||'studio',designOptions.map(([id,name])=>[id,name]))}<div class="design-chooser-grid">${designOptions.map(([id,name,description])=>`<button type="button" class="design-option" data-design-option="${id}" aria-pressed="${(data.design||'studio')===id}" ${!canEdit?'disabled':''}><span class="design-option-sample design-sample-${id}" aria-hidden="true"><i></i><b></b><small></small></span><strong>${name}</strong><span>${description}</span></button>`).join('')}</div><p class="field-hint">Änderung als Entwurf speichern und Einstellungen veröffentlichen. Die Auswahl wirkt auf alle öffentlichen Seiten.</p></section>`:'';
 const details=kind==='page'?`${check('In der Hauptnavigation anzeigen','in_navigation',!!data.in_navigation)}<div class="field-grid">${field('Navigationsname (optional)','navigation_label',data.navigation_label||'','text','maxlength="30"')}${field('Navigationsreihenfolge','order',data.order,'number','required min="0" max="10000"')}</div>`:kind==='settings'?`${field('Name der Website','brand',data.brand,'text','required minlength="2" maxlength="40"')}${field('Unterzeile','tagline',data.tagline,'text','maxlength="80"')}${designSelector}<div class="field-grid">${select('Akzentfarbe','accent',data.accent||'blue',[['blue','Kobaltblau'],['purple','Violett'],['green','Waldgrün'],['orange','Terrakotta']])}${field('Kontakt-E-Mail (optional)','email',data.email,'email','maxlength="200"')}</div>${field('Standort / Kurztext','location',data.location,'text','maxlength="100"')}${check('Journal in der Navigation anzeigen','news_in_navigation',data.news_in_navigation!==false)}${check('Optionale lokale Statistik anbieten','analytics_enabled',!!data.analytics_enabled)}<p class="field-hint">Nach Veröffentlichung erscheint eine Zustimmungsauswahl. Ohne Zustimmung werden keine Statistikereignisse gesendet.</p><div class="settings-motion-card"><span class="eyebrow">MOTION / IDENTITÄT IN BEWEGUNG</span><h3>Wie soll deine Website auftreten?</h3><div class="field-grid">${select('Animationsstil','motion',data.motion||'signature',[['signature','Signature / volle Choreografie'],['subtle','Dezent / ohne großes Intro'],['off','Keine Animationen']])}${select('Öffnungssequenz','intro',data.intro||'session',[['session','Einmal pro Sitzung'],['always','Bei jedem Aufruf'],['off','Nicht automatisch starten']])}</div><p class="field-hint">Reduzierte Bewegung aus den Systemeinstellungen hat immer Vorrang.</p></div>`:kind==='campaign'?`${field('Partner / Werbetreibender','sponsor',data.sponsor,'text','maxlength="80"')}${textarea('Werbetext','body',data.body,4,'maxlength="1500"')}${select('Standardgrafik','art',data.art||'rings',assetOptions)}${select('Eigenes Bild','image',data.image||'',mediaOptions)}<button type="button" class="button small" id="pick-cover">Mediathek durchsuchen ↗</button><div class="field-grid">${field('Buttontext','link_label',data.link_label,'text','required maxlength="60"')}${field('Zieladresse','link_url',data.link_url,'text','required maxlength="1000"')}</div><div class="field-grid">${field('Sichtbar ab (optional, UTC)','starts_on',data.starts_on,'date')}${field('Sichtbar bis (optional, UTC)','ends_on',data.ends_on,'date')}</div><div class="notice">Die Kennzeichnung „ANZEIGE“ ist fest. Zuerst diese Kampagne veröffentlichen, danach in einem Werbeplatz auswählen. Der Zeitraum wird bei jedem Seitenaufruf geprüft.</div>`:`<div class="asset-inspector"><img src="/static/assets/${e(data.art||'web')}.svg" alt="Standardgrafik">${select('Standardgrafik','art',data.art||'web',assetOptions)}</div>${select('Eigenes Titelbild','image',data.image||'',mediaOptions)}<button type="button" class="button small" id="pick-cover">Mediathek durchsuchen ↗</button>${textarea('Inhalt','body',data.body,7,'maxlength="15000"')}<div class="field-grid">${field('Tags (mit Komma trennen)','tags',(data.tags||[]).join(', '),'text','maxlength="320"')}${field('Reihenfolge','order',data.order,'number','required min="0" max="10000"')}</div>${kind==='article'?`<div class="field-grid">${field('Kategorie','category',data.category,'text','required maxlength="50"')}${field('Autor / Redaktion','author',data.author,'text','required maxlength="80"')}${field('Angezeigtes Beitragsdatum','published_on',data.published_on,'date','required')}</div><p class="field-hint">Das Datum sortiert Beiträge, schaltet sie aber nicht automatisch frei. Zusätzliche Bilder, Tabs und Werbeplätze folgen im Baukasten.</p>`:''}${kind==='project'?`<div class="field-grid">${field('Kategorie','category',data.category,'text','required maxlength="50"')}${field('Jahr','year',data.year,'text','required pattern="20[0-9]{2}"')}${field('Kunde / Kontext','client',data.client,'text','maxlength="80"')}</div>${check('Als fiktives Konzeptprojekt kennzeichnen','demo',!!data.demo)}`:''}`;
 const dialog=modal(`<div class="editor-shell"><header class="modal-header"><div><span class="eyebrow">${kindName[kind]} / ${record?'BEARBEITEN':'NEU ANLEGEN'}</span><h2 id="editor-heading">${e(data.title||'Deine nächste Idee.')}</h2></div><button type="button" class="icon-button close-editor" aria-label="Editor schließen">✕</button></header><div class="editor-toolbar"><div id="record-status"></div><div class="toolbar-actions"><span class="action-help"><button type="button" class="button small" id="history-button">Versionen</button>${helpButton('history')}</span>${kind!=='settings'?`<span class="action-help"><button type="button" class="button small" id="toggle-preview" aria-pressed="true">Vorschau</button>${helpButton('preview')}</span>`:''}</div></div><div class="workflow-strip"><span><b>01</b> Inhalt bearbeiten</span><i>→</i><span><b>02</b> Vorschau prüfen</span><i>→</i><span><b>03</b> Bewusst freigeben</span>${helpButton('publish')}</div>
 <div class="editor-workspace"><form id="record-form" class="editor-fields"><details class="editor-meta" ${!record||kind!=='page'?'open':''}><summary><span><span class="eyebrow">01 / GRUNDLAGEN</span><strong>${kind==='page'?'Seitendaten & Navigation':kind==='settings'?'Marke & Verhalten':'Inhaltsdaten'}</strong></span><span class="meta-summary">${kind==='page'?'Titel, URL und Menü':'Texte, Medien und Darstellung'}</span></summary><div class="meta-fields">${basic}${details}</div></details>${hasBlocks?'<div id="page-builder"></div>':''}<div id="history-panel" hidden></div><p class="form-error" id="editor-error" role="alert"></p></form>
 ${kind!=='settings'?`<aside class="editor-preview"><div class="preview-controls"><span class="preview-live-label">SOFORTVORSCHAU</span><div class="segmented" aria-label="Vorschaugröße"><button type="button" data-device="1200" aria-pressed="true">Desktop</button><button type="button" data-device="768" aria-pressed="false">Tablet</button><button type="button" data-device="390" aria-pressed="false">Mobil</button></div></div><div class="preview-experience-tools"><button type="button" class="button small" id="preview-mode" aria-pressed="false">Auswahlmodus</button><button type="button" class="button small" id="preview-play">↻ Animation testen</button><button type="button" class="button small" id="preview-pause" aria-pressed="false">Live pausieren</button><button type="button" class="button small" id="preview-expand" aria-pressed="false">Großansicht ↗</button></div><div class="preview-help" id="preview-status" role="status">Wird vorbereitet …</div><div class="preview-stage"><iframe title="Sofortvorschau der aktuellen Eingaben"></iframe></div><div class="preview-bottom"><span id="preview-size">1200 px · eingepasst</span><span>Modul anklicken zum Auswählen</span>${helpButton('preview')}</div></aside>`:''}</div>
 <footer class="editor-footer"><div class="save-indicator"><span class="save-dot"></span><span id="save-status" role="status">${canEdit?'Vorschau speichert nicht. Entwurf bewusst sichern.':'Prüfansicht · keine Bearbeitungsrechte'}</span></div><div><a class="button small" target="_blank" rel="noopener" id="live-link" hidden>Live ↗</a>${canEdit?`<span class="action-help"><button type="submit" form="record-form" class="button" id="save-button">Entwurf speichern</button>${helpButton('save')}</span><span class="action-help"><button type="button" class="button" id="submit-button">Zur Prüfung</button>${helpButton('submit')}</span>`:''}${user.role==='admin'?'<button type="button" class="button primary" id="publish-button">Veröffentlichen ↗</button>':''}${user.role==='moderator'?'<button type="button" class="button primary" id="approve-button" hidden>Freigeben ↗</button>':''}<button type="button" class="button small danger-text" id="unpublish-button" hidden>Offline nehmen</button></div></footer></div>`);
 dialog.className='editor-dialog editor-v2'+(kind!=='settings'?' with-preview':'');dialog.setAttribute('aria-labelledby','editor-heading');
 const form=dialog.querySelector<HTMLFormElement>('#record-form')!;
 const error=dialog.querySelector<HTMLElement>('#editor-error')!;
 const frame=dialog.querySelector<HTMLIFrameElement>('iframe');
 let previewPaused=false,previewInteractive=false,pendingHTML='',frameReady=false;
 let dirty=!!initial,busy=false,closed=false,previewTimer:number|undefined,previewSequence=0,previewAbort:AbortController|undefined;
 let builder:PageBuilder|undefined;
 function markDirty():void{dirty=true;dialog.querySelector('#save-status')!.textContent='Ungespeichert · Strg / Cmd + S zum Sichern';dialog.querySelector('.save-dot')!.classList.add('is-dirty');schedulePreview();}
 if(hasBlocks)builder=new PageBuilder(dialog.querySelector<HTMLElement>('#page-builder')!,data.blocks||[],catalog,media,user,markDirty);
 if(!canEdit)form.querySelectorAll<HTMLInputElement|HTMLTextAreaElement|HTMLSelectElement>('.meta-fields input,.meta-fields textarea,.meta-fields select').forEach(el=>el.disabled=true);
  form.addEventListener('input',event=>{if(!(event.target as Element).closest('#page-builder'))markDirty();});
  const designSelect=form.querySelector<HTMLSelectElement>('[name=design]');
  const syncDesign=():void=>{dialog.querySelectorAll<HTMLButtonElement>('[data-design-option]').forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.designOption===designSelect?.value)));};
  designSelect?.addEventListener('change',()=>{syncDesign();markDirty();});
  dialog.querySelectorAll<HTMLButtonElement>('[data-design-option]').forEach(button=>button.addEventListener('click',()=>{if(!canEdit||!designSelect)return;designSelect.value=button.dataset.designOption||'studio';syncDesign();markDirty();}));
 form.querySelector<HTMLSelectElement>('[name=art]')?.addEventListener('change',event=>{const image=form.querySelector<HTMLImageElement>('.asset-inspector img');if(image)image.src=assetUrl((event.target as HTMLSelectElement).value);});
 dialog.querySelector('#pick-cover')?.addEventListener('click',()=>{if(!canEdit)return;const input=form.querySelector<HTMLSelectElement>('[name=image]');if(input)void pickMedia(m=>setMediaSelect(input,m));});
 const val=(name:string):string=>form.querySelector<HTMLInputElement|HTMLTextAreaElement|HTMLSelectElement>(`[name="${name}"]`)?.value||'';
 const checked=(name:string):boolean=>form.querySelector<HTMLInputElement>(`[name="${name}"]`)?.checked||false;
 const slug=form.querySelector<HTMLInputElement>('[name=slug]')!;
 form.querySelector<HTMLInputElement>('[name=title]')!.addEventListener('input',()=>{
  if(!current&&!slug.dataset.edited)slug.value=val('title').toLowerCase().replace(/ä/g,'ae').replace(/ö/g,'oe').replace(/ü/g,'ue').replace(/ß/g,'ss').replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'').slice(0,64);
  dialog.querySelector('#editor-heading')!.textContent=val('title')||'Deine nächste Idee.';
 });
 slug.addEventListener('input',()=>{slug.dataset.edited='true';});
 function collect():ContentData{
  const next:ContentData={...data,title:val('title'),slug:val('slug'),description:val('description')};
  if(kind==='page')Object.assign(next,{blocks:builder!.value,in_navigation:checked('in_navigation'),navigation_label:val('navigation_label'),order:Number(val('order')||0)});
  if(kind==='service'||kind==='project'||kind==='article')Object.assign(next,{art:val('art'),body:val('body'),tags:val('tags').split(',').map(t=>t.trim()).filter(Boolean),image:val('image'),order:Number(val('order')||0)});
  if(kind==='article')Object.assign(next,{category:val('category'),author:val('author'),published_on:val('published_on'),blocks:builder!.value});
  if(kind==='campaign')Object.assign(next,{sponsor:val('sponsor'),body:val('body'),image:val('image'),art:val('art'),link_label:val('link_label'),link_url:val('link_url'),starts_on:val('starts_on'),ends_on:val('ends_on')});
  if(kind==='project')Object.assign(next,{category:val('category'),client:val('client'),year:val('year'),demo:checked('demo')});
  if(kind==='settings')Object.assign(next,{brand:val('brand'),tagline:val('tagline'),accent:val('accent'),design:val('design'),email:val('email'),location:val('location'),motion:val('motion'),intro:val('intro'),analytics_enabled:checked('analytics_enabled'),news_in_navigation:checked('news_in_navigation')});
  return next;
 }
 function updateStatus():void{
  dialog.querySelector('#record-status')!.innerHTML=current?`${badge(current.state)} <span class="muted">Version ${current.revision}</span> ${current.live?'<span class="live-snapshot-badge">● Live-Stand vorhanden</span>':''}`:`${badge('draft')} <span class="muted">Noch nicht gespeichert</span>`;
  dialog.querySelector<HTMLButtonElement>('#history-button')!.disabled=!current;
  const live=dialog.querySelector<HTMLAnchorElement>('#live-link')!;live.hidden=!current?.live;if(current?.live)live.href=kind==='settings'?'/':publicPath(current);live.textContent=kind==='campaign'?'Kampagnenvorschau ↗':'Live ↗';
  dialog.querySelector<HTMLButtonElement>('#unpublish-button')!.hidden=!current?.live||user.role==='editor'||kind==='settings';
  const approve=dialog.querySelector<HTMLButtonElement>('#approve-button');if(approve)approve.hidden=current?.state!=='pending';
 }
 function schedulePreview():void{if(!frame||closed||previewPaused)return;clearTimeout(previewTimer);previewTimer=window.setTimeout(()=>void renderPreview(),500);}
 async function renderPreview():Promise<void>{
  if(!frame||closed||previewPaused||dialog.querySelector<HTMLElement>('.editor-preview')!.hidden)return;
  previewAbort?.abort();previewAbort=new AbortController();const sequence=++previewSequence;
  const status=dialog.querySelector<HTMLElement>('#preview-status')!;status.textContent='Aktuelle Eingaben werden geprüft …';status.classList.remove('preview-warning');
  try{
   const next=collect();
   // A named placeholder permits an empty new page to be previewed, not saved.
   if(!next.title.trim())next.title='Neue Seite';if(!next.slug.trim())next.slug='vorschau';
   const result=await api<{html:string}>('/api/admin/preview',{...json('POST',{kind,data:next}),signal:previewAbort.signal});
   if(sequence!==previewSequence||closed||previewPaused)return;
   pendingHTML=result.html;
   if(frameReady)frame.contentWindow?.postMessage({type:'studio-preview-patch',html:result.html},location.origin);else frame.srcdoc=result.html;
   status.textContent='Aktuelle Eingaben · nicht automatisch gespeichert. Verknüpfte Inhalte: Live-Stand.';
  }catch(err){if(sequence!==previewSequence||closed||err instanceof DOMException&&err.name==='AbortError')return;status.textContent='Letzte gültige Vorschau · '+errorMessage(err);status.classList.add('preview-warning');}
 }
 let deviceWidth=1200;
 const stage=dialog.querySelector<HTMLElement>('.preview-stage');
 function fitPreview():void{if(!frame||!stage||stage.clientWidth<1)return;const scale=Math.min(1,stage.clientWidth/deviceWidth);frame.style.width=`${deviceWidth}px`;frame.style.height=`${Math.max(500,stage.clientHeight/scale)}px`;frame.style.transform=`scale(${scale})`;dialog.querySelector('#preview-size')!.textContent=`${deviceWidth} px · ${Math.round(scale*100)} %`;}
 const resizeObserver=stage?new ResizeObserver(fitPreview):null;if(stage)resizeObserver?.observe(stage);
 dialog.querySelectorAll<HTMLButtonElement>('[data-device]').forEach(button=>button.addEventListener('click',()=>{deviceWidth=Number(button.dataset.device);dialog.querySelectorAll<HTMLButtonElement>('[data-device]').forEach(b=>b.setAttribute('aria-pressed',String(b===button)));fitPreview();}));
 dialog.querySelector('#toggle-preview')?.addEventListener('click',()=>{const preview=dialog.querySelector<HTMLElement>('.editor-preview')!;preview.hidden=!preview.hidden;dialog.classList.toggle('with-preview',!preview.hidden);dialog.querySelector('#toggle-preview')!.setAttribute('aria-pressed',String(!preview.hidden));if(!preview.hidden){fitPreview();void renderPreview();}});
 const sendPreview=(data:unknown):void=>frame?.contentWindow?.postMessage(data,location.origin);
 frame?.addEventListener('load',()=>{if(!frame.contentDocument?.body.classList.contains('is-preview'))return;frameReady=true;fitPreview();sendPreview({type:'studio-preview-mode',interactive:previewInteractive});});
 dialog.querySelector('#preview-mode')?.addEventListener('click',()=>{previewInteractive=!previewInteractive;const button=dialog.querySelector('#preview-mode')!;button.setAttribute('aria-pressed',String(previewInteractive));button.textContent=previewInteractive?'Testmodus · Interaktiv':'Auswahlmodus';sendPreview({type:'studio-preview-mode',interactive:previewInteractive});});
 dialog.querySelector('#preview-play')?.addEventListener('click',()=>sendPreview({type:'studio-preview-play'}));
 dialog.querySelector('#preview-expand')?.addEventListener('click',()=>{const expanded=dialog.classList.toggle('preview-focus');dialog.querySelector('#preview-expand')!.setAttribute('aria-pressed',String(expanded));dialog.querySelector('#preview-expand')!.textContent=expanded?'Zur Bearbeitung ←':'Großansicht ↗';requestAnimationFrame(fitPreview);});
 dialog.querySelector('#preview-pause')?.addEventListener('click',()=>{previewPaused=!previewPaused;dialog.querySelector('#preview-pause')!.setAttribute('aria-pressed',String(previewPaused));dialog.querySelector('#preview-pause')!.textContent=previewPaused?'Live fortsetzen':'Live pausieren';if(previewPaused){clearTimeout(previewTimer);previewAbort?.abort();previewSequence++;}else void renderPreview();});
 dialog.addEventListener('studio-module-selected',event=>{const detail=(event as CustomEvent<{id:string}>).detail;sendPreview({type:'studio-preview-select',id:detail.id});});
 const onMessage=(event:MessageEvent):void=>{
  if(event.origin!==location.origin||event.source!==frame?.contentWindow)return;
  if(event.data?.type==='studio-select-block'&&typeof event.data.id==='string')builder?.focusId(event.data.id);
  if(event.data?.type==='studio-preview-link')toast('Vorschaulinks öffnen keine andere Seite. Zum echten Test „Live“ verwenden.');
 };
 window.addEventListener('message',onMessage);
 const beforeUnload=(event:BeforeUnloadEvent):void=>{if(dirty){event.preventDefault();event.returnValue='';}};window.addEventListener('beforeunload',beforeUnload);
 const close=():void=>{if(busy){toast('Der Speichervorgang läuft noch.');return;}if(!dirty||confirm('Ungespeicherte Änderungen verwerfen? Die Vorschau allein speichert nicht.')){dialog.close();refresh();}};
 dialog.querySelector('.close-editor')!.addEventListener('click',close);dialog.oncancel=event=>{event.preventDefault();close();};
 const onKey=(event:KeyboardEvent):void=>{if((event.ctrlKey||event.metaKey)&&event.key.toLowerCase()==='s'&&dialog.open&&Array.from(document.querySelectorAll('dialog[open]')).at(-1)===dialog){event.preventDefault();if(canEdit)void save();}};window.addEventListener('keydown',onKey);
 const cleanup=():void=>{closed=true;clearTimeout(previewTimer);previewAbort?.abort();resizeObserver?.disconnect();builder?.destroy();window.removeEventListener('beforeunload',beforeUnload);window.removeEventListener('keydown',onKey);window.removeEventListener('message',onMessage);dialog.removeEventListener('close',cleanup);dialog.removeEventListener('studio-replace',cleanup);};
 dialog.addEventListener('close',cleanup);dialog.addEventListener('studio-replace',cleanup);
 async function save(action='save'):Promise<void>{
  if(busy||!canEdit)return;
  form.querySelectorAll<HTMLElement>(':invalid').forEach(el=>{let parent=el.parentElement;while(parent&&parent!==form){if(parent instanceof HTMLDetailsElement)parent.open=true;parent=parent.parentElement;}});
  if(!form.reportValidity())return;
  const next=collect();busy=true;error.textContent='';form.inert=true;
  dialog.querySelectorAll<HTMLButtonElement>('.editor-footer button').forEach(b=>b.disabled=true);
  try{
   current=current?await api<RecordItem>(`/api/admin/content/${current.id}`,json('PATCH',{data:next,expected_revision:current.revision})):await api<RecordItem>('/api/admin/content',json('POST',{kind,data:next}));
   dirty=false;dialog.querySelector('.save-dot')!.classList.remove('is-dirty');updateStatus();
   if(action!=='save')current=await api<RecordItem>(`/api/admin/content/${current.id}/${action}`,json('POST',{expected_revision:current.revision}));
   updateStatus();dialog.querySelector('#save-status')!.textContent=`Gespeichert · ${new Date().toLocaleTimeString('de-DE',{hour:'2-digit',minute:'2-digit'})}`;
   toast(action==='publish'?'Veröffentlicht. Dieser Stand ist jetzt öffentlich.':action==='submit'?'Gespeichert und zur Prüfung eingereicht.':'Entwurf gespeichert. Der Live-Stand bleibt unverändert.');
  }catch(err){error.textContent=errorMessage(err);toast(errorMessage(err),true);}
  finally{busy=false;form.inert=false;dialog.querySelectorAll<HTMLButtonElement>('.editor-footer button').forEach(b=>b.disabled=false);updateStatus();refresh();}
 }
 form.addEventListener('submit',event=>{event.preventDefault();void save();});
 dialog.querySelector('#submit-button')?.addEventListener('click',()=>void save('submit'));
 dialog.querySelector('#publish-button')?.addEventListener('click',()=>{if(confirm('Diesen Stand jetzt öffentlich veröffentlichen? Prüfe vorher Texte, Links und die mobile Vorschau.'))void save('publish');});
 dialog.querySelector('#approve-button')?.addEventListener('click',async()=>{if(!current||busy||!confirm('Diesen eingereichten Stand öffentlich freigeben?'))return;busy=true;try{current=await api<RecordItem>(`/api/admin/content/${current.id}/publish`,json('POST',{expected_revision:current.revision}));updateStatus();toast('Inhalt freigegeben.');refresh();}catch(err){toast(errorMessage(err),true);}finally{busy=false;}});
 dialog.querySelector('#unpublish-button')?.addEventListener('click',async()=>{if(!current||busy||!confirm('Diesen Inhalt offline nehmen? Ungespeicherte Eingaben werden verworfen; gespeicherte Versionen bleiben erhalten.'))return;busy=true;try{await api(`/api/admin/content/${current.id}/unpublish`,json('POST',{expected_revision:current.revision}));dirty=false;dialog.close();refresh();toast('Offline genommen.');}catch(err){toast(errorMessage(err),true);}finally{busy=false;}});
 dialog.querySelector('#history-button')!.addEventListener('click',async()=>{
  if(!current)return;
  try{
   const revisions=await api<Revision[]>(`/api/admin/content/${current.id}/history`);
   const panel=dialog.querySelector<HTMLElement>('#history-panel')!;panel.hidden=!panel.hidden;
   panel.innerHTML=`<div class="panel-heading"><h3>Gespeicherte Versionen</h3>${helpButton('history')}</div><p class="field-hint">Wiederherstellen erzeugt einen neuen Entwurf. Der Live-Stand bleibt unverändert.</p>`+revisions.map(rev=>`<div class="history-row"><span><strong>Version ${rev.revision}</strong><small>${date(rev.created_at)} · ${e(rev.name||'Demo-System')} · ${e(rev.action)}</small></span>${canEdit?`<button type="button" class="button small" data-restore="${rev.revision}">Wiederherstellen</button>`:''}</div>`).join('');panel.scrollIntoView({block:'nearest'});
   panel.querySelectorAll<HTMLButtonElement>('[data-restore]').forEach(button=>button.addEventListener('click',async()=>{if(!current||busy||!confirm('Diese Version als neuen Entwurf übernehmen? Ungespeicherte Eingaben gehen verloren.'))return;busy=true;try{const restored=await api<RecordItem>(`/api/admin/content/${current.id}/restore/${button.dataset.restore}`,json('POST',{expected_revision:current.revision}));dirty=false;await openEditor(restored,kind,user,refresh);refresh();toast('Version als Entwurf wiederhergestellt.');}catch(err){toast(errorMessage(err),true);}finally{busy=false;}}));
  }catch(err){toast(errorMessage(err),true);}
 });
 updateStatus();fitPreview();void renderPreview();
}
