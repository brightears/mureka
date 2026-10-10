"""Mix a licensed / Ableton-rendered Christmas overlay into a Mureka base track — locally only
(Spitfire LABS / Fracture renders must never be uploaded to Mureka or any AI service).

Overlay filename carries its metadata:  <name>_<NN>bpm.wav  (loop)  and/or  _<Key>maj / _<Key>min
  e.g. sleighbells_80bpm.wav, silentnight_glock_Cmaj.wav, chimes_free_Fmaj.wav
Modes
  loop : time-stretch the loop to the base track's measured BPM (octave-resolved), align to its first
         beat, repeat for the whole track with 4 s fade-in/out.
  free : place the (unmetered) overlay a few times through the track at musically safe spots
         (default: after the intro, at the middle, before the outro), each with soft fades.
Key guard: pitched overlays must share the base's key signature (C maj = A min, F maj = D min, ...);
otherwise the track is skipped and reported. Unpitched overlays (no key in name) always pass.
Level: both parts loudness-matched first, overlay sits gain_db below (default -12 dB), final -16 LUFS.
Usage: overlay.py <base.mp3|flac> <overlay.wav> <out.mp3> [gain_db] [mode]"""
import json, os, re, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(__file__))
import trackinfo as ti

NOTE = {n: i for i, n in enumerate(['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B'])}
NOTE.update({'Db': 1, 'D#': 3, 'Gb': 6, 'G#': 8, 'A#': 10})

def signature(tonic, quality):            # relative major pitch class identifies the key signature
    pc = NOTE[tonic]; return pc if quality.startswith('maj') else (pc + 3) % 12

def meta(path):
    b = os.path.basename(path)
    bpm = re.search(r'_(\d{2,3})bpm', b, re.I)
    key = re.search(r'_([A-G](?:#|b)?)(maj|min)', b)
    return (float(bpm.group(1)) if bpm else None), (signature(key.group(1), key.group(2)) if key else None)

def dur(p):
    return float(subprocess.run(['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration', '-of', 'csv=p=0', p],
                                capture_output=True, text=True).stdout or 0)

def main(base, ov, out, gain_db=-12.0, mode=None):
    o_bpm, o_sig = meta(ov); mode = mode or ('loop' if o_bpm else 'free')
    x = ti.load(base); S = ti.spectrogram(x)
    bpm, first_beat, _ = ti.tempo_phase(S); key, kconf = ti.key(S)
    tonic, quality = key.split()
    if o_sig is not None and signature(tonic, quality) != o_sig:
        return {'base': os.path.basename(base), 'skipped': f'key {key} does not match overlay'}
    D = dur(base); tmp = tempfile.mkdtemp()
    if mode == 'loop':
        target = min((bpm * m for m in (0.5, 1, 2)), key=lambda b: abs(b - o_bpm))   # nearest octave
        ratio = target / o_bpm                                                         # >1 = speed up
        stretched = os.path.join(tmp, 'loop.wav')
        subprocess.run(['ffmpeg', '-v', 'quiet', '-y', '-i', ov, '-af', f'atempo={ratio:.5f}', stretched], check=True)
        layer = os.path.join(tmp, 'layer.wav')
        subprocess.run(['ffmpeg', '-v', 'quiet', '-y', '-stream_loop', '-1', '-i', stretched, '-af',
                        f'adelay={int(first_beat*1000)}:all=1,atrim=0:{D:.2f},afade=t=in:st=0:d=4,'
                        f'afade=t=out:st={max(D-6,0):.2f}:d=5', '-ar', '44100', '-ac', '2', layer], check=True)
        info = {'mode': 'loop', 'base_bpm': bpm, 'stretch': round(ratio, 3)}
    else:
        od = dur(ov); spots = [s for s in (min(20, D * .15), D * .5 - od / 2, D * .8 - od) if 0 <= s <= D - od]
        delays = '|'.join(str(int(s * 1000)) for s in spots)
        layer = os.path.join(tmp, 'layer.wav')
        n = len(spots)
        split = f'[0:a]asplit={n}' + ''.join(f'[s{i}]' for i in range(n)) + ';' if n > 1 else '[0:a]anull[s0];'
        parts = ''.join(f'[s{i}]afade=t=in:d=0.5,afade=t=out:st={max(od-2,0):.2f}:d=2,adelay={int(s*1000)}:all=1[p{i}];'
                        for i, s in enumerate(spots))
        mix = ''.join(f'[p{i}]' for i in range(n))
        subprocess.run(['ffmpeg', '-v', 'quiet', '-y', '-i', ov, '-filter_complex',
                        split + parts + f'{mix}amix=inputs={n}:duration=longest:normalize=0,apad=whole_dur={D:.2f},atrim=0:{D:.2f}',
                        '-ar', '44100', '-ac', '2', layer], check=True, timeout=300)
        info = {'mode': 'free', 'placements_s': [round(s, 1) for s in spots]}
    subprocess.run(['ffmpeg', '-v', 'quiet', '-y', '-i', base, '-i', layer, '-filter_complex',
                    f'[0:a]loudnorm=I=-20,aresample=44100,aformat=channel_layouts=stereo[a];'
                    f'[1:a]loudnorm=I=-20,volume={gain_db}dB[b];'
                    f'[a][b]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-16:TP=-1.5',
                    '-ab', '256k', out], check=True)
    return {'base': os.path.basename(base), 'overlay': os.path.basename(ov), 'key': key, 'out': out, **info}

if __name__ == '__main__':
    a = sys.argv[1:]
    print(json.dumps(main(a[0], a[1], a[2], float(a[3]) if len(a) > 3 else -12.0, a[4] if len(a) > 4 else None)))
