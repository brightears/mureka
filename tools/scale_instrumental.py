"""Stage 1 for INSTRUMENTAL playlists: families [{key, prompt, gens}] on mureka-9 (instrumental rule),
n=2, ≤5 concurrent, resumable (by generation slot), titles from the TS ledger (generateUniqueTitles),
raw FLAC to output/tracks/_raw/<slug>/, manifest data/<slug>-manifest.json with CDN links. No describe.
Usage: python3 tools/scale_instrumental.py <spec.json> <slug>
spec: {"model": "mureka-9", "title_genre": "christmas jazz", "families": [{"key": "...", "prompt": "...", "gens": 58}]}"""
import json, os, subprocess, sys, threading, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(__file__))
from samples import call
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
lock = threading.Lock()

def titles(n, genre):
    js = ("import {generateUniqueTitles} from './src/prompts/title-generator.ts';"
          f"console.log(JSON.stringify(generateUniqueTitles({n}, {json.dumps(genre)})));")
    out = subprocess.run(['npx', 'tsx', '-e', js], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return json.loads(out.strip().splitlines()[-1])

def run(slot, spec, raw, state, man_path):
    fam, idx = slot
    sid = f"{fam['key']}#{idx}"
    if sid in state['done']: return f'skip {sid}'
    t = call('/v1/instrumental/generate', {'model': spec['model'], 'n': 2, 'prompt': fam['prompt']})
    while True:
        time.sleep(15); q = call(f"/v1/instrumental/query/{t['id']}")
        if q['status'] in ('succeeded', 'failed', 'timeouted', 'cancelled'): break
    if q['status'] != 'succeeded': return f"FAIL {sid}: {q['status']} {q.get('failed_reason') or ''}"
    entries = []
    for c in q['choices']:
        with lock: title = state['titles'].pop()
        src = c.get('flac_url') or c['url']; ext = 'flac' if c.get('flac_url') else 'mp3'
        path = os.path.join(raw, f"{title}.{ext}"); urllib.request.urlretrieve(src, path)
        entries.append({'title': title, 'family': fam['key'], 'genId': t['id'], 'songId': c.get('id'), 'flac': path,
                        'url': c['url'], 'flac_url': c.get('flac_url'), 'durationMs': c.get('duration'),
                        'instruments': [], 'genres': [], 'slot': sid})
    with lock:
        state['man'] += entries; state['done'].add(sid)
        json.dump(state['man'], open(man_path, 'w'), indent=1)
    return f"ok {sid} -> {', '.join(e['title'] for e in entries)} [{len(state['man'])}]"

def main(spec_path, slug):
    spec = json.load(open(spec_path)); raw = os.path.join(ROOT, 'output', 'tracks', '_raw', slug); os.makedirs(raw, exist_ok=True)
    man_path = os.path.join(ROOT, 'data', f'{slug}-manifest.json')
    man = json.load(open(man_path)) if os.path.exists(man_path) else []
    slots = [(f, i) for f in spec['families'] for i in range(f['gens'])]
    done = {e['slot'] for e in man}
    need = 2 * (len(slots) - len(done))
    state = {'man': man, 'done': done, 'titles': titles(need, spec.get('title_genre', 'instrumental')) if need else []}
    print(f'{len(slots)} generations ({len(done)} already done), {need} titles reserved', flush=True)
    with ThreadPoolExecutor(max_workers=5) as ex:
        for msg in ex.map(lambda s: _safe(s, spec, raw, state, man_path), slots): print(msg, flush=True)
    print(f'STAGE1 DONE {slug}: {len(state["man"])} tracks', flush=True)

def _safe(*a):
    try: return run(*a)
    except Exception as e: return f"ERROR {a[0][0]['key']}#{a[0][1]}: {e}"

if __name__ == '__main__': main(sys.argv[1], sys.argv[2])
