/** The editor only sends validated, server-rendered HTML. No arbitrary embeds exist. */
import { refreshReveals, replayModules } from './motion.js';
import { initializeExperience } from './experience.js';
export function initializePreviewBridge() {
    if (!document.body.classList.contains('is-preview') || parent === window)
        return;
    let interactive = false, selected = '', busy = false;
    const fingerprints = new Map();
    document.body.dataset.previewMode = 'select';
    const notify = (data) => parent.postMessage(data, location.origin);
    function highlight(id, scroll = false) {
        selected = id;
        document.querySelectorAll('[data-block-id]').forEach(el => {
            el.classList.toggle('studio-selected', el.dataset.blockId === id);
            el.dataset.moduleLabel = el.dataset.module || 'Modul';
            if (scroll && el.dataset.blockId === id)
                el.scrollIntoView({ block: 'nearest', behavior: 'instant' });
        });
    }
    document.addEventListener('click', event => {
        const target = event.target;
        if (target.closest('a')) {
            event.preventDefault();
            if (interactive)
                notify({ type: 'studio-preview-link' });
        }
        const block = target.closest('[data-block-id]');
        if (block && !interactive) {
            event.preventDefault();
            event.stopImmediatePropagation();
            highlight(block.dataset.blockId || '');
            notify({ type: 'studio-select-block', id: block.dataset.blockId });
        }
    }, true);
    document.addEventListener('submit', event => { event.preventDefault(); event.stopImmediatePropagation(); }, true);
    window.addEventListener('message', event => {
        if (event.origin !== location.origin || event.source !== parent || !event.data || typeof event.data.type !== 'string')
            return;
        const message = event.data;
        if (message.type === 'studio-preview-mode') {
            interactive = message.interactive === true;
            document.body.dataset.previewMode = interactive ? 'interactive' : 'select';
            return;
        }
        if (message.type === 'studio-preview-select' && typeof message.id === 'string') {
            highlight(message.id, true);
            return;
        }
        if (message.type === 'studio-preview-play') {
            replayModules(selected);
            return;
        }
        if (message.type !== 'studio-preview-patch' || typeof message.html !== 'string' || message.html.length > 9000000 || busy)
            return;
        busy = true;
        try {
            const parsed = new DOMParser().parseFromString(message.html, 'text/html');
            const incoming = parsed.getElementById('main'), main = document.getElementById('main');
            if (!incoming || !main)
                return;
            const top = scrollY, left = scrollX;
            const existing = new Map(Array.from(main.querySelectorAll(':scope > [data-block-id]')).map(el => [el.dataset.blockId, el]));
            const fragment = document.createDocumentFragment();
            const nextPrints = new Map();
            incoming.childNodes.forEach(node => {
                if (node instanceof HTMLElement && node.dataset.blockId) {
                    const id = node.dataset.blockId, html = node.outerHTML, previous = existing.get(id);
                    nextPrints.set(id, html);
                    if (previous && fingerprints.get(id) === html)
                        fragment.append(previous);
                    else {
                        const copy = node.cloneNode(true);
                        copy.classList.add('preview-changed');
                        fragment.append(copy);
                    }
                }
                else
                    fragment.append(node.cloneNode(true));
            });
            main.replaceChildren(fragment);
            fingerprints.clear();
            nextPrints.forEach((value, key) => fingerprints.set(key, value));
            document.title = parsed.title;
            initializeExperience(main);
            refreshReveals();
            highlight(selected);
            window.scrollTo({ left, top, behavior: 'instant' });
            document.querySelectorAll('.preview-changed').forEach(el => setTimeout(() => el.classList.remove('preview-changed'), 700));
            notify({ type: 'studio-preview-patched' });
        }
        finally {
            busy = false;
        }
    });
    highlight('');
    notify({ type: 'studio-preview-ready' });
}
