/** Native motion choreography. Content remains visible and usable without JS. */
const reduced = matchMedia('(prefers-reduced-motion: reduce)');
const body = document.body;
const configured = body.dataset.motion || 'signature';
let visitorOff = false;
try {
    visitorOff = sessionStorage.getItem('studio-motion') === 'off';
}
catch { /* Storage is optional. */ }
let abortIntro = null;
const toggle = document.querySelector('.motion-toggle');
const replay = document.querySelector('.replay-intro');
export const motionAllowed = () => !reduced.matches && !visitorOff && configured !== 'off';
const enabledFor = (el) => motionAllowed() && el.closest('[data-animation="none"]') === null;
const ease = 'cubic-bezier(.22,1,.36,1)';
function animate(el, frames, duration, delay = 0) {
    if (!enabledFor(el) || typeof el.animate !== 'function')
        return null;
    return el.animate(frames, { duration, delay, easing: ease, fill: 'backwards' });
}
function syncPreference() {
    body.dataset.motion = motionAllowed() ? configured : 'off';
    window.dispatchEvent(new Event('studio-motion-change'));
    if (toggle) {
        toggle.hidden = false;
        toggle.disabled = reduced.matches || configured === 'off';
        toggle.textContent = reduced.matches ? 'Bewegung reduziert · Systemeinstellung' : configured === 'off' ? 'Animationen deaktiviert' : visitorOff ? 'Bewegung aktivieren' : 'Bewegung reduzieren';
        toggle.setAttribute('aria-pressed', String(!motionAllowed()));
    }
    if (replay)
        replay.hidden = !motionAllowed() || !document.querySelector('[data-signature-hero]') || !!document.querySelector('[data-signature-hero]')?.closest('[data-animation="none"]') || body.classList.contains('is-preview') || configured !== 'signature';
    if (!motionAllowed()) {
        abortIntro?.();
        document.getAnimations().forEach(a => a.cancel());
    }
}
syncPreference();
reduced.addEventListener('change', syncPreference);
toggle?.addEventListener('click', () => { visitorOff = !visitorOff; try {
    sessionStorage.setItem('studio-motion', visitorOff ? 'off' : 'on');
}
catch { /* Optional preference. */ } syncPreference(); });
export function playSignature() {
    abortIntro?.();
    const hero = document.querySelector('[data-signature-hero]');
    if (!hero || typeof hero.animate !== 'function' || !enabledFor(hero) || body.classList.contains('is-preview') || configured !== 'signature')
        return;
    const title = hero.querySelector('h1,h2');
    if (!title)
        return;
    const rect = hero.getBoundingClientRect();
    const header = document.querySelector('.site-header')?.getBoundingClientRect();
    const startY = Math.max(0, Math.min(header?.bottom || 0, innerHeight));
    if (rect.bottom < 0 || rect.top > innerHeight)
        return;
    const height = Math.max(1, innerHeight - startY);
    const width = document.documentElement.clientWidth;
    const mobile = width < 801;
    const duration = mobile ? 1100 : 1750;
    const animations = [];
    const curtain = document.createElement('div');
    curtain.className = 'signature-curtain';
    curtain.setAttribute('aria-hidden', 'true');
    curtain.style.top = `${startY}px`;
    curtain.style.width = `${width}px`;
    curtain.style.height = `${height}px`;
    const titleRect = title.getBoundingClientRect();
    const titleStyle = getComputedStyle(title);
    const floating = document.createElement('div');
    floating.className = 'signature-title';
    floating.textContent = title.textContent;
    floating.setAttribute('aria-hidden', 'true');
    Object.assign(floating.style, { left: `${titleRect.left}px`, top: `${titleRect.top}px`, width: `${titleRect.width}px`, fontSize: titleStyle.fontSize, fontWeight: titleStyle.fontWeight, letterSpacing: titleStyle.letterSpacing, lineHeight: titleStyle.lineHeight });
    const skip = document.createElement('button');
    skip.type = 'button';
    skip.className = 'signature-skip';
    skip.textContent = 'Intro überspringen ↗';
    body.append(curtain, floating, skip);
    body.dataset.introActive = 'true';
    let finished = false;
    const finish = () => {
        if (finished)
            return;
        finished = true;
        animations.forEach(a => a.cancel());
        curtain.remove();
        floating.remove();
        skip.remove();
        delete body.dataset.introActive;
        window.removeEventListener('resize', finish);
        window.removeEventListener('wheel', finish);
        window.removeEventListener('touchstart', finish);
        abortIntro = null;
    };
    abortIntro = finish;
    skip.addEventListener('click', finish);
    window.addEventListener('resize', finish, { once: true });
    window.addEventListener('wheel', finish, { once: true, passive: true });
    window.addEventListener('touchstart', finish, { once: true, passive: true });
    const end = `translate(${rect.left}px,${rect.top - startY}px) scale(${rect.width / width},${rect.height / height})`;
    animations.push(curtain.animate([
        { transform: 'translate(0,0) scale(1)', background: 'var(--accent)', offset: 0 },
        { transform: 'translate(0,0) scale(1)', background: 'var(--accent)', offset: .15 },
        { transform: end, background: 'var(--pale)', offset: .83 },
        { transform: end, background: 'var(--card)', offset: 1 }
    ], { duration, easing: ease, fill: 'both' }));
    const dx = (mobile ? 26 : width * .047) - titleRect.left;
    const dy = startY + height * .38 - titleRect.top;
    animations.push(floating.animate([
        { transform: `translate(${dx}px,${dy}px) scale(${mobile ? 1.05 : 1.24})`, color: '#fff', offset: 0 },
        { transform: `translate(${dx}px,${dy}px) scale(${mobile ? 1.05 : 1.24})`, color: '#fff', offset: .15 },
        { transform: 'translate(0,0) scale(1)', color: titleStyle.color, offset: .87 },
        { transform: 'translate(0,0) scale(1)', color: titleStyle.color, offset: 1 }
    ], { duration, easing: ease, fill: 'both' }));
    hero.parentElement?.querySelectorAll('.service-card,.bento-intro').forEach((tile, i) => {
        const t = tile.getBoundingClientRect();
        const x = (rect.left + rect.width / 2 - t.left - t.width / 2) * .40;
        const y = (rect.top + rect.height / 2 - t.top - t.height / 2) * .40;
        const a = animate(tile, [{ opacity: 0, transform: `translate(${x}px,${y}px) scale(.76)` }, { opacity: 1, transform: 'translate(0,0) scale(1)' }], mobile ? 580 : 900, (mobile ? 150 : 420) + i * 48);
        if (a)
            animations.push(a);
    });
    animations[0].finished.then(finish, finish);
}
replay?.addEventListener('click', () => { const hero = document.querySelector('[data-signature-hero]'); if (hero) {
    window.scrollTo({ top: 0, behavior: 'instant' });
    requestAnimationFrame(playSignature);
} });
let seen = false;
try {
    seen = sessionStorage.getItem('studio-intro-seen') === '1';
}
catch { /* Animation still works with blocked storage. */ }
if (body.dataset.intro !== 'off' && (!seen || body.dataset.intro === 'always')) {
    requestAnimationFrame(playSignature);
    if (motionAllowed() && configured === 'signature' && !body.classList.contains('is-preview') && document.querySelector('[data-signature-hero]') && !document.querySelector('[data-signature-hero]')?.closest('[data-animation="none"]'))
        try {
            sessionStorage.setItem('studio-intro-seen', '1');
        }
        catch { /* No persistent dependency. */ }
}
let revealObserver = null;
const entered = new WeakSet();
export function replayModules(id = '') {
    const targets = id ? Array.from(document.querySelectorAll('[data-block-id]')).filter(el => el.dataset.blockId === id) : Array.from(document.querySelectorAll('.module-shell')).filter(el => { const r = el.getBoundingClientRect(); return r.bottom > 0 && r.top < innerHeight; });
    targets.forEach(el => choreograph(el));
}
function choreograph(el) {
    if (!enabledFor(el))
        return;
    const direction = el.dataset.animation;
    const tiles = Array.from(el.querySelectorAll('.service-card,.bento-intro,.hero-tile,.contact-note,.contact-cta,.feature-card,.news-card,.story-timeline li'));
    if (tiles.length && (direction === 'stack' || direction === 'repeat' || el.dataset.module === 'bento' || el.dataset.module === 'contact')) {
        const container = el.getBoundingClientRect();
        tiles.forEach((tile, i) => { const r = tile.getBoundingClientRect(); const x = (container.left + container.width / 2 - r.left - r.width / 2) * .12; animate(tile, [{ opacity: .08, transform: `translate(${x}px,25px) scale(.94)` }, { opacity: 1, transform: 'none' }], 680, Math.min(i, 9) * 45); });
    }
    else if (direction === 'unfold')
        animate(el, [{ opacity: .15, clipPath: 'inset(0 0 65% 0)', transform: 'translateY(22px)' }, { opacity: 1, clipPath: 'inset(0 0 0% 0)', transform: 'none' }], 850);
    else
        animate(el, [{ opacity: .15, transform: direction === 'slide' ? 'translateX(-32px)' : 'translateY(28px)' }, { opacity: 1, transform: 'none' }], configured === 'subtle' ? 350 : 650);
}
export function refreshReveals() {
    revealObserver?.disconnect();
    if (!('IntersectionObserver' in window))
        return;
    revealObserver = new IntersectionObserver(entries => entries.forEach(entry => {
        const el = entry.target;
        if (!entry.isIntersecting) {
            el.dataset.inSection = 'false';
            return;
        }
        if (el.dataset.inSection === 'true')
            return;
        el.dataset.inSection = 'true';
        const first = !entered.has(el);
        entered.add(el);
        const repeat = el.dataset.animation === 'repeat' || el.dataset.animation === 'auto' && ['bento', 'contact'].includes(el.dataset.module || '');
        if (document.body.classList.contains('is-preview') || document.body.dataset.introActive === 'true')
            return;
        if (first || repeat)
            choreograph(el);
    }), { threshold: .05, rootMargin: '0px 0px -10px 0px' });
    document.querySelectorAll('.module-shell').forEach(el => revealObserver.observe(el));
}
refreshReveals();
/** Animate only changed positions after a filter. No click interception or layout loop. */
export function animateReflow(elements, previous) {
    elements.forEach((el, i) => {
        if (el.hidden || !enabledFor(el))
            return;
        const old = previous.get(el), now = el.getBoundingClientRect();
        animate(el, [{ opacity: old ? 1 : 0, transform: old ? `translate(${old.left - now.left}px,${old.top - now.top}px)` : 'translateY(18px)' }, { opacity: 1, transform: 'none' }], 440, i * 24);
    });
}
