"""Versioned editorial workflow. Draft and public snapshots are deliberately separate."""
import json
import uuid
import sqlite3
from fastapi import HTTPException
from pydantic import ValidationError
from .database import now, encode
from .models import validate_content


def checked(kind, data):
    try:
        return validate_content(kind, data)
    except ValidationError as exc:
        messages = ['.'.join(str(x) for x in e['loc'])+': '+e['msg'] for e in exc.errors()]
        raise HTTPException(422, ' | '.join(messages)) from exc


def record(row):
    if not row:
        raise HTTPException(404, 'Inhalt nicht gefunden.')
    d = dict(row)
    d['data'] = json.loads(d.pop('draft'))
    d['live'] = json.loads(d['published']) if d['published'] else None
    del d['published']
    return d


def public_items(db, kind, limit=120, offset=0):
    """Bounded legacy collection; normal public pages use targeted queries."""
    return [dict(json.loads(r['published']), id=r['id']) for r in db.all(
        "SELECT id,published FROM content WHERE kind=? AND published IS NOT NULL AND archived=0 "
        "ORDER BY json_extract(published,'$.order'),id LIMIT ? OFFSET ?", (kind,limit,offset))]


def public_entry(db, kind, slug):
    row = db.one('SELECT id,published FROM content WHERE kind=? AND published_slug=? '
                 'AND published IS NOT NULL AND archived=0', (kind,slug))
    return dict(json.loads(row['published']), id=row['id']) if row else None


def list_content(db, kind=None, limit=100, offset=0, state=None):
    sql = 'SELECT * FROM content WHERE archived=0'
    params = []
    if kind:
        sql += ' AND kind=?'
        params.append(kind)
    if state:
        sql += ' AND state=?'
        params.append(state)
    return [record(r) for r in db.all(sql+' ORDER BY updated_at DESC,id LIMIT ? OFFSET ?', params+[limit,offset])]


def content_index(db, kind=None, state=None, query='', limit=24, offset=0):
    """Small cards, not the bodies of every document. Full record fetched on edit."""
    conditions=['archived=0']; params=[]
    if kind:
        conditions.append('kind=?'); params.append(kind)
    if state:
        conditions.append('state=?'); params.append(state)
    if query:
        # Literal substring search. The query is never interpolated into SQL.
        conditions.append("(instr(lower(json_extract(draft,'$.title')),lower(?))>0 OR instr(slug,lower(?))>0)")
        params.extend([query,query])
    where=' AND '.join(conditions)
    total=db.one('SELECT count(*) n FROM content WHERE '+where,params)['n']
    fields="""id,kind,state,revision,updated_at,note,
        json_extract(draft,'$.title') title,slug,
        json_extract(draft,'$.description') description,json_extract(draft,'$.order') ordering,
        json_extract(draft,'$.art') art,json_extract(draft,'$.category') category,
        json_array_length(draft,'$.blocks') block_count,published_slug"""
    rows=db.all('SELECT '+fields+' FROM content WHERE '+where+' ORDER BY updated_at DESC,id LIMIT ? OFFSET ?',params+[limit,offset])
    items=[]
    for r in rows:
        items.append(dict(id=r['id'],kind=r['kind'],state=r['state'],revision=r['revision'],
          updated_at=r['updated_at'],note=r['note'],block_count=r['block_count'] or 0,
          data=dict(title=r['title'],slug=r['slug'],description=r['description'] or '',order=r['ordering'] or 0,
                    art=r['art'],category=r['category']),
          live=dict(slug=r['published_slug']) if r['published_slug'] else None))
    return dict(items=items,total=total,limit=limit,offset=offset)


