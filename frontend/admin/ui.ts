import {helpButton} from './help.js';
import type {Kind, RecordItem} from './types.js';
export const escape = (value: unknown): string => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]!));
export const kindName: Record<Kind,string> = {page:'Seite',service:'Leistung',project:'Projekt',settings:'Einstellungen',article:'Beitrag',campaign:'Kampagne'};
export const stateName: Record<string,string> = {draft:'Entwurf',pending:'Zur Prüfung',published:'Veröffentlicht',rejected:'Überarbeiten'};
export function badge(state: string): string { return `<span class="badge badge-${escape(state)}">${escape(stateName[state] || state)}</span>`; }
export function date(time: number): string { return new Date(time*1000).toLocaleDateString('de-DE',{day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit'}); }
export function toast(message: string, error = false): void {
  const el = document.getElementById('toast')!; el.textContent = message; el.className = error ? 'show error' : 'show';
  window.setTimeout(() => el.classList.remove('show'), 6500);
}
export function errorMessage(error: unknown): string { return error instanceof Error ? error.message : 'Ein unerwarteter Fehler ist aufgetreten.'; }
export function modal(html: string): HTMLDialogElement {
  const dialog = document.querySelector<HTMLDialogElement>('#modal')!;
  if(dialog.open) dialog.dispatchEvent(new Event('studio-replace'));
  dialog.oncancel=null;
  dialog.innerHTML = html;
  dialog.querySelectorAll('[data-close]').forEach(button => button.addEventListener('click',() => dialog.close()));
  if(!dialog.open) dialog.showModal();
  return dialog;
}
let fieldCount=0;
export function field(label:string,name:string,value:unknown='',type='text',extra='',helpKey=name):string{
 const id=`field-${++fieldCount}`;
 return `<div class="field"><div class="field-label"><label for="${id}">${escape(label)}</label>${helpButton(helpKey)}</div><input id="${id}" type="${type}" name="${escape(name)}" value="${escape(value)}" ${extra}></div>`;
}
export function textarea(label:string,name:string,value:unknown='',rows=3,extra='',helpKey=name):string{
 const id=`field-${++fieldCount}`;
 return `<div class="field"><div class="field-label"><label for="${id}">${escape(label)}</label>${helpButton(helpKey)}</div><textarea id="${id}" name="${escape(name)}" rows="${rows}" ${extra}>${escape(value)}</textarea></div>`;
}
export function select(label:string,name:string,value:string,items:[string,string][],extra='',helpKey=name):string{
 const id=`field-${++fieldCount}`;
 return `<div class="field"><div class="field-label"><label for="${id}">${escape(label)}</label>${helpButton(helpKey)}</div><select id="${id}" name="${escape(name)}" ${extra}>${items.map(([key,title])=>`<option value="${escape(key)}" ${key===value?'selected':''}>${escape(title)}</option>`).join('')}</select></div>`;
}
export function check(label:string,name:string,value:boolean,helpKey=name,extra=''):string{
 const id=`field-${++fieldCount}`;
 return `<div class="check-row"><label class="check-field" for="${id}"><input id="${id}" name="${escape(name)}" type="checkbox" ${value?'checked':''} ${extra}>${escape(label)}</label>${helpButton(helpKey)}</div>`;
}
export function overlay(html:string,className=''):HTMLDialogElement{
 const previous=document.activeElement as HTMLElement|null;
 const dialog=document.createElement('dialog');dialog.className=className;dialog.innerHTML=html;
 const heading=dialog.querySelector('h2');if(heading){heading.id=`dialog-title-${++fieldCount}`;dialog.setAttribute('aria-labelledby',heading.id);}
 else dialog.setAttribute('aria-label','Zusätzliche Auswahl');
 document.body.append(dialog);dialog.showModal();
 dialog.querySelectorAll('[data-close]').forEach(b=>b.addEventListener('click',()=>dialog.close()));
 dialog.addEventListener('close',()=>{dialog.remove();if(previous?.isConnected)previous.focus();},{once:true});
 return dialog;
}
export function publicPath(record: RecordItem): string {
  const slug = record.live?.slug || record.data.slug;
  if(record.kind === 'article') return '/news/'+slug;
  if(record.kind === 'campaign') return '/admin/preview/'+record.id;
  if(record.kind === 'page') return slug==='home' ? '/' : '/p/'+slug;
  return (record.kind === 'service' ? '/leistungen/' : '/arbeiten/')+slug;
}
export function bindAsync(element: Element | null, event: string, callback: (event: Event) => Promise<unknown>): void {
  element?.addEventListener(event, e => { void callback(e).catch(error => toast(errorMessage(error),true)); });
}
const symbols: Record<string,string> = {
  analytics:'<path d="M3 3v18h18M7 15l4-6 4 3 5-8"/>',
  articles:'<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M7 7h10M7 11h5M7 15h10M7 18h6"/>',
  campaigns:'<path d="M3 10v4l17 5V5ZM7 15v6h5l-2-5"/>',
  help:'<circle cx="12" cy="12" r="9"/><path d="M9 9a3 3 0 0 1 6 0c0 3-3 2-3 5m0 3h.01"/>',
  overview:'<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
  pages:'<path d="M6 3h9l4 4v14H6Z"/><path d="M14 3v5h5M9 12h7M9 16h7"/>',
  services:'<path d="m12 3 9 5-9 5-9-5ZM3 12l9 5 9-5M3 16l9 5 9-5"/>',
  projects:'<rect x="3" y="6" width="18" height="15" rx="2"/><path d="M8 6V3h8v3M3 12h18M10 12v3h4v-3"/>',
  moderation:'<path d="m12 3 8 3v7c0 5-8 9-8 9S4 18 4 13V6Z"/><path d="m8 12 3 3 5-6"/>',
  inbox:'<rect x="3" y="5" width="18" height="15" rx="2"/><path d="m3 6 9 7 9-7"/>',
  media:'<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8" cy="8" r="2"/><path d="m3 18 6-6 4 4 3-3 5 5"/>',
  team:'<circle cx="9" cy="8" r="3"/><path d="M3 21v-3a6 6 0 0 1 12 0v3M17 5a3 3 0 0 1 0 6M18 15a5 5 0 0 1 3 5"/>',
  settings:'<circle cx="12" cy="12" r="3"/><path d="M12 2v4M12 18v4M2 12h4M18 12h4M5 5l3 3M16 16l3 3M5 19l3-3M16 8l3-3"/>',
  activity:'<path d="M3 12h4l3-8 4 16 3-8h4"/>',
  arrow:'<path d="M6 18 18 6M6 6h12v12"/>',plus:'<path d="M12 4v16M4 12h16"/>'
};
export function icon(name: string): string { return `<svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${symbols[name] || symbols.overview}</svg>`; }
