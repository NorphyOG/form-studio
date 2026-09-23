# Release check · 0.4.0

This file records checks for the ten-design and open-source packaging change. The [0.3 report](TESTBERICHT.md) remains historical evidence for the uploaded archive. A GitHub release should cite the exact commit and CI run rather than treating the older report as current proof.

## Scope

- Ten site-wide design packages selected in admin settings.
- Existing publish workflow preserves the live design until settings are published.
- AGPL-3.0-only license, source link, documentation and contribution files.
- Existing screenshots and motion GIF demonstrate the original Studio design. `designs/*.png`, `design-gallery.png` and `design-switcher.gif` are fresh Chromium captures of the same demo page with each design. The capture script checks all ten designs at desktop and mobile widths for overflow and page errors.

## Local result · 2026-09-23

- Python 3.13.2: **156 passed**, one third-party Starlette deprecation warning.
- TypeScript 5.8.3: `npm run typecheck` and `npm run build` passed. `npm ci --offline` reproduced the locked dependency.
- Installed Chrome with Playwright: ten public designs at 1200 px and 390 px without horizontal overflow or uncaught page errors. Admin design chooser displayed all ten options; choosing Noir updated the selected value. Captures in `docs/designs/` and `docs/admin-designs.png`.
- The browser run used FastAPI TestClient plus `set_content` because direct local socket binding was denied in this environment. It does not verify a deployed server, HTTPS, real same-origin navigation, Safari or Firefox.

## Commands

```bash
python -m pytest tests -q
npm ci
npm run typecheck
npm run build
```

## Limits

Local tests, visual captures and CI do not prove a production deployment is ready. Hosting requires the controls in `README.md` and `docs/SICHERHEIT-STATISTIK.md`. Browser and device coverage must be reported separately from server/API tests.
