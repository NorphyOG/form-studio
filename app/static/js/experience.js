/** Lightweight, repeatable interactions; no animation framework or scroll hijacking. */
import { motionAllowed } from './motion.js';
let visibility = null;
export function initializeExperience(root = document) {
    root.querySelectorAll('[data-tabs]:not([data-enhanced])').forEach(group => {
        group.dataset.enhanced = 'true';
        const tabs = Array.from(group.querySelectorAll('[role=tab]'));
        const panels = Array.from(group.querySelectorAll('.topic-panel'));
        const bar = group.querySelector('.topic-buttons');
        if (bar)
            bar.hidden = false;
        const activate = (index, focus = false) => {
            tabs.forEach((tab, i) => { tab.setAttribute('aria-selected', String(i === index)); tab.tabIndex = i === index ? 0 : -1; });
            panels.forEach((panel, i) => { panel.hidden = i !== index; panel.setAttribute('role', 'tabpanel'); panel.tabIndex = 0; });
            if (focus)
                tabs[index]?.focus();
            if (motionAllowed())
                panels[index]?.animate([{ opacity: .1, transform: 'translateY(15px)' }, { opacity: 1, transform: 'none' }], { duration: 420, easing: 'cubic-bezier(.22,1,.36,1)' });
        };
        tabs.forEach((tab, i) => {
            tab.addEventListener('click', () => activate(i));
            tab.addEventListener('keydown', event => {
                let next = i;
                if (event.key === 'ArrowRight')
                    next = (i + 1) % tabs.length;
                else if (event.key === 'ArrowLeft')
                    next = (i + tabs.length - 1) % tabs.length;
                else if (event.key === 'Home')
                    next = 0;
                else if (event.key === 'End')
                    next = tabs.length - 1;
                else
                    return;
                event.preventDefault();
                activate(next, true);
            });
        });
        activate(0);
    });
    root.querySelectorAll('[data-comparison]:not([data-enhanced])').forEach(group => {
        group.dataset.enhanced = 'true';
        const input = group.querySelector('input[type=range]');
        input.addEventListener('input', () => { const value = Math.max(0, Math.min(100, Number(input.value))); group.style.setProperty('--split', value + '%'); input.setAttribute('aria-valuetext', value + ' Prozent Nachher'); });
    });
    // Each card only updates while a precise pointer is actually over it.
    if (matchMedia('(hover:hover) and (pointer:fine)').matches) {
        root.querySelectorAll('.service-card:not([data-kinetic]),.news-cover:not([data-kinetic]),.spotlight-visual:not([data-kinetic])').forEach(card => {
            card.dataset.kinetic = 'true';
            let frame = 0, x = 0, y = 0, rect = null;
            card.addEventListener('pointerenter', () => { rect = card.getBoundingClientRect(); card.classList.add('is-pointing'); });
            card.addEventListener('pointermove', event => {
                if (!motionAllowed() || card.closest('[data-animation="none"]') || document.body.dataset.motion !== 'signature' || !rect)
                    return;
                x = Math.min(1, Math.max(-1, (event.clientX - rect.left) / rect.width * 2 - 1));
                y = Math.min(1, Math.max(-1, (event.clientY - rect.top) / rect.height * 2 - 1));
                if (!frame)
                    frame = requestAnimationFrame(() => { frame = 0; card.style.transform = `perspective(1000px) rotateX(${-y * 3}deg) rotateY(${x * 4}deg) translateY(-3px)`; card.style.setProperty('--pointer-x', `${(x + 1) * 50}%`); card.style.setProperty('--pointer-y', `${(y + 1) * 50}%`); });
            });
            const reset = () => { cancelAnimationFrame(frame); frame = 0; rect = null; card.style.removeProperty('transform'); card.classList.remove('is-pointing'); };
            card.addEventListener('pointerleave', reset);
            card.addEventListener('blur', reset);
        });
    }
    visibility?.disconnect();
    if ('IntersectionObserver' in window) {
        visibility = new IntersectionObserver(entries => entries.forEach(entry => entry.target.classList.toggle('in-viewport', entry.isIntersecting)), { rootMargin: '40px' });
        document.querySelectorAll('.spotlight-visual,.hero-tile,.story-timeline').forEach(el => visibility.observe(el));
    }
}
let scrollFrame = 0;
function updateProgress() {
    scrollFrame = 0;
    const distance = Math.max(1, document.documentElement.scrollHeight - innerHeight);
    const progress = document.querySelector('.reading-progress');
    if (progress)
        progress.style.transform = `scaleX(${Math.max(0, Math.min(1, scrollY / distance))})`;
}
window.addEventListener('scroll', () => { if (!scrollFrame)
    scrollFrame = requestAnimationFrame(updateProgress); }, { passive: true });
window.addEventListener('resize', updateProgress);
updateProgress();
document.addEventListener('visibilitychange', () => document.body.classList.toggle('page-sleeping', document.hidden));
// Native navigation stays native. Supporting browsers morph the selected graphic.
document.addEventListener('click', event => {
    if (event.defaultPrevented || event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey || !motionAllowed() || document.body.classList.contains('is-preview'))
        return;
    const link = event.target.closest('a');
    if (!link || link.target || !link.href || new URL(link.href).origin !== location.origin)
        return;
    const graphic = link.querySelector('.news-cover,.project-cover,.art');
    if (graphic) {
        document.querySelectorAll('[data-shared-transition]').forEach(el => { el.style.removeProperty('view-transition-name'); delete el.dataset.sharedTransition; });
        graphic.style.viewTransitionName = 'content-visual';
        graphic.dataset.sharedTransition = 'true';
    }
});
window.addEventListener('pageshow', () => document.querySelectorAll('[data-shared-transition]').forEach(el => { el.style.removeProperty('view-transition-name'); delete el.dataset.sharedTransition; }));