def create_content(db, kind, data, user_id=None, publish=False):
    data = checked(kind, data)
    identity = uuid.uuid4().hex
    state = 'published' if publish else 'draft'
    try:
        with db.connect(write=True) as con:
            if kind == 'settings' and con.execute("SELECT 1 FROM content WHERE kind='settings'").fetchone():
                raise HTTPException(409, 'Globale Einstellungen existieren bereits.')
            con.execute('INSERT INTO content(id,kind,slug,draft,published,published_slug,state,updated_at,updated_by) VALUES(?,?,?,?,?,?,?,?,?)',
                (identity,kind,data['slug'],encode(data),encode(data) if publish else None,data['slug'] if publish else None,state,now(),user_id))
            con.execute('INSERT INTO revisions(content_id,revision,data,action,user_id,created_at) VALUES(?,1,?,?,?,?)',
                (identity,encode(data),'created',user_id,now()))
            db.audit(con,user_id,'created',identity)
    except sqlite3.IntegrityError as exc:
        raise HTTPException(409,'Diese URL ist bereits vergeben.') from exc
    return record(db.one('SELECT * FROM content WHERE id=?',(identity,)))


def mutate_content(db, identity, action, expected_revision, user_id, data=None, note='', restore_revision=None):
    try:
        with db.connect(write=True) as con:
            row = con.execute('SELECT * FROM content WHERE id=? AND archived=0',(identity,)).fetchone()
            old = record(row)
            if old['revision'] != expected_revision:
                raise HTTPException(409,'Der Inhalt wurde zwischenzeitlich geändert. Bitte neu laden, bevor du speicherst.')
            new_data = old['data']
            live = old['live']
            live_slug = old['published_slug']
            state = old['state']
            archived = 0
            if action == 'save':
                new_data = checked(old['kind'],data)
                if old['kind']=='page' and old['slug']=='home' and new_data['slug']!='home':
                    raise HTTPException(422,'Die Startseite behält die URL-ID home.')
                state = 'draft'
                note = ''
            elif action == 'submit':
                if state not in ('draft','rejected'):
                    raise HTTPException(409,'Nur Entwürfe oder zurückgegebene Inhalte können eingereicht werden.')
                state = 'pending'
            elif action == 'publish':
                live = checked(old['kind'],new_data)
                live_slug = new_data['slug']
                state = 'published'
                note = ''
            elif action == 'reject':
                if state != 'pending':
                    raise HTTPException(409,'Dieser Inhalt wartet nicht auf Prüfung.')
                if not note.strip():
                    raise HTTPException(422,'Bitte einen Grund für die Rückgabe angeben.')
                state = 'rejected'
            elif action == 'unpublish':
                live = None
                live_slug = None
                state = 'draft'
            elif action == 'restore':
                rev = con.execute('SELECT data FROM revisions WHERE content_id=? AND revision=?',(identity,restore_revision)).fetchone()
                if not rev:
                    raise HTTPException(404,'Version nicht gefunden.')
                new_data = checked(old['kind'],json.loads(rev[0]))
                state = 'draft'
                note = ''
            elif action == 'archive':
                if old['kind']=='settings' or (old['kind']=='page' and old['slug']=='home'):
                    raise HTTPException(409,'Dieser zentrale Inhalt kann nicht archiviert werden.')
                archived = 1
                live = None
                live_slug = None
            else:
                raise HTTPException(400,'Unbekannte Aktion.')
            revision = expected_revision+1
            con.execute('UPDATE content SET slug=?,draft=?,published=?,published_slug=?,state=?,revision=?,note=?,archived=?,updated_at=?,updated_by=? WHERE id=?',
                (new_data['slug'],encode(new_data),encode(live) if live else None,live_slug,state,revision,note,archived,now(),user_id,identity))
            con.execute('INSERT INTO revisions(content_id,revision,data,action,user_id,created_at) VALUES(?,?,?,?,?,?)',
                (identity,revision,encode(new_data),action,user_id,now()))
            db.audit(con,user_id,action,identity)
    except sqlite3.IntegrityError as exc:
        raise HTTPException(409,'Diese URL ist bereits vergeben, möglicherweise noch von einer veröffentlichten Version.') from exc
    return record(db.one('SELECT * FROM content WHERE id=?',(identity,)))
