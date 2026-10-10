"""SAMPLE-round generator (durable; the session scratchpad gets wiped between days).
Reads a spec JSON, fires every family on mureka-9.5 (≤5 concurrent), polls, downloads MP3s to
~/Downloads/<root>/<playlist>/<playlist> Sample <KEY>-<i>.mp3, optionally runs /v1/song/describe
($0.10/track) and writes <spec>.results.json with generation ids + describe tags.

Spec: {"root": "Christmas", "model": "mureka-9.5", "describe": true,   (per-family "model" overrides, for A/B only)
       "families": [{"key": "J1", "playlist": "Christmas Jazz", "kind": "instrumental"|"song",
                     "prompt": "...", "lyrics": "... (song only)", "gender": "female|male", "n": 2}]}
Usage: python3 tools/samples.py data/samples/<spec>.json [KEY ...]   (keys = run a subset)"""
import json, os, sys, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEY = next((l.split('=', 1)[1].strip() for l in open(os.path.join(ROOT_DIR, '.env')) if l.startswith('MUREKA_API_KEY=')), None)
API = 'https://api.mureka.ai'

def call(path, body=None, tries=6):
    for i in range(tries):
        req = urllib.request.Request(API + path, data=json.dumps(body).encode() if body is not None else None,
                                     headers={'Authorization': f'Bearer {KEY}', 'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=120) as r: return json.load(r)
        except urllib.error.HTTPError as e:
            msg = e.read().decode()[:300]
            if e.code in (429, 500, 502, 503) and i < tries - 1: time.sleep(20 * (i + 1)); continue
            raise RuntimeError(f'{path} -> {e.code} {msg}')
        except (urllib.error.URLError, TimeoutError):
            if i < tries - 1: time.sleep(10); continue
            raise

def run_family(f, spec):
    kind = f.get('kind', 'instrumental')
    default_model = spec.get('song_model', 'mureka-9.5') if kind == 'song' else spec.get('model', 'mureka-9')  # blind test 2026-09-29
    body = {'model': f.get('model') or default_model, 'n': f.get('n', 2), 'prompt': f['prompt']}
    if kind == 'song':
        body['lyrics'] = f['lyrics']
        if f.get('gender'): body['gender'] = f['gender']
    task = call(f'/v1/{kind}/generate', body)
    tid = task['id']
    while True:
        time.sleep(10)
        q = call(f'/v1/{kind}/query/{tid}')
        if q['status'] in ('succeeded', 'failed', 'timeouted', 'cancelled'): break
    if q['status'] != 'succeeded':
        return {'key': f['key'], 'status': q['status'], 'reason': q.get('failed_reason'), 'genId': tid}
    out_dir = os.path.expanduser(f"~/Downloads/{spec['root']}/{f['playlist']}")
    os.makedirs(out_dir, exist_ok=True)
    tracks = []
    for i, c in enumerate(q['choices'], 1):
        path = os.path.join(out_dir, f"{f['playlist']} Sample {f['key']}-{i}.mp3")
        urllib.request.urlretrieve(c['url'], path)
        t = {'file': path, 'songId': c.get('id'), 'url': c['url'], 'flac_url': c.get('flac_url'),
             'durationMs': c.get('duration')}
        if spec.get('describe', False):  # $0.10/track — off by default; Norbert judges by ear
            try:
                d = call('/v1/song/describe', {'url': c['url']})
                t.update(instruments=d.get('instrument', []), genres=d.get('genres', []), tags=d.get('tags', []))
            except Exception as e: t['describe_error'] = str(e)
        tracks.append(t)
    return {'key': f['key'], 'playlist': f['playlist'], 'status': 'succeeded', 'genId': tid,
            'prompt': f['prompt'], 'tracks': tracks}

def main():
    spec_path = sys.argv[1]; only = set(sys.argv[2:])
    spec = json.load(open(spec_path))
    fams = [f for f in spec['families'] if not only or f['key'] in only]
    res_path = spec_path.replace('.json', '.results.json')
    results = json.load(open(res_path)) if os.path.exists(res_path) else {}
    with ThreadPoolExecutor(max_workers=5) as ex:
        for r in ex.map(lambda f: _safe(run_family, f, spec), fams):
            results[r['key']] = r
            print(f"[{r['key']}] {r['status']}", *[
                f"\n   {os.path.basename(t['file'])} | {round((t.get('durationMs') or 0)/1000)}s | "
                f"{', '.join(t.get('instruments', []))} | {', '.join(t.get('genres', []))}" for t in r.get('tracks', [])],
                flush=True)
            json.dump(results, open(res_path, 'w'), indent=1)
    print('RESULTS ->', res_path)

def _safe(fn, f, spec):
    try: return fn(f, spec)
    except Exception as e: return {'key': f['key'], 'status': 'error', 'reason': str(e)}

if __name__ == '__main__': main()
