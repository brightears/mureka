"""Test two ways of getting a PUBLIC-DOMAIN carol melody into Mureka output:
 A) song/generate with melody_id (MIDI upload) + wordless vocalise lyrics (mureka-9.5)
 B) track/generate generate_type=Instrumental around the rendered melody audio (V8, $0.09)
Outputs -> ~/Downloads/Christmas/Carol Tests/. Waits for free concurrency via samples.call retries."""
import json, os, subprocess, sys, time, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
from samples import call, KEY, API
OUT = os.path.expanduser('~/Downloads/Christmas/Carol Tests'); os.makedirs(OUT, exist_ok=True)
MEL = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'melodies')

def upload(path, purpose):
    r = subprocess.run(['curl', '-s', f'{API}/v1/files/upload', '-H', f'Authorization: Bearer {KEY}',
                        '-F', f'purpose={purpose}', '-F', f'file=@{path}'], capture_output=True, text=True).stdout
    d = json.loads(r); print('upload', os.path.basename(path), purpose, '->', d.get('id') or d); return d['id']

def wait(kind, tid):
    while True:
        time.sleep(10); q = call(f'/v1/{kind}/query/{tid}')
        if q['status'] in ('succeeded', 'failed', 'timeouted', 'cancelled'): return q

VOCALISE = "[Verse]\nOoh, ooh, ooh\nOoh, ooh, ooh\nLa, la, la, la\nLa, la, la, la\n\n[Chorus]\nOoh, ooh, ooh\nAh, ah, ah\nLa, la, la, la\nOoh, ooh"
jobs = []
for tune in ('silent-night', 'jingle-bells'):
    try: mid = upload(f'{MEL}/{tune}.mid', 'melody')
    except KeyError: mid = upload(f'{MEL}/{tune}.mp3', 'melody')
    t = call('/v1/song/generate', {'model': 'mureka-9.5', 'n': 2, 'melody_id': mid, 'lyrics': VOCALISE})
    jobs.append(('song', t['id'], f'{tune} A-melody-id'))
    aud = upload(f'{MEL}/{tune}.mp3', 'audio')
    style = ('christmas music, slow jazz piano trio, upright bass, brushed drums, sleigh bells, celesta, 70 BPM'
             if tune == 'silent-night' else
             'christmas music, cheerful swing jazz band, real piano, upright bass, brushed drums, sleigh bells, 120 BPM')
    t = call('/v1/track/generate', {'upload_audio_id': aud, 'generate_type': 'Instrumental', 'prompt': style})
    jobs.append(('song', t['id'], f'{tune} B-track-generate'))
for kind, tid, label in jobs:
    q = wait(kind, tid); print(label, q['status'], q.get('model'), q.get('failed_reason') or '')
    for i, c in enumerate(q.get('choices') or [], 1):
        p = f'{OUT}/{label}-{i}.mp3'; urllib.request.urlretrieve(c['url'], p); print('  ->', p, round((c.get('duration') or 0) / 1000), 's')
