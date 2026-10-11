"""Per-track musical metadata for overlay mixing (and later: Beat Breeze transitions).
tempo (BPM, octave-resolved into a musical range), beat phase (seconds to first beat), key (major/minor,
Krumhansl-Schmuckler on a chroma profile), confidence values. Pure numpy + ffmpeg, free, local.
Usage: trackinfo.py <audio> [...]  -> prints one JSON line per file"""
import json, subprocess, sys, numpy as np

SR, HOP, WIN = 22050, 512, 2048
MAJ = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
MIN = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
NAMES = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']

def load(path):
    raw = subprocess.run(['ffmpeg', '-v', 'quiet', '-i', path, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'],
                         capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32)

def spectrogram(x):
    n = 1 + (len(x) - WIN) // HOP
    fr = np.lib.stride_tricks.as_strided(x, (n, WIN), (x.strides[0] * HOP, x.strides[0]))
    return np.abs(np.fft.rfft(fr * np.hanning(WIN), axis=1))

def tempo_phase(S, lo=60, hi=150):
    flux = np.maximum(np.diff(np.log1p(S), axis=0), 0).sum(axis=1)
    flux = (flux - flux.mean()) / (flux.std() + 1e-9)
    fps = SR / HOP
    ac = np.correlate(flux, flux, 'full')[len(flux) - 1:]; ac /= ac[0]
    lags = np.arange(int(fps * 60 / 200), int(fps * 60 / 40))
    best = lags[np.argmax(ac[lags])]; bpm = 60 * fps / best
    while bpm < lo: bpm *= 2
    while bpm > hi: bpm /= 2
    period = fps * 60 / bpm
    offs = np.arange(int(period))
    score = [flux[np.minimum(np.arange(o, len(flux), period).astype(int), len(flux) - 1)].sum() for o in offs]
    return round(bpm, 1), round(float(offs[int(np.argmax(score))]) / fps, 3), round(float(ac[best]), 2)

def key(S):
    freqs = np.fft.rfftfreq(WIN, 1 / SR); m = (freqs > 55) & (freqs < 2000)
    pc = np.round(12 * np.log2(freqs[m] / 440.0) + 9).astype(int) % 12   # 0 = C
    chroma = np.zeros(12); np.add.at(chroma, pc, S[:, m].sum(axis=0))
    best = max(((np.corrcoef(np.roll(prof, k), chroma)[0, 1], k, q) for q, prof in (('major', MAJ), ('minor', MIN))
                for k in range(12)))
    return f'{NAMES[best[1]]} {best[2]}', round(float(best[0]), 2)

if __name__ == '__main__':
    for p in sys.argv[1:]:
        x = load(p); S = spectrogram(x)
        bpm, phase, tconf = tempo_phase(S); k, kconf = key(S)
        print(json.dumps({'file': p.split('/')[-1], 'bpm': bpm, 'first_beat_s': phase, 'tempo_conf': tconf,
                          'key': k, 'key_conf': kconf, 'duration_s': round(len(x) / SR, 1)}), flush=True)
