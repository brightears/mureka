#!/usr/bin/env python3
"""Approach B overlay library: Christmas parts to mix softly into Mureka base tracks.

Writes MIDI only (instrument-agnostic). Render each file in Ableton with REAL instruments (Festive Bells,
LABS Christmas, Orchestral Mallets) and export WAV 44.1 kHz under the same name. Never render these with the
GM preview synth, and never upload LABS/Fracture renders to Mureka or any AI service.

Spec from the Mureka session (Round 6 overlay bases, 2026-10-10):
  keys   C major (= A minor) and F major (= D minor) only
  synced loops for Lounge (~80 BPM, time-stretched per track) and Jazz (64 BPM); BPM in the filename
  free-time overlays (no grid, natural decay) for Classical and Acoustic
Melodies come from carols.py (score-checked, public domain).
Usage: python3 tools/xmas/overlays.py [out_dir]
"""
import os, random, sys
from carols import TUNES
from arrange import Song, SLEIGH, key_shift

OUT = os.path.expanduser('~/Downloads/Christmas Ableton/overlays/midi')
KEYS = {'Cmaj': 'C', 'Fmaj': 'F'}
MINOR_OF = {'Cmaj': 'Am', 'Fmaj': 'Dm'}


def phrase(tune_name, from_bar, to_bar, key, include_pickup=True, trim=0.0):
    t = TUNES[tune_name]
    t = t.transposed(key_shift(t, key))
    bl = float(t.bar_len)
    s0, e0 = (from_bar - 1) * bl, to_bar * bl
    lead = float(t.pickup) if include_pickup else 0.0
    notes = [(p, float(s) - s0 + lead, float(d)) for p, s, d in t.melody if s0 - lead - 1e-9 <= float(s) < e0 - trim - 1e-9]
    return notes, bl, (e0 - s0) + lead


def octave_to(notes, target):
    mean = sum(p for p, _, _ in notes) / len(notes)
    k = 12 * round((target - mean) / 12)
    return [(p + k, s, d) for p, s, d in notes]


def write(name, tempo, bar_len, key, tracks):
    song = Song(name, tempo, bar_len, key)
    for trk, drum, notes in tracks:
        song.track(trk, 9 if not drum else 0, drum=drum)
        for s, d, p, v in notes:
            song.n(trk, s, d, p, v)
    song.write(os.path.join(OUT, name + '.mid'))
    return name


def sleighbells(bpm, sparse, rng):
    notes = []
    for bar in range(8):
        for e in range(8):
            t = bar * 4 + e * 0.5
            if sparse and e not in (2, 6):
                continue
            accent = e % 2 == 0
            v = (60 if bar % 4 == 0 and e == 0 else 48 if accent else 32) + rng.gauss(0, 3)
            notes.append((t + (0.02 if not accent else 0), 0.4, SLEIGH, v))
    return write(f"sleighbells{'_sparse' if sparse else ''}_{bpm}bpm", bpm, 4, 'C', [('Sleigh Bells', True, notes)])


def synced(motif, tune, bars, key_label, bpm, instr, target, rng, minor=False):
    key = MINOR_OF[key_label] if minor else KEYS[key_label]
    notes, bl, length = phrase(tune, bars[0], bars[1], key)
    notes = octave_to(notes, target)
    ev = [(s, d * 0.9, p, 62 + rng.gauss(0, 3) - (6 if i % 2 else 0)) for i, (p, s, d) in enumerate(notes)]
    label = key.replace('m', 'min') if minor else key_label
    return write(f'{motif}_{instr}_{bpm}bpm_{label}', bpm, bl, key, [(instr, False, ev)])


def free(motif, tune, bars, key_label, instr, target, rng, minor=False, rubato=0.06, slow=1.25, ring=6.0, trim=0.0):
    """Free time: written at 60 BPM so one beat = one second; gentle rubato, phrase-end broadening, long ring."""
    key = MINOR_OF[key_label] if minor else KEYS[key_label]
    notes, bl, length = phrase(tune, bars[0], bars[1], key, trim=trim)
    notes = octave_to(notes, target)
    ev, t_prev, warp = [], 0.0, 0.0
    for i, (p, s, d) in enumerate(notes):
        broaden = 1.0 + (0.35 if i >= len(notes) - 2 else 0.0)
        warp += rng.gauss(0, rubato)
        t = max(t_prev, s * slow * broaden + warp)
        ev.append((t, d * slow + (ring if i == len(notes) - 1 else 1.0), p, 58 + rng.gauss(0, 4)))
        t_prev = t + 0.05
    label = key.replace('m', 'min') if minor else key_label
    return write(f'{motif}_{instr}_free_{label}', 60, 4, key, [(instr, False, ev)])


def chimes(key_label, rng):
    """Tubular-bell accents: three spaced strikes (tonic, fifth, octave) with long natural decay."""
    root = 60 + {'Cmaj': 0, 'Fmaj': 5}[key_label]
    ev = [(0.0, 8, root, 56), (4.5, 8, root + 7, 50), (9.0, 10, root + 12, 54)]
    return write(f'chimes_tubular_free_{key_label}', 60, 4, KEYS[key_label], [('Tubular Bells', False, ev)])


def bellswell(key_label, rng):
    """Soft glockenspiel/celesta sparkle: rising tonic arpeggio, ringing out (transition / phrase-end accent)."""
    root = 84 + {'Cmaj': 0, 'Fmaj': 5}[key_label] - (12 if key_label == 'Fmaj' else 0)
    ivs = [0, 4, 7, 12, 16, 19, 24]
    ev = [(i * 0.18 + abs(rng.gauss(0, 0.01)), 6 - i * 0.18, root + iv, 40 + i * 3) for i, iv in enumerate(ivs)]
    return write(f'bellswell_glock_free_{key_label}', 60, 4, KEYS[key_label], [('Glockenspiel', False, ev)])


if __name__ == '__main__':
    if len(sys.argv) > 1:
        OUT = sys.argv[1]
    os.makedirs(OUT, exist_ok=True)
    rng = random.Random('overlays')
    made = []
    for bpm in (64, 80):
        made += [sleighbells(bpm, False, rng), sleighbells(bpm, True, rng)]
    for k in KEYS:
        for bpm in (64, 80):
            made.append(synced('jinglebells', 'jingle-bells', (1, 4), k, bpm, 'glock', 84, rng))
            made.append(synced('hark', 'hark-the-herald', (1, 4), k, bpm, 'glock', 84, rng))
            made.append(synced('ocome', 'o-come-all-ye-faithful', (13, 20), k, bpm, 'handbells', 74, rng))
            made.append(synced('carolbells', 'carol-of-the-bells', (1, 4), k, bpm, 'handbells', 74, rng, minor=True))
        made.append(free('silentnight', 'silent-night', (1, 8), k, 'handbells', 74, rng))
        made.append(free('silentnight', 'silent-night', (1, 8), k, 'celesta', 84, rng))
        made.append(free('joy', 'joy-to-the-world', (1, 4), k, 'glock', 84, rng, trim=0.5))
        made.append(free('carolbells', 'carol-of-the-bells', (1, 2), k, 'handbells', 74, rng, minor=True, slow=1.4))
        made.append(chimes(k, rng))
        made.append(bellswell(k, rng))
    print(len(made), 'overlay MIDI files ->', OUT)
    for m in made:
        print(' ', m)
