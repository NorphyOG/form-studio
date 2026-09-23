#!/usr/bin/env python3
"""Restore an own trusted backup into an empty directory; revoke saved sessions."""
from __future__ import annotations
import argparse
from contextlib import closing
from pathlib import Path
import re
import shutil
import sqlite3
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]

def restore(source: Path, target: Path) -> None:
    if target.exists() and any(target.iterdir()):
        raise ValueError('Zielordner ist nicht leer. Server stoppen und bisherigen Datenordner zuerst umbenennen.')
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=target.parent) as temporary:
        stage = Path(temporary)
        with zipfile.ZipFile(source) as archive:
            names = archive.namelist()
            if 'studio.sqlite3' not in names or len(names) != len(set(names)):
                raise ValueError('Kein eindeutiges Studio-Backup.')
            for member in archive.infolist():
                if member.filename != 'studio.sqlite3' and not re.fullmatch(r'media/[a-f0-9]{32}\.webp', member.filename):
                    raise ValueError('Unerwarteter Dateipfad im Backup.')
                output = stage / member.filename
                output.parent.mkdir(exist_ok=True)
                with archive.open(member) as src, output.open('wb') as dest:
                    shutil.copyfileobj(src, dest)
        with closing(sqlite3.connect(stage/'studio.sqlite3')) as db, db:
            if db.execute('PRAGMA quick_check').fetchone()[0] != 'ok':
                raise ValueError('Datenbankpruefung fehlgeschlagen.')
            if db.execute('PRAGMA user_version').fetchone()[0] not in (1, 2, 3):
                raise ValueError('Nicht unterstuetzte Datenbankversion.')
            for name, in db.execute('SELECT filename FROM media'):
                if not (stage/'media'/name).is_file():
                    raise ValueError('Ein referenziertes Medium fehlt.')
            db.execute('DELETE FROM sessions')
            db.commit()
        if target.exists():
            target.rmdir()
        shutil.copytree(stage, target)
        (target/'media').mkdir(exist_ok=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Eigenes, vertrauenswuerdiges Backup wiederherstellen')
    parser.add_argument('backup', type=Path)
    parser.add_argument('--data-dir', type=Path, default=ROOT/'data')
    args = parser.parse_args()
    try:
        restore(args.backup,args.data_dir)
        print(f'Wiederhergestellt: {args.data_dir}\nAlle Sitzungen wurden beendet. Jetzt Server starten und neu anmelden.')
    except (OSError, ValueError, sqlite3.Error, zipfile.BadZipFile) as error:
        parser.exit(1, f'Wiederherstellung fehlgeschlagen: {error}\n')
