#!/usr/bin/env python3
"""Christmas pilot arranger (Approach A): public-domain carol data -> multi-track MIDI for Ableton,
plus a crude General-MIDI 'note check' preview (fluidsynth) so melodies can be verified by ear.

The MIDI is the deliverable: drag the .mid into Live's Arrangement (one Live track per MIDI track) and load real
instruments (Grand Piano, Orchestral Strings, Mallets, Festive Bells, LABS ...). The preview is NOT the sound.

Usage: python3 tools/xmas/arrange.py [--no-preview] [pilot_id ...]      (pure stdlib; preview needs fluidsynth+ffmpeg)
"""
import math, os, random, re, struct, subprocess, sys
from carols import TUNES, parse_chords
from theory import Chord, nearest, voicing

TPQ = 480
OUT = os.path.expanduser('~/Downloads/Christmas Ableton')
SF2 = '/opt/homebrew/Cellar/fluid-synth/2.6.0/share/fluid-synth/sf2/VintageDreamsWaves-v2.sf2'
GM_DRUM_CH = 9
KICK, RIM, SNARE, HAT_C, HAT_P, HAT_O, RIDE, SLEIGH = 36, 37, 38, 42, 44, 46, 51, 54
MAJ_SF = {'C': 0, 'G': 1, 'D': 2, 'A': 3, 'E': 4, 'B': 5, 'F#': 6, 'F': -1, 'Bb': -2, 'Eb': -3, 'Ab': -4, 'Db': -5}
NAMES = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']


# ----------------------------------------------------------------------------------------------- song + MIDI
class Song:
    def __init__(self, title, tempo, bar_len, key):
        self.title, self.tempo, self.bar_len, self.key = title, tempo, float(bar_len), key
        self.tracks, self.end = {}, 0.0

    def track(self, name, prog, drum=False):
        if name not in self.tracks:
            ch = GM_DRUM_CH if drum else [c for c in range(16) if c != GM_DRUM_CH][len([t for t in self.tracks.values() if not t['drum']])]
            self.tracks[name] = dict(prog=prog, ch=ch, drum=drum, notes=[], cc=[])
        return name

    def n(self, trk, start, dur, pitch, vel):
        if pitch is None or start < 0:
            return
        self.tracks[trk]['notes'].append((float(start), max(0.03, float(dur)), int(pitch), max(1, min(127, int(round(vel))))))
        self.end = max(self.end, float(start) + float(dur))

    def cc(self, trk, t, num, val):
        self.tracks[trk]['cc'].append((max(0.0, float(t)), num, val))

    def _key_sig(self):
        minor = self.key.endswith('m')
        root = self.key[:-1] if minor else self.key
        if minor:
            root = NAMES[(NAMES.index(root) + 3) % 12] if root in NAMES else root
        return MAJ_SF.get(root, 0) & 0xFF, 1 if minor else 0

    def write(self, path, only=None):
        def vlq(n):
            b = [n & 0x7F]
            n >>= 7
            while n:
                b.insert(0, (n & 0x7F) | 0x80)
                n >>= 7
            return bytes(b)

        def chunk(events):
            events.sort(key=lambda e: (e[0], e[1]))
            out, last = b'', 0
            for tick, _, data in events:
                out += vlq(tick - last) + data
                last = tick
            out += vlq(0) + b'\xff\x2f\x00'
            return b'MTrk' + struct.pack('>I', len(out)) + out

        tk = lambda b: int(round(b * TPQ))
        num = int(self.bar_len)
        sf, mi = self._key_sig()
        cond = [(0, 0, b'\xff\x03' + vlq(len(self.title.encode())) + self.title.encode()),
                (0, 0, b'\xff\x51\x03' + int(60e6 / self.tempo).to_bytes(3, 'big')),
                (0, 0, bytes([0xFF, 0x58, 4, num, 2, 24, 8])),
                (0, 0, bytes([0xFF, 0x59, 2, sf, mi]))]
        chunks = [chunk(cond)]
        for name, t in self.tracks.items():
            if only and name != only:
                continue
            ch, ev = t['ch'], [(0, 0, b'\xff\x03' + vlq(len(name.encode())) + name.encode())]
            if not t['drum']:
                ev.append((0, 1, bytes([0xC0 | ch, t['prog']])))
            for s, d, p, v in t['notes']:
                ev.append((tk(s), 3, bytes([0x90 | ch, p, v])))
                ev.append((max(tk(s) + 1, tk(s + d) - 2), 2, bytes([0x80 | ch, p, 0])))
            for s, num_, val in t['cc']:
                ev.append((tk(s), 2 if val == 0 else 4, bytes([0xB0 | ch, num_, val])))
            chunks.append(chunk(ev))
        with open(path, 'wb') as f:
            f.write(b'MThd' + struct.pack('>IHHH', 6, 1, len(chunks), TPQ) + b''.join(chunks))


