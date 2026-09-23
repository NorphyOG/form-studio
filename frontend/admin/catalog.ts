import {api,json} from './api.js';
import {escape as e,overlay,field,toast,errorMessage} from './ui.js';
import {helpButton,registerHelp} from './help.js';
import type {Block,Catalog,Preset,User} from './types.js';
let cache:Promise<Catalog>|null=null;
export function getCatalog():Promise<Catalog>{
 if(!cache)cache=api<Catalog>('/api/admin/catalog').then(catalog=>{
  catalog.modules.forEach(module=>registerHelp('module:'+module.type,{title:module.name,short:module.description,paragraphs:[module.description+' Alle Texte sind als Entwurf editierbar. Eine vorhandene öffentliche Version bleibt bis zur nächsten Freigabe unverändert.',module.type==='bento'||module.type==='projects'?'Die sichtbaren Karten stammen aus separat veröffentlichten Leistungen beziehungsweise Projekten. Lege neue Einträge im passenden Inhaltsbereich an. Ein Modulduplikat erzeugt keine neuen Leistungen oder Projekte.':module.type==='advert'?'Zuerst unter Werbung & Partner eine Kampagne erstellen und freigeben. Anschließend dieses Modul mit der Kampagne verbinden und die Seite freigeben. Ohne aktive Kampagne wird öffentlich kein Platzhalter angezeigt. Die ANZEIGE-Kennzeichnung ist fest.':module.type==='news'?'Beiträge werden unter Journal & News gepflegt. Nach Freigabe erscheinen sie hier automatisch, optional nach exakter Kategorie gefiltert. Ein bis zwölf Karten; alle weiteren Beiträge bleiben im Journal erreichbar.':module.type==='comparison'?'Genau zwei Einträge anlegen, Bilder oder Standardgrafiken auswählen und passende Bezeichnungen vergeben. Im Vorschau-Testmodus den Regler verschieben. Ohne JavaScript erscheinen beide Bilder nebeneinander.':'Modul hinzufügen, Beispieltexte ersetzen und die Einträge sowie Darstellungsoptionen anpassen. Die Vorschau rendert aktuelle Eingaben nach einer kurzen Pause ohne Speicherung.'],example:module.category+' / '+module.name,note:module.type==='pricing'?'Nur Darstellung von Angebotspaketen, kein Warenkorb oder Zahlungsprozess.':undefined}));
  return catalog;
 }).catch(err=>{cache=null;throw err;});
 return cache;
}
export function cloneBlock(block:Block):Block{
 // getRandomValues also works in preview/test contexts without randomUUID.
 const id=typeof crypto.randomUUID==='function'?crypto.randomUUID():Array.from(crypto.getRandomValues(new Uint8Array(16)),n=>n.toString(16).padStart(2,'0')).join('');
 return {...structuredClone(block),id:'b-'+id};
}
export function miniModule(type:string):string{return `<div class="module-mini mini-${e(type)}" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i></div>`;}
export async function openCatalog(catalog:Catalog,user:User,remaining:number,onInsert:(blocks:Block[])=>void):Promise<void>{
 const presets=await api<Preset[]>('/api/admin/block-presets');
 let tab='modules',category='Alle';
 const dialog=overlay(`<header class="modal-header"><div><span class="eyebrow">DEIN BAUKASTEN / ${catalog.modules.length} MODULE</span><h2>Was soll deine Seite können?</h2><p class="field-hint">Bausteine auswählen. Ideen zusammensetzen. ${remaining} freie Modulplätze.</p></div><button class="icon-button" data-close aria-label="Modulkatalog schließen">✕</button></header><div class="library-controls"><div class="segmented" aria-label="Bibliotheksbereich"><button type="button" data-tab="modules" aria-pressed="true">Module</button><button type="button" data-tab="templates" aria-pressed="false">Seitenvorlagen</button><button type="button" data-tab="presets" aria-pressed="false">Eigene Bausteine <span>${presets.length}</span></button></div><input type="search" id="library-search" placeholder="Baustein suchen …" aria-label="Bausteine durchsuchen"><div class="library-categories"></div></div><div class="library-content"></div><footer class="library-footer"><span>Vorlagen werden angehängt – bestehende Inhalte bleiben erhalten.</span>${helpButton('templates')}</footer>`,'library-dialog');
 const input=dialog.querySelector<HTMLInputElement>('#library-search')!;
 function insert(blocks:Block[]):void{if(blocks.length>remaining){toast(`Es sind nur noch ${remaining} Modulplätze frei.`,true);return;}onInsert(blocks.map(cloneBlock));dialog.close();}
 function render():void{
  const query=input.value.trim().toLowerCase();const content=dialog.querySelector<HTMLElement>('.library-content')!;
  dialog.querySelectorAll<HTMLButtonElement>('[data-tab]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.tab===tab)));
  const cats=dialog.querySelector<HTMLElement>('.library-categories')!;
  cats.innerHTML=tab==='modules'?['Alle',...new Set(catalog.modules.map(m=>m.category))].map(c=>`<button type="button" class="category-chip" data-category="${e(c)}" aria-pressed="${c===category}">${e(c)}</button>`).join(''):'';
  cats.querySelectorAll<HTMLButtonElement>('button').forEach(b=>b.addEventListener('click',()=>{category=b.dataset.category!;render();}));
  if(tab==='modules'){
   const modules=catalog.modules.filter(m=>(category==='Alle'||m.category===category)&&`${m.name} ${m.description} ${m.keywords||m.type}`.toLowerCase().includes(query));
   content.innerHTML=`<div class="library-grid">${modules.map(m=>`<article class="library-card">${miniModule(m.type)}<div class="library-card-title"><span class="eyebrow">${e(m.category)}</span>${helpButton('module:'+m.type)}</div><h3>${e(m.name)}</h3><p>${e(m.description)}</p><button type="button" class="button" data-insert="${m.type}" ${remaining<1?'disabled':''}>＋ Hinzufügen</button></article>`).join('')}</div>${modules.length?'':'<div class="empty-state">Keine passenden Bausteine. Versuche einen anderen Begriff.</div>'}`;
   content.querySelectorAll<HTMLButtonElement>('[data-insert]').forEach(b=>b.addEventListener('click',()=>insert([catalog.modules.find(m=>m.type===b.dataset.insert)!.defaults])));
  }else if(tab==='templates'){
   const templates=catalog.templates.filter(t=>`${t.name} ${t.description}`.toLowerCase().includes(query));
   content.innerHTML=`<div class="template-grid">${templates.map(t=>`<article class="library-card template-card"><div class="template-stack">${t.blocks.slice(0,4).map(b=>miniModule(b.type)).join('')}</div><span class="eyebrow">${t.blocks.length} VORBEREITETE MODULE</span><h3>${e(t.name)}</h3><p>${e(t.description)}</p><button type="button" class="button primary" data-template="${e(t.id)}" ${t.blocks.length>remaining?'disabled':''}>Vorlage anhängen ↗</button></article>`).join('')}</div>`;
   content.querySelectorAll<HTMLButtonElement>('[data-template]').forEach(b=>b.addEventListener('click',()=>insert(catalog.templates.find(t=>t.id===b.dataset.template)!.blocks)));
  }else{
   const visible=presets.filter(p=>p.name.toLowerCase().includes(query));
   content.innerHTML=visible.length?`<div class="library-grid">${visible.map(p=>`<article class="library-card">${miniModule(p.block.type)}<span class="eyebrow">EIGENER BAUSTEIN</span><h3>${e(p.name)}</h3><p>Unabhängige Kopie · ${e(catalog.modules.find(m=>m.type===p.block.type)?.name||p.block.type)}</p><button type="button" class="button" data-preset="${p.id}" ${remaining<1?'disabled':''}>＋ Einfügen</button>${user.role==='admin'||p.created_by===user.id?`<button type="button" class="button small danger-text" data-delete-preset="${p.id}">Aus Bibliothek entfernen</button>`:''}</article>`).join('')}</div>`:'<div class="empty-state"><h3>Noch kein passender eigener Baustein.</h3><p>Öffne ein Modul und wähle „Als Baustein speichern“. Seine Kopie steht danach hier bereit.</p></div>';
   content.querySelectorAll<HTMLButtonElement>('[data-preset]').forEach(b=>b.addEventListener('click',()=>insert([presets.find(p=>p.id===b.dataset.preset)!.block])));
   content.querySelectorAll<HTMLButtonElement>('[data-delete-preset]').forEach(b=>b.addEventListener('click',async()=>{if(!confirm('Diese Vorlage entfernen? Bereits eingefügte Kopien bleiben erhalten.'))return;try{await api('/api/admin/block-presets/'+b.dataset.deletePreset,{method:'DELETE'});presets.splice(presets.findIndex(p=>p.id===b.dataset.deletePreset),1);render();toast('Vorlage entfernt.');}catch(err){toast(errorMessage(err),true);}}));
  }
 }
 dialog.querySelectorAll<HTMLButtonElement>('[data-tab]').forEach(b=>b.addEventListener('click',()=>{tab=b.dataset.tab!;render();}));
 input.addEventListener('input',render);render();input.focus();
}
export function saveAsPreset(block:Block):void{
 const dialog=overlay(`<header class="modal-header"><div><span class="eyebrow">BIBLIOTHEK / EIGENER BAUSTEIN</span><h2>Einmal vorbereiten. Wiederverwenden.</h2></div><button class="icon-button" data-close aria-label="Schließen">✕</button></header><form id="preset-form" class="modal-body">${field('Name des Bausteins','name',block.title.replace(/\n/g,' ').slice(0,80),'text','required minlength="2" maxlength="80"','preset')}<p class="field-hint">Speichert eine Kopie. Deine Seite wird dabei nicht gespeichert oder veröffentlicht. Bilder bleiben referenziert.</p><p class="form-error" role="alert"></p><button type="submit" class="button primary">Baustein speichern</button></form>`,'preset-dialog');
 dialog.querySelector('form')!.addEventListener('submit',async event=>{event.preventDefault();const button=dialog.querySelector<HTMLButtonElement>('button[type=submit]')!;button.disabled=true;try{await api('/api/admin/block-presets',json('POST',{name:(new FormData(event.target as HTMLFormElement)).get('name'),block}));dialog.close();toast('Baustein in der gemeinsamen Bibliothek gespeichert.');}catch(err){dialog.querySelector('.form-error')!.textContent=errorMessage(err);}finally{button.disabled=false;}});
}
