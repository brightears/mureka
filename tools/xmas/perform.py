"""Expressive performance layer for generated arrangements (pilot v2).

Replaces v1's white-noise humanising with structured deviations from the performance research
(reports/Making MIDI arrangements sound human.md):
  * dynamics by role + section energy + nested phrase arches (KTH phrase arch), "high loud", agogic weight
  * melody lead ~25 ms over the accompaniment (Goebl 2001) and bottom-up chord spread
  * slowly drifting (AR(1)) velocity/timing variation shared within a chord, never independent per-note jitter
  * tempo map: phrase rubato (+-2-3 %), inner-cadence easing, Friberg-Sundberg final ritardando (q=2.5)
  * syncopated sustain pedal: lift just after each harmony change, folded into note lengths
  * legato overlap clamp(0.12 x gap, 15, 100 ms); per-articulation note-on offsets for sampled strings
"""
import math, random

ROLE_BASE = {'mel': 66, 'mel2': 52, 'inner': 46, 'acc': 43, 'bass': 52, 'fill': 38, 'pad': 50, 'harp': 46,
             'bell': 50, 'drum': 0, 'keys': 58, 'lead': 70}
ROLE_ARCH = {'mel': 1.0, 'mel2': 0.9, 'inner': 0.6, 'acc': 0.55, 'bass': 0.5, 'fill': 0.5, 'pad': 0.7,
             'harp': 0.6, 'bell': 0.5, 'drum': 0.0, 'keys': 0.5, 'lead': 0.8}


def ms2b(ms, bpm):
    return ms / 1000 * bpm / 60


class Shape:
    """Dynamic plan of a piece: section energies and nested phrase spans (beats)."""

    def __init__(self, depth=7.0, contrast=1.0):
        self.sections, self.phrases, self.periods, self.depth, self.contrast = [], [], [], depth, contrast

    def section(self, s, e, energy):
        self.sections.append((s, e, energy))

    def phrase(self, s, e):
        self.phrases.append((s, e))

    def period(self, s, e):
        self.periods.append((s, e))

    def energy(self, t):
        for s, e, en in self.sections:
            if s - 1e-6 <= t < e:
                return en * self.contrast
        return 0.0

    @staticmethod
    def _pos(t, spans):
        for s, e in spans:
            if s - 1e-6 <= t < e:
                return (t - s) / (e - s)
        return None

    def arch(self, t):
        """-1..+1-ish: phrase arch peaking ~60 % through the phrase, plus a slower period arch."""
        a = 0.0
        x = self._pos(t, self.phrases)
        if x is not None:
            a += math.sin(math.pi * min(1.0, x / 1.2)) ** 1.2 - 0.45
        x = self._pos(t, self.periods)
        if x is not None:
            a += 0.6 * (math.sin(math.pi * x) - 0.5)
        return a

    def vel(self, role, t, extra=0.0):
        return ROLE_BASE[role] + self.energy(t) + ROLE_ARCH[role] * self.depth * self.arch(t) + extra


class AR1:
    """Slowly drifting noise (rho close to 1): correlated deviations listeners hear as 'alive', not 'sloppy'."""

    def __init__(self, rng, sd, rho=0.85):
        self.rng, self.sd, self.rho, self.x = rng, sd, rho, 0.0

    def __call__(self):
        self.x = self.rho * self.x + self.rng.gauss(0, self.sd * math.sqrt(1 - self.rho ** 2))
        return self.x


def tempo_map(base, total, phrases, final_beats, cadences=(), rubato=0.025, w=0.5, q=2.5, step=0.5):
    """[(beat, bpm)] with phrase rubato (slower at phrase edges, a touch faster mid-phrase), eased inner
    cadences and the Friberg-Sundberg final ritardando v(x) = [1 + (w^q - 1) x]^(1/q)."""
    ev, t = [], 0.0
    fs = total - final_beats
    while t <= total + 1e-6:
        f = 1.0
        for s, e in phrases:
            if s <= t < e:
                x = (t - s) / (e - s)
                f *= 1 + rubato * (math.sin(math.pi * x) - 0.55)
                if e - t <= 1.0:
                    f *= 1 - 0.05 * (1 - (e - t))  # breathe into the phrase end
        for c in cadences:
            if c - 2 <= t < c:
                f *= 1 - 0.07 * (1 - (c - t) / 2)
        if t >= fs and final_beats > 0:
            x = min(1.0, (t - fs) / final_beats)
            f *= (1 + (w ** q - 1) * x) ** (1 / q)
        ev.append((round(t, 4), round(base * f, 3)))
        t += step
    return ev


