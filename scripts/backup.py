#!/usr/bin/env python3
"""Consistent SQLite backup plus immutable referenced media. Treat output as private."""
from __future__ import annotations
import argparse
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]

def backup(data: Path, destination: Path) -> Path:
    database = data / 'studio.sqlite3'
    if not database.is_file():
        raise FileNotFoundError(f'Keine Datenbank: {database}')
    destination.mkdir(parents=True, exist_ok=True)
    target = destination / ('studio-backup-' + datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f') + '.zip')
    with tempfile.TemporaryDirectory() as temporary:
        snapshot = Path(temporary) / 'studio.sqlite3'
        with closing(sqlite3.connect(f'{database.resolve().as_uri()}?mode=ro', uri=True)) as source:
            with closing(sqlite3.connect(snapshot)) as copy:
                source.backup(copy)
                media = [row[0] for row in copy.execute('SELECT filename FROM media')]
        # Media names never change in this version, and there is no media deletion endpoint.
        # Therefore referenced files remain valid after the database snapshot.
        try:
            with zipfile.ZipFile(target, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
                archive.write(snapshot, 'studio.sqlite3')
                for name in media:
                    if Path(name).name != name:
                        raise ValueError('Ungueltiger Medienname in der Datenbank.')
                    archive.write(data / 'media' / name, 'media/' + name)
            target.chmod(0o600)
        except Exception:
            target.unlink(missing_ok=True)
            raise
    return target

def main() -> None:
    parser = argparse.ArgumentParser(description='Datenbank und Medien sichern')
    parser.add_argument('--data-dir', type=Path, default=ROOT/'data')
    parser.add_argument('--output', type=Path, default=ROOT/'backups')
    args = parser.parse_args()
    try:
        print(backup(args.data_dir, args.output))
        print('Enthaelt private Inhalte, Konten und Anfragen. Geschuetzt aufbewahren.')
    except (OSError, ValueError, sqlite3.Error) as error:
        parser.exit(1, f'Backup fehlgeschlagen: {error}\n')

if __name__ == '__main__':
    main()
