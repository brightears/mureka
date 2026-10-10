"""Public-domain carol melodies -> MIDI (for Mureka melody_id uploads) and a simple rendered
audio (for track/generate). Only PUBLIC-DOMAIN tunes belong here (e.g. Silent Night 1818,
Jingle Bells 1857). Notes: (midi_pitch, duration_in_units); unit seconds set per tune.
Usage: python3 tools/melody.py <out_dir> [piano|musicbox] [repeats]   (needs numpy)"""
import struct, sys, os, subprocess, math, wave, array

C4,D4,E4,F4,G4,A4,B4,C5,D5,E5,F5 = 60,62,64,65,67,69,71,72,74,76,77
TUNES = {
 # 6/8, unit = eighth note
 'silent-night': (0.36, [
  (G4,3),(A4,1),(G4,2),(E4,6), (G4,3),(A4,1),(G4,2),(E4,6),
  (D5,4),(D5,2),(B4,6), (C5,4),(C5,2),(G4,6),
  (A4,4),(A4,2),(C5,3),(B4,1),(A4,2), (G4,3),(A4,1),(G4,2),(E4,6),
  (A4,4),(A4,2),(C5,3),(B4,1),(A4,2), (G4,3),(A4,1),(G4,2),(E4,6),
  (D5,4),(D5,2),(F5,3),(D5,1),(B4,2), (C5,6),(E5,6),
  (C5,3),(G4,1),(E4,2),(G4,3),(F4,1),(D4,2),(C4,12)]),
 # 4/4 chorus, unit = eighth note
 'jingle-bells': (0.25, [
  (E4,2),(E4,2),(E4,4), (E4,2),(E4,2),(E4,4), (E4,2),(G4,2),(C4,3),(D4,1),(E4,8),
  (F4,2),(F4,2),(F4,3),(F4,1), (F4,2),(E4,2),(E4,2),(E4,1),(E4,1), (E4,2),(D4,2),(D4,2),(E4,2),(D4,4),(G4,4),
  (E4,2),(E4,2),(E4,4), (E4,2),(E4,2),(E4,4), (E4,2),(G4,2),(C4,3),(D4,1),(E4,8),
  (F4,2),(F4,2),(F4,3),(F4,1), (F4,2),(E4,2),(E4,2),(E4,1),(E4,1), (G4,2),(G4,2),(F4,2),(D4,2),(C4,8)]),
}

def vlq(n):
    b = [n & 0x7F]; n >>= 7
    while n: b.insert(0, (n & 0x7F) | 0x80); n >>= 7
    return bytes(b)

def write_midi(path, unit_s, notes, tpq=480):
    # unit = eighth note -> quarter = 2 units; tempo from unit length
    us_per_q = int(unit_s * 2 * 1e6); ticks = tpq // 2
    ev = b'\x00\xff\x51\x03' + us_per_q.to_bytes(3, 'big') + b'\x00\xc0\x00'
    gap = 0
    for p, d in notes:
        ev += vlq(gap) + bytes([0x90, p, 90]) + vlq(d * ticks - 10) + bytes([0x80, p, 0]); gap = 10
    ev += vlq(gap) + b'\xff\x2f\x00'
    open(path, 'wb').write(b'MThd' + struct.pack('>IHHH', 6, 0, 1, tpq) + b'MTrk' + struct.pack('>I', len(ev)) + ev)

def render(path_wav, unit_s, notes, sr=44100, timbre='piano', repeats=1, transpose=0):
    """timbre 'piano' = soft harmonic tone; 'musicbox' = struck metal (celesta / music box), inharmonic
    partials with fast-decaying overtones. Each note starts on its grid position and rings on naturally.
    repeats = play the tune N times with a short breath between passes (full-length track input)."""
    import numpy as np
    PART = {'piano': ((1, 1, 2.2), (2, .35, 2.2), (3, .12, 2.2)),
            'musicbox': ((1, 1, 1.1), (2.76, .45, 3.5), (5.40, .18, 6.0), (8.93, .08, 9.0))}[timbre]
    seq = (list(notes) + [(None, 4)]) * repeats
    total = sum(d for _, d in seq) * unit_s
    tail = 2.5 if timbre == 'musicbox' else 0.5
    y = np.zeros(int((total + tail) * sr), dtype=np.float64)
    pos = 0.0
    for p, d in seq:
        if p is not None:
            f = 440 * 2 ** ((p + transpose - 69) / 12)
            ring = d * unit_s + (1.8 if timbre == 'musicbox' else 0.0)
            t = np.arange(int(ring * sr)) / sr
            tone = sum(a * np.exp(-dec * t) * np.sin(2 * np.pi * f * h * t) for h, a, dec in PART)
            tone *= np.minimum(1, t / 0.004)
            if timbre == 'piano':  # piano-ish: stop at note end with a short release
                tone *= np.clip((ring - t) / 0.05, 0, 1)
            i0 = int(pos * sr); y[i0:i0 + len(tone)] += tone[:len(y) - i0]
        pos += d * unit_s
    y *= 0.8 / max(1e-9, np.max(np.abs(y)))
    w = wave.open(path_wav, 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
    w.writeframes((y * 32767).astype('<i2').tobytes()); w.close()

if __name__ == '__main__':
    od = sys.argv[1]; os.makedirs(od, exist_ok=True)
    timbre = sys.argv[2] if len(sys.argv) > 2 else 'piano'; reps = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    sfx = '' if timbre == 'piano' and reps == 1 else f'-{timbre}-x{reps}'
    for name, (u, notes) in TUNES.items():
        write_midi(f'{od}/{name}.mid', u, notes)
        render(f'{od}/{name}{sfx}.wav', u, notes, timbre=timbre, repeats=reps)
        # soft room reverb so the melody sits in a space instead of sounding dry/synthetic
        subprocess.run(['ffmpeg', '-v', 'quiet', '-y', '-i', f'{od}/{name}{sfx}.wav', '-af',
                        'aecho=0.8:0.7:60|110|170:0.35|0.25|0.18', '-ab', '192k', f'{od}/{name}{sfx}.mp3'])
        os.remove(f'{od}/{name}{sfx}.wav')
        print(name, sfx, f'{(sum(d for _, d in notes) + 4) * u * reps:.1f}s')