# ----------------------------------------------------------------------------------------------- form
class Form:
    """Lays a tune out in time as segments: intro / tune pass / interlude / outro tag / final chord."""

    def __init__(self, tune):
        self.t, self.time, self.segs = tune, 0.0, []
        self.bl = float(tune.bar_len)

    def _chords(self, s0, e0):
        out = []
        for ch, s, d in self.t.chords:
            s, e = float(s), float(s + d)
            a, b = max(s, s0), min(e, e0)
            if b > a:
                out.append((ch, self.time + a - s0, b - a))
        return out

    def _add(self, kind, s0, e0, melody, opts):
        self.segs.append(dict(kind=kind, start=self.time, end=self.time + e0 - s0, bl=self.bl,
                              chords=self._chords(s0, e0), melody=melody, o=opts))
        self.time += e0 - s0

    def intro(self, bars, from_bar=None, **o):
        b0 = self.t.n_bars - bars if from_bar is None else from_bar - 1
        self._add('intro', b0 * self.bl, (b0 + bars) * self.bl, [], o)
        return self

    def tune(self, from_bar=1, **o):
        s0, e0 = (from_bar - 1) * self.bl, self.t.n_bars * self.bl
        lead = float(o.pop('lead', self.t.pickup))
        mel = [(p, self.time + float(s) - s0, float(d)) for p, s, d in self.t.melody if float(s) >= s0 - lead - 1e-9]
        self._add('tune', s0, e0, mel, o)
        return self

    def interlude(self, from_bar, to_bar, **o):
        self._add('interlude', (from_bar - 1) * self.bl, to_bar * self.bl, [], o)
        return self

    def outro(self, tag_from_bar, hold_bars=2, **o):
        self.tune(tag_from_bar, **o)
        self.segs[-1]['kind'] = 'tag'
        last = self.t.chords[-1][0]
        hold = hold_bars * self.bl
        self.segs.append(dict(kind='final', start=self.time, end=self.time + hold, bl=self.bl,
                              chords=[(last, self.time, hold)], melody=[], o=dict(self.segs[-1]['o'])))
        mel = self.segs[-2]['melody']
        if mel:  # let the last melody note ring into the final chord
            p, s, d = mel[-1]
            mel[-1] = (p, s, d + hold * 0.75)
        self.time += hold
        return self


# ----------------------------------------------------------------------------------------------- helpers
def mel_during(seg, s, e, min_dur=0.0):
    """Melody pitches sounding in [s, e) - looks across segments, so a pickup colours the bar before it."""
    return [p for p, ms, md in seg.get('allmel', seg['melody']) if ms < e - 1e-6 and ms + md > s + 1e-6 and md >= min_dur]


def mel_top(seg, s, e, default=127):
    ps = mel_during(seg, s, e)
    return min(ps) if ps else default


def enrich(ch, mel_pcs, style):
    """Jazz/lounge colour: triads -> 9th chords, with a 6/9 instead of maj7 when the melody sits on the root."""
    if style not in ('jazz', 'lounge'):
        return ch
    q = {'': 'maj9', 'maj7': 'maj9', 'm': 'm9', 'm7': 'm9', '7': '9', '6': '6/9', 'add9': 'maj9'}.get(ch.qual, ch.qual)
    if q == 'maj9' and ch.root in mel_pcs:
        q = '6/9'
    return ch.with_qual(q)


def safe_pcs(ch, mel_pcs):
    """Chord pitch classes minus colour tones a semitone away from a held melody note (root and 3rd are kept)."""
    keep = {ch.root, ch.third}
    return [p for p in ch.pcs() if p in keep or not any((p - m) % 12 in (1, 11) for m in mel_pcs)]


def arc(seg, t, depth=8.0):
    """Phrase dynamics: a gentle swell over each 4-bar phrase."""
    pos = ((t - seg['start']) % (4 * seg['bl'])) / (4 * seg['bl'])
    return depth * math.sin(math.pi * pos)


def place_melody(segs, target):
    """Octave shift that centres all melody notes of these segments on `target`."""
    ps = [p for s in segs for p, _, _ in s['melody']]
    if not ps:
        return 0
    mean = sum(ps) / len(ps)
    return 12 * round((target - mean) / 12)


def pedal(song, trk, s, e):
    song.cc(trk, s + 0.04, 64, 127)
    song.cc(trk, e - 0.03, 64, 0)


def chord_tone_below(ch_pcs, mel, lo_off=3, hi_off=9, n=1, prefer=()):
    cands = [p for p in range(mel - hi_off, mel - lo_off + 1) if p % 12 in ch_pcs]
    cands.sort(key=lambda p: (p % 12 not in prefer, -p))
    picked = []
    for p in cands:
        if all(abs(p - q) > 2 for q in picked):
            picked.append(p)
        if len(picked) == n:
            break
    return picked


# ----------------------------------------------------------------------------------------------- styles
class Style:
    style = 'classical'

    def __init__(self, song, segs, rng):
        self.song, self.segs, self.rng = song, segs, rng
        self.bl = song.bar_len

    def j(self, sd=0.008):
        return self.rng.gauss(0, sd)

    def v(self, base, sd=3.0):
        return base + self.rng.gauss(0, sd)

    def colour(self, seg, ch, s, d):
        long = {p % 12 for p in mel_during(seg, s, s + d, min_dur=0.75)}
        ch2 = enrich(ch, long, self.style)
        return ch2, safe_pcs(ch2, long | {p % 12 for p in mel_during(seg, s, s + 0.5)})


