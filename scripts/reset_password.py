#!/usr/bin/env python3
"""Local administrative recovery. Run with the project's installed environment."""
from pathlib import Path
import argparse
import getpass
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.database import Database
from app.security import HASHER

parser = argparse.ArgumentParser(description='Passwort eines lokalen Teamkontos zuruecksetzen')
parser.add_argument('email')
parser.add_argument('--data-dir',type=Path,default=Path(__file__).resolve().parents[1]/'data')
args = parser.parse_args()
if not (args.data_dir/'studio.sqlite3').is_file():
    parser.exit(1,'Keine bestehende Datenbank gefunden.\n')
db = Database(args.data_dir)
user = db.one('SELECT id FROM users WHERE email=?',(args.email.lower(),))
if not user:
    parser.exit(1,'Konto nicht gefunden.\n')
password = getpass.getpass('Neues Passwort (mindestens 12 Zeichen): ')
if len(password)<12 or len(password)>256 or password != getpass.getpass('Passwort wiederholen: '):
    parser.exit(1,'Passwoerter stimmen nicht ueberein oder sind zu kurz/lang.\n')
with db.connect(write=True) as con:
    con.execute('UPDATE users SET password_hash=? WHERE id=?',(HASHER.hash(password),user['id']))
    con.execute('DELETE FROM sessions WHERE user_id=?',(user['id'],))
    db.audit(con,user['id'],'local_password_reset',str(user['id']))
print('Passwort geaendert und alle Sitzungen dieses Kontos beendet.')
