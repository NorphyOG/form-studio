import {animateReflow} from './motion.js';
import {initializeExperience} from './experience.js';
import {initializePreviewBridge} from './preview-bridge.js';
import {initializeAnalytics} from './analytics.js';
initializePreviewBridge();
initializeExperience();
initializeAnalytics();
/** Progressive enhancements; all public content is server-rendered. */
const menu = document.querySelector<HTMLButtonElement>('.menu-toggle');
const nav = document.querySelector<HTMLElement>('#main-nav');
menu?.addEventListener('click', () => {
  const open = menu.getAttribute('aria-expanded') !== 'true';
  menu.setAttribute('aria-expanded', String(open));
  menu.setAttribute('aria-label', open ? 'Menü schließen' : 'Menü öffnen');
  nav?.classList.toggle('is-open', open);
});
nav?.querySelectorAll('a').forEach(link => link.addEventListener('click', () => {
  nav.classList.remove('is-open');
  menu?.setAttribute('aria-expanded', 'false');
}));
document.addEventListener('keydown', event => {
  if(event.key === 'Escape' && nav?.classList.contains('is-open')) {
    nav.classList.remove('is-open'); menu?.setAttribute('aria-expanded', 'false'); menu?.focus();
  }
});
document.addEventListener('click',event=>{
 const button=(event.target as Element).closest<HTMLButtonElement>('[data-filter]');const section=button?.closest<HTMLElement>('.works-section');if(!button||!section)return;
 const cards=Array.from(section.querySelectorAll<HTMLElement>('[data-category]'));
 const previous=new Map(cards.filter(c=>!c.hidden).map(c=>[c,c.getBoundingClientRect()]));
 section.querySelectorAll<HTMLButtonElement>('[data-filter]').forEach(other=>{other.classList.toggle('active',other===button);other.setAttribute('aria-pressed',String(other===button));});
 cards.forEach(card=>card.hidden=button.dataset.filter!=='all'&&card.dataset.category!==button.dataset.filter);
 const empty=section.querySelector<HTMLElement>('.filter-empty');if(empty)empty.hidden=cards.some(c=>!c.hidden);
 animateReflow(cards,previous);
});
const form = document.querySelector<HTMLFormElement>('#contact-form');
const select = document.querySelector<HTMLSelectElement>('#service-select');
const service = new URLSearchParams(location.search).get('service');
if(select && service && Array.from(select.options).some(option => option.value === service)) select.value = service;
form?.addEventListener('submit', async event => {
  event.preventDefault();
  if(document.body.classList.contains('is-preview')) return;
  const button = form.querySelector<HTMLButtonElement>('button[type=submit]')!;
  const status = document.querySelector<HTMLElement>('#form-status')!;
  const data = new FormData(form);
  button.disabled = true; status.textContent = 'Deine Anfrage wird gespeichert …';
  try {
    const response = await fetch('/api/inquiries', { method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({name:data.get('name'),email:data.get('email'),message:data.get('message'),
        service:data.get('service'),website:data.get('website') || '',privacy:data.get('privacy') === 'on'}) });
    const result = await response.json();
    if(!response.ok) throw new Error(typeof result.detail === 'string' ? result.detail : 'Bitte prüfe deine Eingaben.');
    status.textContent = 'Deine Anfrage ist im Studio-Postfach eingegangen. In dieser lokalen Version wird keine E-Mail verschickt.';
    form.reset();
  } catch(error) {
    status.textContent = error instanceof Error ? error.message : 'Die Anfrage konnte nicht gespeichert werden.';
  } finally { button.disabled = false; }
});
export {};