class JazzPiano(Style):
    """Solo jazz-ballad piano: RH melody with inner chord tones, LH root + shell. Straight, no swing, no runs."""
    style = 'jazz'

    def render(self, mel_target=72):
        s = self.song
        P = s.track('Piano', 0)
        prev_root, prev_shell = 43, None
        for seg in self.segs:
            o = seg['o']
            dens = o.get('density', 1)
            shift = 0
            for ch, cs, cd in seg['chords']:
                ch2, pcs = self.colour(seg, ch, cs, cd)
                top = mel_top(seg, cs, cs + cd) + shift if seg['melody'] else 76
                root = nearest(ch.bass, 34, 50, prev_root)
                prev_root = root
                shell_pcs = [p for p in pcs if p not in (ch2.root,)]
                shell_pcs = sorted(shell_pcs, key=lambda p: [ch2.third, (ch2.root + 10) % 12, (ch2.root + 11) % 12,
                                                             (ch2.root + 9) % 12, (ch2.root + 2) % 12].index(p)
                                   if p in [ch2.third, (ch2.root + 10) % 12, (ch2.root + 11) % 12,
                                            (ch2.root + 9) % 12, (ch2.root + 2) % 12] else 9)[:3 if dens else 2]
                shell = [p for p in voicing(shell_pcs, 50, min(66, top - 2), prev_shell) if p < top - 1]
                prev_shell = shell or prev_shell
                lv = self.v(52 if seg['kind'] != 'final' else 46)
                t0 = cs + abs(self.j())
                if seg['kind'] == 'final':  # rolled final chord
                    for i, p in enumerate([root] + shell):
                        s.n(P, cs + i * 0.09, cd, p, lv)
                    pedal(s, P, cs, cs + cd)
                    continue
                s.n(P, t0, cd, root, lv + 4)
                if dens >= 1 and cd >= self.bl and len(shell) > 1:
                    s.n(P, cs + 1 + abs(self.j()), cd - 1, shell[0], lv - 4)
                    for p in shell[1:]:
                        s.n(P, cs + 1 + abs(self.j()), cd - 1, p, lv - 6)
                else:
                    for p in shell:
                        s.n(P, t0 + 0.02, cd, p, lv - 4)
                pedal(s, P, cs, cs + cd)
            for p, ms, md in seg['melody']:
                p += shift
                vel = self.v(70 + arc(seg, ms) + o.get('mel_vel', 0))
                t0 = ms + self.j(0.006)
                s.n(P, t0, md, p, vel)
                chs = [c for c in seg['chords'] if c[1] <= ms + 1e-6 < c[1] + c[2]]
                if not chs:
                    continue
                ch, cs, cd = chs[0]
                ch2, pcs = self.colour(seg, ch, cs, cd)
                if o.get('octaves'):
                    s.n(P, t0, md, p - 12, vel - 14)
                if md >= 1 or abs(ms - cs) < 1e-6:
                    for q in chord_tone_below(pcs, p, 3, 9, 2 if md >= 2 else 1, prefer=(ch2.third, (ch2.root + 10) % 12)):
                        if not o.get('octaves') or q > p - 12:
                            s.n(P, t0 + 0.01, md, q, vel - 20)
                if dens >= 1 and md >= 2.5 and self.rng.random() < 0.6:  # quiet answer under a held note
                    ans = sorted(chord_tone_below(pcs, p, 4, 14, 3), reverse=True)
                    for i, q in enumerate(ans):
                        if ms + 1 + i < ms + md - 0.4:
                            s.n(P, ms + 1 + i + self.j(), 1.0, q, vel - 24)


class JazzTrio(Style):
    """Piano trio ballad: piano melody + rootless LH, upright bass in two, brushes. Straight eighths."""
    style = 'jazz'

    def render(self):
        s = self.song
        P, B, D = s.track('Piano', 0), s.track('Upright Bass', 32), s.track('Brushes', 0, drum=True)
        prev_lh, prev_b = None, 38
        for seg in self.segs:
            o = seg['o']
            dens, shift = o.get('density', 1), 0
            chords = seg['chords']
            for i, (ch, cs, cd) in enumerate(chords):
                ch2, pcs = self.colour(seg, ch, cs, cd)
                top = (mel_top(seg, cs, cs + cd) + shift) if seg['melody'] else 74
                order = [ch2.third, (ch2.root + 10) % 12, (ch2.root + 11) % 12, (ch2.root + 9) % 12,
                         (ch2.root + 2) % 12, (ch2.root + 7) % 12]
                lh_pcs = sorted([p for p in pcs if p != ch2.root], key=lambda p: order.index(p) if p in order else 9)[:4]
                lh = [p for p in voicing(lh_pcs, 50, min(68, top - 2), prev_lh) if p < top - 1]
                prev_lh = lh or prev_lh
                lv = self.v(50)
                if seg['kind'] == 'final':
                    for k, p in enumerate(lh):
                        s.n(P, cs + k * 0.08, cd, p, lv)
                    s.n(B, cs, cd, nearest(ch.bass, 28, 43, prev_b), 66)
                    pedal(s, P, cs, cs + cd)
                    continue
                for p in lh:
                    s.n(P, cs + abs(self.j()) + 0.01, min(cd, self.bl), p, lv)
                if dens >= 1 and cd >= self.bl and self.bl == 4:  # soft re-voice on beat 3
                    for p in lh:
                        s.n(P, cs + 2 + abs(self.j()), cd - 2, p, lv - 8)
                pedal(s, P, cs, cs + cd)
                # bass
                if o.get('bass', True):
                    root = nearest(ch.bass, 31, 45, prev_b)
                    prev_b = root
                    nxt = chords[i + 1][0] if i + 1 < len(chords) else ch
                    nroot = nearest(nxt.bass, 31, 45, root)
                    bv = self.v(74)
                    if dens == 0 or cd < 2:
                        s.n(B, cs, cd * 0.95, root, bv)
                    else:
                        half = 2.0 if self.bl == 4 else 2.0
                        s.n(B, cs, half * 0.95, root, bv)
                        rest = cd - half
                        if rest > 0:
                            fifth = nearest(ch.root + 7, 31, 48, root + 7)
                            if dens >= 2 and rest >= 2 and nroot != root:
                                s.n(B, cs + half, 0.95, fifth, bv - 6)
                                s.n(B, cs + cd - 1, 0.95, nroot + (1 if self.rng.random() < .5 else -1), bv - 8)
                            else:
                                s.n(B, cs + half, rest * 0.95, fifth if rest >= 1 else root, bv - 6)
            # brushes, bar by bar
            if o.get('drums', 1) and seg['kind'] != 'final':
                bar = seg['start']
                while bar < seg['end'] - 1e-6:
                    self.brush_bar(D, bar, dens)
                    bar += self.bl
            for p, ms, md in seg['melody']:
                p += shift
                vel = self.v(72 + arc(seg, ms) + o.get('mel_vel', 0))
                s.n(P, ms + self.j(0.006), md, p, vel)
                chs = [c for c in chords if c[1] <= ms + 1e-6 < c[1] + c[2]]
                if chs and md >= 1.5:
                    ch2, pcs = self.colour(seg, *chs[0])
                    for q in chord_tone_below(pcs, p, 3, 8, 1, prefer=(ch2.third,)):
                        s.n(P, ms + 0.01, md, q, vel - 22)

    def brush_bar(self, D, t, dens):
        s, bl = self.song, int(self.bl)
        backs = (1, 3) if bl == 4 else (1, 2)
        s.n(D, t, 0.2, KICK, self.v(26))
        for b in backs:
            s.n(D, t + b, 0.2, HAT_P, self.v(34))
            s.n(D, t + b + self.j(0.004), 0.2, SNARE, self.v(40 if dens else 32))
        if dens >= 1:
            for b in range(bl):
                if b not in backs:
                    s.n(D, t + b, 0.2, SNARE, self.v(22))
        if dens >= 2:
            for k in range(bl * 2):
                if k % 2:
                    s.n(D, t + k / 2, 0.2, SNARE, self.v(16, 2))


