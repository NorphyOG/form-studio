#!/usr/bin/env python3
"""Capture real local site HTML in Chromium and build design showcase media.

This is a local visual check, not a deployed-host browser test. Page resources
are served by FastAPI TestClient while the HTML is loaded through set_content.
"""
from io import BytesIO
from pathlib import Path
import os
import sys
import tempfile

from fastapi.testclient import TestClient
from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.config import Settings
from app.main import create_app


OUT = ROOT / 'docs'
DESIGNS = ('studio', 'noir', 'editorial', 'atelier', 'aurora',
           'brutalist', 'minimal', 'garden', 'sunset', 'terminal')
BASE = 'http://127.0.0.1:8765'


def capture() -> None:
    shots = OUT / 'designs'
    shots.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='form-studio-designs-') as data:
        app = create_app(Settings(Path(data), origin=BASE))
        with TestClient(app, base_url=BASE) as client, sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=os.environ.get('CHROMIUM_EXECUTABLE'),
                headless=True,
                args=['--no-sandbox'],
            )
            page = browser.new_page(viewport={'width': 1200, 'height': 780}, reduced_motion='reduce', device_scale_factor=1)
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))

            def route(request):
                path = request.request.url.removeprefix(BASE)
                response = client.get(path)
                request.fulfill(status=response.status_code, body=response.content,
                                headers={'content-type': response.headers.get('content-type', 'application/octet-stream'),
                                         'access-control-allow-origin': '*'})

            page.route(BASE + '/**', route)
            html = client.get('/').text.replace('<head>', f'<head><base href="{BASE}/">', 1)
            page.set_content(html, wait_until='networkidle')
            assert page.locator('.service-card').count() == 7
            images = []
            for design in DESIGNS:
                page.locator('body').evaluate('(body, name) => body.dataset.design = name', design)
                assert page.locator('body').get_attribute('data-design') == design
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'), design
                content = page.screenshot(path=str(shots / f'{design}.png'))
                images.append((design, Image.open(BytesIO(content)).convert('RGB')))
                page.set_viewport_size({'width': 390, 'height': 844})
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'), f'{design} mobile'
                page.set_viewport_size({'width': 1200, 'height': 780})
            setup_key = (Path(data) / '.setup-key').read_text()
            setup = client.post('/api/setup', json={
                'setup_key': setup_key, 'name': 'Visual Test',
                'email': 'visual@example.test', 'password': 'Visual-test-password-2026!',
            }, headers={'Origin': BASE})
            assert setup.status_code == 200, setup.text
            admin = browser.new_page(viewport={'width': 1440, 'height': 1000}, reduced_motion='reduce')
            admin.on('pageerror', lambda error: errors.append(str(error)))
            admin.route(BASE + '/**', route)
            admin_html = client.get('/admin').text.replace('<head>', f'<head><base href="{BASE}/">', 1)
            admin.set_content(admin_html, wait_until='networkidle')
            # In about:blank transport, a literal #settings link resolves via <base>
            # to the public URL. Set the local hash to exercise the same route.
            admin.evaluate("location.hash = 'settings'")
            admin.locator('#open-settings').click()
            admin.locator('[data-design-option]').first.wait_for(timeout=10000)
            assert admin.locator('[data-design-option]').count() == 10
            admin.locator('[data-design-option="noir"]').click()
            assert admin.locator('[name="design"]').input_value() == 'noir'
            admin.screenshot(path=str(OUT / 'admin-designs.png'))
            assert not errors, errors
            browser.close()

    font = ImageFont.load_default()
    thumb_w, thumb_h = 480, 312
    board = Image.new('RGB', (thumb_w * 2 + 72, (thumb_h + 48) * 5 + 48), '#eef0ed')
    draw = ImageDraw.Draw(board)
    gif_frames = []
    for index, (design, shot) in enumerate(images):
        thumb = shot.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        x = 24 + (index % 2) * (thumb_w + 24)
        y = 24 + (index // 2) * (thumb_h + 48)
        board.paste(thumb, (x, y + 24))
        draw.text((x, y + 5), f'{index + 1:02}  {design.upper()}', fill='#202b2b', font=font)
        frame = Image.new('RGB', (800, 570), '#eef0ed')
        frame_draw = ImageDraw.Draw(frame)
        frame_draw.text((24, 20), f'FORM / STUDIO  |  {index + 1:02} / 10  |  {design.upper()}', fill='#202b2b', font=font)
        frame.paste(shot.resize((752, 489), Image.Resampling.LANCZOS), (24, 55))
        gif_frames.append(frame)
    board.save(OUT / 'design-gallery.png', optimize=True)
    gif_frames[0].save(OUT / 'design-switcher.gif', save_all=True,
                       append_images=gif_frames[1:], duration=900, loop=0, optimize=True)
    print('Captured 10 desktop and 10 mobile layouts; no overflow or page errors.')


if __name__ == '__main__':
    capture()
