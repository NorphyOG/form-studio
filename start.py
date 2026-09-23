#!/usr/bin/env python3
"""Local launcher: isolated dependencies, first-admin setup, and a single server."""
from __future__ import annotations
import argparse
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import threading
import webbrowser

ROOT = Path(__file__).resolve().parent

def load_env() -> None:
    allowed = {'SITE_ORIGIN', 'SECURE_COOKIES', 'DATA_DIR', 'HOST', 'PORT'}
    env_file = ROOT / '.env'
    if env_file.exists():
        for line in env_file.read_text(encoding='utf-8-sig').splitlines():
            if not line.strip() or line.lstrip().startswith('#') or '=' not in line:
                continue
            key, value = line.split('=', 1)
            if key.strip() in allowed:
                os.environ.setdefault(key.strip(), value.strip().strip('"\''))

def bootstrap() -> Path:
    environment = ROOT / '.venv'
    executable = environment / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    if not executable.exists():
        print('1/2  Lokale Python-Umgebung wird angelegt ...', flush=True)
        subprocess.run([sys.executable, '-m', 'venv', str(environment)], check=True)
    requirements = ROOT / 'requirements.txt'
    expected = hashlib.sha256(requirements.read_bytes()).hexdigest()
    marker = environment / '.studio-dependencies'
    if not marker.exists() or marker.read_text().strip() != expected:
        print('2/2  Abhaengigkeiten werden installiert. Beim ersten Start ist Internet erforderlich.', flush=True)
        subprocess.run([str(executable), '-m', 'pip', 'install', '--disable-pip-version-check', '-r', str(requirements)], check=True)
        marker.write_text(expected)
    return executable

def main() -> int:
    if sys.version_info < (3, 11):
        print('Python 3.11 oder neuer ist erforderlich.')
        return 1
    parser = argparse.ArgumentParser(description='FORM / STUDIO lokal starten')
    parser.add_argument('--no-browser', action='store_true', help='Browser nicht automatisch oeffnen')
    parser.add_argument('--no-bootstrap', action='store_true', help='Bereits installierte Python-Umgebung verwenden')
    parser.add_argument('--check', action='store_true', help='Konfiguration und Datenbank pruefen, ohne Serverstart')
    args = parser.parse_args()
    os.chdir(ROOT)
    load_env()
    if not args.no_bootstrap:
        try:
            executable = bootstrap()
            return subprocess.call([str(executable), str(Path(__file__)), '--no-bootstrap', *sys.argv[1:]])
        except (subprocess.CalledProcessError, OSError) as error:
            print(f'Einrichtung fehlgeschlagen: {error}\nPython-Installation und Internetzugang pruefen, danach erneut starten.')
            return 1
    try:
        import uvicorn
        from app.main import create_app
        port = int(os.getenv('PORT', '8000'))
        host = os.getenv('HOST', '127.0.0.1')
        os.environ.setdefault('SITE_ORIGIN', f'http://127.0.0.1:{port}')
        app = create_app()
        origin = app.state.settings.origin
        print(f'\nFORM / STUDIO\nWebsite: {origin}/\nAdmin:   {origin}/admin\nDaten:   {app.state.db.data_dir.resolve()}\n', flush=True)
        key = app.state.db.data_dir / '.setup-key'
        if key.exists():
            print(f'Einmaliger Einrichtungscode:\n{key.read_text().strip()}\n\nNur im lokalen Admin-Setup eingeben. Nicht weitergeben.\n', flush=True)
        if args.check:
            print('Konfiguration, Datenbank und Module erfolgreich geladen.')
            return 0
        if not args.no_browser:
            timer = threading.Timer(1.8, lambda: webbrowser.open(origin + ('/admin' if key.exists() else '/')))
            timer.daemon = True
            timer.start()
        print('Dieses Terminal offen lassen. Beenden mit Strg+C.\n', flush=True)
        uvicorn.run(app, host=host, port=port, proxy_headers=False)
        return 0
    except (ImportError, OSError, ValueError, RuntimeError) as error:
        print(f'Start fehlgeschlagen: {error}')
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
