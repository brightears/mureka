"""STAGE 2 (light) — for full-band genres that need NO spectral masks (country, jazz...).
Per track: micro-fades + loudnorm I=-17.5 + tags -> cleaned FLAC.
Selection from manifest by describe() evidence: `--require family:Instrument` keeps only
tracks of that family whose instruments contain the term. Best keep_n by preference
(required-instrument matches first), spares to _spares/.
Usage: stage2_light.py <manifest.json> <out_dir> <album> <keep_n> [--require G1:Fiddle ...]"""
import json, os, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

MANIFEST, OUT_DIR, ALBUM, KEEP_N = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
REQ = {}
for a in sys.argv[5:]:
    if a.startswith('--require'): continue
    fam, inst = a.split(':', 1); REQ.setdefault(fam, []).append(inst.lower())
TMP = os.path.join(OUT_DIR, '_processing'); SPARES = os.path.join(OUT_DIR, '_spares')
os.makedirs(TMP, exist_ok=True); os.makedirs(SPARES, exist_ok=True)
entries = json.load(open(MANIFEST))
san = lambda s: re.sub(r'\s+', ' ', re.sub(r'[<>:"/\\|?*]+', '-', s)).strip()

# Drift terms are GENRE-SPECIFIC: default = country list; override per run with
# DRIFT_TERMS="vocal,sax,trumpet" (comma-separated). Describe labels chillout/nylon-guitar
# material as 'Smooth Jazz' routinely - that label alone is NOT drift for chillout runs.
HARD_DRIFT = tuple(t.strip().lower() for t in os.environ.get('DRIFT_TERMS', 'hawaiian,celtic,jazz,ukulele,bossa').split(',') if t.strip())
def ok(e):
    need = REQ.get(e['family'], [])
    ins = ' '.join(e.get('instruments', [])).lower()
    gen = ' '.join(e.get('genres', [])).lower()
    return all(n in ins for n in need) and not any(t in gen or t in ins for t in HARD_DRIFT)

def clean(e):
    out = os.path.join(TMP, san(e['title']) + '.flac')
    if os.path.exists(out): return out
    dur = float(subprocess.run(['ffprobe','-v','quiet','-show_entries','format=duration','-of','csv=p=0',e['flac']],
                               capture_output=True, text=True).stdout.strip() or 0)
    r = subprocess.run(['ffmpeg','-v','quiet','-y','-i',e['flac'],'-af',
        f'afade=t=in:st=0:d={os.environ.get("FADE_IN", "0.05")},afade=t=out:st={max(dur-0.8,0):.2f}:d=0.8,loudnorm=I=-17.5:TP=-1.5:LRA=11',
        '-metadata',f'title={e["title"]}','-metadata','artist=BMAsia','-metadata',f'album={ALBUM}',
        '-metadata',f'genre={os.environ.get("GENRE_TAG","Country")}','-metadata','date=2026','-ar','44100','-acodec','flac', out])
    return out if r.returncode == 0 and os.path.exists(out) else None

good = [e for e in entries if ok(e)]; bad = [e for e in entries if not ok(e)]
print(f'manifest {len(entries)} | pass describe-filter {len(good)} | fail {len(bad)}')
keep, spare = good[:KEEP_N], good[KEEP_N:] + bad
with ThreadPoolExecutor(max_workers=5) as ex:
    for i, out in enumerate(ex.map(clean, keep), 1):
        print(f'[{i}/{len(keep)}] {"ok" if out else "FAILED"}')
        if out: os.replace(out, os.path.join(OUT_DIR, os.path.basename(out)))
    for out in ex.map(clean, spare):
        if out: os.replace(out, os.path.join(SPARES, os.path.basename(out)))
if not os.listdir(TMP): os.rmdir(TMP)
print(f'STAGE2 DONE: kept {len(keep)} (of {len(good)} passing), spares {len(spare)}')
