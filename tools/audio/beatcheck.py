"""Beat/periodicity detector: spectral-flux onset envelope -> autocorrelation.
Prints periodicity strength (0-1) and implied BPM. Pure numpy."""
import subprocess, sys, numpy as np

def load(path, off, dur=30, sr=22050):
    raw = subprocess.run(['ffmpeg','-v','quiet','-ss',str(off),'-t',str(dur),'-i',path,
        '-ac','1','-ar',str(sr),'-f','f32le','-'], capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32), sr

def beat_strength(x, sr):
    hop, win = 512, 1024
    n = (len(x)-win)//hop
    frames = np.lib.stride_tricks.as_strided(x, (n, win), (x.strides[0]*hop, x.strides[0]))
    mag = np.abs(np.fft.rfft(frames*np.hanning(win), axis=1))
    flux = np.maximum(mag[1:]-mag[:-1], 0).sum(axis=1)
    flux = (flux-flux.mean())/ (flux.std()+1e-9)
    ac = np.correlate(flux, flux, 'full')[len(flux)-1:]
    ac /= (ac[0]+1e-9)
    fps = sr/hop
    lo, hi = int(fps*60/200), int(fps*60/40)   # 40-200 BPM lag range
    seg = ac[lo:hi]
    peak = int(np.argmax(seg))+lo
    return float(seg.max()), 60.0/(peak/fps)

for path, off in [(sys.argv[i], sys.argv[i+1]) for i in range(1, len(sys.argv), 2)]:
    x, sr = load(path, off)
    if len(x) < sr*5: print(f'{path}: too short'); continue
    s, bpm = beat_strength(x, sr)
    verdict = 'STRONG BEAT' if s > 0.35 else ('weak pulse' if s > 0.18 else 'no beat')
    print(f'{verdict:12s} strength={s:.2f} ~{bpm:5.1f} BPM  {path.split("/")[-1]}')
