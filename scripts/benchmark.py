#!/usr/bin/env python3
"""Reproducible local read benchmark on an isolated synthetic database.
Not a production capacity, cross-device latency or concurrent-writer guarantee.
"""
import argparse,json,statistics,sys,tempfile,time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from app.main import create_app
from app.config import Settings
from app.content import create_content


def run(count=2000):
 with tempfile.TemporaryDirectory(prefix='studio-benchmark-') as d:
  app=create_app(Settings(Path(d),origin='http://testserver'))
  for i in range(count):
   create_content(app.state.db,'article',dict(title=f'Synthetic article {i:05}',slug=f'benchmark-{i}',description='Synthetic benchmark record.',body='Sample content. '*250,category='Benchmark',published_on='2026-01-01'),publish=True)
  client=TestClient(app,headers={'Origin':'http://testserver'})
  result={'synthetic_articles':count,'method':'Linux container, isolated TestClient, warm local reads, no network/TLS, no concurrent writers','routes':{}}
  for path in ['/','/news','/news/benchmark-100','/news?q=Synthetic']:
   response=client.get(path);assert response.status_code==200
   times=[]
   for _ in range(30):
    start=time.perf_counter();response=client.get(path);times.append((time.perf_counter()-start)*1000);assert response.status_code==200
   result['routes'][path]={'median_ms':round(statistics.median(times),2),'p95_ms':round(sorted(times)[28],2),'html_bytes':len(response.content),'runs':30}
  def request(_):
   start=time.perf_counter();r=client.get('/news');return r.status_code,round((time.perf_counter()-start)*1000,2)
  with ThreadPoolExecutor(max_workers=4) as pool:responses=list(pool.map(request,range(40)))
  assert all(status==200 for status,_ in responses)
  result['parallel_read_check']={'workers':4,'requests':40,'errors':0,'median_ms':round(statistics.median(x[1] for x in responses),2)}
  return result

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--count',type=int,default=2000);parser.add_argument('--output',type=Path,default=Path('docs/benchmark.json'));args=parser.parse_args()
 if not 101<=args.count<=100000:parser.error('count muss zwischen 101 und 100000 liegen')
 result=run(args.count);args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
