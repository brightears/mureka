"""Render a blend plan (from blend_plan.py) — chain each track's layers through overlay.py.
Usage: apply_plan.py <plan.json> <out_root> [ext=mp3|flac] [workers=4]
Output: <out_root>/<playlist>/<base name>.<ext>; plain (no-layer) tracks are copied/converted as-is."""
import json, os, shutil, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(__file__))
import overlay
LIB = os.path.expanduser('~/Downloads/Christmas Ableton/overlays')

def render(entry, out_root, ext):
    name = os.path.splitext(os.path.basename(entry['base']))[0]
    dst_dir = os.path.join(out_root, entry['playlist']); os.makedirs(dst_dir, exist_ok=True)
    dst = os.path.join(dst_dir, f'{name}.{ext}')
    if os.path.exists(dst): return f'skip {name}'
    cur, tmp = entry['base'], tempfile.mkdtemp()
    for i, l in enumerate(entry['layers']):
        nxt = os.path.join(tmp, f'step{i}.flac')
        r = overlay.main(cur, os.path.join(LIB, l['overlay']), nxt, l['gain_db'], 'free' if l['kind'] == 'free' else None, check_key=False)  # planner already matched keys on the clean base; re-measuring a layered mix misreads it
        if 'skipped' in r: return f"KEYSKIP {name}: {r['skipped']} ({l['overlay']})"
        cur = nxt
    if cur == entry['base']:
        subprocess.run(['ffmpeg', '-v', 'quiet', '-y', '-i', cur, '-ar', '44100'] + (['-c:a', 'flac'] if ext == 'flac' else ['-ab', '256k']) + [dst], check=True)
    else:
        subprocess.run(['ffmpeg', '-v', 'quiet', '-y', '-i', cur] + (['-c:a', 'copy'] if ext == 'flac' else ['-ab', '256k']) + [dst], check=True)
    shutil.rmtree(tmp, ignore_errors=True)
    return f"ok {name} [{' + '.join(l['overlay'] for l in entry['layers']) or 'plain'}]"

def _s(e, o, x):
    try: return render(e, o, x)
    except Exception as ex: return f"ERROR {os.path.basename(e['base'])}: {ex}"

if __name__ == '__main__':
    plan = json.load(open(sys.argv[1])); out_root = sys.argv[2]
    ext = sys.argv[3] if len(sys.argv) > 3 else 'mp3'; w = int(sys.argv[4]) if len(sys.argv) > 4 else 4
    with ThreadPoolExecutor(w) as ex:
        for m in ex.map(lambda e: _s(e, out_root, ext), plan): print(m, flush=True)

