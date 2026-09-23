"""Opt-in, first-party aggregates. No raw IPs, user agents or visitor histories.

Active tabs exist only in this process's bounded RAM and expire after 90 seconds.
Counts are observational, not unique people, revenue attribution or anti-fraud data.
"""
from datetime import datetime, timedelta, timezone
from collections import OrderedDict
from threading import Lock
import hashlib
import hmac
import secrets
import time
from .collections import active_campaign
from .content import public_entry


class AnalyticsRuntime:
    def __init__(self):
        self.lock = Lock()
        self.tabs = OrderedDict()
        self.rates = OrderedDict()
        self.key = secrets.token_bytes(32)
        self.cleanup_at = 0.0

    def accept(self, token, path, event, address, resource):
        clock = time.monotonic()
        key = hmac.new(self.key, address.encode(), hashlib.sha256).digest()[:16]
        with self.lock:
            for collection, lifetime in ((self.tabs, 90), (self.rates, 60)):
                expired = [k for k, v in collection.items() if clock-v['time'] > lifetime]
                for item in expired:
                    del collection[item]
            rate = self.rates.get(key, {'time': clock, 'count': 0})
            if rate['count'] >= 180:
                return False
            rate['count'] += 1
            self.rates[key] = rate
            if len(self.rates) > 10000:
                self.rates.popitem(last=False)
            if event == 'leave':
                self.tabs.pop(token, None)
                return False
            tab = self.tabs.get(token, {'time': clock, 'path': path, 'seen': set()})
            tab['time'] = clock
            tab['path'] = path
            self.tabs[token] = tab
            self.tabs.move_to_end(token)
            if len(self.tabs) > 5000:
                self.tabs.popitem(last=False)
            identity = (event, resource)
            if event == 'heartbeat' or identity in tab['seen']:
                return False
            if len(tab['seen']) >= 100:
                return False
            tab['seen'].add(identity)
            return True

    def active(self):
        clock = time.monotonic()
        with self.lock:
            return sum(clock-tab['time'] <= 90 for tab in self.tabs.values())

    def clear(self):
        with self.lock:
            self.tabs.clear()
            self.rates.clear()


def enabled(db):
    settings = public_entry(db, 'settings', 'site')
    return bool(settings and settings.get('analytics_enabled', False))


def public_path_exists(db, path):
    if path in ('/', '/kontakt', '/news', '/leistungen', '/arbeiten'):
        return path != '/' or public_entry(db, 'page', 'home') is not None
    for prefix, kind in (('/p/', 'page'), ('/news/', 'article'), ('/arbeiten/', 'project'), ('/leistungen/', 'service')):
        if path.startswith(prefix):
            return public_entry(db, kind, path[len(prefix):]) is not None
    return False


def save_count(db, runtime, event, resource):
    today = datetime.now(timezone.utc).date()
    with db.connect(write=True) as con:
        con.execute('INSERT INTO metrics_daily(day,event,resource,count) VALUES(?,?,?,1) '
                    'ON CONFLICT(day,event,resource) DO UPDATE SET count=count+1',
                    (today.isoformat(), event, resource))
        # Deletion is occasional, not a full-table scan on every heartbeat.
        if time.monotonic() > runtime.cleanup_at:
            con.execute('DELETE FROM metrics_daily WHERE day<?', ((today-timedelta(days=89)).isoformat(),))
            runtime.cleanup_at = time.monotonic()+3600


def summary(db, runtime, days):
    today = datetime.now(timezone.utc).date()
    since = today-timedelta(days=days-1)
    rows = db.all('SELECT day,sum(count) count FROM metrics_daily WHERE day>=? AND event=? GROUP BY day',
                  (since.isoformat(), 'pageview'))
    by_day = {row['day']: row['count'] for row in rows}
    series = [dict(day=(since+timedelta(days=i)).isoformat(), count=by_day.get((since+timedelta(days=i)).isoformat(), 0)) for i in range(days)]
    top = db.all("SELECT resource,sum(count) count FROM metrics_daily WHERE day>=? AND event='pageview' "
                 'GROUP BY resource ORDER BY count DESC,resource LIMIT 10', (since.isoformat(),))
    campaigns = db.all("SELECT m.resource,max(json_extract(c.published,'$.title')) title,"
                     "sum(CASE WHEN m.event='ad_impression' THEN m.count ELSE 0 END) impressions,"
                     "sum(CASE WHEN m.event='ad_click' THEN m.count ELSE 0 END) clicks "
                     "FROM metrics_daily m LEFT JOIN content c ON c.id=m.resource WHERE day>=? AND event IN ('ad_impression','ad_click') "
                     'GROUP BY m.resource ORDER BY impressions DESC LIMIT 20', (since.isoformat(),))
    totals = db.one("SELECT coalesce(sum(CASE WHEN event='ad_impression' THEN count ELSE 0 END),0) impressions,coalesce(sum(CASE WHEN event='ad_click' THEN count ELSE 0 END),0) clicks FROM metrics_daily WHERE day>=?", (since.isoformat(),))
    return dict(ad_impressions=totals['impressions'],ad_clicks=totals['clicks'],enabled=enabled(db), days=days, timezone='UTC', retention_days=90,
                pageviews=sum(x['count'] for x in series), active_tabs=runtime.active(),
                series=series, top_pages=top, campaigns=campaigns,
                definitions='Nur zugestimmte, sichtbare Seitenfenster. Keine eindeutigen Personen. Aktive Tabs: letzte 90 Sekunden, eine Serverinstanz.')
