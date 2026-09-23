import {analyticsView} from './analytics.js';
import {initializeHelp,helpView} from './help.js';
initializeHelp();
import {api,json,setCSRF} from './api.js';
import {escape as e,field,icon,toast,errorMessage,bindAsync} from './ui.js';
import {overviewView,contentView,moderationView,inboxView,mediaView,teamView,activityView,libraryView} from './views.js';
import type {User} from './types.js';

const app=document.querySelector<HTMLElement>('#app')!;
let user:User|null=null;
let rendering=0;
async function authenticate():Promise<void>{
  const status=await api<{setup_required:boolean}>('/api/setup-status');
  if(status.setup_required){renderLogin(true);return;}
  try{user=await api<User>('/api/admin/session');setCSRF(user.csrf);shell();}
  catch{renderLogin(false);}
}
function renderLogin(setup:boolean):void{
  user=null;setCSRF('');
  const dialog=document.querySelector<HTMLDialogElement>('#modal');if(dialog?.open)dialog.close();
  app.innerHTML=`<div class="auth-layout"><section class="auth-story"><a class="cms-brand" href="/">${icon('services')} FORM / STUDIO</a><span class="eyebrow">DEIN KREATIVER WORKSPACE</span><h1>Gute Ideen.<br>Ein gutes<br><em>System.</em></h1><p>Inhalte, Seiten und Freigaben.<br>Ein Ort für alles, was dein Studio bewegt.</p><span class="auth-foot">STUDIO CMS / VERSION 0.4</span></section><section class="auth-form-wrap"><a class="auth-back" href="/">Website ansehen ↗</a><form id="auth-form" class="auth-form"><span class="eyebrow">${setup?'ERSTER START':'WILLKOMMEN IM WORKSPACE'}</span><h2>${setup?'Dein Studio einrichten.':'Zurück an die Ideen.'}</h2><p>${setup?'Lege dein persönliches Administratorkonto an. Den einmaligen Einrichtungscode findest du im Startfenster oder in data/.setup-key.':'Melde dich mit deinem Teamzugang an.'}</p>${setup?field('Einmaliger Einrichtungscode','setup_key','','password','required minlength="16" autocomplete="off"'):''}${setup?field('Dein Name','name','','text','required minlength="2" maxlength="80" autocomplete="name"'):''}${field('E-Mail-Adresse','email','','email','required autocomplete="username"')}${field(setup?'Passwort (mindestens 12 Zeichen)':'Passwort','password','','password',`required ${setup?'minlength="12"':''} maxlength="256" autocomplete="${setup?'new-password':'current-password'}"`)}<button class="button primary auth-submit" type="submit">${setup?'Studio einrichten':'Anmelden'} <span>↗</span></button><p class="form-error" id="auth-error" role="alert"></p><div class="auth-security">Persönliche Zugänge · rollenbasierte Rechte · versionierte Inhalte</div></form></section></div>`;
  const form=app.querySelector<HTMLFormElement>('#auth-form')!;
  form.addEventListener('submit',async event=>{
    event.preventDefault();const button=form.querySelector<HTMLButtonElement>('button[type=submit]')!;button.disabled=true;
    app.querySelector('#auth-error')!.textContent='';
    try{const data=Object.fromEntries(new FormData(form));await api(setup?'/api/setup':'/api/login',json('POST',data));await authenticate();}
    catch(err){app.querySelector('#auth-error')!.textContent=errorMessage(err);}
    finally{button.disabled=false;}
  });
}
function shell():void {
  if(!user)return;
  const groups:[string,[string,string][]][] = [
    ['WORKSPACE', [['overview','Übersicht'],['help','Hilfe & Handbuch']]],
    ['INHALTE', [['pages','Seiten & Module'],['articles','Journal & News'],['campaigns','Werbung & Partner'],['services','Leistungen'],['projects','Arbeiten'],['media','Medien & Assets'],['library','Bausteine & Vorlagen']]],
    ['REDAKTION', [['moderation','Freigaben']]],
  ];
  if(user.role !== 'editor'){groups[2][1].push(['inbox','Anfragen']);groups[0][1].push(['analytics','Analyse']);}
  if(user.role === 'admin') groups.push(['VERWALTUNG', [['team','Team & Rollen'],['settings','Einstellungen'],['activity','Aktivität']]]);

  app.innerHTML=`<div class="admin-shell"><aside class="sidebar"><a class="cms-brand" href="#overview"><span class="cms-logo">F</span><span>FORM / STUDIO<small>CONTENT WORKSPACE</small></span></a><nav aria-label="Adminnavigation">${groups.map(([name,links])=>`<div class="nav-group"><span>${name}</span>${links.map(([id,label])=>`<a href="#${id}" data-nav="${id}">${icon(id)}<span>${label}</span></a>`).join('')}</div>`).join('')}</nav><div class="sidebar-bottom"><a class="site-link" href="/" target="_blank" rel="noopener">Website öffnen ${icon('arrow')}</a><div class="user-card"><span class="avatar">${e(user.name.slice(0,1).toUpperCase())}</span><div><strong>${e(user.name)}</strong><small>${({admin:'Administration',editor:'Redaktion',moderator:'Moderation'})[user.role]}</small></div><button class="logout-button" id="logout" aria-label="Abmelden">↪</button></div></div></aside><div class="admin-main"><header class="admin-topbar"><button class="icon-button mobile-sidebar-button" id="sidebar-toggle" aria-label="Adminmenü öffnen" aria-expanded="false">☰</button><div class="breadcrumb">Workspace <span>/</span> <strong id="breadcrumb-title">Übersicht</strong></div><div class="topbar-right"><span class="workspace-status"><i></i> Lokaler Workspace</span><a href="/" target="_blank" rel="noopener" class="button small">Live-Vorschau ↗</a></div></header><main class="admin-content" id="view"><div class="loading">Inhalte werden geladen …</div></main></div></div>`;
  bindAsync(app.querySelector('#logout'),'click',async()=>{await api('/api/admin/logout',{method:'POST'});renderLogin(false);});
  app.querySelector('#sidebar-toggle')!.addEventListener('click',()=>{const shell=app.querySelector('.admin-shell')!;const open=shell.classList.toggle('sidebar-open');app.querySelector('#sidebar-toggle')!.setAttribute('aria-expanded',String(open));});
  void renderRoute();
}
async function renderRoute():Promise<void>{
  if(!user)return;
  const route=location.hash.slice(1)||'overview';
  const view=app.querySelector<HTMLElement>('#view');if(!view)return;
  app.querySelector('.admin-shell')?.classList.remove('sidebar-open');
  app.querySelector('#sidebar-toggle')?.setAttribute('aria-expanded','false');
  app.querySelectorAll<HTMLAnchorElement>('[data-nav]').forEach(link=>{link.classList.toggle('active',link.dataset.nav===route);if(link.dataset.nav===route){link.setAttribute('aria-current','page');app.querySelector('#breadcrumb-title')!.textContent=link.querySelector('span')!.textContent;}else link.removeAttribute('aria-current');});
  const tick=++rendering;
  const buffer=document.createElement('div');
  const refresh=()=>{void renderRoute();};
  try {
    const u=user;
    switch(route){
      case 'pages':await contentView(buffer,'page',u,refresh);break;
      case 'services':await contentView(buffer,'service',u,refresh);break;
      case 'help':helpView(buffer);break;
      case 'analytics':if(u.role==='editor')throw new Error('Keine Berechtigung.');await analyticsView(buffer,u);break;
      case 'articles':await contentView(buffer,'article',u,refresh);break;
      case 'campaigns':await contentView(buffer,'campaign',u,refresh);break;
      case 'projects':await contentView(buffer,'project',u,refresh);break;
      case 'settings':if(u.role!=='admin')throw new Error('Keine Berechtigung.');await contentView(buffer,'settings',u,refresh);break;
      case 'moderation':await moderationView(buffer,u,refresh);break;
      case 'inbox':await inboxView(buffer,u,refresh);break;
      case 'media':await mediaView(buffer,u,refresh);break;
      case 'library':await libraryView(buffer,u,refresh);break;
      case 'team':await teamView(buffer,u,refresh);break;
      case 'activity':await activityView(buffer);break;
      default:await overviewView(buffer,u,refresh);
    }
    if(tick===rendering){view.replaceChildren(buffer);}
  }catch(err){if(tick===rendering){view.innerHTML=`<div class="panel empty-state"><h2>Die Ansicht konnte nicht geladen werden.</h2><p>${e(errorMessage(err))}</p><button class="button" id="retry-view">Erneut versuchen</button></div>`;view.querySelector('#retry-view')?.addEventListener('click',()=>void renderRoute());}}
}
window.addEventListener('hashchange',()=>void renderRoute());
window.addEventListener('session-expired',()=>{if(user){user=null;renderLogin(false);toast('Sitzung abgelaufen. Bitte neu anmelden.',true);}});
void authenticate().catch(err=>{app.innerHTML=`<div class="loading"><h1>Studio CMS</h1><p>${e(errorMessage(err))}</p><p>Server starten und diese Seite neu laden.</p></div>`;});
