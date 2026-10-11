"""Boundary-click detector: counts adjacent-sample jumps > THRESH (implausible in music
without transients at track edges). Clean batch = 0. Usage: clickscan.py '<glob>'"""
import glob, subprocess, sys, numpy as np
THRESH = 0.25
files = sorted(glob.glob(sys.argv[1])); total = 0; worst = []
for p in files:
    raw = subprocess.run(['ffmpeg','-v','quiet','-i',p,'-f','f32le','-ac','1','-ar','44100','-'], capture_output=True).stdout
    x = np.frombuffer(raw, np.float32)
    if len(x) < 44100: continue
    # first/last 100 ms only, each edge diffed SEPARATELY (concatenating them faked a jump at the
    # junction whenever a track is already loud 0.1 s in — false positive found 2026-10-11)
    n = int(sum((np.abs(np.diff(seg)) > THRESH).sum() for seg in (x[:4410], x[-4410:])))
    total += n; worst.append((n, p.split('/')[-1]))
worst.sort(reverse=True)
print(f'files: {len(files)} | boundary-click jumps: {total}' + (f' | worst: {worst[0]}' if worst and worst[0][0] else ''))
