"""Background-chord extractor: keeps only quasi-stationary spectral content
(pad chords held for seconds), suppresses foreground melody notes (0.5-2s events).
Per-bin long-window temporal median as background estimate, Wiener-style mask.
Usage: padonly.py <in.mp3> <out.mp3>"""
import subprocess, sys
import numpy as np

IN, OUT = sys.argv[1], sys.argv[2]
SR = 44100
WIN, HOP = 4096, 1024
BG_WIN_S = 8.0        # background = median over +-4s
POWER = 2.0

raw = subprocess.run(['ffmpeg', '-v', 'quiet', '-i', IN, '-f', 'f32le', '-ac', '2',
                      '-ar', str(SR), '-'], capture_output=True).stdout
x = np.frombuffer(raw, dtype=np.float32).reshape(-1, 2).T.copy()
n = x.shape[1]
window = np.hanning(WIN).astype(np.float32)
fps = SR / HOP

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

def background(mag):
    """Per-bin temporal median over a long window, decimated + interpolated."""
    nf, nb = mag.shape
    half = int(BG_WIN_S * fps / 2)
    step, sub = 8, 4                      # centers every 8 frames; subsample window by 4
    centers = np.arange(0, nf, step)
    offs = np.arange(-half, half + 1, sub)
    idx = np.clip(centers[:, None] + offs[None, :], 0, nf - 1)   # (nc, nw)
    B = np.empty((nf, nb), dtype=np.float32)
    slab = 128
    for b0 in range(0, nb, slab):
        gathered = mag[idx, b0:b0 + slab]                        # (nc, nw, slab)
        Bc = np.median(gathered, axis=1)                         # (nc, slab)
        for j in range(Bc.shape[1]):
            B[:, b0 + j] = np.interp(np.arange(nf), centers, Bc[:, j])
    return B

chans = []
for ch in range(2):
    S = stft(x[ch])
    mag = np.abs(S).astype(np.float32)
    B = background(mag)
    F = np.maximum(mag - B, 0.0)
    Bp, Fp = B ** POWER, F ** POWER
    mask = Bp / (Bp + Fp + 1e-12)
    chans.append(istft(S * mask, n))

y = np.stack(chans, axis=1).astype(np.float32)
peak = float(np.max(np.abs(y))) or 1.0
if peak > 0.99:
    y *= 0.99 / peak
subprocess.run(['ffmpeg', '-v', 'quiet', '-y', '-f', 'f32le', '-ac', '2',
                '-ar', str(SR), '-i', '-', '-acodec', 'libmp3lame', '-ab', '256k', OUT],
               input=y.tobytes())
print(f'wrote {OUT} (peak {peak:.2f})')
