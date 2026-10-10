"""Can melody_id (song endpoint) yield an INSTRUMENTAL rendering of a public-domain carol?
Lyrics = structure tags only. Outputs -> ~/Downloads/Christmas/Carol Tests/<tune> C-melody-instrumental-N.mp3"""
import os, sys, time, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
from samples import call
from carol_test_ids import IDS  # melody upload ids from the first carol test
OUT = os.path.expanduser('~/Downloads/Christmas/Carol Tests')
LY = "[Intro]\n\n[Instrumental]\n\n[Instrumental]\n\n[Outro]"
jobs = [(t, call('/v1/song/generate', {'model': 'mureka-9.5', 'n': 2, 'melody_id': m, 'lyrics': LY})['id']) for t, m in IDS.items()]
for t, tid in jobs:
    while True:
        time.sleep(10); q = call(f'/v1/song/query/{tid}')
        if q['status'] in ('succeeded', 'failed', 'timeouted', 'cancelled'): break
    print(t, q['status'], q.get('failed_reason') or '')
    for i, c in enumerate(q.get('choices') or [], 1):
        p = f'{OUT}/{t} C-melody-instrumental-{i}.mp3'; urllib.request.urlretrieve(c['url'], p); print('  ->', os.path.basename(p), round((c.get('duration') or 0)/1000), 's')
