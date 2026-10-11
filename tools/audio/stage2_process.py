"""Spa Ambient scale — STAGE 2: parallel clean pipeline over the manifest,
then rank by pulse strength and place best N in the playlist folder (spares aside).
Usage: stage2_process.py <manifest.json> <out_dir> <album> <keep_n> <venv_python>"""
import json, os, subprocess, sys
# Threads, not processes: the heavy lifting happens in clean_track.py SUBPROCESSES,
# and macOS spawn + no __main__ guard makes ProcessPoolExecutor re-exec this script.
from concurrent.futures import ThreadPoolExecutor

MANIFEST, OUT_DIR, ALBUM, KEEP_N, PY = (
    sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), sys.argv[5])
HERE = os.path.dirname(os.path.abspath(__file__))
TMP_DIR = os.path.join(OUT_DIR, '_processing')
SPARES = os.path.join(OUT_DIR, '_spares')
os.makedirs(TMP_DIR, exist_ok=True)
os.makedirs(SPARES, exist_ok=True)

entries = json.load(open(MANIFEST))

def sanitize(s):
    import re
    return re.sub(r'\s+', ' ', re.sub(r'[<>:"/\\|?*]+', '-', s)).strip()

def process(e):
    # Cleaned output is lossless FLAC (the single archived playlist artifact
    # on the personal drive); production MP3s are derived from these in stage 3.
    out = os.path.join(TMP_DIR, sanitize(e['title']) + '.flac')
    if not os.path.exists(out):
        r = subprocess.run([PY, os.path.join(HERE, 'clean_track.py'),
                            e['flac'], out, e['title'], ALBUM],
                           capture_output=True, text=True)
        if r.returncode != 0 or not os.path.exists(out):
            return (e['title'], None, f'clean failed: {r.stderr[-200:]}')
    r = subprocess.run([PY, os.path.join(HERE, 'beatcheck.py'), out, '60'],
                       capture_output=True, text=True)
    strength = None
    for tok in r.stdout.split():
        if tok.startswith('strength='):
            strength = float(tok.split('=')[1])
    return (e['title'], out, strength)

results = []
with ThreadPoolExecutor(max_workers=5) as ex:
    for i, res in enumerate(ex.map(process, entries), 1):
        results.append(res)
        print(f'[{i}/{len(entries)}] {res[0]} -> pulse {res[2]}')

ok = [r for r in results if r[1] and isinstance(r[2], float)]
bad = [r for r in results if not r[1]]
ok.sort(key=lambda r: r[2])                      # lowest pulse = best
keep, spare = ok[:KEEP_N], ok[KEEP_N:]
for title, path, s in keep:
    os.replace(path, os.path.join(OUT_DIR, os.path.basename(path)))
for title, path, s in spare:
    os.replace(path, os.path.join(SPARES, os.path.basename(path)))
os.rmdir(TMP_DIR) if not os.listdir(TMP_DIR) else None

report = {
    'kept': len(keep), 'spares': len(spare), 'failed': [r[0] for r in bad],
    'pulse_kept_min': keep[0][2] if keep else None,
    'pulse_kept_max': keep[-1][2] if keep else None,
    'pulse_spares': [round(s, 3) for _, _, s in spare],
}
json.dump(report, open(os.path.join(OUT_DIR, '_stage2_report.json'), 'w'), indent=1)
print('STAGE2 DONE', json.dumps(report))
