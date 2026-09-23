/** Optional first-party telemetry. Before opt-in this module makes no requests. */
export function initializeAnalytics() {
    const body = document.body;
    if (body.dataset.analytics !== 'on' || body.classList.contains('is-preview'))
        return;
    const panel = document.querySelector('.privacy-panel');
    const privacySignal = navigator.doNotTrack === '1' || navigator.globalPrivacyControl === true;
    const key = 'studio-statistics-choice-v1';
    let accepted = false, started = false, viewSent = false, interval, observer = null;
    const token = Array.from(crypto.getRandomValues(new Uint8Array(16)), v => v.toString(16).padStart(2, '0')).join('');
    const canonical = document.querySelector('link[rel=canonical]')?.href || location.href;
    const path = new URL(canonical).pathname;
    const pending = new Map();
    const impressions = new Set();
    function emit(event, resource = '') {
        if (!accepted || privacySignal)
            return;
        if (event === 'pageview') {
            if (viewSent)
                event = 'heartbeat';
            else
                viewSent = true;
        }
        void fetch('/api/analytics/event', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ event, resource, token, path, consent: true }), keepalive: true }).catch(() => { });
    }
    function stop() {
        clearInterval(interval);
        observer?.disconnect();
        pending.forEach(clearTimeout);
        pending.clear();
        started = false;
    }
    function start() {
        if (started || !accepted || privacySignal)
            return;
        started = true;
        if (!document.hidden)
            emit('pageview');
        interval = window.setInterval(() => { if (!document.hidden)
            emit('heartbeat'); }, 30000);
        if ('IntersectionObserver' in window) {
            observer = new IntersectionObserver(entries => entries.forEach(entry => {
                const el = entry.target, id = el.dataset.campaign;
                if (entry.isIntersecting && entry.intersectionRatio >= .5 && !document.hidden && !impressions.has(id) && !pending.has(el)) {
                    pending.set(el, window.setTimeout(() => { pending.delete(el); if (!accepted || document.hidden)
                        return; impressions.add(id); emit('ad_impression', id); observer?.unobserve(el); }, 1000));
                }
                else if (!entry.isIntersecting || entry.intersectionRatio < .5) {
                    const timer = pending.get(el);
                    if (timer)
                        clearTimeout(timer);
                    pending.delete(el);
                }
            }), { threshold: [0, .5] });
            document.querySelectorAll('[data-campaign]').forEach(el => observer.observe(el));
        }
    }
    function choose(choice) {
        if (accepted && choice === 'denied')
            emit('leave');
        accepted = choice === 'accepted' && !privacySignal;
        try {
            localStorage.setItem(key, JSON.stringify({ choice, expires: Date.now() + 180 * 86400000 }));
        }
        catch { /* Preference lasts for this page when storage is unavailable. */ }
        if (panel)
            panel.hidden = true;
        if (accepted)
            start();
        else
            stop();
    }
    try {
        const stored = JSON.parse(localStorage.getItem(key) || 'null');
        if (stored && stored.expires > Date.now()) {
            accepted = stored.choice === 'accepted' && !privacySignal;
            if (accepted)
                start();
        }
        else if (panel && !privacySignal)
            panel.hidden = false;
    }
    catch {
        if (panel && !privacySignal)
            panel.hidden = false;
    }
    document.querySelectorAll('[data-consent]').forEach(button => button.addEventListener('click', () => choose(button.dataset.consent === 'accepted' ? 'accepted' : 'denied')));
    document.querySelector('.privacy-settings')?.addEventListener('click', () => { if (!panel)
        return; panel.hidden = !panel.hidden; if (!panel.hidden) {
        panel.querySelector('button')?.focus();
        if (privacySignal)
            panel.querySelector('strong').textContent = 'Dein Browser verlangt: nicht erfassen. Das wird respektiert.';
    } });
    document.addEventListener('click', event => { const link = event.target.closest('[data-ad-click]'); if (link && !document.hidden)
        emit('ad_click', link.dataset.adClick); });
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            pending.forEach(clearTimeout);
            pending.clear();
            emit('leave');
        }
        else if (accepted) {
            emit('pageview');
            observer?.disconnect();
            document.querySelectorAll('[data-campaign]').forEach(el => observer?.observe(el));
        }
    });
    window.addEventListener('pagehide', () => { emit('leave'); stop(); });
    window.addEventListener('pageshow', () => { if (accepted)
        start(); });
}