class Classical(Style):
    """Strings (vln1 vln2 vla vc cb) + harp + celesta. Melody moves between instruments pass by pass."""
    style = 'classical'

    def render(self, mel_target=76):
        s = self.song
        V1, V2, VA, VC, CB = (s.track(n, p) for n, p in
                              [('Violins 1', 48), ('Violins 2', 48), ('Violas', 48), ('Cellos', 42), ('Basses', 43)])
        H, CE = s.track('Harp', 46), s.track('Celesta', 8)
        prev = dict(v2=67, va=60, vc=48, up=None)
        for seg in self.segs:
            o = seg['o']
            mel_in, dens, shift = o.get('mel', 'vln1'), o.get('density', 1), 0
            harp = o.get('harp', 'arp')
            for ch, cs, cd in seg['chords']:
                pcs = ch.pcs()
                mel_lo = mel_top(seg, cs, cs + cd, 200) + shift
                sv = self.v(48 + (6 if dens >= 2 else 0) - (8 if mel_in == 'celesta' else 0))
                final = seg['kind'] == 'final'
                bass = nearest(ch.bass, 36, 55, prev['vc'])
                if mel_in == 'cello' and not final:
                    s.n(CB, cs, cd, nearest(ch.bass, 28, 43, bass - 12), sv)
                    above = {(m + 1) % 12 for m in mel_during(seg, cs, cs + cd, 0.75)}
                    up = voicing([q for q in pcs[:3] if q not in above] or pcs[:3], max(60, min(mel_lo + 3, 64)), 81, prev['up'])
                    prev['up'] = up
                    for trk, p in zip((VA, V2, V1), up):
                        s.n(trk, cs, cd, p, sv - 4)
                else:
                    prev['vc'] = bass
                    s.n(VC, cs, cd, bass, sv)
                    if dens >= 1 or final:
                        s.n(CB, cs, cd, bass - 12 if bass - 12 >= 28 else bass, sv - 6)
                    v2, va = self.inner(ch, prev, mel_lo if seg['melody'] else 79)
                    s.n(V2, cs, cd, v2, sv - 2)
                    s.n(VA, cs, cd, va, sv - 2)
                    if final or (not seg['melody'] and dens >= 1):
                        top = nearest(ch.root if final else ch.third or ch.root, 72, 86, 76)
                        s.n(V1, cs, cd, top, sv - 6)
                # harp
                hv = self.v(46)
                tones = self.harp_tones(ch, min(74, mel_lo - 2) if seg['melody'] else 76,
                                        {(m - 1) % 12 for m in mel_during(seg, cs, cs + cd, 0.75)})
                if final:
                    for k, p in enumerate(tones + [p + 12 for p in tones[1:3]]):
                        s.n(H, cs + k * 0.25, cd - k * 0.25, p, hv - 4)
                    s.n(CE, cs + 1.5, cd - 1.5, nearest(ch.root, 84, 96, 88), 50)
                    s.n(CE, cs + 2.0, cd - 2.0, nearest(ch.third or ch.root, 84, 96, 91), 46)
                elif harp == 'roll':
                    for k, p in enumerate(tones[:4]):
                        s.n(H, cs + k * 0.08, cd, p, hv)
                elif harp == 'arp':
                    n = int(round(cd * 2))
                    seq = tones + tones[-2:0:-1]
                    for k in range(n):
                        s.n(H, cs + k * 0.5 + abs(self.j(0.005)), min(1.5, cd - k * 0.5 + 0.1), seq[k % len(seq)], hv - (k % 2) * 4)
            for p, ms, md in seg['melody']:
                vel = self.v(70 + arc(seg, ms, 10) + o.get('mel_vel', 0))
                p += shift
                if mel_in in ('vln1', 'vln1_8va'):
                    s.n(V1, ms, md + 0.03, p, vel)
                    if mel_in == 'vln1_8va':
                        s.n(V2, ms, md + 0.03, p - 12, vel - 10)
                elif mel_in == 'cello':
                    s.n(VC, ms, md + 0.03, p - 12, vel + 2)
                elif mel_in == 'celesta':
                    s.n(CE, ms, md, p + 12, vel - 6)
                    if md >= 1.5:
                        s.n(V1, ms, md, p, vel - 30)  # a whisper of strings under the long celesta notes

    def inner(self, ch, prev, mel):
        pcs = ch.pcs()
        best, bc = None, 1e9
        for v2 in range(55, 78):
            if v2 % 12 not in pcs or v2 >= mel - 1:
                continue
            for va in range(48, 69):
                if va % 12 not in pcs or va >= v2 - 1:
                    continue
                cost = abs(v2 - prev['v2']) + abs(va - prev['va'])
                cost += 3 * (v2 % 12 == va % 12) + (v2 % 12 == mel % 12) + 2 * (v2 - va > 12)
                cost += 8 * ((mel - v2) % 12 == 1) + 8 * ((mel - va) % 12 == 1)
                cost += 6 * (ch.third is not None and ch.third not in (v2 % 12, va % 12, mel % 12))
                if cost < bc:
                    best, bc = (v2, va), cost
        if best is None:
            best = (nearest(ch.third or ch.root, 55, 72, prev['v2']), nearest(ch.root + 7, 48, 64, prev['va']))
        prev['v2'], prev['va'] = best
        return best

    def harp_tones(self, ch, top, avoid=()):
        b = nearest(ch.bass, 41, 52, 46)
        out, p = [b], b + 3
        while p <= top and len(out) < 6:
            if p % 12 in ch.pcs() and p % 12 not in avoid and p - out[-1] >= 3:
                out.append(p)
            p += 1
        return out


