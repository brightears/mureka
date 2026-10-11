#!/usr/bin/env python3
"""Pilot v2: hand-planned arrangements built from reusable arranging blocks + the perform.py performance layer.

v1 (arrange.py) stacked a rule-based accompaniment under the melody and repeated it; Norbert judged it
"too simple / like a beginner". v2 follows the research report: a form with intro -> sparse pass -> interlude
-> modulated, reharmonised fuller pass -> lighter half pass -> deceptive tag; a different texture in every
pass; fills in held notes; two-level reharmonisation checked against the melody; structured performance.

Usage: python3 tools/xmas/v2.py <piece> [tempo]    pieces: silent-night-piano, away-strings-os,
                                                       away-strings-ssq, jingle-lounge
"""
import math, random, sys
from arrange import Song, NAMES
from carols import TUNES, parse_chords
from theory import parse_chord, nearest, voicing
from perform import Shape, AR1, tempo_map, perform, pedal_bake, ms2b


class Song2(Song):
    def __init__(self, title, tempo, bar_len, key):
        super().__init__(title, tempo, bar_len, key)
        self.tempo_events, self.autom, self.pan = [], {}, {}

    def track(self, name, prog, drum=False):
        n = super().track(name, prog, drum)
        self.tracks[n].setdefault('roles', [])
        return n

    def n(self, trk, start, dur, pitch, vel, role='acc'):
        if pitch is None or start < 0:
            return
        super().n(trk, start, dur, pitch, vel)
        self.tracks[trk]['roles'].append(role)


def chart(s, bar_len, n_bars=None):
    bars = s.count('|') + 1
    return parse_chords(s, bar_len, n_bars or bars, 0, 'chart')


def shifted(ch_list, offset, tr=0):
    return [(c.transposed(tr), s + offset, d) for c, s, d in ch_list]


def chord_at(chords, t):
    for c, s, d in chords:
        if s - 1e-6 <= t < s + d - 1e-6:
            return c, s, d
    return chords[-1] if t >= chords[-1][1] else chords[0]


def mel_notes(tune, bars, offset, tr):
    """Melody notes of tune bars [b0, b1] (1-based, incl. the pickup into b0), placed at offset (= start of b0)."""
    bl = float(tune.bar_len)
    s0, e0 = (bars[0] - 1) * bl, bars[1] * bl
    lead = float(tune.pickup) if bars[0] == 1 else 0.0
    return [(p + tr, float(s) - s0 + offset, float(d)) for p, s, d in tune.melody if s0 - lead - 1e-9 <= float(s) < e0 - 1e-9]


def check(melody, chords, name=''):
    """Long melody notes that rub a semitone against a chord tone (a v1-style safety net for hand charts)."""
    bad = []
    for p, s, d in melody:
        if d < 0.99:
            continue
        c, cs, cd = chord_at(chords, s)
        core = [(c.root + i) % 12 for i in c.ivs if i % 12 in (0, 3, 4, 7, 10, 11)]
        if any((p - q) % 12 in (1, 11) for q in core):
            if not (p % 12 == (c.root + 11) % 12 and c.qual in ('maj7', 'maj9')):
                bad.append(f'{s:.1f} {NAMES[p % 12]} over {c}')
    if bad:
        print(f'  [{name}] melody/chord rubs:', bad)
    return bad


class Safe:
    """A chord with colour tones removed where they would rub a semitone against a held melody note."""

    def __init__(self, ch, melody, s, d):
        held = {p % 12 for p, ms, md in melody if ms < s + d - 1e-6 and ms + md > s + 1e-6 and md >= 0.99}
        core = {0, 3, 4, 7}
        self.root, self.bass, self.qual = ch.root, ch.bass, ch.qual
        self.ivs = tuple(i for i in ch.ivs if i % 12 in core or i in (6,) or
                         not any(((ch.root + i) - m) % 12 in (1, 11) for m in held))
        self.third = ch.third

    def pcs(self):
        return [(self.root + i) % 12 for i in self.ivs]

    @property
    def minor(self):
        return 3 in self.ivs and 4 not in self.ivs


