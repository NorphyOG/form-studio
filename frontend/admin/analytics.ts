import {api} from './api.js';
import {escape as e, errorMessage, icon, toast} from './ui.js';
import {helpButton} from './help.js';
import type {User} from './types.js';
interface Report{ad_impressions:number;ad_clicks:number;enabled:boolean;days:number;timezone:string;retention_days:number;pageviews:number;active_tabs:number;definitions:string;series:{day:string;count:number}[];top_pages:{resource:string;count:number}[];campaigns:{resource:string;title:string|null;impressions:number;clicks:number}[]}

function graph(series:Report['series']):string{
 const max=Math.max(1,...series.map(i=>i.count));
 const points=series.map((item,i)=>`${40+(i/Math.max(1,series.length-1))*820},${215-(item.count/max)*175}`).join(' ');
 return `<svg class="analytics-chart" viewBox="0 0 900 265" role="img" aria-label="Seitenaufrufe pro Tag; exakte Werte in der Tabelle darunter"><title>Seitenaufrufe der letzten ${series.length} Tage</title><g class="chart-grid"><path d="M40 40H860M40 127H860M40 215H860"/></g><text x="5" y="45">${max}</text><text x="15" y="220">0</text><polygon class="chart-area" points="40,215 ${points} 860,215"/><polyline class="chart-line" points="${points}"/><text x="40" y="253">${e(series[0]?.day||'')}</text><text text-anchor="end" x="860" y="253">${e(series.at(-1)?.day||'')}</text></svg>`;
}
export async function analyticsView(container:HTMLElement,user:User):Promise<void>{
 let days=30,tick=0;
 container.innerHTML=`<div class="page-head"><div><span class="eyebrow">STUDIO / ANALYSE</span><h1>Verstehen, was ankommt.</h1><p>Echte Messwerte. Klare Grenzen. Ohne externe Analyse-Dienste.</p></div>${helpButton('analytics')}</div><div class="analytics-toolbar"><div class="segmented" aria-label="Analysezeitraum">${[7,30,90].map(n=>`<button type="button" data-days="${n}" aria-pressed="${n===days}">${n} Tage</button>`).join('')}</div><button type="button" class="button" data-refresh>Aktualisieren ↻</button><span id="analytics-updated" class="muted"></span></div><div id="analytics-body"></div>`;
 const body=container.querySelector<HTMLElement>('#analytics-body')!;
 async function load():Promise<void>{
  const sequence=++tick;
  try{
   const data=await api<Report>('/api/admin/analytics?days='+days);
   if(sequence!==tick)return;
   const totalImpressions=data.ad_impressions,totalClicks=data.ad_clicks;
   body.innerHTML=`<div class="analytics-note ${data.enabled?'':'analytics-disabled'}"><span>${icon(data.enabled?'moderation':'settings')}</span><div><strong>${data.enabled?'Zustimmungsbasierte Messung aktiviert':'Statistik ist ausgeschaltet'}</strong><p>${data.enabled?'Gezählt werden nur Besucher, die zugestimmt haben. Das sind keine Gesamtbesucherzahlen.':'Unter Einstellungen aktivieren und veröffentlichen. Erst nach Zustimmung eines Besuchers werden Ereignisse gezählt; keine erfundenen Demo-Werte.'}</p></div>${user.role==='admin'?'<a class="button small" href="#settings">Einstellungen ↗</a>':''}</div>
    <div class="stats-grid analytics-stats"><div class="stat-card"><span>Seitenaufrufe ${helpButton('pageviews')}</span><strong>${data.pageviews.toLocaleString('de-DE')}</strong><small>Im gewählten Zeitraum</small></div><div class="stat-card"><span>Aktive Seitenfenster ${helpButton('active_tabs')}</span><strong>${data.active_tabs.toLocaleString('de-DE')}<i class="live-dot"></i></strong><small>Letzte 90 Sekunden · nicht Personen</small></div><div class="stat-card"><span>Sichtbare Anzeigen ${helpButton('ad_metrics')}</span><strong>${totalImpressions.toLocaleString('de-DE')}</strong><small>Mind. 50 % sichtbar, 1 Sekunde</small></div><div class="stat-card"><span>Anzeigenklicks ${helpButton('ad_metrics')}</span><strong>${totalClicks.toLocaleString('de-DE')}</strong><small>Ohne Umsatz- oder Kaufmessung</small></div></div>
    <section class="panel analytics-main"><div class="panel-heading"><div><span class="eyebrow">NUTZUNG IM VERLAUF</span><h2>Jeder Aufruf. Ein Signal.</h2></div><span class="badge">${days} Tage / UTC</span></div>${graph(data.series)}${data.pageviews===0?'<p class="chart-empty">Noch keine erfassten Aufrufe im Zeitraum. Eine leere Messreihe ist kein Fehler.</p>':''}<details class="analytics-table-details"><summary>Exakte Tageswerte als Tabelle</summary><table><thead><tr><th>Tag (UTC)</th><th>Seitenaufrufe</th></tr></thead><tbody>${data.series.map(d=>`<tr><td>${e(d.day)}</td><td>${d.count}</td></tr>`).join('')}</tbody></table></details></section>
    <div class="analytics-columns"><section class="panel"><div class="panel-heading"><h2>Aufgerufene Seiten</h2>${helpButton('pageviews')}</div>${data.top_pages.length?`<div class="top-pages">${data.top_pages.map((row,i)=>`<div><span class="rank">${String(i+1).padStart(2,'0')}</span><a href="${e(row.resource)}" target="_blank" rel="noopener">${e(row.resource)}</a><strong>${row.count}</strong></div>`).join('')}</div>`:'<p class="empty-state">Hier erscheinen die meistaufgerufenen Seiten.</p>'}</section><section class="panel"><div class="panel-heading"><h2>Partner & Kampagnen</h2>${helpButton('ad_metrics')}</div>${data.campaigns.length?`<div class="table-wrap"><table><thead><tr><th>Kampagne</th><th>Sichtbar</th><th>Klicks</th></tr></thead><tbody>${data.campaigns.map(c=>`<tr><td>${e(c.title||'Ehemalige Kampagne')}</td><td>${c.impressions}</td><td>${c.clicks}</td></tr>`).join('')}</tbody></table></div>`:'<p class="empty-state">Noch keine erfassten Werbeinteraktionen.</p>'}</section></div>
    <div class="analytics-footnote"><p>Auswertung: ${data.retention_days} Tage. Ältere Tageswerte werden beim nächsten gezählten Ereignis bereinigt · Tagesgrenzen: UTC · Aktive Tabs: Arbeitsspeicher einer Serverinstanz. Keine IP-Adressen, Geräteprofile, Referrer oder vollständigen URLs in der Statistik gespeichert.</p>${user.role==='admin'?'<button class="button small danger-text" type="button" data-erase>Statistikdaten löschen</button>':''}</div>`;
   container.querySelector('#analytics-updated')!.textContent='Stand '+new Date().toLocaleTimeString('de-DE');
   body.querySelector('[data-erase]')?.addEventListener('click',async()=>{if(!confirm('Alle Statistik-Aggregate aus der aktiven Datenbank löschen? Bestehende Backups bleiben unverändert.'))return;try{await api('/api/admin/analytics',{method:'DELETE'});toast('Statistik gelöscht.');await load();}catch(err){toast(errorMessage(err),true);}});
  }catch(err){body.textContent=errorMessage(err);}
 }
 container.querySelectorAll<HTMLButtonElement>('[data-days]').forEach(button=>button.addEventListener('click',()=>{days=Number(button.dataset.days);container.querySelectorAll('[data-days]').forEach(b=>b.setAttribute('aria-pressed',String(b===button)));void load();}));
 container.querySelector('[data-refresh]')!.addEventListener('click',()=>void load());
 await load();
 // Never keep polling a hidden/removed route; controls and tables are not replaced while focused.
 const interval=window.setInterval(()=>{if(!container.isConnected){clearInterval(interval);return;}if(!document.hidden&&!body.contains(document.activeElement))void load();},30000);
}
