"""Christmas hybrid scale step: key-measure raw bases, pick keepers (C/F key families first), plan layers over ALL
tracks (spares too), render blended FLACs, write a stage2-ready manifest (keepers first).
Usage: <numpy-python> tools/xmas_blend_scale.py <slug> <Playlist Name> <keep_n> <blend_plan.py>"""
import json, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'audio'))
import trackinfo as ti
NOTE = {n: i for i, n in enumerate(['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B'])}
slug, playlist, keep_n, bp = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
man = json.load(open(os.path.join(ROOT, 'data', f'{slug}-manifest.json')))
def key_of(e):
    x = ti.load(e['flac']); k, conf = ti.key(ti.spectrogram(x)); t, q = k.split()
    return e['title'], k, (NOTE[t] if q == 'major' else (NOTE[t] + 3) % 12)
with ThreadPoolExecutor(6) as ex: keys = {t: (k, sig) for t, k, sig in ex.map(key_of, man)}
for e in man: e['key'], e['keysig'] = keys[e['title']]
fam_ok = [e for e in man if e['keysig'] in (0, 5)]; other = [e for e in man if e['keysig'] not in (0, 5)]
print(f'key families C/F: {len(fam_ok)} of {len(man)}; others: {sorted(set(e["key"] for e in other))}')
order = sorted(fam_ok, key=lambda e: -e['durationMs']) + sorted(other, key=lambda e: -e['durationMs'])
# planner input dir (folder name drives the genre recipe), keepers named first so rotation covers them
pdir = os.path.join(ROOT, 'output', 'tracks', '_plan', slug, playlist); os.makedirs(pdir, exist_ok=True)
for i, e in enumerate(order):
    link = os.path.join(pdir, f'{i:03d}__{os.path.basename(e["flac"])}')
    if not os.path.exists(link): os.symlink(e['flac'], link)
plan_path = os.path.join(ROOT, 'data', 'samples', f'{slug}-blend-plan.json')
subprocess.run([sys.executable, bp, os.path.dirname(pdir), plan_path], check=True, stdout=subprocess.DEVNULL)
out_root = os.path.join(ROOT, 'output', 'tracks', '_blend', slug)
subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'audio', 'apply_plan.py'), plan_path, out_root, 'flac', '4'], check=True)
plan = json.load(open(plan_path)); layers = {os.path.basename(p['base']).split('__', 1)[1]: p['layers'] for p in plan}
blended_dir = os.path.join(out_root, playlist)
new = []
for i, e in enumerate(order):
    fn = os.path.basename(e['flac']); b = os.path.join(blended_dir, f'{i:03d}__{os.path.splitext(fn)[0]}.flac')
    e2 = dict(e, raw=e['flac'], flac=b, layers=[l['overlay'] for l in layers.get(fn, [])], keeper=i < keep_n)
    if not os.path.exists(b): print('MISSING blend', fn)
    new.append(e2)
json.dump(new, open(os.path.join(ROOT, 'data', f'{slug}-manifest-blended.json'), 'w'), indent=1)
from collections import Counter
kept = new[:keep_n]
print(f'keepers {len(kept)} | layered {sum(1 for e in kept if e["layers"])} | plain {sum(1 for e in kept if not e["layers"])} '
      f'| layer files used {len({l for e in kept for l in e["layers"]})} | most-used {Counter(l for e in kept for l in e["layers"]).most_common(3)}')