class Lounge(Style):
    """Chillhop: soft lo-fi beat, warm electric-piano 9th chords, round bass, melody on keys or bells, sleigh bells."""
    style = 'lounge'

    def render(self):
        s = self.song
        D, K, B = s.track('Drums', 0, drum=True), s.track('Keys (electric piano)', 4), s.track('Bass', 33)
        L, BE, SL = s.track('Lead (melody)', 4), s.track('Bells (glockenspiel or celesta)', 9), s.track('Sleigh Bells', 0, drum=True)
        prev_k, prev_b = None, 40
        for seg in self.segs:
            o = seg['o']
            dens, shift, mel_in = o.get('density', 1), 0, o.get('mel', 'keys')
            for ch, cs, cd in seg['chords']:
                ch2, pcs = self.colour(seg, ch, cs, cd)
                lead_lo = mel_top(seg, cs, cs + cd, 200) + shift + (12 if mel_in == 'bells' else 0)
                kp = [p for p in pcs if p != ch2.root] if len(pcs) > 3 else pcs
                kv = voicing(kp[:4], 52, min(72, lead_lo - 2), prev_k)
                prev_k = kv
                vel = self.v(58)
                final = seg['kind'] == 'final'
                hits = [(0, cd)] if (dens == 0 or final or cd < 2) else (
                    [(0, 1.5), (2.5, cd - 2.5)] if cd >= 4 else [(0, cd - 0.25)])
                for off, dur in hits:
                    for k, p in enumerate(sorted(kv)):
                        s.n(K, cs + off + 0.02 + k * 0.012, dur, p, vel - (6 if off else 0))
                if o.get('bass', True):
                    r = nearest(ch.bass, 33, 47, prev_b)
                    prev_b = r
                    if final or dens == 0 or cd < 4:
                        s.n(B, cs, min(cd, 3.5) * 0.95, r, self.v(80))
                    else:
                        s.n(B, cs, 1.4, r, self.v(84))
                        s.n(B, cs + 2.5, 0.45, r + 12 if r + 12 <= 52 else r, self.v(66))
                        s.n(B, cs + 3, 0.9, nearest(ch.root + 7, 33, 50, r + 7), self.v(72))
            if seg['kind'] != 'final':
                bar, k = seg['start'], 0
                while bar < seg['end'] - 1e-6:
                    if o.get('drums', 2):
                        self.drum_bar(D, bar, o.get('drums', 2), k)
                    if o.get('sleigh'):
                        for e in range(8):
                            s.n(SL, bar + e * 0.5 + (0.03 if e % 2 else 0), 0.2, SLEIGH, self.v(52 if e % 2 == 0 else 34))
                    bar, k = bar + self.bl, k + 1
            for p, ms, md in seg['melody']:
                p += shift
                vel = self.v(70 + arc(seg, ms, 6))
                if mel_in == 'keys':
                    s.n(L, ms + 0.015, md, p, vel)
                elif mel_in == 'bells':
                    s.n(BE, ms + 0.01, md, p + 12, vel - 8)
                elif mel_in == 'both':
                    s.n(L, ms + 0.015, md, p, vel - 4)
                    s.n(BE, ms + 0.01, md, p + 12, vel - 16)

    def drum_bar(self, D, t, level, k):
        s = self.song
        sw = 0.04  # lazy offbeat
        for e in range(8):
            if level >= 1:
                s.n(D, t + e * 0.5 + (sw if e % 2 else 0), 0.1, HAT_C, self.v(50 if e % 2 == 0 else 34))
        if level == 1:
            s.n(D, t + 1, 0.1, RIM, self.v(60))
            s.n(D, t + 3, 0.1, RIM, self.v(60))
            return
        s.n(D, t, 0.1, KICK, self.v(92))
        s.n(D, t + 1.5 + sw, 0.1, KICK, self.v(70))
        if k % 2 == 1:
            s.n(D, t + 2.75, 0.1, KICK, self.v(62))
        s.n(D, t + 1, 0.1, SNARE, self.v(78))
        s.n(D, t + 3, 0.1, SNARE, self.v(80))
        if k % 4 == 3:
            s.n(D, t + 3.5 + sw, 0.1, HAT_O, self.v(42))
            s.n(D, t + 3.75, 0.1, SNARE, self.v(30))


