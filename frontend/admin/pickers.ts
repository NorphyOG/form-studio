/** Bounded, searchable selection dialogs. Libraries do not load all assets at once. */
import {api} from './api.js';
import {overlay, escape as e, errorMessage, badge} from './ui.js';
import type {Media, RecordItem} from './types.js';

export async function pickMedia(onPick:(media:Media|null)=>void):Promise<void>{
 const dialog=overlay(`<header class="modal-header"><div><span class="eyebrow">MEDIATHEK / AUSWAHL</span><h2>Das passende Bild.</h2><p class="field-hint">Bilder werden seitenweise geladen. Suche im Alternativtext.</p></div><button data-close type="button" class="icon-button" aria-label="Auswahl schließen">×</button></header><div class="picker-toolbar"><input type="search" placeholder="Bild suchen …" aria-label="Medien durchsuchen"><button class="button" type="button" data-none>Standardgrafik verwenden</button></div><div class="picker-results"></div><div class="picker-pagination"></div>`,'picker-dialog');
 let offset=0,sequence=0,timer:number|undefined;
 const search=dialog.querySelector<HTMLInputElement>('input')!;
 async function load():Promise<void>{
  const tick=++sequence;
  try{
   const items=await api<Media[]>('/api/admin/media?'+new URLSearchParams({q:search.value,limit:'24',offset:String(offset)}));
   if(tick!==sequence||!dialog.open)return;
   dialog.querySelector('.picker-results')!.innerHTML=items.length?`<div class="picker-grid">${items.map(m=>`<button type="button" class="picker-card" data-media="${m.id}"><img src="/media/${m.id}" alt="" loading="lazy"><strong>${e(m.alt)}</strong><small>${m.width} × ${m.height}</small></button>`).join('')}</div>`:'<p class="empty-state">Keine weiteren passenden Bilder. Neue Bilder unter „Medien & Assets“ hochladen.</p>';
   dialog.querySelector('.picker-pagination')!.innerHTML=`<button type="button" class="button" data-prev ${offset===0?'disabled':''}>← Zurück</button><span>Seite ${offset/24+1}</span><button type="button" class="button" data-next ${items.length<24?'disabled':''}>Weiter →</button>`;
   dialog.querySelectorAll<HTMLButtonElement>('[data-media]').forEach(b=>b.addEventListener('click',()=>{onPick(items.find(m=>m.id===b.dataset.media)!);dialog.close();}));
   dialog.querySelector('[data-prev]')!.addEventListener('click',()=>{offset=Math.max(0,offset-24);void load();});
   dialog.querySelector('[data-next]')!.addEventListener('click',()=>{offset+=24;void load();});
  }catch(err){if(dialog.open)dialog.querySelector('.picker-results')!.textContent=errorMessage(err);}
 }
 search.addEventListener('input',()=>{clearTimeout(timer);timer=window.setTimeout(()=>{offset=0;void load();},250);});
 dialog.querySelector('[data-none]')!.addEventListener('click',()=>{onPick(null);dialog.close();});
 dialog.addEventListener('close',()=>{clearTimeout(timer);sequence++;},{once:true});
 await load();search.focus();
}

export async function pickCampaign(onPick:(item:RecordItem|null)=>void):Promise<void>{
 const dialog=overlay(`<header class="modal-header"><div><span class="eyebrow">WERBUNG / KAMPAGNE AUSWÄHLEN</span><h2>Ein Platz für den richtigen Partner.</h2><p class="field-hint">Nur veröffentlichte Kampagnen im gültigen Zeitraum erscheinen auf der Website.</p></div><button data-close class="icon-button" aria-label="Schließen">×</button></header><div class="picker-toolbar"><input type="search" placeholder="Kampagne suchen …" aria-label="Kampagnen durchsuchen"><button class="button" data-none type="button">Verknüpfung entfernen</button></div><div class="picker-results"></div><div class="picker-pagination"></div>`,'picker-dialog');
 let offset=0,sequence=0,timer:number|undefined;
 const search=dialog.querySelector<HTMLInputElement>('input')!;
 async function load():Promise<void>{
  const tick=++sequence;
  try{
   const result=await api<{items:RecordItem[];total:number}>('/api/admin/content-index?'+new URLSearchParams({kind:'campaign',q:search.value,limit:'24',offset:String(offset)}));
   if(tick!==sequence||!dialog.open)return;
   dialog.querySelector('.picker-results')!.innerHTML=result.items.length?`<div class="campaign-picker-list">${result.items.map(item=>`<button type="button" class="campaign-choice" data-campaign="${item.id}"><span><strong>${e(item.data.title)}</strong><small>${e(item.data.description)}</small></span>${badge(item.state)}<span>Auswählen ↗</span></button>`).join('')}</div>`:'<p class="empty-state">Noch keine passende Kampagne. Unter „Werbung & Partner“ zunächst eine Kampagne anlegen.</p>';
   dialog.querySelector('.picker-pagination')!.innerHTML=`<button type="button" class="button" data-prev ${offset===0?'disabled':''}>← Zurück</button><span>${result.total} Kampagnen</span><button type="button" class="button" data-next ${offset+24>=result.total?'disabled':''}>Weiter →</button>`;
   dialog.querySelectorAll<HTMLButtonElement>('[data-campaign]').forEach(b=>b.addEventListener('click',()=>{onPick(result.items.find(i=>i.id===b.dataset.campaign)!);dialog.close();}));
   dialog.querySelector('[data-prev]')!.addEventListener('click',()=>{offset=Math.max(0,offset-24);void load();});dialog.querySelector('[data-next]')!.addEventListener('click',()=>{offset+=24;void load();});
  }catch(err){if(dialog.open)dialog.querySelector('.picker-results')!.textContent=errorMessage(err);}
 }
 search.addEventListener('input',()=>{clearTimeout(timer);timer=window.setTimeout(()=>{offset=0;void load();},250);});
 dialog.querySelector('[data-none]')!.addEventListener('click',()=>{onPick(null);dialog.close();});
 dialog.addEventListener('close',()=>{clearTimeout(timer);sequence++;},{once:true});await load();search.focus();
}

export function setMediaSelect(select:HTMLSelectElement,media:Media|null):void{
 if(media&&!Array.from(select.options).some(o=>o.value===media.id))select.add(new Option(media.alt,media.id));
 select.value=media?.id||'';select.dispatchEvent(new Event('input',{bubbles:true}));
}
