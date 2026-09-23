"""Read models for archives, automatic modules and campaign slots."""
from datetime import datetime, timezone
import json
from .content import public_entry


def utc_day():
    return datetime.now(timezone.utc).date().isoformat()


def news_list(db, limit=12, offset=0, category='', query=''):
    where="kind='article' AND published IS NOT NULL AND archived=0"
    params=[]
    if category:
        where+=" AND json_extract(published,'$.category')=?"; params.append(category)
    if query:
        where+=" AND (instr(lower(json_extract(published,'$.title')),lower(?))>0 OR instr(lower(json_extract(published,'$.description')),lower(?))>0)"
        params.extend([query,query])
    total=db.one('SELECT count(*) n FROM content WHERE '+where,params)['n']
    rows=db.all("SELECT id,json_object('title',json_extract(published,'$.title'), 'slug',published_slug,"
        "'description',json_extract(published,'$.description'),'category',json_extract(published,'$.category'),"
        "'published_on',json_extract(published,'$.published_on'),'author',json_extract(published,'$.author'),"
        "'image',json_extract(published,'$.image'),'art',json_extract(published,'$.art'),"
        "'featured',json_extract(published,'$.featured')) data FROM content WHERE "+where+
        " ORDER BY json_extract(published,'$.published_on') DESC,id LIMIT ? OFFSET ?",params+[limit,offset])
    return dict(items=[dict(json.loads(r['data']),id=r['id']) for r in rows],total=total,limit=limit,offset=offset)


def active_campaign(db, identity):
    if not identity:
        return None
    row=db.one("SELECT published FROM content WHERE id=? AND kind='campaign' AND archived=0 AND published IS NOT NULL",(identity,))
    if not row:
        return None
    data=json.loads(row['published']); today=utc_day()
    if data.get('starts_on') and data['starts_on']>today or data.get('ends_on') and data['ends_on']<today:
        return None
    return dict(data,id=identity)


def collect_media_ids(value):
    ids=set()
    if isinstance(value,dict):
        if value.get('image'):
            ids.add(value['image'])
        for item in value.values():
            ids.update(collect_media_ids(item))
    elif isinstance(value,list):
        for item in value:
            ids.update(collect_media_ids(item))
    return ids


def media_for(db, *values):
    ids=set()
    for value in values:
        ids.update(collect_media_ids(value))
    # Page contracts cap this set; no full media-library scan per public request.
    ids=sorted(ids)
    rows=[]
    for start in range(0,len(ids),400):
        batch=ids[start:start+400]
        rows.extend(db.all('SELECT * FROM media WHERE id IN ('+','.join('?' for _ in batch)+')',batch))
    return {r['id']:r for r in rows}
