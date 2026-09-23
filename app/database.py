"""SQLite repository boundary with atomic writes and an explicit schema version."""
from contextlib import contextmanager
from pathlib import Path
import sqlite3
import json
import time

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
 id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE,
 password_hash TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('admin','editor','moderator')),
 active INTEGER NOT NULL DEFAULT 1, created_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
 token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 csrf TEXT NOT NULL, expires INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS content (
 id TEXT PRIMARY KEY, kind TEXT NOT NULL, slug TEXT NOT NULL,
 draft TEXT NOT NULL, published TEXT, published_slug TEXT,
 state TEXT NOT NULL DEFAULT 'draft', revision INTEGER NOT NULL DEFAULT 1,
 note TEXT NOT NULL DEFAULT '', archived INTEGER NOT NULL DEFAULT 0,
 updated_at INTEGER NOT NULL, updated_by INTEGER REFERENCES users(id),
 UNIQUE(kind,slug)
);
CREATE UNIQUE INDEX IF NOT EXISTS content_live_slug ON content(kind,published_slug) WHERE published IS NOT NULL;
CREATE TABLE IF NOT EXISTS revisions (
 id INTEGER PRIMARY KEY, content_id TEXT NOT NULL REFERENCES content(id),
 revision INTEGER NOT NULL, data TEXT NOT NULL, action TEXT NOT NULL,
 user_id INTEGER REFERENCES users(id), created_at INTEGER NOT NULL,
 UNIQUE(content_id,revision)
);
CREATE TABLE IF NOT EXISTS inquiries (
 id TEXT PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL, service TEXT NOT NULL,
 message TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'new', created_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS media (
 id TEXT PRIMARY KEY, filename TEXT NOT NULL, alt TEXT NOT NULL, width INTEGER NOT NULL,
 height INTEGER NOT NULL, created_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS audit (
 id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES users(id), action TEXT NOT NULL,
 target TEXT NOT NULL, created_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS rate_limits (key TEXT PRIMARY KEY, hits INTEGER NOT NULL, expires INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS block_presets (
 id TEXT PRIMARY KEY, name TEXT NOT NULL, block TEXT NOT NULL,
 created_by INTEGER REFERENCES users(id), created_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS content_admin ON content(kind,archived,updated_at DESC,id);
CREATE INDEX IF NOT EXISTS content_state ON content(archived,state,updated_at DESC);
CREATE INDEX IF NOT EXISTS content_public_order ON content(kind, json_extract(published,'$.order'), id)
 WHERE published IS NOT NULL AND archived=0;
CREATE INDEX IF NOT EXISTS content_article_date ON content(json_extract(published,'$.published_on') DESC,id)
 WHERE kind='article' AND published IS NOT NULL AND archived=0;
CREATE INDEX IF NOT EXISTS content_navigation ON content(json_extract(published,'$.order'),id)
 WHERE kind='page' AND published IS NOT NULL AND archived=0 AND json_extract(published,'$.in_navigation')=1;
CREATE INDEX IF NOT EXISTS media_recent ON media(created_at DESC,id);
CREATE INDEX IF NOT EXISTS inquiries_recent ON inquiries(created_at DESC,id);
CREATE TABLE IF NOT EXISTS metrics_daily (
 day TEXT NOT NULL, event TEXT NOT NULL, resource TEXT NOT NULL, count INTEGER NOT NULL DEFAULT 0,
 PRIMARY KEY(day,event,resource)
);
PRAGMA user_version = 3;
"""

def now():
    return int(time.time())

def encode(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))

class Database:
    def __init__(self, data_dir: Path):
        data_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir = data_dir
        self.path = data_dir / "studio.sqlite3"
        self.media_dir = data_dir / "media"
        self.media_dir.mkdir(exist_ok=True)

    @contextmanager
    def connect(self, write=False):
        con = sqlite3.connect(self.path, timeout=15)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys=ON")
        con.execute("PRAGMA busy_timeout=15000")
        try:
            if write:
                con.execute("BEGIN IMMEDIATE")
            yield con
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()

    def init(self):
        with self.connect() as con:
            version = con.execute("PRAGMA user_version").fetchone()[0]
            if version > 3:
                raise RuntimeError("Die Datenbank ist neuer als diese Programmversion.")
            con.execute("PRAGMA journal_mode=WAL")
            con.executescript(SCHEMA)

    def one(self, sql, params=()):
        with self.connect() as con:
            row = con.execute(sql, params).fetchone()
            return dict(row) if row else None

    def all(self, sql, params=()):
        with self.connect() as con:
            return [dict(row) for row in con.execute(sql, params).fetchall()]

    @staticmethod
    def audit(con, user_id, action, target):
        con.execute("INSERT INTO audit(user_id,action,target,created_at) VALUES(?,?,?,?)",
                    (user_id, action, target, now()))

    def rate(self, key, limit, seconds):
        with self.connect(write=True) as con:
            t = now()
            con.execute("DELETE FROM rate_limits WHERE expires<?", (t,))
            row = con.execute("SELECT hits FROM rate_limits WHERE key=?", (key,)).fetchone()
            if row and row[0] >= limit:
                return False
            con.execute("INSERT INTO rate_limits VALUES(?,1,?) ON CONFLICT(key) DO UPDATE SET hits=hits+1", (key, t+seconds))
            return True
