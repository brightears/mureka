"""Harmonic/percussive separation (median-filter HPSS, Fitzgerald 2010) in pure numpy.
Keeps the harmonic (sustained) component — strips drum hits from pad/ambient material.
Usage: hpss.py <in.mp3> <out.mp3>"""
import subprocess, sys
import numpy as np

IN, OUT = sys.argv[1], sys.argv[2]
SR = 44100
WIN, HOP = 4096, 1024
K_T, K_F = 31, 31          # median kernels: frames (~0.72s), freq bins (~330 Hz)
POWER = 2.0                # soft (Wiener) mask exponent

raw = subprocess.run(['ffmpeg', '-v', 'quiet', '-i', IN, '-f', 'f32le', '-ac', '2',
                      '-ar', str(SR), '-'], capture_output=True).stdout
x = np.frombuffer(raw, dtype=np.float32).reshape(-1, 2).T.copy()   # (2, n)
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
    """Median filter along one axis (reflect padding), slab-wise to bound memory."""
    pad = k // 2
    a = np.moveaxis(a, axis, -1)
    ap = np.pad(a, [(0, 0)] * (a.ndim - 1) + [(pad, pad)], mode='reflect')
    outshape = a.shape
    res = np.empty(outshape, dtype=np.float32)
    step = 256
    for start in range(0, outshape[0], step):
        sl = ap[start:start + step]
        wins = np.lib.stride_tricks.sliding_window_view(sl, k, axis=-1)
        res[start:start + step] = np.median(wins, axis=-1)
    return np.moveaxis(res, -1, axis)

chans = []
for ch in range(2):
    S = stft(x[ch])
    mag = np.abs(S).astype(np.float32)
    H = med_along(mag, K_T, axis=0)    # median across time  -> harmonic estimate
    P = med_along(mag, K_F, axis=1)    # median across freq  -> percussive estimate
    Hp, Pp = H ** POWER, P ** POWER
    mask = Hp / (Hp + Pp + 1e-12)
    chans.append(istft(S * mask, n))

y = np.stack(chans, axis=1).astype(np.float32)   # (n, 2) interleave on tobytes
peak = np.max(np.abs(y)) or 1.0
if peak > 0.99:
    y *= 0.99 / peak
enc = subprocess.run(['ffmpeg', '-v', 'quiet', '-y', '-f', 'f32le', '-ac', '2',
                      '-ar', str(SR), '-i', '-', '-acodec', 'libmp3lame', '-ab', '256k', OUT],
                     input=y.tobytes())
print(f'wrote {OUT} (peak {peak:.2f})')