def bpm_at(tmap, t):
    best = tmap[0][1]
    for b, v in tmap:
        if b <= t:
            best = v
        else:
            break
    return best


def perform(song, rng, lead_ms=25, spread_ms=9, timing_sd_ms=4, vel_sd=2.2, string_offsets=None,
            legato_roles=('mel',), drums=()):
    """Apply melody lead, chord spread, correlated micro-variation and legato to song.tracks in place.
    Notes are (start, dur, pitch, vel) with a parallel 'roles' list."""
    tm = song.tempo_events or [(0, song.tempo)]
    for name, t in song.tracks.items():
        if name in drums or t['drum']:
            continue
        roles = t.get('roles') or ['acc'] * len(t['notes'])
        vn, tn = AR1(rng, vel_sd), AR1(rng, timing_sd_ms, 0.9)
        groups = {}
        for i, (s, d, p, v) in enumerate(t['notes']):
            groups.setdefault(round(s, 3), []).append(i)
        out = list(t['notes'])
        for onset, idx in sorted(groups.items()):
            bpm = bpm_at(tm, onset)
            shift = ms2b(tn(), bpm)
            acc = sorted((i for i in idx if roles[i] not in ('mel', 'mel2')), key=lambda i: t['notes'][i][2])
            for k, i in enumerate(acc):
                s, d, p, v = out[i]
                out[i] = (s + shift + ms2b(k * spread_ms, bpm), d, p, v)
            for i in idx:
                s, d, p, v = out[i]
                if roles[i] in ('mel', 'mel2'):
                    out[i] = (s + shift - ms2b(lead_ms, bpm), d, p, v)
                if string_offsets and name in string_offsets:
                    out[i] = (out[i][0] + ms2b(string_offsets[name], bpm),) + out[i][1:]
            dv = vn()
            for i in idx:
                s, d, p, v = out[i]
                out[i] = (max(0.0, s), d, p, int(max(12, min(118, round(v + dv)))))
        # legato overlap for melodic lines (monophonic per role)
        for role in legato_roles:
            line = sorted((i for i in range(len(out)) if roles[i] == role), key=lambda i: out[i][0])
            for a, b in zip(line, line[1:]):
                s, d, p, v = out[a]
                gap = out[b][0] - s
                bpm = bpm_at(tm, s)
                if 0 < gap <= d + ms2b(120, bpm):
                    ov = ms2b(max(15, min(100, 0.12 * gap / (bpm / 60) * 1000)), bpm)
                    out[a] = (s, gap + ov, p, v)
        t['notes'] = out


def pedal_bake(song, track, changes, down_ms=100, up_ms=30):
    """Syncopated pedal: down just after each change, up just after the next one. Notes ring to pedal-up."""
    t = song.tracks[track]
    tm = song.tempo_events or [(0, song.tempo)]
    changes = sorted(set(round(c, 4) for c in changes))
    spans = []
    for a, b in zip(changes, changes[1:] + [song.end + 8]):
        spans.append((a + ms2b(down_ms, bpm_at(tm, a)), b + ms2b(up_ms, bpm_at(tm, b))))
    by_pitch = {}
    for i, n in enumerate(t['notes']):
        by_pitch.setdefault(n[2], []).append(i)
    out = list(t['notes'])
    for p, idx in by_pitch.items():
        idx.sort(key=lambda i: out[i][0])
        for k, i in enumerate(idx):
            s, d, _, v = out[i]
            end = s + d
            for a, b in spans:
                if a <= end < b:  # key released while the pedal is down: rings until the pedal lifts
                    end = b
                    break
            if k + 1 < len(idx):
                end = min(end, out[idx[k + 1]][0] - 0.005)
            out[i] = (s, max(0.05, end - s), p, v)
    t['notes'] = out