class AcousticGuitar(Style):
    """Fingerpicked nylon guitar: thumb bass + inner picking, melody on top (separate tracks for mixing)."""
    style = 'acoustic'

    def render(self):
        s = self.song
        M, G = s.track('Guitar (melody)', 24), s.track('Guitar (picking)', 24)
        prev_mid, prev_b = None, 45
        for seg in self.segs:
            o = seg['o']
            dens, shift = o.get('density', 1), 0
            for ch, cs, cd in seg['chords']:
                pcs = ch.pcs()
                if o.get('add9') and ch.qual == '' and not any((p - (ch.root + 2)) % 12 in (1, 11)
                                                              for p in [q % 12 for q in mel_during(seg, cs, cs + cd)]):
                    pcs = pcs + [(ch.root + 2) % 12]
                b = nearest(ch.bass, 40, 52, prev_b)
                prev_b = b
                alt = nearest(ch.root + 7, 43, 55, b + 7)
                final = seg['kind'] == 'final'
                if final:
                    for k, p in enumerate([b, alt] + voicing(pcs, 55, 69, prev_mid)):
                        s.n(G, cs + k * 0.11, cd, p, self.v(52))
                    continue
                slots = int(round(cd * 2))
                for k in range(slots):
                    t = cs + k * 0.5
                    beat_in_bar = ((t - seg['start']) % self.bl)
                    if dens == 0 and k % 2:
                        continue
                    top = mel_top(seg, t, t + 0.5, 200) + shift
                    mids = [p for p in voicing([p for p in pcs if p != ch.bass] or pcs, 52, min(67, top - 3), prev_mid)]
                    prev_mid = mids or prev_mid
                    if k == 0 or abs(beat_in_bar) < 1e-6:
                        p, v = b, 56
                    elif self.bl == 4 and abs(beat_in_bar - 2) < 1e-6:
                        p, v = alt, 50
                    else:
                        if not mids:
                            continue
                        idx = [0, 1, 2, 1, 2, 1, 2, 1][k % 8] if len(mids) > 2 else [0, 1][k % 2]
                        p, v = mids[min(idx, len(mids) - 1)], 40 + (4 if k % 2 == 0 else 0)
                    ring = min(cs + cd - t, 1.5 if p >= 52 else 2.0)
                    s.n(G, t + abs(self.j(0.01)), ring, p, self.v(v))
            for p, ms, md in seg['melody']:
                p += shift
                vel = self.v(72 + arc(seg, ms, 8) + o.get('mel_vel', 0))
                s.n(M, ms + self.j(0.008), md + 0.15, p, vel)
                if o.get('thirds') and md >= 1.5:
                    chs = [c for c in seg['chords'] if c[1] <= ms + 1e-6 < c[1] + c[2]]
                    if chs:
                        for q in chord_tone_below(chs[0][0].pcs(), p, 3, 9, 1):
                            s.n(M, ms + 0.02, md, q, vel - 18)


class AcousticPiano(Style):
    """Peaceful solo piano: LH broken chords (root-5th-10th), RH melody with a soft 3rd/6th on long notes."""
    style = 'acoustic'

    def render(self):
        s = self.song
        P = s.track('Piano', 0)
        prev_r = 43
        for seg in self.segs:
            o = seg['o']
            dens, shift = o.get('density', 1), 0
            for ch, cs, cd in seg['chords']:
                r = nearest(ch.bass, 36, 50, prev_r)
                prev_r = r
                third = (3 if ch.minor else 4) if ch.third is not None else 7
                root_above = nearest(ch.root, r, r + 11, r)
                fig = [r, root_above + 7, root_above + 12 + third]
                if seg['kind'] == 'final':
                    for k, p in enumerate(fig + [root_above + 19]):
                        s.n(P, cs + k * 0.12, cd, p, self.v(46))
                    pedal(s, P, cs, cs + cd)
                    continue
                top = mel_top(seg, cs, cs + cd, 200) + shift
                fig = [p for p in fig if p < top - 2] or fig[:1]
                step = 0.5 if dens >= 1 else 1.0
                pattern = [0, 1, 2, 1] if len(fig) == 3 else [0, 1]
                k, t = 0, cs
                while t < cs + cd - 1e-6:
                    p = fig[pattern[k % len(pattern)]] if k else fig[0]
                    s.n(P, t + abs(self.j()), cs + cd - t, p, self.v(50 if k == 0 else 42))
                    k, t = k + 1, t + step
                pedal(s, P, cs, cs + cd)
            for p, ms, md in seg['melody']:
                p += shift
                vel = self.v(68 + arc(seg, ms, 8))
                s.n(P, ms + self.j(0.006), md, p, vel)
                if md >= 1.5:
                    chs = [c for c in seg['chords'] if c[1] <= ms + 1e-6 < c[1] + c[2]]
                    if chs:
                        for q in chord_tone_below(chs[0][0].pcs(), p, 3, 9, 1, prefer=(chs[0][0].third,)):
                            s.n(P, ms + 0.01, md, q, vel - 20)


