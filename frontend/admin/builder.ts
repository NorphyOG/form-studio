import {pickMedia,pickCampaign,setMediaSelect} from './pickers.js';
import {field,textarea,select,check,escape as e,toast,errorMessage} from './ui.js';
import {helpButton} from './help.js';
import {openCatalog,cloneBlock,saveAsPreset} from './catalog.js';
import {assetUrl} from './asset-url.js';
import type {Block,BlockItem,Catalog,Media,User} from './types.js';

type Control=HTMLInputElement|HTMLTextAreaElement|HTMLSelectElement;
export class PageBuilder {
 private blocks:Block[];
 private selected=0;
 private snapshots:string[]=[];
 private cursor=0;
 private timer:number|undefined;
 private editable:boolean;
 constructor(private root:HTMLElement,initial:Block[],private catalog:Catalog,private media:Media[],private user:User,private onChange:()=>void){
  this.editable=user.role!=='moderator';
  this.blocks=initial.map(block=>({...structuredClone(catalog.modules.find(m=>m.type===block.type)!.defaults),...structuredClone(block)}));
  this.snapshots=[JSON.stringify(this.blocks)];this.render();
 }
 get value():Block[]{this.collect();return structuredClone(this.blocks);}
 destroy():void{clearTimeout(this.timer);}
 private collect():void{
  this.root.querySelectorAll<HTMLElement>('[data-block-index]').forEach(row=>{
   const block=this.blocks[Number(row.dataset.blockIndex)];if(!block)return;
   const next=block as unknown as Record<string,unknown>;
   row.querySelectorAll<Control>('[data-bfield]').forEach(input=>{next[input.dataset.bfield!]=input instanceof HTMLInputElement&&input.type==='checkbox'?input.checked:['columns','limit'].includes(input.dataset.bfield!)?Number(input.value):input.value;});
   const itemRows=row.querySelectorAll<HTMLElement>('[data-item-index]');
   if(itemRows.length || this.catalog.modules.find(m=>m.type===block.type)!.supports.includes('items')){
    block.items=Array.from(itemRows).map(itemRow=>{
     const old=block.items[Number(itemRow.dataset.itemIndex)]||{title:'',text:''};
     const item={...old} as unknown as Record<string,unknown>;
     itemRow.querySelectorAll<Control>('[data-ifield]').forEach(input=>{item[input.dataset.ifield!]=input.value;});
     return item as unknown as BlockItem;
    });
   }
  });
 }
 private remember():void{
  clearTimeout(this.timer);const state=JSON.stringify(this.blocks);
  if(state===this.snapshots[this.cursor])return;
  this.snapshots=this.snapshots.slice(0,this.cursor+1);this.snapshots.push(state);
  if(this.snapshots.length>50)this.snapshots.shift();this.cursor=this.snapshots.length-1;this.syncHistoryButtons();
 }
 private syncHistoryButtons():void{
  const undo=this.root.querySelector<HTMLButtonElement>('[data-undo]'),redo=this.root.querySelector<HTMLButtonElement>('[data-redo]');
  if(undo)undo.disabled=!this.editable||this.cursor===0;if(redo)redo.disabled=!this.editable||this.cursor===this.snapshots.length-1;
 }
 private change(callback:()=>void):void{
  if(!this.editable)return;this.collect();this.remember();callback();this.remember();this.render();this.onChange();
 }
 insert(blocks:Block[]):void{
  if(this.blocks.length+blocks.length>this.catalog.limits.blocks){toast('Eine Seite kann höchstens 30 Module enthalten.',true);return;}
  this.change(()=>{this.selected=this.blocks.length;this.blocks.push(...blocks);});this.focusIndex(this.selected);
 }
 focusId(id:string):void{const index=this.blocks.findIndex(b=>b.id===id);if(index>=0)this.focusIndex(index);}
 private focusIndex(index:number):void{
  this.selected=index;this.root.dispatchEvent(new CustomEvent('studio-module-selected',{bubbles:true,detail:{id:this.blocks[index]?.id}}));this.root.querySelectorAll<HTMLDetailsElement>('.block-editor').forEach((row,i)=>{row.open=i===index;});
  const row=this.root.querySelector<HTMLElement>(`[data-block-index="${index}"]`);row?.scrollIntoView({block:'nearest',behavior:'smooth'});
  this.root.querySelectorAll<HTMLElement>('[data-outline]').forEach(b=>b.classList.toggle('active',Number(b.dataset.outline)===index));
 }
 private blockFields(block:Block,index:number):string{
  const spec=this.catalog.modules.find(m=>m.type===block.type)!;const supports=spec.supports;const maxItems=['contact','comparison'].includes(block.type)?2:20;
  const opts=this.catalog.assets.map(a=>[a.id,a.name] as [string,string]);
  const images:[string,string][]=[['','Standardgrafik verwenden'],...this.media.map(m=>[m.id,m.alt] as [string,string])];
  const f=(label:string,key:string,value:unknown,helpKey=key,extra='')=>field(label,`b${index}-${key}`,value,'text',`data-bfield="${key}" ${extra}`,helpKey);
  const t=(label:string,key:string,value:unknown,helpKey=key)=>textarea(label,`b${index}-${key}`,value,key==='text'?3:2,`data-bfield="${key}" maxlength="${key==='text'?10000:150}"`,helpKey);
  const s=(label:string,key:string,value:string,options:[string,string][])=>select(label,`b${index}-${key}`,value,options,`data-bfield="${key}"`,key);
  return `<div class="module-description">${e(spec.description)} ${helpButton('module:'+block.type)}</div><div class="block-tools">${check('Sichtbar',`b${index}-enabled`,block.enabled,'enabled','data-bfield="enabled"')}<div><button type="button" class="icon-button" data-move="${index}:-1" aria-label="Modul nach oben" ${index===0?'disabled':''}>↑</button><button type="button" class="icon-button" data-move="${index}:1" aria-label="Modul nach unten" ${index===this.blocks.length-1?'disabled':''}>↓</button><button type="button" class="icon-button" data-duplicate-block="${index}" aria-label="Modul duplizieren" ${this.blocks.length>=30?'disabled':''}>⧉</button><button type="button" class="icon-button danger-text" data-remove-block="${index}" aria-label="Modul entfernen">×</button></div></div>
   ${f('Kleine Überschrift','eyebrow',block.eyebrow,'eyebrow','maxlength="80"')}${t(block.type==='quote'?'Zitat':'Überschrift','title',block.title,'block_title')}${supports.includes('text')?t(block.type==='quote'?'Quelle / Einordnung':'Text','text',block.text):''}
   ${supports.includes('art')?`<div class="asset-inspector"><img src="/static/assets/${e(block.art||'space')}.svg" alt="Vorschau der Standardgrafik">${s('Standardgrafik','art',block.art||'space',opts)}</div>`:''}
   ${supports.includes('image')?s('Eigenes Bild','image',block.image||'',images)+'<button type="button" class="button small" data-pick-media="'+index+'">Mediathek durchsuchen ↗</button>':''}
   ${supports.includes('news')?`<div class="field-grid">${f('Kategorie (leer = alle)','category',block.category||'','news_category','maxlength="50"')}${s('Anzahl Beiträge','limit',String(block.limit||6),Array.from({length:12},(_,i)=>[String(i+1),String(i+1)] as [string,string]))}</div><p class="field-hint">Beiträge unter „Journal & News“ anlegen und veröffentlichen. Der Inhalt bleibt zentral gepflegt.</p>`:''}
   ${supports.includes('campaign')?`<div class="campaign-slot-field">${f('Kampagnen-ID','campaign',block.campaign||'','campaign','readonly')}<button type="button" class="button" data-pick-campaign="${index}">Kampagne auswählen ↗</button><p class="field-hint">Ohne aktive Kampagne öffentlich unsichtbar. Keine Fremd-Skripte oder HTML-Einbettungen.</p></div>`:''}
   ${supports.includes('link')?`<div class="field-grid">${f('Linktext','link_label',block.link_label||'','link_label','maxlength="60"')}${f('Linkziel','link_url',block.link_url||'','link_url','maxlength="1000"')}</div>`:''}
   ${supports.includes('items')?`<div class="items-heading"><h4>Einträge <span>${block.items.length} / ${maxItems}</span></h4>${helpButton('items')}</div><div class="block-items">${block.items.map((item,j)=>{
     const attr=(key:string)=>`data-ifield="${key}"`;
     const name=(key:string)=>`b${index}-i${j}-${key}`;
     return `<div class="block-item" data-item-index="${j}"><div class="item-header"><span>${String(j+1).padStart(2,'0')} / ${block.type==='faq'?'FRAGE':'EINTRAG'}</span><div><button type="button" class="icon-button" data-item-move="${index}:${j}:-1" aria-label="Eintrag nach oben" ${j===0?'disabled':''}>↑</button><button type="button" class="icon-button" data-item-move="${index}:${j}:1" aria-label="Eintrag nach unten" ${j===block.items.length-1?'disabled':''}>↓</button><button type="button" class="icon-button" data-remove-item="${index}:${j}" aria-label="Eintrag entfernen">×</button></div></div>${field(block.type==='faq'?'Frage':'Titel',name('title'),item.title,'text',`${attr('title')} required maxlength="150"`,'item_title')}${textarea(block.type==='faq'?'Antwort':'Beschreibung',name('text'),item.text,2,`${attr('text')} maxlength="3000"`,'text')}${supports.includes('values')?field('Wert / Preistext',name('value'),item.value||'','text',`${attr('value')} maxlength="60"`,'value'):''}${supports.includes('art_items')?select('Grafik',name('art'),item.art||'brand',opts,attr('art'),'art'):''}${supports.includes('image_items')?select('Eigenes Bild',name('image'),item.image||'',images,attr('image'),'image')+`<button type="button" class="button small" data-pick-item-media="${index}:${j}">Mediathek durchsuchen ↗</button>`:''}${supports.includes('links_items')?`<div class="field-grid">${field('Linktext',name('link_label'),item.link_label||'','text',`${attr('link_label')} maxlength="60"`,'link_label')}${field('Linkziel',name('link_url'),item.link_url||'','text',`${attr('link_url')} maxlength="1000"`,'link_url')}</div>`:''}</div>`;
   }).join('')}</div><button type="button" class="button small" data-add-item="${index}" ${block.items.length>=maxItems?'disabled':''}>＋ Eintrag hinzufügen</button>`:''}
   <details class="appearance-section"><summary>Darstellung & Verhalten <span>Farbe · Abstand · Animation</span></summary><div class="field-grid">${s('Abschnittsfarbe','theme',block.theme||'paper',[['paper','Hell / Standard'],['blue','Akzentfarbe'],['dark','Dunkel']])}${s('Abstand davor','spacing',block.spacing||'normal',[['compact','Kompakt'],['normal','Normal'],['spacious','Großzügig']])}${s('Breite','width',block.width||'wide',[['wide','Breit'],['narrow','Schmal']])}${s('Animation','animation',block.animation||'auto',[['auto','Automatisch'],['reveal','Sanft einblenden'],['slide','Seitlich einfahren'],['unfold','Auffalten / Bühne'],['stack','Gestaffelte Karten'],['repeat','Bei Rückkehr erneut'],['none','Ohne Bewegung']])}${s('Überschrift ausrichten','align',block.align||'left',[['left','Linksbündig'],['center','Zentriert']])}${supports.includes('columns')?s('Spalten auf Desktop','columns',String(block.columns||3),[['2','Zwei'],['3','Drei'],['4','Vier']]):''}</div>${f('Abschnittsanker','id',block.id,'anchor','required pattern="[a-zA-Z0-9_-]{1,50}" maxlength="50"')}</details><div class="module-preset-row"><button type="button" class="button small" data-save-preset="${index}">⧉ Als Baustein speichern</button>${helpButton('preset')}</div>`;
 }
 private render():void{
  this.selected=Math.min(Math.max(0,this.selected),Math.max(0,this.blocks.length-1));
  this.root.innerHTML=`<div class="builder-heading"><div><span class="eyebrow">02 / SEITENAUFBAU</span><h3>Deine Seite. Baustein für Baustein.</h3><p>Eine Zeile auswählen, Inhalte ändern und rechts direkt prüfen.</p></div><span class="badge">${this.blocks.length} / 30</span></div><div class="builder-actionbar"><div><button type="button" class="button small" data-undo aria-label="Moduländerung rückgängig">↶ Rückgängig</button><button type="button" class="button small" data-redo aria-label="Moduländerung wiederholen">↷</button>${helpButton('undo')}</div>${this.editable?'<button type="button" class="button primary" data-open-library>＋ Modul / Vorlage</button>':''}</div><div class="builder-layout"><nav class="module-outline" aria-label="Seitenstruktur"><span class="eyebrow">STRUKTUR</span>${this.blocks.map((block,i)=>`<button type="button" data-outline="${i}" class="${i===this.selected?'active':''} ${block.enabled?'':'outline-disabled'}"><span>${String(i+1).padStart(2,'0')}</span><span>${e(this.catalog.modules.find(m=>m.type===block.type)!.name)}<small>${e(block.title.replace(/\n/g,' ').slice(0,38)||'Ohne Titel')}</small></span><i>${block.enabled?'':'○'}</i></button>`).join('')}</nav><div class="module-stack">${this.blocks.length?this.blocks.map((block,i)=>`<details class="block-editor ${block.enabled?'':'is-disabled'}" data-block-index="${i}" ${i===this.selected?'open':''}><summary><span class="drag-handle" draggable="${this.editable}" aria-hidden="true">⠿</span><span><strong>${e(this.catalog.modules.find(m=>m.type===block.type)!.name)}</strong><small>${e(block.title.replace(/\n/g,' ')||'Ohne Titel')}</small></span><span class="block-index">${String(i+1).padStart(2,'0')} ${block.enabled?'':'· ausgeblendet'}</span></summary><div class="block-fields">${this.blockFields(block,i)}</div></details>`).join(''):`<div class="builder-empty"><div class="empty-block-mark" aria-hidden="true">＋</div><h3>Ein leerer Raum für deine Idee.</h3><p>Starte mit einem Modul oder einer vollständigen Seitenvorlage. Du kannst alles anschließend anpassen.</p>${this.editable?'<button type="button" class="button primary" data-open-library>Katalog öffnen ↗</button>':''}</div>`}</div></div>${this.blocks.length&&this.editable?'<button type="button" class="builder-add-bottom" data-open-library>＋ Einen weiteren Baustein hinzufügen</button>':''}`;
  if(!this.editable)this.root.querySelectorAll<Control|HTMLButtonElement>('input,textarea,select,button:not(.help-trigger):not([data-outline])').forEach(el=>el.disabled=true);
  this.syncHistoryButtons();
  this.root.querySelectorAll<HTMLButtonElement>('[data-outline]').forEach(b=>b.addEventListener('click',()=>this.focusIndex(Number(b.dataset.outline))));
  this.root.querySelectorAll<HTMLButtonElement>('[data-open-library]').forEach(b=>b.addEventListener('click',()=>{this.collect();void openCatalog(this.catalog,this.user,30-this.blocks.length,blocks=>this.insert(blocks)).catch(err=>toast(errorMessage(err),true));}));
  this.root.querySelector('[data-undo]')?.addEventListener('click',()=>{this.collect();this.remember();if(this.cursor>0){this.blocks=JSON.parse(this.snapshots[--this.cursor]) as Block[];this.render();this.onChange();}});
  this.root.querySelector('[data-redo]')?.addEventListener('click',()=>{if(this.cursor<this.snapshots.length-1){this.blocks=JSON.parse(this.snapshots[++this.cursor]) as Block[];this.render();this.onChange();}});
  this.root.querySelectorAll<HTMLButtonElement>('[data-move]').forEach(b=>b.addEventListener('click',()=>this.change(()=>{const [i,d]=b.dataset.move!.split(':').map(Number),j=i+d;if(j>=0&&j<this.blocks.length){[this.blocks[i],this.blocks[j]]=[this.blocks[j],this.blocks[i]];this.selected=j;}})));
  this.root.querySelectorAll<HTMLButtonElement>('[data-duplicate-block]').forEach(b=>b.addEventListener('click',()=>{if(this.blocks.length>=30)return;this.change(()=>{const i=Number(b.dataset.duplicateBlock);this.blocks.splice(i+1,0,cloneBlock(this.blocks[i]));this.selected=i+1;});}));
  this.root.querySelectorAll<HTMLButtonElement>('[data-remove-block]').forEach(b=>b.addEventListener('click',()=>{if(confirm('Dieses Modul aus dem Entwurf entfernen? Mit Rückgängig kannst du es in dieser Sitzung wiederherstellen.'))this.change(()=>this.blocks.splice(Number(b.dataset.removeBlock),1));}));
  this.root.querySelectorAll<HTMLButtonElement>('[data-save-preset]').forEach(b=>b.addEventListener('click',()=>{this.collect();saveAsPreset(this.blocks[Number(b.dataset.savePreset)]);}));
  this.root.querySelectorAll<HTMLButtonElement>('[data-add-item]').forEach(b=>b.addEventListener('click',()=>this.change(()=>{const block=this.blocks[Number(b.dataset.addItem)];if(block.items.length<(['contact','comparison'].includes(block.type)?2:20))block.items.push({title:'Neuer Eintrag',text:'',art:'brand',value:'',link_label:'',link_url:'',image:''});})));
  this.root.querySelectorAll<HTMLButtonElement>('[data-remove-item]').forEach(b=>b.addEventListener('click',()=>this.change(()=>{const[i,j]=b.dataset.removeItem!.split(':').map(Number);this.blocks[i].items.splice(j,1);})));
  this.root.querySelectorAll<HTMLButtonElement>('[data-item-move]').forEach(b=>b.addEventListener('click',()=>this.change(()=>{const[i,j,d]=b.dataset.itemMove!.split(':').map(Number),items=this.blocks[i].items;if(j+d>=0&&j+d<items.length)[items[j],items[j+d]]=[items[j+d],items[j]];})));
  this.root.querySelectorAll<Control>('input,textarea,select').forEach(input=>input.addEventListener('input',()=>{
   this.collect();clearTimeout(this.timer);this.timer=window.setTimeout(()=>this.remember(),650);this.onChange();
   const row=input.closest<HTMLElement>('[data-block-index]');if(row){const block=this.blocks[Number(row.dataset.blockIndex)];row.classList.toggle('is-disabled',!block.enabled);row.querySelector('summary small')!.textContent=block.title.replace(/\n/g,' ')||'Ohne Titel';const outline=this.root.querySelector<HTMLElement>(`[data-outline="${row.dataset.blockIndex}"]`);if(outline){outline.querySelector('small')!.textContent=block.title.replace(/\n/g,' ').slice(0,38)||'Ohne Titel';outline.classList.toggle('outline-disabled',!block.enabled);outline.querySelector('i')!.textContent=block.enabled?'':'○';}}
   if(input.dataset.bfield==='art'){const img=input.closest('.asset-inspector')?.querySelector('img');if(img)img.src=assetUrl(input.value);}
  }));
  this.root.querySelectorAll<HTMLButtonElement>('[data-pick-media],[data-pick-item-media]').forEach(button=>button.addEventListener('click',()=>{
   const locator=button.dataset.pickItemMedia;const index=Number(locator?locator.split(':')[0]:button.dataset.pickMedia);
   const row=this.root.querySelector<HTMLElement>(`[data-block-index="${index}"]`)!;
   const target=locator?row.querySelector<HTMLSelectElement>(`[data-item-index="${locator.split(':')[1]}"] select[data-ifield="image"]`):row.querySelector<HTMLSelectElement>('select[data-bfield="image"]');
   if(target)void pickMedia(media=>{if(media&&!this.media.some(m=>m.id===media.id))this.media.push(media);setMediaSelect(target,media);});
  }));
  this.root.querySelectorAll<HTMLButtonElement>('[data-pick-campaign]').forEach(button=>button.addEventListener('click',()=>{
   const index=Number(button.dataset.pickCampaign);void pickCampaign(item=>this.change(()=>{this.blocks[index].campaign=item?.id||'';}));
  }));
  // Drag only from an explicit handle; arrow controls provide a touch/keyboard alternative.
  let source=-1;
  this.root.querySelectorAll<HTMLElement>('[data-block-index]').forEach(row=>{
   row.addEventListener('dragstart',event=>{if(!this.editable||!(event.target as Element).closest('.drag-handle')){event.preventDefault();return;}source=Number(row.dataset.blockIndex);event.dataTransfer?.setData('text/plain',String(source));row.classList.add('dragging');});
   row.addEventListener('dragover',event=>{if(source>=0){event.preventDefault();row.classList.add('drop-target');}});
   row.addEventListener('dragleave',()=>row.classList.remove('drop-target'));
   row.addEventListener('drop',event=>{event.preventDefault();const target=Number(row.dataset.blockIndex);if(source>=0&&source!==target)this.change(()=>{const[moved]=this.blocks.splice(source,1);this.blocks.splice(target,0,moved);this.selected=target;});source=-1;row.classList.remove('drop-target');});
   row.addEventListener('dragend',()=>{source=-1;this.root.querySelectorAll('.dragging,.drop-target').forEach(el=>el.classList.remove('dragging','drop-target'));});
  });
 }
}
