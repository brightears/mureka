#!/usr/bin/env python3
"""Write the pilot-v2 Ableton sets for Norbert's blind A/B tests (renders are exported from Live afterwards).

Blind naming: each experiment's versions are lettered (A, B, C) in a shuffled order; KEY.txt (kept out of the
listening folders) says which is which.
Usage: python3 tools/xmas/v2_render.py
"""
import json, os, random
import v2
from als import write_set, PARTS

OUT = os.path.expanduser(os.environ.get('XMAS_OUT', '~/Downloads/Christmas Ableton/v3'))

PARTS.update({
    'Quartet Violin 1': ('Long Normale - String Quartet', -1, -11, 5, None, {2: 28}),
    'Quartet Violin 2': ('Long Flautando - String Quartet', -4, -11, 6, None, {2: 28}),
    'Quartet Viola': ('Long Flautando - String Quartet', -4, -11, 7, None, {2: 28}),
    'Quartet Cello': ('Long Normale - String Quartet', -3, -11, 8, None, {2: 28}),
    'Quartet Ensemble': ('Long Normale - String Quartet', -4, -11, 7, None, {2: 28}),
})

PT_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pianist_transformer', 'sn_v2_pt.json')


def pianist_transformer_song(path=PT_JSON):
    """Pianist Transformer output (absolute seconds) as a Song at a fixed 120 BPM (1 beat = 0.5 s), pedal folded in."""
    from als import bake_pedal
    d = json.load(open(path))
    song = v2.Song2('Silent Night - romantic piano (Pianist Transformer)', 120, 3, 'C')
    P = song.track('Piano', 0)
    notes = [(s * 2, du * 2, p, v) for s, du, p, v in d['notes']]
    notes = bake_pedal(notes, [(t * 2, num, val) for t, num, val in d['cc']])
    for s, du, p, v in notes:
        song.n(P, s, du, p, v, 'mel')
    return song


EXPERIMENTS = {
    # round 3 (after Norbert's v2 feedback: more life/tempo/dynamics, real strings, softer bells)
    'E4 Silent Night piano - livelier': [('84 BPM', lambda: v2.silent_night_piano(tempo=84)),
                                        ('92 BPM', lambda: v2.silent_night_piano(tempo=92))],
    'E5 Away in a Manger - String Quartet': [('Spitfire String Quartet + hand bells', lambda: v2.away_strings('ssq', tempo=76))],
    'L1v3 Jingle Bells chillhop': [('v3: vibraphone, softer sleigh bells', lambda: v2.jingle_lounge(tempo=90))],
}
REVERB = {'E1': (2200, 12), 'E2': (2200, 12), 'E3': (2800, 16), 'E4': (2200, 12), 'E5': (2800, 16), 'L1': (1600, 10)}


def main(only=None):
    rng = random.Random(20261010)
    key = {}
    for exp, versions in EXPERIMENTS.items():
        if only and not exp.startswith(only):
            continue
        letters = list('ABC'[:len(versions)])
        if len(versions) > 1:
            rng.shuffle(letters)
        for (label, make), letter in zip(versions, letters):
            song = make()
            name = f'{exp} - version {letter}' if len(versions) > 1 else exp
            out = os.path.join(OUT, exp, name + '.als')
            write_set(song, out, reverb=REVERB[exp.split()[0][:2]])
            key[name] = label
            print(f'{name:58} <- {label:26} {song.end:6.1f} beats')
    path = os.path.join(OUT, 'KEY (open after listening).json')
    old = json.load(open(path)) if os.path.exists(path) else {}
    old.update(key)
    json.dump(old, open(path, 'w'), indent=1)


if __name__ == '__main__':
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else None)