# ----------------------------------------------------------------------------------------------- pilots
def with_chords(tune, chords):
    t = tune.transposed(0)
    t.chords = parse_chords(chords, tune.bar_len, tune.n_bars, tune.pickup, tune.name)
    return t


def key_shift(tune, key):
    src = tune.key.rstrip('m')
    dst = key.rstrip('m')
    d = (NAMES.index(dst if dst in NAMES else {'C#': 'Db', 'D#': 'Eb', 'G#': 'Ab', 'A#': 'Bb'}[dst]) -
         NAMES.index(src if src in NAMES else {'C#': 'Db', 'D#': 'Eb', 'G#': 'Ab', 'A#': 'Bb'}[src])) % 12
    return d - 12 if d > 6 else d


JB_LOUNGE = ('Cmaj9 | Cmaj9:2 Am9:2 | Em7:2 Am9:2 | Dm9:2 G13:2 | Fmaj9 | Fmaj9:1 Em7:1 Am9:2 | D9 | Dm9:2 G13:2 | '
             'Cmaj9 | Cmaj9:2 Am9:2 | Em7:2 Am9:2 | Dm9:2 G13:2 | Fmaj9 | Fmaj9:1 Em7:1 Am9:2 | Dm9:2 G13:2 | Cmaj9')

PILOTS = {
    # ---------------------------------------------------------------- Christmas Jazz
    'J1': dict(playlist='Christmas Jazz', file='Silent Night - jazz solo piano', tune='silent-night', key='Bb',
               tempo=62, style=JazzPiano, target=72,
               form=lambda f: f.intro(4, density=0).tune(density=0).tune(density=1, mel_shift=12, octaves=True)
               .interlude(13, 16, density=1).outro(13, hold_bars=2, density=0)),
    'J2': dict(playlist='Christmas Jazz', file='O Christmas Tree - jazz piano trio', tune='o-christmas-tree', key='F',
               tempo=66, style=JazzTrio, target=72,
               form=lambda f: f.intro(4, density=0, drums=0).tune(density=0).tune(density=1).tune(density=2, mel_shift=12)
               .interlude(5, 8, density=1).tune(density=1).outro(9, hold_bars=2, density=0)),
    'J3': dict(playlist='Christmas Jazz', file='O Come All Ye Faithful - jazz piano trio', tune='o-come-all-ye-faithful',
               key='F', tempo=68, style=JazzTrio, target=72,
               form=lambda f: f.intro(4, density=0, drums=0).tune(density=0, drums=0).tune(density=1)
               .interlude(9, 12, density=1).tune(13, density=2, lead=1).outro(17, hold_bars=2, density=0)),
    # ---------------------------------------------------------------- Christmas Classical
    'C1': dict(playlist='Christmas Classical', file='Away in a Manger - strings harp celesta', tune='away-in-a-manger-uk',
               key='F', tempo=66, style=Classical, target=76,
               form=lambda f: f.intro(4, harp='arp', density=0).tune(mel='vln1', density=0).tune(mel='celesta', density=1)
               .tune(mel='cello', density=1).tune(mel='vln1_8va', density=2).outro(13, hold_bars=2, mel='vln1')),
    'C2': dict(playlist='Christmas Classical', file='Hark the Herald - strings and harp', tune='hark-the-herald',
               key='F', tempo=60, style=Classical, target=76,
               form=lambda f: f.intro(2, harp='roll', density=0).tune(mel='vln1', harp='roll', density=0)
               .tune(mel='cello', harp='arp', density=1).interlude(17, 20, harp='arp', density=1)
               .tune(13, mel='vln1_8va', density=2, lead=0).outro(17, hold_bars=2, mel='vln1')),
    'C3': dict(playlist='Christmas Classical', file='Joy to the World - gentle strings', tune='joy-to-the-world',
               key='D', tempo=64, style=Classical, target=76,
               form=lambda f: f.intro(4, harp='arp', density=0).tune(mel='celesta', density=0).tune(mel='vln1', density=1)
               .tune(mel='cello', density=1).interlude(17, 20, density=1).tune(mel='vln1_8va', density=2)
               .outro(17, hold_bars=2, mel='vln1')),
    # ---------------------------------------------------------------- Christmas Lounge
    'L1': dict(playlist='Christmas Lounge', file='Jingle Bells - chillhop', tune='jingle-bells', key='F', tempo=80,
               style=Lounge, target=72, chords=JB_LOUNGE,
               form=lambda f: f.intro(4, density=0, drums=1).tune(mel='keys', drums=2).tune(mel='bells', drums=2, sleigh=True)
               .interlude(1, 8, drums=1, density=0).tune(mel='both', drums=2, sleigh=True).outro(13, hold_bars=2, mel='keys', drums=1)),
    'L2': dict(playlist='Christmas Lounge', file='Deck the Halls - chillhop (melody from memory)', tune='deck-the-halls',
               key='F', tempo=82, style=Lounge, target=70,
               form=lambda f: f.intro(4, density=0, drums=1).tune(mel='keys', drums=2).tune(mel='bells', drums=2, sleigh=True)
               .interlude(9, 12, drums=1, density=0).tune(mel='both', drums=2).outro(13, hold_bars=2, mel='keys', drums=1)),
    'L3': dict(playlist='Christmas Lounge', file='Carol of the Bells - chillhop', tune='carol-of-the-bells', key='Gm',
               tempo=84, style=Lounge, target=70,
               form=lambda f: f.intro(4, density=0, drums=1, from_bar=1).tune(mel='bells', drums=2)
               .tune(mel='keys', drums=2, sleigh=True).outro(21, hold_bars=2, mel='bells', drums=1)),
    # ---------------------------------------------------------------- Christmas Acoustic
    'A1': dict(playlist='Christmas Acoustic', file='Silent Night - solo piano', tune='silent-night', key='C',
               tempo=62, style=AcousticPiano, target=72,
               form=lambda f: f.intro(4, density=0).tune(density=0).tune(density=1)
               .interlude(17, 20, density=0).outro(13, hold_bars=2, density=0)),
    'A2': dict(playlist='Christmas Acoustic', file='Away in a Manger - solo piano', tune='away-in-a-manger-us', key='F',
               tempo=63, style=AcousticPiano, target=72,
               form=lambda f: f.intro(4, density=0).tune(density=0).tune(density=1).tune(density=1, mel_shift=12)
               .outro(13, hold_bars=2, density=0)),
    'A3': dict(playlist='Christmas Acoustic', file='God Rest Ye Merry Gentlemen - solo piano', tune='god-rest-ye',
               key='Em', tempo=66, style=AcousticPiano, target=72,
               form=lambda f: f.intro(4, density=0).tune(density=0).tune(density=1)
               .interlude(9, 12, density=0).outro(15, hold_bars=2, density=0)),
}