# ------------------------------------------------------------------------------------------- piano blocks
class Piano:
    def __init__(self, song, trk, shape, bl):
        self.s, self.t, self.sh, self.bl = song, trk, shape, bl
        self.prev_bass, self.prev_inner = 40, None
        self.changes, self.mel = [], []

    def safe(self, ch, s, d):
        return Safe(ch, self.mel, s, d)

    def note(self, t, d, p, role, extra=0.0):
        self.s.n(self.t, t, d, p, self.sh.vel(role, t, extra), role)

    def _tones(self, ch, top):
        r = nearest(ch.bass, 36, 48, self.prev_bass)
        self.prev_bass = r
        root = ch.root
        third = ch.third if ch.third is not None else root + 7
        fifth = nearest(root + 7, r + 5, r + 16, r + 7)
        tenth = nearest(third, r + 12, r + 24, r + 16)
        color_pc = (root + 2) % 12 if any(i % 12 == 2 for i in ch.ivs) else (
            (root + 11) % 12 if 11 in ch.ivs else ((root + 10) % 12 if 10 in ch.ivs else (root + 9) % 12 if 9 in ch.ivs else root))
        color = nearest(color_pc, tenth + 1, tenth + 12, tenth + 4)
        return r, fifth, tenth, min(color, top - 3) if color and color < top - 2 else None

    def lh_flow(self, ch, s, d, top, variant=0):
        """Nocturne-style broken chord in eighths (3/4: R 5 10 c 10 5), re-voiced each bar."""
        ch = self.safe(ch, s, d)
        self.changes.append(s)
        r, fifth, tenth, color = self._tones(ch, top)
        pats = [[r, fifth, tenth, color, tenth, fifth], [r, tenth, fifth + 12 if fifth + 12 < top - 2 else fifth, color, tenth, fifth]]
        t, k = s, 0
        while t < s + d - 1e-6:
            pat = pats[(variant + int((t - s) // self.bl)) % 2]
            p = pat[k % len(pat)] if k % len(pat) else r
            if p is not None and p < top - 2:
                role = 'bass' if k % len(pat) == 0 else 'acc'
                self.note(t, s + d - t, p, role, extra=-3 if k % 2 else 0)
            t += 0.5
            k += 1

    def lh_roll(self, ch, s, d, top):
        """Bass + rolled 10th on the downbeat, a soft 3rd/7th dyad on beat 2 (repeated each bar)."""
        ch = self.safe(ch, s, d)
        self.changes.append(s)
        r, fifth, tenth, color = self._tones(ch, top)
        pcs = [p for p in ch.pcs() if p not in (ch.root,)][:3]
        t = s
        while t < s + d - 1e-6:
            self.note(t, s + d - t, r, 'bass', 2)
            self.note(t + ms2b(55, self.s.tempo), s + d - t, tenth, 'acc')
            if d - (t - s) >= 2:
                dy = [p for p in voicing(pcs[:2], 52, min(66, top - 3), self.prev_inner) if p < top - 2]
                self.prev_inner = dy or self.prev_inner
                for p in dy:
                    self.note(t + 1, s + d - t - 1, p, 'acc', -4)
            t += self.bl

    def lh_waltz(self, ch, s, d, top):
        """Romantic waltz lilt for 3/4: bass on 1, a light chord on 2 and 3; every 4th bar a rising arpeggio."""
        ch = self.safe(ch, s, d)
        self.changes.append(s)
        r, fifth, tenth, color = self._tones(ch, top)
        pcs = [p for p in ch.pcs() if p != ch.root][:3]
        t = s
        while t < s + d - 1e-6:
            self.note(t, min(self.bl, s + d - t), r, 'bass', 3)
            if r - 12 >= 31 and self.sh.energy(t) > 6:
                self.note(t, min(self.bl, s + d - t), r - 12, 'bass', -2)  # octave bass at the climax
            if int(round(t / self.bl)) % 4 == 3 and s + d - t >= self.bl:
                for k, p in enumerate([fifth, tenth, color or tenth + 3]):
                    if p < top - 2:
                        self.note(t + 1 + 0.5 * k, 0.5 * (4 - k), p, 'acc', -1)
            else:
                ch3 = [p for p in voicing(pcs, 53, min(67, top - 3), self.prev_inner) if p < top - 2]
                self.prev_inner = ch3 or self.prev_inner
                for b, ex in ((1, -2), (2, -6)):
                    if s + d - t > b:
                        for p in ch3:
                            self.note(t + b, 0.7, p, 'acc', ex)
            t += self.bl

    def lh_sparse(self, ch, s, d, top, roll_ms=60):
        ch = self.safe(ch, s, d)
        self.changes.append(s)
        r, fifth, tenth, color = self._tones(ch, top)
        for k, p in enumerate([r, fifth, tenth, color]):
            if p is not None and p < top - 2:
                self.note(s + ms2b(k * roll_ms, self.s.tempo), d, p, 'bass' if k == 0 else 'acc', -2)

    def melody(self, notes, chords, harmony='sixths', extra=0.0, octave_double=False):
        for i, (p, s, d) in enumerate(notes):
            self.note(s, d, p, 'mel', extra + 0.35 * max(-6, min(6, p - 76)) + (2 if d >= 2 else 0))
            c, cs, cd = chord_at(chords, s)
            c = self.safe(c, cs, cd)
            pcs = c.pcs()
            if p % 12 not in pcs and d < 1:
                self.changes.append(s)  # re-pedal after a passing tone so it does not blur
            if octave_double:
                self.note(s, d, p - 12, 'mel2', extra)
                inner = [q for q in range(p - 11, p - 2) if q % 12 in pcs and abs(q - (p - 12)) > 2]
                if inner and d >= 1:
                    self.note(s, d, inner[len(inner) // 2], 'inner', extra - 2)
                continue
            if harmony == 'sixths' and d >= 2:
                cands = [q for q in range(p - 9, p - 2) if q % 12 in pcs]
                if cands:
                    self.note(s, d, max(cands, key=lambda q: (q % 12 == c.third, -abs(p - q - 8))), 'inner', extra)
            elif harmony == 'block' and (d >= 1 or abs(((s % self.bl) or self.bl) - self.bl) < 1e-6):
                cands = sorted({q for q in range(p - 10, p - 2) if q % 12 in pcs}, reverse=True)
                pick = []
                for q in cands:
                    if all(abs(q - x) > 2 for x in pick):
                        pick.append(q)
                    if len(pick) == 2:
                        break
                for q in pick:
                    self.note(s, d, q, 'inner', extra - 1)

    def fills(self, notes, chords, lo, every=1, extra=0.0):
        """Answer held melody notes (>= 2.5 beats) with a soft 3-note chord-tone figure in the gap."""
        k = 0
        for i, (p, s, d) in enumerate(notes):
            if d < 2.5:
                continue
            k += 1
            if k % every:
                continue
            c, cs, cd = chord_at(chords, s + 1)
            pcs = self.safe(c, cs, cd).pcs()
            pool = [q for q in range(lo, p - 2) if q % 12 in pcs and (q - p) % 12 not in (1, 11)]
            if len(pool) < 3:
                continue
            fig = pool[-3:] if k % 2 else pool[-4:-1][::-1]
            for j, q in enumerate(fig):
                self.note(s + 1 + 0.5 * j, 1.5 - 0.5 * j + 0.25, q, 'fill', extra)


# ------------------------------------------------------------------------------------------- Silent Night
SN_LIGHT = 'Cadd9 | Cadd9 | C | C6 | G7 | G7 | C | C7 | F | Fmaj7 | C | A7 | Dm7 | F | C | C6 | G7 | G7 | C | Am7 | C | G7 | C | Cadd9'
SN_RICH = ('Cmaj9 | Am9 | Cmaj9 | Dm9 | G9 | G13 | Am9 | Gm7:1.5 C9:1.5 | Fmaj9 | Dm9 | Em7 | A7b9 | Dm9 | Fmaj7 | '
           'C6/9 | Am9 | Dm9 | G13 | C6/9 | Em7 | Fmaj9 | Dm9/G | C6/9 | C6/9')


def silent_night_piano(tempo=84, seed=1, arch_depth=10.0, lead_ms=25, raw=False, contrast=1.6):
    tune = TUNES['silent-night']  # C, 3/4, 24 bars
    bl = 3.0
    song = Song2(f'Silent Night - romantic piano ({tempo} BPM)', tempo, bl, 'C')
    P = song.track('Piano', 0)
    sh = Shape(arch_depth, contrast)
    pn = Piano(song, P, sh, bl)
    t = 0.0
    phrases = []

    def phrase_spans(start, nbars, size=4):
        for b in range(0, nbars, size):
            sp = (start + b * bl, start + min(nbars, b + size) * bl)
            sh.phrase(*sp)
            phrases.append(sp)
        for b in range(0, nbars, 8):
            sh.period(start + b * bl, start + min(nbars, b + 8) * bl)

    # intro: the last phrase ("sleep in heavenly peace") an octave up over Fmaj9 - G9sus - Am9 - G13
    ch = shifted(chart('Fmaj9 | Dm9/G | Am7 | G13', bl), t)
    sh.section(t, t + 4 * bl, -7)
    phrase_spans(t, 4)
    intro_mel = [(84, 0, 1.5), (79, 1.5, .5), (76, 2, 1), (79, 3, 1.5), (77, 4.5, .5), (74, 5, 1), (72, 6, 3), (71, 9, 3)]
    intro_mel = [(p, s + t, d) for p, s, d in intro_mel]
    check(intro_mel, ch, 'intro')
    pn.mel = intro_mel
    for c, s, d in ch:
        pn.lh_sparse(c, s, d, 72)
    pn.melody(intro_mel, ch, harmony='sixths', extra=-6)
    t += 4 * bl

    # pass 1: C, light reharm, melody up an octave, flowing nocturne LH, fills in held notes
    ch = shifted(chart(SN_LIGHT, bl), t)
    m = mel_notes(tune, (1, 24), t, 12)
    check(m, ch, 'pass1')
    pn.mel = m
    sh.section(t, t + 16 * bl, -3)
    sh.section(t + 16 * bl, t + 24 * bl, 0)
    phrase_spans(t, 24)
    for i, (c, s, d) in enumerate(ch):
        pn.lh_flow(c, s, d, min(p for p, _, _ in m), variant=i)
    pn.melody(m, ch, harmony='sixths')
    pn.fills(m, ch, 62, every=2)
    t += 24 * bl

    # interlude: falling line over Fmaj9 - Em7 - Dm9 - A7sus4 A7, sets up D major
    ch = shifted(chart('Fmaj9 | Em7 | Dm9 | A7sus4:1.5 A7:1.5', bl), t)
    sh.section(t, t + 4 * bl, -2)
    phrase_spans(t, 4)
    il = [(81, 0, 3), (79, 3, 3), (77, 6, 1.5), (76, 7.5, 1.5), (74, 9, 1.5), (73, 10.5, 1.5)]
    il = [(p, s + t, d) for p, s, d in il]
    check(il, ch, 'interlude')
    pn.mel = il
    for i, (c, s, d) in enumerate(ch):
        pn.lh_flow(c, s, d, 72, variant=i + 1)
    pn.melody(il, ch, harmony='sixths', extra=-3)
    t += 4 * bl

    # pass 2: D (whole step up), rich reharm, melody in the middle register with RH block harmony,
    # LH bass + rolled 10th, climax bars 17-20 with the melody in octaves
    ch = shifted(chart(SN_RICH, bl), t, 2)
    m = mel_notes(tune, (1, 24), t, 2)
    check(m, ch, 'pass2')
    pn.mel = m
    sh.section(t, t + 16 * bl, 2)
    sh.section(t + 16 * bl, t + 20 * bl, 8)
    sh.section(t + 20 * bl, t + 24 * bl, 3)
    phrase_spans(t, 24)
    for c, s, d in ch:
        pn.lh_waltz(c, s, d, 62)
    climax = [n for n in m if t + 16 * bl <= n[1] < t + 20 * bl]
    rest = [n for n in m if n not in climax]
    pn.melody(rest, ch, harmony='block')
    pn.melody([(p + 12, s, d) for p, s, d in climax], ch, octave_double=True, extra=2)
    pn.fills([n for n in rest if n[1] < t + 16 * bl], ch, 60, every=1, extra=-2)
    t += 24 * bl

    # half pass: bars 13-24 in D, melody high and alone, rolled open chords
    ch = shifted(chart(SN_RICH, bl), t - 12 * bl, 2)
    ch = [(c, s, d) for c, s, d in ch if s >= t - 1e-6]
    m = mel_notes(tune, (13, 24), t, 14)
    sh.section(t, t + 12 * bl, -7)
    phrase_spans(t, 12)
    m = [n for n in m if n[1] < t + 10 * bl]  # leave the last 2 bars to the tag
    pn.mel = m
    for c, s, d in ch[:-2]:
        pn.lh_sparse(c, s, d, min(p for p, _, _ in m) if m else 84)
    pn.melody(m, ch, harmony='sixths', extra=-4)
    t += 10 * bl

    # tag: last phrase twice - first over Bm9 -> Gm6 (deceptive, borrowed iv), then home to D6/9
    tag_m = [(p + 14, s, d) for p, s, d in [(72, 0, 1.5), (67, 1.5, .5), (64, 2, 1), (67, 3, 1.5), (65, 4.5, .5), (62, 5, 1)]]
    ch = shifted(chart('Bm9 | Gm6 | D6/9 | D6/9', bl), t)
    sh.section(t, t + 4 * bl, -9)
    phrase_spans(t, 4)
    tag = [(p, s + t, d) for p, s, d in tag_m] + [(74 + 12, t + 6, 6)]
    pn.mel = tag
    for c, s, d in ch[:2]:
        pn.lh_sparse(c, s, d, 74)
    pn.lh_sparse(ch[2][0], ch[2][1], 6, 86, roll_ms=110)
    pn.melody(tag, ch, harmony='sixths', extra=-5)
    t += 4 * bl

    total = t
    if raw:  # plain score (no rubato, lead, pedal or micro-variation) for an external performance model
        return song
    song.tempo_events = tempo_map(tempo, total, phrases, final_beats=12, cadences=[4 * bl + 24 * bl + 4 * bl], rubato=0.015, w=0.62)
    rng = random.Random(seed)
    perform(song, rng, lead_ms=lead_ms, spread_ms=9)
    pedal_bake(song, P, pn.changes)
    return song


# ------------------------------------------------------------------------------------------- strings blocks
def scale_pcs(key_root, minor=False):
    steps = [0, 2, 3, 5, 7, 8, 10] if minor else [0, 2, 4, 5, 7, 9, 11]
    return {(key_root + i) % 12 for i in steps}


def voice_lead(chords, voices, mel, scale, prev=None, suspend=True, passing=True, rearticulate=None, bl=3.0):
    """SATB-style inner/bass lines under (or over) a melody.
    voices: [(name, lo, hi, kind)] kind 'bass' (chord bass) or 'inner' (distinct chord tones, voice-led).
    Returns {name: [(start, dur, pitch)]} with 4-3 / 9-8 suspensions and diatonic passing tones."""
    prev = dict(prev or {})
    plan = {v[0]: [] for v in voices}
    for c, s, d in chords:
        held = [p for p, ms, md in mel if ms < s + d - 1e-6 and ms + md > s + 1e-6]
        mlo, mhi = (min(held), max(held)) if held else (200, -1)
        used = set()
        for name, lo, hi, kind in voices:
            if kind == 'bass':
                p = nearest(c.bass, lo, hi, prev.get(name, (lo + hi) // 2))
            else:
                cands = []
                for q in range(lo, hi + 1):
                    if q % 12 not in c.pcs() or (held and lo < mlo and q >= mlo - 1) or (held and lo > mhi and q <= mhi + 1):
                        continue
                    cost = abs(q - prev.get(name, (lo + hi) // 2)) + 4 * (q % 12 in used) + 3 * (q % 12 == c.root and c.third not in used)
                    cost -= 3 * (q % 12 == c.third and c.third not in used)
                    cands.append((cost, q))
                p = min(cands)[1] if cands else nearest(c.third or c.root, lo, hi, prev.get(name, lo))
            used.add(p % 12)
            plan[name].append([s, d, p])
            prev[name] = p
    out = {}
    for name, lo, hi, kind in voices:
        evs = plan[name]
        line = []
        for k, (s, d, p) in enumerate(evs):
            c = chord_at(chords, s)[0]
            nxt = evs[k + 1][2] if k + 1 < len(evs) else p
            pieces = [(s, d, p)]
            if suspend and kind == 'inner' and k > 0 and d >= 2:
                pp = evs[k - 1][2]
                if pp % 12 not in c.pcs() and (pp - p) in (1, 2):
                    pieces = [(s, 1.0, pp), (s + 1.0, d - 1.0, p)]  # hold the old tone, resolve down
            if passing and d >= 2 and 3 <= abs(nxt - p) <= 4 and not (len(pieces) > 1):
                step = 1 if nxt > p else -1
                pt = next((q for q in range(p + step, nxt, step) if q % 12 in scale), None)
                if pt is not None:
                    pieces = [(s, d - 1.0, p), (s + d - 1.0, 1.0, pt)]
            if rearticulate:
                split = []
                for ps, pd, pp in pieces:
                    while pd > rearticulate + 1e-6:
                        split.append((ps, rearticulate, pp))
                        ps, pd = ps + rearticulate, pd - rearticulate
                    split.append((ps, pd, pp))
                pieces = split
            line.extend(pieces)
        merged = []
        for ps, pd, pp in line:  # tie repeated pitches unless re-articulation was asked for
            if merged and not rearticulate and merged[-1][2] == pp and abs(merged[-1][0] + merged[-1][1] - ps) < 1e-6:
                merged[-1] = (merged[-1][0], merged[-1][1] + pd, pp)
            else:
                merged.append((ps, pd, pp))
        out[name] = merged
    return out, prev


def swell(notes, sh, base, step=0.5, floor=-20, tail=-13, arch=6.0, lo=0, hi=127):
    """Macro automation for a monophonic string line: every note >= ~1 beat swells (peak at 40 %),
    riding a phrase arch; short notes sit a little under the phrase level. Returns [(beat, value)]."""
    ev = []
    for s, d in sorted((n[0], n[1]) for n in notes):
        lvl = lambda t: base(t) + arch * sh.arch(t)
        if d >= 0.9:
            pts = [(s, lvl(s) + floor), (s + 0.4 * d, lvl(s + 0.4 * d)), (s + 0.92 * d, lvl(s + d) + tail)]
        else:
            pts = [(s, lvl(s) - 4)]
        ev.extend(pts)
    ev.sort()
    clean = []
    for b, v in ev:
        v = max(lo, min(hi, v))
        if clean and b <= clean[-1][0] + 0.02:
            continue
        clean.append((round(b, 3), round(v, 2)))
    return clean


def harp_roll(song, trk, sh, ch, s, top, n=4, roll_ms=45):
    tones, p = [nearest(ch.bass, 41, 52, 46)], None
    q = tones[0] + 3
    while len(tones) < n and q <= top:
        if q % 12 in ch.pcs() and q - tones[-1] >= 3:
            tones.append(q)
        q += 1
    for k, p in enumerate(tones):
        song.n(trk, s + ms2b(k * roll_ms, song.tempo), 2.5, p, sh.vel('harp', s, 2 - k), 'harp')


def harp_arp(song, trk, sh, ch, s, d, lo=48, top=76, up=True):
    tones = [q for q in range(lo, top + 1) if q % 12 in ch.pcs()]
    tones = [q for i, q in enumerate(tones) if i == 0 or q - tones[i - 1] >= 3][:7]
    seq = tones + tones[-2:0:-1]
    k, t = 0, s
    while t < s + d - 1e-6:
        song.n(trk, t, min(1.5, s + d - t + 0.1), seq[k % len(seq)], sh.vel('harp', t, -3 if k % 2 else 0), 'harp')
        t += 0.5
        k += 1


AWAY_V1 = 'F | F | F:2 Bb:1 | Bb:2 Gm:1 | Bb6:2 C7:1 | F | Gm7 | C:2 C7:1 | F | F | F:2 Bb:1 | Bb:2 Gm:1 | Bb6:2 C7:1 | F | Gm7:1 C7:2 | F'
AWAY_V2 = ('F | F/A | Dm:2 Bb:1 | Bb:2 Gm7:1 | Bb:2 C7:1 | F/A:2 Dm7:1 | Gm7 | Csus4:1 C:1 C7:1 | F | Dm7 | Dm:2 Bb:1 | '
           'Bb:2 Gm7:1 | Bb6:2 C7:1 | F/A:2 Dm7:1 | Gm7:1 C7:2 | F')


def away_strings(lib='os', tempo=76, seed=2):
    tune = TUNES['away-in-a-manger-uk']  # F, 3/4, pickup 1, 16 bars
    bl = 3.0
    q = lib == 'ssq'
    song = Song2(f'Away in a Manger - strings ({"String Quartet" if q else "Orchestral Strings"}, {tempo} BPM)', tempo, bl, 'F')
    names = (['Quartet Violin 1', 'Quartet Violin 2', 'Quartet Viola', 'Quartet Cello'] if q else
             ['Violins 1', 'Violins 2', 'Violas', 'Cellos'])
    V1, V2, VA, VC = (song.track(n, 48) for n in names)
    CB, H, CE = song.track('Basses', 43), song.track('Harp', 46), song.track('Hand Bells', 8)
    song.pan = {V1: -0.45, V2: -0.2, VA: 0.15, VC: 0.4, CB: 0.5, H: -0.3, CE: 0.25}
    sh = Shape(8.0, 1.5)
    t, phrases, prev = 0.0, [], {}
    lines = {n: [] for n in (V1, V2, VA, VC, CB)}

    def spans(start, nbars, size=4):
        for b in range(0, nbars, size):
            sp = (start + b * bl, start + min(nbars, b + size) * bl)
            sh.phrase(*sp)
            phrases.append(sp)
        sh.period(start, start + nbars * bl)

    def put(trk, notes, role):
        """notes as (start, dur, pitch)"""
        for s, d, p in notes:
            song.n(trk, s, d, p, sh.vel(role, s), role)
            lines[trk].append((s, d, p))

    # intro: harp + soft low strings, a three-note glockenspiel echo of the tune's opening
    ch = shifted(chart('F | Bbmaj7 | Gm7 | C7sus4:2 C7:1', bl), t)
    sh.section(t, t + 4 * bl, -8)
    spans(t, 4)
    vl, prev = voice_lead(ch, [(VC, 36, 50, 'bass'), (VA, 52, 64, 'inner')], [], scale_pcs(5), prev)
    for trk, ns in vl.items():
        put(trk, ns, 'pad')
    for c, s, d in ch:
        harp_arp(song, H, sh, c, s, d, 48, 74)
    for k, p in enumerate([72, 69, 65]):
        song.n(CE, t + 6 + k, 1.5, p, sh.vel('bell', t + 6, -6), 'bell')
    t += 4 * bl

    # verse 1: violin melody (up an octave), viola + cello sustain, rolled harp chords; basses rest
    ch = shifted(chart(AWAY_V1, bl), t)
    m = mel_notes(tune, (1, 16), t, 12)
    sh.section(t, t + 16 * bl, -4)
    spans(t, 16)
    put(V1, [(s, d, p) for p, s, d in m], 'mel')
    vl, prev = voice_lead(ch, [(VC, 36, 52, 'bass'), (VA, 53, 67, 'inner')], m, scale_pcs(5), prev)
    for trk, ns in vl.items():
        put(trk, ns, 'pad')
    for c, s, d in ch:
        if abs((s - t) % (2 * bl)) < 1e-6 or d >= bl:
            harp_roll(song, H, sh, c, s, 72)
    t += 16 * bl

    # verse 2: melody to the cellos, violins 2 + violas above it with suspensions/passing tones,
    # basses on the bass line, harp eighths; violins 1 enter with a high descant in bars 9-16
    ch = shifted(chart(AWAY_V2, bl), t)
    m = mel_notes(tune, (1, 16), t, 0)
    sh.section(t, t + 16 * bl, 0)
    sh.section(t + 8 * bl, t + 16 * bl, 2)
    spans(t, 16)
    put(VC, [(s, d, p) for p, s, d in m], 'mel')
    vl, prev = voice_lead(ch, [(CB, 29, 43, 'bass'), (VA, 65, 76, 'inner'), (V2, 70, 82, 'inner')], m, scale_pcs(5), prev,
                          rearticulate=None)
    for trk, ns in vl.items():
        put(trk, ns, 'pad' if trk != CB else 'bass')
    desc, _ = voice_lead([x for x in ch if x[1] >= t + 8 * bl], [(V1, 79, 89, 'inner')], [], scale_pcs(5), {V1: 84},
                         passing=False)
    put(V1, desc[V1], 'pad')
    for c, s, d in ch:
        harp_arp(song, H, sh, c, s, d, 50, 72)
    t += 16 * bl

    # interlude: C7 -> D7 turns the music up a whole step to G
    ch = shifted(chart('C7 | D7', bl), t)
    sh.section(t, t + 2 * bl, 1)
    spans(t, 2, 2)
    put(V1, [(t, 3, 76), (t + 3, 2, 78)], 'mel')
    vl, prev = voice_lead(ch, [(CB, 29, 43, 'bass'), (VC, 41, 55, 'inner'), (VA, 55, 67, 'inner')], [], scale_pcs(5), prev)
    for trk, ns in vl.items():
        put(trk, ns, 'pad')
    for c, s, d in ch:
        harp_arp(song, H, sh, c, s, d, 50, 76)
    t += 2 * bl

    # verse 3 in G: violins 1 melody + violins 2 an octave below, violas inner, cellos + basses in octaves,
    # harp eighths, glockenspiel doubling bars 9-12 only
    ch = shifted(chart(AWAY_V2, bl), t, 2)
    m = mel_notes(tune, (1, 16), t, 14)
    sh.section(t, t + 16 * bl, 5)
    sh.section(t + 8 * bl, t + 12 * bl, 9)
    spans(t, 16)
    put(V1, [(s, d, p) for p, s, d in m], 'mel')
    put(V2, [(s, d, p - 12) for p, s, d in m], 'mel2')
    vl, prev = voice_lead(ch, [(VC, 38, 55, 'bass'), (VA, 55, 69, 'inner')], [(p - 12, s, d) for p, s, d in m],
                          scale_pcs(7), prev)
    for trk, ns in vl.items():
        put(trk, ns, 'pad' if trk != VC else 'bass')
    put(CB, [(s, d, p - 12) for s, d, p in vl[VC]], 'bass')
    for c, s, d in ch:
        harp_arp(song, H, sh, c, s, d, 50, 76)
    for p, s, d in m:
        if t + 8 * bl <= s < t + 12 * bl:
            song.n(CE, s, d, p, sh.vel('bell', s, -4), 'bell')
    t += 16 * bl

    # tag: the last four bars again, softer, slowing; final G(add9) with a rising harp roll
    ch = shifted(chart('Cmaj7:2 D7:1 | G/B:2 Em7:1 | Am7:1 D7:2 | G', bl), t)
    tag = mel_notes(tune, (13, 16), t, 14)
    sh.section(t, t + 6 * bl, -6)
    spans(t, 4)
    put(V1, [(s, d, p) for p, s, d in tag], 'mel')
    vl, prev = voice_lead(ch, [(VC, 38, 55, 'bass'), (VA, 55, 69, 'inner'), (V2, 62, 74, 'inner')], tag, scale_pcs(7), prev)
    for trk, ns in vl.items():
        put(trk, ns, 'pad')
    for c, s, d in ch[:-1]:
        harp_arp(song, H, sh, c, s, d, 50, 74)
    fin = t + 3 * bl
    gch = parse_chord('Gadd9')
    for trk, p in [(V1, 86), (V2, 79), (VA, 71), (VC, 55), (CB, 31)]:
        put(trk, [(fin, 2 * bl + 1, p)], 'pad')
    for k, p in enumerate([43, 50, 55, 59, 62, 67, 71, 74, 79]):
        song.n(H, fin + k * 0.25, 6 - k * 0.25, p, sh.vel('harp', fin, -k), 'harp')
    song.n(CE, fin + 1.5, 4, 79, sh.vel('bell', fin, -8), 'bell')
    t = fin + 2 * bl

    song.tempo_events = tempo_map(tempo, t, phrases, final_beats=9, rubato=0.02, w=0.6)
    offsets = {V1: -100, V2: -60, VA: -60, VC: -60, CB: -60}
    perform(song, random.Random(seed), lead_ms=0, spread_ms=0, timing_sd_ms=6, vel_sd=2.5, string_offsets=offsets)
    # dynamics automation: Orchestral Strings -> rack Volume macro (index 7, 0 dB ~ 108); Quartet -> Dynamics (0)
    lvl = lambda t_: sh.energy(t_) * 1.2
    for trk in (V1, V2, VA, VC, CB):
        if q and trk != CB:
            song.autom[trk] = [(('macro', 0), swell(lines[trk], sh, lambda t_: 68 + 2.5 * sh.energy(t_), floor=-22, tail=-14, arch=10, lo=20, hi=118))]
        else:
            song.autom[trk] = [(('macro', 7), swell(lines[trk], sh, lambda t_: 104 + lvl(t_), floor=-16, tail=-10, arch=4, lo=70, hi=114))]
    if q:  # Live crashes loading 4 String Quartet instances (64 Max devices); merge the lower three into one
        ens = 'Quartet Ensemble'
        tr = {k: v for k, v in song.tracks.items()}
        merged = dict(prog=48, ch=tr[V2]['ch'], drum=False, cc=[], notes=[], roles=[])
        for n in (V2, VA, VC):
            merged['notes'] += tr[n]['notes']
            merged['roles'] += tr[n]['roles']
        song.tracks = {}
        for k, v in tr.items():
            if k == V2:
                song.tracks[ens] = merged
            elif k not in (VA, VC):
                song.tracks[k] = v
        song.autom[ens] = song.autom.pop(VC)
        for n in (V2, VA):
            song.autom.pop(n, None)
        song.pan[ens] = 0.1
    return song


# ------------------------------------------------------------------------------------------- lounge (chillhop)
JB_F = ('Fmaj9 | Fmaj9:2 Dm9:2 | Am7:2 Dm9:2 | Gm9:2 C13:2 | Bb6/9 | Bb6/9:1 Am7:1 Dm9:2 | G9 | Gm9:2 C13:2 | '
        'Fmaj9 | Fmaj9:2 Dm9:2 | Am7:2 Dm9:2 | Gm9:2 C13:2 | Bb6/9 | Bb6/9:1 Am7:1 Dm9:2 | Gm9:2 C13:2 | F6/9')
LOOP_A = 'Fmaj9 | Dm9 | Gm9 | C13'
LOOP_B = 'Bbmaj9 | Am7 | Gm9 | C9sus4:2 C13:2'
HOOK = [(0.5, 69, .5), (1.0, 69, .5), (1.5, 69, 1.25), (4.5, 69, .5), (5.0, 69, .5), (5.5, 69, 1.25),
        (8.0, 69, .5), (8.5, 72, .5), (9.0, 65, .75), (9.75, 67, .25), (10.0, 69, 2.0)]
FUN = [(0.5, 70, .5), (1.0, 70, .5), (1.5, 70, .75), (2.5, 70, .5), (4.0, 70, .5), (4.5, 69, .5), (5.0, 69, .5),
       (5.5, 69, .25), (5.75, 69, .75), (8.5, 69, .5), (9.0, 67, .5), (9.5, 67, .5), (10.0, 69, .5), (10.5, 67, 1.0),
       (12.0, 72, 2.5)]
KICK, RIM, SNARE, HAT, OHAT = 36, 37, 38, 42, 44


def swing16(t, amount=0.57):
    """Shared 16th swing for every part: the off-16th of each 8th moves to amount x 1/8."""
    pos = (t * 4) % 2
    return t + (amount - 0.5) * 0.5 if abs(pos - 1) < 1e-3 else t


def jingle_lounge(tempo=90, seed=3, swing=0.57):
    bl = 4.0
    song = Song2(f'Jingle Bells - chillhop ({tempo} BPM)', tempo, bl, 'F')
    D, K, B = song.track('Drums', 0, drum=True), song.track('Keys (electric piano)', 4), song.track('Bass', 33)
    L, BE, SL = song.track('Lead (melody)', 4), song.track('Vibraphone', 11), song.track('Sleigh Bells', 0, drum=True)
    sh = Shape(5.0)
    rng = random.Random(seed)
    jit = AR1(rng, 2.5, 0.9)
    ms = lambda x: ms2b(x, tempo)
    prev_k, prev_b = None, 40

    def hit(trk, t, p, v, d=0.12, off_ms=0.0, role='drum'):
        song.n(trk, swing16(t, swing) + ms(off_ms + jit()), d, p, max(1, min(127, int(v + rng.gauss(0, 2)))), role)

    def drums(bar_t, bar, level, fill=False):
        if level == 0:
            return
        for e in range(8):  # hats: 8ths, accented on the beat, a 16th pickup every other bar
            t = bar_t + e * 0.5
            hit(D, t, HAT, (86 if e % 2 == 0 else 58) + sh.energy(t), off_ms=0)
        if bar % 2 and level >= 2:
            hit(D, bar_t + 3.75, HAT, 48)
        if level == 1:
            hit(D, bar_t + 1, RIM, 72, off_ms=-3)
            hit(D, bar_t + 3, RIM, 74, off_ms=-3)
            return
        hit(D, bar_t, KICK, 108, off_ms=8)
        hit(D, bar_t + 1.75, KICK, 86, off_ms=8)
        if bar % 2 == 1:
            hit(D, bar_t + 2.5, KICK, 94, off_ms=8)
        if bar % 4 == 3:
            hit(D, bar_t + 3.25, KICK, 78, off_ms=8)
        hit(D, bar_t + 1, SNARE, 102, off_ms=-4)
        hit(D, bar_t + 3, SNARE, 104, off_ms=-4)
        hit(D, bar_t + 0.75, SNARE, 36, off_ms=6)
        hit(D, bar_t + 2.75, SNARE, 38, off_ms=6)
        if fill:
            hit(D, bar_t + 3.5, SNARE, 70, off_ms=-2)
            hit(D, bar_t + 3.75, SNARE, 58, off_ms=-2)
            hit(D, bar_t + 3.5, OHAT, 60, d=0.4)

    def sleigh(bar_t, mode):
        if mode == 'quarters':
            for b in range(4):
                hit(SL, bar_t + b, 60, 64 if b % 2 == 0 else 52)
        elif mode == 'eighths':
            for e in range(8):
                hit(SL, bar_t + e * 0.5, 60, 70 if e % 2 == 0 else 46)

    def keys(chords, pattern='A', soft=0):
        nonlocal prev_k
        for c, s, d in chords:
            pcs = [p for p in c.pcs() if p != c.root] if len(c.pcs()) > 3 else c.pcs()
            v = voicing(pcs[:4], 53, 72, prev_k)
            prev_k = v
            if pattern == 'pad':
                hits = [(0, d - 0.1)]
            elif pattern == 'A':
                hits = [(0, 1.4), (2.5, max(0.5, d - 2.6))] if d >= 4 else [(0, d - 0.2)]
            else:
                hits = [(0, 1.1), (1.75, 0.6), (3.0, max(0.4, d - 3.1))] if d >= 4 else [(0, 0.9), (1.5, d - 1.6)]
            for off, dur in hits:
                for k, p in enumerate(sorted(v)):
                    top = k == len(v) - 1
                    t0 = swing16(s + off, swing) + ms(k * 14)  # strum 14 ms bottom-up
                    song.n(K, t0, dur, p, int(sh.vel('keys', s, (8 if top else 0) - (6 if off else 0) + soft)), 'keys')

    def bass(chords, style='move'):
        nonlocal prev_b
        for i, (c, s, d) in enumerate(chords):
            r = nearest(c.bass, 33, 45, prev_b)
            prev_b = r
            if style == 'whole':
                song.n(B, s, d - 0.1, r, 78, 'bass')
                continue
            song.n(B, swing16(s, swing) + ms(6), 1.4, r, 92, 'bass')
            if d >= 4:
                song.n(B, swing16(s + 2.5, swing) + ms(6), 0.7, nearest(c.root + 7, 33, 50, r + 7), 74, 'bass')
                nxt = chords[i + 1][0] if i + 1 < len(chords) else c
                tgt = nearest(nxt.bass, 33, 45, r)
                if tgt != r and i % 2:
                    song.n(B, swing16(s + 3.5, swing) + ms(6), 0.45, tgt + (1 if tgt < r else -1), 70, 'bass')

    def lead(notes, t0, trk=None, tr=0, soft=0, role='lead'):
        for s, p, d in notes:
            tt = swing16(t0 + s, swing) + ms(12)  # melody sits a hair behind the beat
            song.n(trk or L, tt, d, p + tr, int(sh.vel(role, t0 + s, soft)), role)

    t = 0.0
    loopA = lambda t0, n=2: shifted(chart(' | '.join([LOOP_A] * n), bl), t0)
    # intro (8): keys alone, then hats/rim, bass and sleigh quarters from bar 5
    sh.section(t, t + 8 * bl, -8)
    ch = loopA(t)
    keys(ch, 'pad', -4)
    bass(ch[4:], 'whole')
    for b in range(8):
        if b >= 4:
            drums(t + b * bl, b, 1)
            sleigh(t + b * bl, 'quarters')
    t += 8 * bl
    # A1 (8): full groove, the hook twice on the lead
    sh.section(t, t + 8 * bl, 0)
    ch = loopA(t)
    keys(ch, 'A')
    bass(ch)
    for b in range(8):
        drums(t + b * bl, b, 2, fill=b == 7)
    lead(HOOK, t)
    lead(HOOK, t + 4 * bl, soft=2)
    t += 8 * bl
    # A2 (8): hook + glockenspiel echo an octave up, sleigh bells in eighths, busier comping
    sh.section(t, t + 8 * bl, 2)
    ch = loopA(t)
    keys(ch, 'B')
    bass(ch)
    for b in range(8):
        drums(t + b * bl, b, 2, fill=b == 7)
        sleigh(t + b * bl, 'eighths')
    lead(HOOK, t)
    lead(HOOK, t + 4 * bl)
    lead(HOOK, t + 4 * bl, trk=BE, tr=12, soft=-14, role='bell')
    t += 8 * bl
    # B (8): "oh what fun" rephrased over a new loop
    sh.section(t, t + 8 * bl, 3)
    ch = shifted(chart(' | '.join([LOOP_B] * 2), bl), t)
    keys(ch, 'A')
    bass(ch)
    for b in range(8):
        drums(t + b * bl, b, 2, fill=b == 7)
        sleigh(t + b * bl, 'quarters')
    lead(FUN, t)
    lead(FUN, t + 4 * bl, soft=2)
    t += 8 * bl
    # breakdown (8): no drums, long chords, the hook on glockenspiel, sleigh bells carry the pulse
    sh.section(t, t + 8 * bl, -5)
    ch = loopA(t)
    keys(ch, 'pad', -2)
    bass(ch, 'whole')
    for b in range(8):
        sleigh(t + b * bl, 'eighths' if b >= 4 else 'quarters')
    lead(HOOK, t, trk=BE, tr=12, soft=-6, role='bell')
    lead(HOOK, t + 4 * bl, trk=BE, tr=12, soft=-4, role='bell')
    t += 8 * bl
    # chorus (16): the full refrain once, reharmonised, full band
    sh.section(t, t + 16 * bl, 5)
    ch = shifted(chart(JB_F, bl), t)
    keys(ch, 'A')
    bass(ch)
    for b in range(16):
        drums(t + b * bl, b, 2, fill=b in (7, 15))
        sleigh(t + b * bl, 'eighths')
    m = mel_notes(TUNES['jingle-bells'], (1, 16), t, 5)
    check(m, ch, 'chorus')
    lead([(s - t, p, d) for p, s, d in m], t)
    t += 16 * bl
    # A3 (8): hook with glockenspiel, kick drops out for the last bars
    sh.section(t, t + 8 * bl, 1)
    ch = loopA(t)
    keys(ch, 'B')
    bass(ch)
    for b in range(8):
        drums(t + b * bl, b, 2 if b < 6 else 1)
        sleigh(t + b * bl, 'eighths' if b < 6 else 'quarters')
    lead(HOOK, t)
    lead(HOOK, t + 4 * bl, trk=BE, tr=12, soft=-8, role='bell')
    t += 8 * bl
    # outro (4): chords settle on Fmaj9, last sleigh shake, a single glockenspiel note
    sh.section(t, t + 4 * bl, -7)
    ch = shifted(chart('Fmaj9 | Dm9 | Gm9 | Fmaj9', bl), t)
    keys(ch, 'pad', -4)
    bass(ch, 'whole')
    sleigh(t, 'quarters')
    hit(SL, t + 4 * bl - 1, 60, 60)
    song.n(BE, t + 3 * bl, 4, 81, int(sh.vel('bell', t, -6)), 'bell')
    t += 4 * bl
    song.tempo_events = tempo_map(tempo, t, [], final_beats=6, rubato=0, w=0.8)
    return song


PIECES = {'jingle-lounge': jingle_lounge, 'silent-night-piano': silent_night_piano,
          'away-strings-os': lambda **k: away_strings('os', **k), 'away-strings-ssq': lambda **k: away_strings('ssq', **k)}

if __name__ == '__main__':
    piece = sys.argv[1] if len(sys.argv) > 1 else 'silent-night-piano'
    tempo = float(sys.argv[2]) if len(sys.argv) > 2 else None
    song = PIECES[piece](**({'tempo': tempo} if tempo else {}))
    n = sum(len(t['notes']) for t in song.tracks.values())
    vs = [v for t in song.tracks.values() for _, _, _, v in t['notes']]
    print(f'{piece}: {n} notes, {song.end:.1f} beats, vel {min(vs)}-{max(vs)}, tempo pts {len(song.tempo_events)}')
