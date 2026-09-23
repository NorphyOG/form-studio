"""Public collection is opt-in; dashboards and deletion have explicit permissions."""
from typing import Literal
from fastapi import APIRouter, Depends, Request, Query, HTTPException
from pydantic import Field
from ..models import Model
from ..security import roles, COOKIE
from ..analytics import enabled, public_path_exists, save_count, summary
from ..collections import active_campaign

router = APIRouter()


class Event(Model):
    event: Literal['pageview', 'heartbeat', 'leave', 'ad_impression', 'ad_click']
    token: str = Field(pattern=r'^[a-f0-9]{32}$')
    path: str = Field(pattern=r'^/(?:[a-z0-9-]+/?)*$', max_length=150)
    resource: str = Field(default='', pattern=r'^(|[a-f0-9]{32})$')
    consent: Literal[True]


@router.post('/api/analytics/event')
def collect(body: Event, request: Request):
    db = request.app.state.db
    # Logged-in browser previews and privacy signals are never counted.
    if request.cookies.get(COOKIE) or request.headers.get('DNT') == '1' or request.headers.get('Sec-GPC') == '1' or not enabled(db):
        return {'recorded': False}
    if not public_path_exists(db, body.path):
        raise HTTPException(422, 'Nur veröffentlichte öffentliche Seiten können gezählt werden.')
    resource = body.path
    if body.event.startswith('ad_'):
        if not active_campaign(db, body.resource):
            return {'recorded': False}
        resource = body.resource
    runtime = request.app.state.analytics
    accepted = runtime.accept(body.token, body.path, body.event,
                              request.client.host if request.client else 'unknown', resource)
    if accepted:
        save_count(db, runtime, body.event, resource)
    return {'recorded': accepted}


@router.get('/api/admin/analytics')
def report(request: Request, days: int = Query(30, ge=1, le=90), user=Depends(roles('admin', 'moderator'))):
    return summary(request.app.state.db, request.app.state.analytics, days)


@router.delete('/api/admin/analytics')
def erase(request: Request, user=Depends(roles('admin'))):
    db = request.app.state.db
    with db.connect(write=True) as con:
        con.execute('DELETE FROM metrics_daily')
        db.audit(con, user['id'], 'analytics_erased', 'metrics_daily')
    request.app.state.analytics.clear()
    return {'ok': True}
