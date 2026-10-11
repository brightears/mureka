"""Stage 1 for VOCAL playlists: one song per lyric set (n=1) on mureka-9.5 (vocal rule), ≤5 concurrent,
resumable (skips titles already in the manifest), raw FLAC masters to output/tracks/_raw/<slug>/,
manifest data/<slug>-manifest.json with CDN links. Reserves all titles in data/used-titles.json first.
No describe calls. Usage: python3 tools/scale_songs.py data/samples/<spec>.json <slug>"""
import json, os, sys, threading, time, urllib.request, datetime
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(__file__))
from samples import call
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
lock = threading.Lock()

def reserve_titles(titles):
    p = os.path.join(ROOT, 'data', 'used-titles.json'); d = json.load(open(p))
    s = set(d['titles']); new = [t.lower() for t in titles if t.lower() not in s]
    d['titles'] = sorted(s | set(new)); d['count'] = len(d['titles'])
    d['lastUpdated'] = datetime.datetime.utcnow().isoformat(timespec='milliseconds') + 'Z'
    json.dump(d, open(p, 'w'), indent=2); return len(new)

def run(song, spec, raw, man, man_path):
    title = f"MU - {song['title']}"
    if title in man: return f"skip {title}"
    body = {'model': spec['model'], 'n': 1, 'lyrics': song['lyrics'], 'prompt': song['prompt']}
    if song.get('gender'): body['gender'] = song['gender']
    t = call('/v1/song/generate', body)
    while True:
        time.sleep(15); q = call(f"/v1/song/query/{t['id']}")
        if q['status'] in ('succeeded', 'failed', 'timeouted', 'cancelled'): break
    if q['status'] != 'succeeded': return f"FAIL {title}: {q['status']} {q.get('failed_reason') or ''}"
    c = q['choices'][0]; src = c.get('flac_url') or c['url']; ext = 'flac' if c.get('flac_url') else 'mp3'
    path = os.path.join(raw, f"{song['title']}.{ext}"); urllib.request.urlretrieve(src, path)
    entry = {'title': title, 'family': song['style'], 'genId': t['id'], 'songId': c.get('id'), 'flac': path,
             'url': c['url'], 'flac_url': c.get('flac_url'), 'durationMs': c.get('duration'),
             'instruments': [], 'genres': [], 'lyrics_title': song['title']}
    with lock:
        man[title] = entry; json.dump(list(man.values()), open(man_path, 'w'), indent=1)
    return f"ok {title} ({round((c.get('duration') or 0)/1000)}s) [{len(man)}]"

def main(spec_path, slug):
    spec = json.load(open(spec_path)); raw = os.path.join(ROOT, 'output', 'tracks', '_raw', slug); os.makedirs(raw, exist_ok=True)
    man_path = os.path.join(ROOT, 'data', f'{slug}-manifest.json')
    man = {e['title']: e for e in json.load(open(man_path))} if os.path.exists(man_path) else {}
    print('titles newly reserved in ledger:', reserve_titles([s['title'] for s in spec['songs']]), flush=True)
    with ThreadPoolExecutor(max_workers=5) as ex:
        for msg in ex.map(lambda s: _safe(s, spec, raw, man, man_path), spec['songs']): print(msg, flush=True)
    print(f'STAGE1 DONE {slug}: {len(man)} songs', flush=True)

def _safe(*a):
    try: return run(*a)
    except Exception as e: return f"ERROR {a[0]['title']}: {e}"

if __name__ == '__main__': main(sys.argv[1], sys.argv[2])
