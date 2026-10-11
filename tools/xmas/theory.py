"""Small music-theory helpers: note names, chord symbols, voicings."""
import re

NOTE_PC = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
ACC = {'#': 1, 'b': -1}

QUAL = {
    '': (0, 4, 7), 'm': (0, 3, 7), '7': (0, 4, 7, 10), 'maj7': (0, 4, 7, 11), 'm7': (0, 3, 7, 10),
    '6': (0, 4, 7, 9), 'm6': (0, 3, 7, 9), '9': (0, 4, 7, 10, 14), 'maj9': (0, 4, 7, 11, 14),
    'm9': (0, 3, 7, 10, 14), 'add9': (0, 4, 7, 14), '6/9': (0, 4, 7, 9, 14), '13': (0, 4, 7, 10, 14, 21),
    '7b9': (0, 4, 7, 10, 13), '7b13': (0, 4, 7, 10, 20), 'sus4': (0, 5, 7), 'sus2': (0, 2, 7),
    '7sus4': (0, 5, 7, 10), '9sus4': (0, 5, 7, 10, 14), 'dim': (0, 3, 6), 'm7b5': (0, 3, 6, 10), 'madd9': (0, 3, 7, 14),
}


def pc(name):
    v = NOTE_PC[name[0]]
    for ch in name[1:]:
        v += ACC[ch]
    return v % 12


def midi(name):
    m = re.fullmatch(r'([A-G])([#b]*)(-?\d)', name)
    if not m:
        raise ValueError(f'bad note {name!r}')
    return 12 * (int(m.group(3)) + 1) + NOTE_PC[m.group(1)] + sum(ACC[c] for c in m.group(2))


class Chord:
    def __init__(self, root, qual, bass=None):
        if qual not in QUAL:
            raise ValueError(f'unknown chord quality {qual!r}')
        self.root, self.qual = root % 12, qual
        self.bass = self.root if bass is None else bass % 12

    @property
    def ivs(self):
        return QUAL[self.qual]

    @property
    def minor(self):
        return 3 in self.ivs and 4 not in self.ivs

    @property
    def third(self):
        return (self.root + (3 if self.minor else 4)) % 12 if (3 in self.ivs or 4 in self.ivs) else None

    def pcs(self):
        return [(self.root + i) % 12 for i in self.ivs]

    def with_qual(self, qual):
        return Chord(self.root, qual, self.bass)

    def transposed(self, t):
        return Chord(self.root + t, self.qual, self.bass + t)

    def __repr__(self):
        names = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']
        s = names[self.root] + self.qual
        return s + ('/' + names[self.bass] if self.bass != self.root else '')


def parse_chord(sym):
    m = re.fullmatch(r'([A-G][#b]?)([^/]*(?:/9)?)(?:/([A-G][#b]?))?', sym)
    if not m:
        raise ValueError(f'bad chord {sym!r}')
    return Chord(pc(m.group(1)), m.group(2), pc(m.group(3)) if m.group(3) else None)


def nearest(pcl, lo, hi, near):
    """Pitch with pitch class pcl inside [lo, hi] closest to `near` (None if the range has none)."""
    c = [p for p in range(lo, hi + 1) if p % 12 == pcl % 12]
    return min(c, key=lambda p: (abs(p - near), p)) if c else None


def voicing(pcs, lo, hi, prev=None):
    """Close-position voicing of the given pitch classes inside [lo, hi], voice-led from `prev`."""
    pcs = list(dict.fromkeys(p % 12 for p in pcs))
    best, best_cost = None, 1e9
    centre = (lo + hi) / 2
    for b in pcs:
        for start in range(lo, lo + 12):
            if start % 12 != b:
                continue
            rest = sorted((q - b) % 12 for q in pcs if q != b)
            v = [start] + [start + r for r in rest]
            if v[-1] > hi:
                continue
            if prev:
                ps = sorted(prev)
                if len(ps) == len(v):
                    cost = sum(abs(a - c) for a, c in zip(v, ps))
                else:
                    cost = abs(sum(v) / len(v) - sum(ps) / len(ps)) * len(v)
            else:
                cost = abs(sum(v) / len(v) - centre)
            if cost < best_cost:
                best, best_cost = v, cost
    if best is None:  # range too narrow: drop the last pitch class and retry
        return voicing(pcs[:-1], lo, hi, prev) if len(pcs) > 1 else [nearest(pcs[0], lo - 12, hi, centre)]
    return best
