"""Christmas-identity layering via Mureka single-track generation (/v1/track/generate, V8, $0.09/call).
Two modes (jobs from a JSON spec):
  layer   : input = an approved instrumental; Mureka generates a matching <generate_type> layer
            (e.g. Percussion 'soft sleigh bells and chimes'); mixed UNDER the original at `gain_db`.
  arrange : input = a public-domain carol melody render (tools/melody.py); Mureka generates the
            accompaniment (generate_type Instrumental, style prompt) following the melody's key/tempo;
            the melody is mixed back on top at `gain_db`.
Both inputs are loudness-matched (-20 LUFS) before mixing so gain_db means the same thing every time;
final mix -> loudnorm -16 LUFS mp3 in ~/Downloads/<root>/<name>.mp3.  No describe calls.
Usage: python3 tools/layer.py <spec.json>"""
import json, os, subprocess, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(__file__))
from samples import call, KEY, API

def upload(path):
    r = subprocess.run(['curl', '-s', f'{API}/v1/files/upload', '-H', f'Authorization: Bearer {KEY}',
                        '-F', 'purpose=audio', '-F', f'file=@{path}'], capture_output=True, text=True).stdout
    d = json.loads(r)
    if 'id' not in d: raise RuntimeError(f'upload {os.path.basename(path)}: {d}')
    return d['id']

def run(job, root):
    out_dir = os.path.expanduser(f'~/Downloads/{root}'); os.makedirs(out_dir, exist_ok=True)
    src = os.path.expanduser(job['input'])
    t = call('/v1/track/generate', {'upload_audio_id': upload(src), 'generate_type': job['generate_type'],
                                    'prompt': job['prompt']})
    while True:
        time.sleep(10); q = call(f"/v1/song/query/{t['id']}")
        if q['status'] in ('succeeded', 'failed', 'timeouted', 'cancelled'): break
    if q['status'] != 'succeeded': return f"{job['name']}: {q['status']} {q.get('failed_reason') or ''}"
    gen = os.path.join(out_dir, f"_{job['name']} (generated {job['generate_type']}).mp3")
    urllib.request.urlretrieve(q['choices'][0]['url'], gen)
    RESULTS[job['name']] = {'task_id': t['id'], 'url': q['choices'][0]['url'], 'generated_file': gen, 'input': src}
    # base = the part that stays at full level; top = the part mixed at gain_db
    base, top = (src, gen) if job['mode'] == 'layer' else (gen, src)
    g = job.get('gain_db', -9 if job['mode'] == 'layer' else -3)
    dst = os.path.join(out_dir, f"{job['name']}.mp3")
    subprocess.run(['ffmpeg', '-v', 'quiet', '-y', '-i', base, '-i', top, '-filter_complex',
                    f'[0:a]loudnorm=I=-20,aresample=44100,aformat=channel_layouts=stereo[a];'
                    f'[1:a]loudnorm=I=-20,aresample=44100,aformat=channel_layouts=stereo,volume={g}dB[b];'
                    f'[a][b]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-16:TP=-1.5', '-ab', '256k', dst], check=True)
    d = float(subprocess.run(['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration', '-of', 'csv=p=0', dst],
                             capture_output=True, text=True).stdout or 0)
    return f"{job['name']}: ok ({d:.0f}s, generated layer kept as '_{job['name']} (generated ...)')"

RESULTS = {}  # name -> task id + CDN url of the generated part (CDN links live ~30 days)

def _safe(j, root):
    try: return run(j, root)
    except Exception as e: return f"{j['name']}: ERROR {e}"

if __name__ == '__main__':
    spec = json.load(open(sys.argv[1]))
    with ThreadPoolExecutor(max_workers=5) as ex:
        for msg in ex.map(lambda j: _safe(j, spec['root']), spec['jobs']):
            print(msg, flush=True)
    json.dump(RESULTS, open(sys.argv[1].replace('.json', '.results.json'), 'w'), indent=1)
