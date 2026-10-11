"""Spa-ambient clean pipeline, single pass: HPSS transient-strip + background-chord
extraction + loudness normalize + tagging. FLAC in -> tagged MP3 or FLAC out
(codec chosen by the output extension; .flac = lossless cleaned master).
Usage: clean_track.py <in.flac> <out.mp3|out.flac> <title> <album> [artist]"""
import subprocess, sys, tempfile, os
import numpy as np

IN, OUT, TITLE, ALBUM = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
ARTIST = sys.argv[5] if len(sys.argv) > 5 else 'BMAsia'
SR = 44100
WIN, HOP = 4096, 1024
K_T, K_F = 31, 31          # HPSS median kernels
HPSS_POWER = 2.0
BG_WIN_S = 8.0             # background estimate window (s)
BG_POWER = 2.0
fps = SR / HOP

raw = subprocess.run(['ffmpeg', '-v', 'quiet', '-i', IN, '-f', 'f32le', '-ac', '2',
                      '-ar', str(SR), '-'], capture_output=True).stdout
x = np.frombuffer(raw, dtype=np.float32).reshape(-1, 2).T.copy()
n = x.shape[1]
window = np.hanning(WIN).astype(np.float32)

def stft(sig):
    nf = 1 + (len(sig) - WIN) // HOP
    frames = np.lib.stride_tricks.as_strided(
        sig, (nf, WIN), (sig.strides[0] * HOP, sig.strides[0]))
    return np.fft.rfft(frames * window, axis=1)

def istft(S, length):
    frames = np.fft.irfft(S, n=WIN, axis=1).astype(np.float32) * window
    out = np.zeros(length, dtype=np.float32)
    norm = np.zeros(length, dtype=np.float32)
    w2 = (window ** 2).astype(np.float32)
    for i in range(S.shape[0]):
        s = i * HOP
        out[s:s + WIN] += frames[i]
        norm[s:s + WIN] += w2
    norm[norm < 1e-8] = 1e-8
    return out / norm

def med_along(a, k, axis):
    pad = k // 2
    a = np.moveaxis(a, axis, -1)
    ap = np.pad(a, [(0, 0)] * (a.ndim - 1) + [(pad, pad)], mode='reflect')
    res = np.empty(a.shape, dtype=np.float32)
    step = 256
    for s in range(0, a.shape[0], step):
        wins = np.lib.stride_tricks.sliding_window_view(ap[s:s + step], k, axis=-1)
        res[s:s + step] = np.median(wins, axis=-1)
    return np.moveaxis(res, -1, axis)

def background(mag):
    nf, nb = mag.shape
    half = int(BG_WIN_S * fps / 2)
    step, sub = 8, 4
    centers = np.arange(0, nf, step)
    offs = np.arange(-half, half + 1, sub)
    idx = np.clip(centers[:, None] + offs[None, :], 0, nf - 1)
    B = np.empty((nf, nb), dtype=np.float32)
    for b0 in range(0, nb, 128):
        g = mag[idx, b0:b0 + 128]
        Bc = np.median(g, axis=1)
        for j in range(Bc.shape[1]):
            B[:, b0 + j] = np.interp(np.arange(nf), centers, Bc[:, j])
    return B

chans = []
for ch in range(2):
    S = stft(x[ch])
    mag = np.abs(S).astype(np.float32)
    # pass 1: transient (drum) suppression
    H = med_along(mag, K_T, axis=0)
    P = med_along(mag, K_F, axis=1)
    m1 = H ** HPSS_POWER / (H ** HPSS_POWER + P ** HPSS_POWER + 1e-12)
    mag2 = mag * m1
    # pass 2: foreground-melody suppression on the de-drummed magnitude
    B = background(mag2)
    F = np.maximum(mag2 - B, 0.0)
    m2 = B ** BG_POWER / (B ** BG_POWER + F ** BG_POWER + 1e-12)
    chans.append(istft(S * (m1 * m2), n))

y = np.stack(chans, axis=1).astype(np.float32)
peak = float(np.max(np.abs(y))) or 1.0
if peak > 0.99:
    y *= 0.99 / peak

with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as t:
    tmp = t.name
subprocess.run(['ffmpeg', '-v', 'quiet', '-y', '-f', 'f32le', '-ac', '2', '-ar', str(SR),
                '-i', '-', tmp], input=y.tobytes())
codec = ['-acodec', 'flac'] if OUT.lower().endswith('.flac') else ['-acodec', 'libmp3lame', '-ab', '256k']
# Micro-fades: generations can start/end at non-zero amplitude -> audible click
# at track boundaries (heard on the Beat Breeze sample page, 2026-08-20).
dur = n / SR
subprocess.run(['ffmpeg', '-v', 'quiet', '-y', '-i', tmp,
                '-af', 'loudnorm=I=-17.5:TP=-1.5:LRA=11,'
                       f'afade=t=in:st=0:d=0.05,afade=t=out:st={max(dur - 0.8, 0):.2f}:d=0.8',
                '-metadata', f'title={TITLE}', '-metadata', f'artist={ARTIST}',
                '-metadata', f'album={ALBUM}', '-metadata', 'genre=Ambient',
                '-metadata', 'date=2026',
                '-ar', str(SR)] + codec + [OUT])
os.unlink(tmp)
print(f'cleaned: {os.path.basename(OUT)}')