def build(pid, preview=True):
    cfg = PILOTS[pid]
    tune = TUNES[cfg['tune']]
    if cfg.get('chords'):
        tune = with_chords(tune, cfg['chords'])
    tune = tune.transposed(key_shift(tune, cfg['key']))
    tune.key = cfg['key']
    form = cfg['form'](Form(tune))
    segs = form.segs
    shift = place_melody(segs, cfg['target'])
    for sg in segs:
        sg['melody'] = [(p + shift + sg['o'].get('mel_shift', 0), s, d) for p, s, d in sg['melody']]
    allmel = sorted(n for sg in segs for n in sg['melody'])
    for sg in segs:
        sg['allmel'] = allmel
    song = Song(f"{tune.title} ({cfg['key']}, {cfg['tempo']} BPM)", cfg['tempo'], tune.bar_len, cfg['key'])
    cfg['style'](song, segs, random.Random(pid)).render()
    # keep everything that starts before 0 (pickup into bar 1 of an intro-less form) out
    folder = os.path.join(OUT, cfg['playlist'], f"{pid} {cfg['file']}")
    os.makedirs(os.path.join(folder, 'parts'), exist_ok=True)
    base = os.path.join(folder, cfg['file'])
    song.write(base + '.mid')
    for name in song.tracks:
        song.write(os.path.join(folder, 'parts', re.sub(r'[^\w\- ()]', '', name) + '.mid'), only=name)
    secs = song.end * 60 / cfg['tempo']
    if preview:
        wav = base + '.wav'
        subprocess.run(['fluidsynth', '-ni', '-q', '-g', '0.5', '-r', '44100', '-F', wav, SF2, base + '.mid'],
                       check=True, capture_output=True)
        subprocess.run(['ffmpeg', '-v', 'quiet', '-y', '-i', wav, '-af',
                        'aecho=0.8:0.6:70|130:0.25|0.15,loudnorm=I=-18:TP=-2', '-ab', '160k',
                        base + ' - NOTE CHECK preview (not the final sound).mp3'], check=True)
        os.remove(wav)
    return folder, secs, song, segs


def clash_report(song, segs):
    """Held melody notes (>= 1 beat) that rub a semitone against an accompaniment note sounding with them."""
    others = [(s, s + d, p) for t in song.tracks.values() if not t['drum'] for s, d, p, _ in t['notes']]
    bad, total = [], 0
    for sg in segs:
        off = {'celesta': 12, 'bells': 12, 'cello': -12}.get(sg['o'].get('mel'), 0)
        for p, ms, md in sg['melody']:
            if md < 1:
                continue
            total += 1
            p += off
            harsh = lambda q: (p - q) in (1, 13) or (q > p and (q - p) % 12 in (1, 11))
            hits = {q for s, e, q in others if s < ms + 0.25 and e > ms + 0.5 and q != p and harsh(q)}
            if hits:
                bad.append(f"{ms:.1f}:{NAMES[p % 12]} vs {'/'.join(NAMES[q % 12] for q in hits)}")
    return bad, total


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    preview = '--no-preview' not in sys.argv
    for pid in args or PILOTS:
        folder, secs, song, segs = build(pid, preview)
        bad, total = clash_report(song, segs)
        print(f'{pid}: {int(secs // 60)}:{int(secs % 60):02d}  {len(song.tracks)} tracks  clashes {len(bad)}/{total} {bad[:6]}')
