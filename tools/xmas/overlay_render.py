#!/usr/bin/env python3
"""Approach B overlay pilot: render warm Christmas layers for the Mureka-side mixer (tools/audio/overlay.py there).

All overlays of one tempo go into ONE Ableton set, laid end to end with gaps, so Live exports once per tempo;
`slice` then cuts the export into one WAV per overlay at known times.
Names follow the mixer's parser: `_<NN>bpm` = loop, `_<Tonic>maj` / `_<Tonic>min` = key guard, `_free_` = one-shot.
Instruments follow Norbert's taste: warm hand bells / vibraphone, EQ-softened sleigh bells, no bright glockenspiel.
NEVER upload these renders to Mureka or any AI service (Festive Bells / Spitfire EULAs) - local mixing only.

Usage: python3 tools/xmas/overlay_render.py sets     -> writes the 3 .als sets
       python3 tools/xmas/overlay_render.py slice    -> cuts the exported WAVs into overlays/<name>.wav
"""
import json, math, os, random, subprocess, sys
import v2
from overlays import phrase, octave_to, KEYS, MINOR_OF
from als import write_set

OUT = os.path.expanduser('~/Downloads/Christmas Ableton/overlays')
SETS = os.path.join(OUT, '_sets')
GAP_BARS = 3  # silence after each item (bell tails ring into it; cut before the next item)


def notes_for(tune, bars, key, target, trim=0.0):
    ns, bl, length = phrase(tune, bars[0], bars[1], key, trim=trim)
    return octave_to(ns, target), bl, length


def build(tempo, bar_len, items, title):
    """items: [(name, part, [(start, dur, pitch, vel)], length_beats, kind)] -> Song2 + manifest of times."""
    song = v2.Song2(title, tempo, bar_len, 'C')
    tracks = {}
    t, manifest = 0.0, []
    for name, part, notes, length, kind in items:
        if part not in tracks:
            tracks[part] = song.track(part, 0, drum=(part == 'Sleigh Bells'))
        for s, d, p, v in notes:
            song.n(tracks[part], t + s, d, p, v, 'bell')
        sec = 60.0 / tempo
        manifest.append(dict(name=name, kind=kind, start=t * sec, length=length * sec,
                             next=(t + length + GAP_BARS * bar_len) * sec))
        t += length + GAP_BARS * bar_len
    song.tempo_events = [(0, tempo)]
    return song, manifest


def sleigh(bars, sparse, rng):
    out = []
    for b in range(bars):
        for e in range(8):
            if sparse and e not in (2, 6):
                continue
            accent = e % 2 == 0
            v = (66 if b % 4 == 0 and e == 0 else 60 if accent else 44) + rng.gauss(0, 2)
            out.append((b * 4 + e * 0.5 + (0.0 if accent else 0.02), 0.4, 60, int(v)))
    return out


def phrase_items(tempo, rng):
    items = []
    for k in KEYS:  # Cmaj, Fmaj
        for part, motif, tune, bars, target, minor in [
                ('Hand Bells', 'jinglebells_handbells', 'jingle-bells', (1, 4), 72, False),
                ('Vibraphone', 'jinglebells_vibes', 'jingle-bells', (1, 4), 72, False),
                ('Hand Bells', 'carolbells_handbells', 'carol-of-the-bells', (1, 4), 70, True)]:
            key = MINOR_OF[k] if minor else KEYS[k]
            ns, bl, length = notes_for(tune, bars, key, target)
            label = key.replace('m', 'min') if minor else k
            ev = [(s, d * 0.95, p, int(62 + rng.gauss(0, 3) - (5 if i % 2 else 0))) for i, (p, s, d) in enumerate(ns)]
            items.append((f'{motif}_{tempo}bpm_{label}', part, ev, length, 'loop'))
    return items


def sets():
    rng = random.Random('overlays-v1')
    os.makedirs(SETS, exist_ok=True)
    allman = {}
    # 80 BPM (Lounge bases measured 80-90): sleigh loops + carol hooks
    items = [('sleighbells_80bpm', 'Sleigh Bells', sleigh(8, False, rng), 32, 'loop'),
             ('sleighbells_sparse_80bpm', 'Sleigh Bells', sleigh(8, True, rng), 32, 'loop')] + phrase_items(80, rng)
    # 64 BPM (Jazz bases): sparse sleigh + hymn phrases on hand bells / vibes
    items64 = [('sleighbells_sparse_64bpm', 'Sleigh Bells', sleigh(8, True, rng), 32, 'loop')]
    for k in KEYS:
        for part, motif, tune, bars, target in [('Vibraphone', 'jinglebells_vibes', 'jingle-bells', (1, 4), 72),
                                                ('Hand Bells', 'ocome_handbells', 'o-come-all-ye-faithful', (13, 20), 72),
                                                ('Hand Bells', 'hark_handbells', 'hark-the-herald', (1, 4), 72)]:
            ns, bl, length = notes_for(tune, bars, KEYS[k], target)
            ev = [(s, d * 0.95, p, int(60 + rng.gauss(0, 3))) for p, s, d in ns]
            items64.append((f'{motif}_64bpm_{k}', part, ev, length, 'loop'))
    # free time at 60 BPM (1 beat = 1 s): Classical / Acoustic bases have no steady beat
    free = []
    for k in KEYS:
        for part, motif, tune, bars, target, minor, slow, trim in [
                ('Hand Bells', 'silentnight_handbells', 'silent-night', (1, 8), 72, False, 1.3, 0.0),
                ('Hand Bells', 'joy_handbells', 'joy-to-the-world', (1, 4), 74, False, 1.5, 0.5),
                ('Hand Bells', 'carolbells_handbells', 'carol-of-the-bells', (1, 2), 70, True, 1.4, 0.0),
                ('Vibraphone', 'silentnight_vibes', 'silent-night', (1, 8), 76, False, 1.3, 0.0)]:
            key = MINOR_OF[k] if minor else KEYS[k]
            ns, bl, length = notes_for(tune, bars, key, target, trim)
            ev, warp = [], 0.0
            for i, (p, s, d) in enumerate(ns):  # gentle rubato, broadening into the last notes, long ring
                warp += rng.gauss(0, 0.05)
                broaden = 1.35 if i >= len(ns) - 2 else 1.0
                ev.append((max(0.0, s * slow * broaden + warp), d * slow + (5.0 if i == len(ns) - 1 else 0.8), p,
                           int(58 + rng.gauss(0, 4))))
            label = key.replace('m', 'min') if minor else k
            free.append((f'{motif}_free_{label}', part, ev, max(e[0] + e[1] for e in ev) + 1, 'free'))
        root = 60 + {'Cmaj': 0, 'Fmaj': 5}[k]
        free.append((f'chimes_handbells_free_{k}', 'Hand Bells',
                     [(0, 6, root, 66), (0.04, 6, root + 7, 54), (3.0, 6, root + 12, 60), (6.0, 8, root + 4, 52)], 14, 'free'))
        free.append((f'bellswell_vibes_free_{k}', 'Vibraphone',
                     [(i * 0.22, 6 - i * 0.22, root + 12 + iv, 40 + i * 4) for i, iv in enumerate([0, 4, 7, 12, 16, 19])], 8, 'free'))
    for tag, tempo, bar_len, its in [('overlays_80bpm', 80, 4, items), ('overlays_64bpm', 64, 4, items64),
                                     ('overlays_free', 60, 4, free)]:
        song, man = build(tempo, bar_len, its, tag)
        write_set(song, os.path.join(SETS, tag + '.als'), reverb=(2000, 10))
        allman[tag] = man
        print(f'{tag}: {len(its)} overlays, {song.end:.0f} beats')
    json.dump(allman, open(os.path.join(SETS, 'manifest.json'), 'w'), indent=1)


def slice_(manifest='manifest.json'):
    man = json.load(open(os.path.join(SETS, manifest)))
    catalog = []
    for tag, items in man.items():
        src = os.path.expanduser(f'~/Downloads/Christmas Ableton/_renders/{tag}.wav')
        if not os.path.exists(src):
            print('missing export', src)
            continue
        for it in items:
            out = os.path.join(OUT, it['name'] + '.wav')
            bar = 4 * 60.0 / it.get('tempo', 60)
            if it['kind'] == 'loop':  # exact musical length so the mixer can loop it; tiny fades against clicks
                dur, pad = it['length'], None
                af = f'afade=t=in:d=0.005,afade=t=out:st={dur - 0.01:.3f}:d=0.01'
            elif it['kind'] == 'phrase':  # hook + its natural ring, then silence to exactly 16 bars
                pad = it.get('pad_bars', 16) * bar
                dur = min(pad, it['next'] - it['start'] - 0.15)
                af = f'afade=t=in:d=0.005,afade=t=out:st={max(0.0, dur - 0.4):.3f}:d=0.4,apad=whole_dur={pad:.4f}'
            else:  # free one-shot: natural ring up to the next item, fade the very end
                dur, pad = it['next'] - it['start'] - 0.15, None
                af = f'afade=t=out:st={max(0.0, dur - 1.0):.3f}:d=1.0'
            cmd = ['ffmpeg', '-v', 'quiet', '-y', '-ss', f"{it['start']:.4f}", '-t', f'{dur:.4f}', '-i', src, '-af', af]
            if pad:
                cmd += ['-t', f'{pad:.4f}']
            subprocess.run(cmd + ['-ar', '44100', '-c:a', 'pcm_s24le', out + '.tmp.wav'], check=True)
            # peak-normalise to -3 dBFS so the mixer's overlay level means the same for every file
            r = subprocess.run(['ffmpeg', '-i', out + '.tmp.wav', '-af', 'volumedetect', '-f', 'null', '-'],
                               capture_output=True, text=True).stderr
            peak = float(r.split('max_volume:')[1].split('dB')[0])
            subprocess.run(['ffmpeg', '-v', 'quiet', '-y', '-i', out + '.tmp.wav', '-af', f'volume={-3.0 - peak:.2f}dB',
                            '-c:a', 'pcm_s24le', out], check=True)
            os.remove(out + '.tmp.wav')
            parts = it['name'].split('_')
            catalog.append(dict(file=it['name'] + '.wav', kind=it['kind'], tempo=it.get('tempo') if it['kind'] != 'free' else None,
                                key=next((x for x in parts if x.endswith(('maj', 'min'))), None),
                                carol=parts[0] if not parts[0].startswith(('sleighbells', 'chimes', 'bellswell', 'harp', 'sparkle', 'shimmer')) else None,
                                motif='_'.join(parts[:3]) if parts[1] == 'flip' else ('_'.join(parts[:2]) if parts[1] in ('a', 'b', 'refrain', 'verse', 'ostinato', 'uk', 'us', 'frag', 'twinkle', 'fall', 'call', 'single', 'descend', 'toll', 'tonic', 'subdominant', 'eighths', 'sparse', 'build', 'fade') else parts[0]),
                                instrument=it.get('instrument'), seconds=round(pad or dur, 2), peak_db_before_norm=round(peak, 1)))
            print(f"{it['name']:44} {it['kind']:6} {pad or dur:6.2f}s")
    if manifest != 'manifest.json':
        path = os.path.join(OUT, 'overlay_catalog.json')
        if manifest != 'library_manifest.json' and os.path.exists(path):  # add to the existing catalog
            names = {c['file'] for c in catalog}
            catalog = [c for c in json.load(open(path)) if c['file'] not in names] + catalog
        json.dump(catalog, open(path, 'w'), indent=1)
        print(len(catalog), 'files catalogued ->', os.path.join(OUT, 'overlay_catalog.json'))


# ------------------------------------------------------------------------------------------- full library (v2)
SYNC_MAJOR = [('jinglebells_a', 'jingle-bells', (1, 4), 0.0), ('jinglebells_b', 'jingle-bells', (5, 8), 0.0),
              ('joy', 'joy-to-the-world', (1, 8), 0.5), ('hark_a', 'hark-the-herald', (1, 4), 0.0),
              ('hark_b', 'hark-the-herald', (9, 12), 0.0), ('ocome_refrain', 'o-come-all-ye-faithful', (13, 20), 0.0),
              ('ocome_verse', 'o-come-all-ye-faithful', (1, 4), 1.0)]
SYNC_MINOR = [('godrest', 'god-rest-ye', (1, 4), 1.0), ('carolbells_ostinato', 'carol-of-the-bells', (1, 4), 0.0),
              ('carolbells_b', 'carol-of-the-bells', (13, 16), 0.0)]
FREE = [('silentnight_a', 'silent-night', (1, 8), 0.0, False), ('silentnight_b', 'silent-night', (17, 24), 0.0, False),
        ('ochristmastree', 'o-christmas-tree', (1, 4), 0.5, False), ('awayinamanger_uk', 'away-in-a-manger-uk', (1, 8), 1.0, False),
        ('awayinamanger_us', 'away-in-a-manger-us', (1, 8), 1.0, False), ('joy', 'joy-to-the-world', (1, 8), 0.5, False),
        ('ocome', 'o-come-all-ye-faithful', (13, 20), 0.0, False), ('godrest', 'god-rest-ye', (1, 4), 1.0, True)]
INSTR = {'handbells': ('Hand Bells', 72), 'vibes': ('Vibraphone', 67)}  # vibes kept low: bright vibes stuck out of mixes


def _label(k, minor):
    return MINOR_OF[k].replace('m', 'min') if minor else k


def sync_item(motif, tune, bars, trim, k, minor, inst, tempo, rng):
    part, target = INSTR[inst]
    key = MINOR_OF[k] if minor else KEYS[k]
    ns, bl, length = notes_for(tune, bars, key, target, trim)
    n = len(ns)
    ev = []
    for i, (p, s, d) in enumerate(ns):  # phrase arch + slight emphasis on longer notes
        arch = 6 * math.sin(math.pi * (i + 0.5) / n)
        ev.append((s, d * 0.95, p, int(56 + arch + (3 if d >= 1 else 0) + rng.gauss(0, 2.5))))
    return (f'{motif}_{inst}_{tempo}bpm_{_label(k, minor)}', part, ev, length, 'phrase')


def free_item(motif, tune, bars, trim, k, minor, inst, rng, slow=1.3):
    part, target = INSTR[inst]
    key = MINOR_OF[k] if minor else KEYS[k]
    ns, bl, length = notes_for(tune, bars, key, target, trim)
    ev, warp, n = [], 0.0, len(ns)
    for i, (p, s, d) in enumerate(ns):
        warp += rng.gauss(0, 0.05)
        broaden = 1.35 if i >= n - 2 else 1.0
        arch = 7 * math.sin(math.pi * (i + 0.5) / n)
        ev.append((max(0.0, s * slow * broaden + warp), d * slow + (5.0 if i == n - 1 else 0.8), p,
                   int(54 + arch + rng.gauss(0, 3))))
    return (f'{motif}_{inst}_free_{_label(k, minor)}', part, ev, max(e[0] + e[1] for e in ev) + 1, 'free')


def sleigh_pattern(bars, pattern, rng):
    out = []
    for b in range(bars):
        for e in range(8):
            t = b * 4 + e * 0.5
            accent = e % 2 == 0
            if pattern == 'sparse' and e not in (2, 6):
                continue
            if pattern == 'quarters' and not accent:
                continue
            v = (66 if b % 4 == 0 and e == 0 else 60 if accent else 44) + rng.gauss(0, 2)
            out.append((t + (0.0 if accent else 0.02), 0.4, 60, int(v)))
    return out


def library():
    rng = random.Random('overlay-library-v2')
    os.makedirs(SETS, exist_ok=True)
    groups = {}
    for tempo in (64, 80, 90):
        items = [(f'sleighbells_{pat}_{tempo}bpm' if pat != 'eighths' else f'sleighbells_{tempo}bpm', 'Sleigh Bells',
                  sleigh_pattern(8, pat, rng), 32, 'loop') for pat in ('eighths', 'sparse', 'quarters')]
        if tempo in (64, 80):
            for k in KEYS:
                for inst in INSTR:
                    for motif, tune, bars, trim in SYNC_MAJOR:
                        items.append(sync_item(motif, tune, bars, trim, k, False, inst, tempo, rng))
                    for motif, tune, bars, trim in SYNC_MINOR:
                        items.append(sync_item(motif, tune, bars, trim, k, True, inst, tempo, rng))
        groups[f'library_{tempo}bpm'] = (tempo, items)
    free = []
    for k in KEYS:
        root = 60 + {'Cmaj': 0, 'Fmaj': 5}[k]
        for inst in INSTR:
            for motif, tune, bars, trim, minor in FREE:
                free.append(free_item(motif, tune, bars, trim, k, minor, inst, rng))
            part = INSTR[inst][0]
            free.append((f'chimes_{inst}_free_{k}', part, [(0, 6, root, 64), (0.04, 6, root + 7, 52), (3.0, 6, root + 12, 58),
                                                           (6.0, 8, root + 4, 50)], 14, 'free'))
            free.append((f'bellswell_{inst}_free_{k}', part, [(i * 0.22, 6 - i * 0.22, root + 12 + iv, 40 + i * 4)
                                                              for i, iv in enumerate([0, 4, 7, 12, 16, 19])], 8, 'free'))
        free.append((f'harpsweep_harp_free_{k}', 'Harp', [(i * 0.09, 5 - i * 0.09, p, 44 + i)
                     for i, p in enumerate([q for q in range(root - 12, root + 26) if q % 12 in {root % 12, (root + 4) % 12, (root + 7) % 12, (root + 11) % 12}])], 7, 'free'))
    groups['library_free'] = (60, free)
    allman = {}
    for tag, (tempo, its) in groups.items():
        song, man = build(tempo, 4, its, tag)
        write_set(song, os.path.join(SETS, tag + '.als'), reverb=(2600, 18))  # longer, more distant hall: blends
        for m, it in zip(man, its):
            m['instrument'], m['tempo'] = it[1], tempo
        allman[tag] = man
        print(f'{tag}: {len(its)} overlays, {song.end:.0f} beats = {song.end * 60 / tempo / 60:.1f} min')
    json.dump(allman, open(os.path.join(SETS, 'library_manifest.json'), 'w'), indent=1)
    print('total', sum(len(v) for v in allman.values()))


# ------------------------------------------------------------------------------------------- variety expansion (v3)
# Norbert: layers fit smoothly but "sound the same at every track" -> more timbres, layer types and patterns.
INSTR.update({'handbellslow': ('Hand Bells', 63), 'piano': ('Piano Sparkle', 81), 'harp': ('Harp', 70),
              'tubular': ('Tubular Bells', 67), 'bowedvibes': ('Vibraphone Bowed', 67)})
FRAGS_MAJOR = [('jinglebells_frag', 'jingle-bells', (1, 2), 0.0), ('joy_frag', 'joy-to-the-world', (1, 4), 0.0),
               ('hark_frag', 'hark-the-herald', (1, 2), 0.0), ('ocome_frag', 'o-come-all-ye-faithful', (13, 14), 1.0)]
FRAGS_MINOR = [('godrest_frag', 'god-rest-ye', (1, 2), 1.0), ('carolbells_frag', 'carol-of-the-bells', (1, 2), 0.0)]
FLIPS = {'jinglebells_flip_a': [(s, p - 5, d) for s, p, d in [(0.5, 69, .5), (1.0, 69, .5), (1.5, 69, 1.25), (4.5, 69, .5),
                                (5.0, 69, .5), (5.5, 69, 1.25), (8.0, 69, .5), (8.5, 72, .5), (9.0, 65, .75), (9.75, 67, .25),
                                (10.0, 69, 2.0)]],
         'jinglebells_flip_b': [(s, p - 5, d) for s, p, d in [(0.5, 70, .5), (1.0, 70, .5), (1.5, 70, .75), (2.5, 70, .5),
                                (4.0, 70, .5), (4.5, 69, .5), (5.0, 69, .5), (5.5, 69, .25), (5.75, 69, .75), (8.5, 69, .5),
                                (9.0, 67, .5), (9.5, 67, .5), (10.0, 69, .5), (10.5, 67, 1.0), (12.0, 72, 2.5)]]}  # written in C
SPARKLE = {'twinkle': [(0, 0, .5), (.5, 1, .5), (1, 2, .5), (1.5, 3, .5), (2, 4, 2.0)],
           'fall': [(0, 4, .5), (.5, 3, .5), (1, 2, .5), (1.5, 1, .5), (2, 0, .5), (2.5, -1, .5), (3, 0, 1.5)],
           'call': [(0, 0, 1.0), (1, 3, 1.0), (4, 0, 1.0), (5, 3, 2.0)]}


def pent(key_label, deg, base):
    """Degree of the major pentatonic (fits almost any chord of the key) as a pitch near `base`."""
    root = {'Cmaj': 0, 'Fmaj': 5}[key_label]
    steps = [0, 2, 4, 7, 9]
    octv, i = divmod(deg, 5)
    p = root + steps[i] + 12 * octv
    return p + 12 * round((base - p) / 12)


def vel_arch(i, n, base, depth=6):
    return int(base + depth * math.sin(math.pi * (i + 0.5) / max(1, n)))


def variety():
    rng = random.Random('overlay-variety-v3')
    os.makedirs(SETS, exist_ok=True)
    groups = {64: [], 80: [], 'free': []}
    # A. sleigh-bell variety: other Festive sleigh bells (keys 61-65) x steady / sparse / build / fade
    for tempo in (64, 80):
        for bell in (61, 62, 64, 65):
            for pat in ('eighths', 'sparse', 'build', 'fade'):
                ev = []
                for b in range(8):
                    for e in range(8):
                        if pat == 'sparse' and e not in (2, 6):
                            continue
                        x = (b * 8 + e) / 63.0
                        base = 60 if e % 2 == 0 else 44
                        if pat == 'build':
                            base = int(26 + 44 * x) - (0 if e % 2 == 0 else 12)
                        elif pat == 'fade':
                            base = int(70 - 44 * x) - (0 if e % 2 == 0 else 12)
                        ev.append((b * 4 + e * 0.5 + (0 if e % 2 == 0 else 0.02), 0.4, bell, max(12, int(base + rng.gauss(0, 2)))))
                groups[tempo].append((f'sleighbells{bell - 59}_{pat}_{tempo}bpm', 'Sleigh Bells', ev, 32, 'loop'))
    # B. short 2-bar carol fragments + C. pentatonic sparkle figures, both tempos
    for tempo in (64, 80):
        for k in KEYS:
            for inst in ('handbellslow', 'vibes', 'piano'):
                part, target = INSTR[inst]
                for motif, tune, bars, trim in FRAGS_MAJOR + FRAGS_MINOR:
                    minor = (motif, tune, bars, trim) in FRAGS_MINOR
                    key = MINOR_OF[k] if minor else KEYS[k]
                    ns, bl, length = notes_for(tune, bars, key, target, trim)
                    ev = [(s, d * 0.95, p, vel_arch(i, len(ns), 50 if inst == 'piano' else 55) + int(rng.gauss(0, 2)))
                          for i, (p, s, d) in enumerate(ns)]
                    groups[tempo].append((f'{motif}_{inst}_{tempo}bpm_{_label(k, minor)}', part, ev, length, 'phrase'))
            for inst in ('vibes', 'handbells', 'harp'):
                part, target = INSTR[inst]
                for name, fig in SPARKLE.items():
                    ev = [(s, d, pent(k, deg, target + 5), vel_arch(i, len(fig), 50)) for i, (s, deg, d) in enumerate(fig)]
                    groups[tempo].append((f'sparkle_{name}_{inst}_{tempo}bpm_{k}', part, ev, 8, 'phrase8'))
    # D. chillhop flips of the Jingle Bells hook for Lounge (80 BPM)
    for k in KEYS:
        tr = {'Cmaj': 0, 'Fmaj': 5}[k]
        for inst in ('vibes', 'handbellslow', 'piano'):
            part, target = INSTR[inst]
            for motif, notes in FLIPS.items():
                mean = sum(p for _, p, _ in notes) / len(notes) + tr
                sh = 12 * round((target - mean) / 12)
                ev = [(s, d, p + tr + sh, vel_arch(i, len(notes), 54) + int(rng.gauss(0, 2))) for i, (s, p, d) in enumerate(notes)]
                groups[80].append((f'{motif}_{inst}_80bpm_{k}', part, ev, 16, 'phrase'))
    # E. free time (Classical / Acoustic): tubular chimes, bowed-vibes shimmer, harp, piano sparkle, low hand bells
    for k in KEYS:
        root = 60 + {'Cmaj': 0, 'Fmaj': 5}[k]
        tub = root if root <= 64 else root - 12 + 12  # tubular bells live around C4-F5
        peals = {'single': [(0, 8, tub, 58), (0.03, 8, tub + 7, 44), (4.5, 8, tub, 54), (9, 9, tub + 7, 50)],
                 'descend': [(0, 5, tub + 12, 56), (1.6, 5, tub + 7, 52), (3.2, 5, tub + 4, 50), (4.8, 8, tub, 56)],
                 'toll': [(i * 2.4, 4, tub + (7 if i % 2 else 0), 54 - i * 2) for i in range(6)]}
        for name, ev in peals.items():
            groups['free'].append((f'chimes_{name}_tubular_free_{k}', 'Tubular Bells', ev, max(e[0] + e[1] for e in ev) + 1, 'free'))
        pad = [[root - 5, root, root + 4, root + 14], [root - 7, root - 3, root, root + 2]]  # tonic add9 / IV6 (vibes: F3 up)
        for i, chord in enumerate(pad):
            ev = [(0.05 * j, 9, p, 44 + 3 * j) for j, p in enumerate(chord)]
            groups['free'].append((f'shimmer_{["tonic", "subdominant"][i]}_bowedvibes_free_{k}', 'Vibraphone Bowed', ev, 10, 'free'))
        for motif, tune, bars, trim, minor in [('silentnight_a', 'silent-night', (1, 8), 0.0, False),
                                               ('awayinamanger_uk', 'away-in-a-manger-uk', (1, 8), 1.0, False),
                                               ('ochristmastree', 'o-christmas-tree', (1, 4), 0.5, False),
                                               ('joy', 'joy-to-the-world', (1, 8), 0.5, False)]:
            groups['free'].append(free_item(motif, tune, bars, trim, k, minor, 'harp', rng, slow=1.25))
        for motif, tune, bars, trim in [('silentnight_a', 'silent-night', (1, 8), 0.0), ('joy', 'joy-to-the-world', (1, 8), 0.5),
                                        ('awayinamanger_us', 'away-in-a-manger-us', (1, 8), 1.0)]:
            groups['free'].append(free_item(motif, tune, bars, trim, k, False, 'piano', rng, slow=1.25))
        for motif, tune, bars, trim in [('silentnight_b', 'silent-night', (17, 24), 0.0), ('ochristmastree', 'o-christmas-tree', (1, 4), 0.5),
                                        ('awayinamanger_us', 'away-in-a-manger-us', (1, 8), 1.0), ('joy', 'joy-to-the-world', (1, 8), 0.5)]:
            groups['free'].append(free_item(motif, tune, bars, trim, k, False, 'handbellslow', rng, slow=1.3))
        arps = {'glissup': [(i * 0.08, 6 - i * 0.08, p, 40 + i) for i, p in enumerate(
                    [q for q in range(root - 12, root + 26) if q % 12 in {root % 12, (root + 4) % 12, (root + 7) % 12, (root + 11) % 12}])],
                'cascade': [(i * 0.18, 5, pent(k, 9 - i, root + 14), 50 - i) for i in range(10)],
                'rolling': [(i * 0.35, 4, pent(k, [0, 2, 4, 2, 5, 4, 7, 5][i % 8], root + 2), 46 + (i % 4)) for i in range(12)]}
        for name, ev in arps.items():
            groups['free'].append((f'harp{name}_harp_free_{k}', 'Harp', ev, max(e[0] + e[1] for e in ev) + 1, 'free'))
    allman = {}
    for tag, tempo in [('variety_64bpm', 64), ('variety_80bpm', 80), ('variety_free', 'free')]:
        its = groups[tempo]
        t = 60 if tempo == 'free' else tempo
        song, man = build(t, 4, its, tag)
        write_set(song, os.path.join(SETS, tag + '.als'), reverb=(2600, 18))
        for m, it in zip(man, its):
            m['instrument'], m['tempo'] = it[1], t
            if it[4] == 'phrase8':
                m['kind'], m['pad_bars'] = 'phrase', 8
        allman[tag] = man
        print(f'{tag}: {len(its)} overlays, {song.end:.0f} beats = {song.end * 60 / t / 60:.1f} min')
    json.dump(allman, open(os.path.join(SETS, 'variety_manifest.json'), 'w'), indent=1)
    print('total new', sum(len(v) for v in allman.values()))


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'sets'
    if cmd == 'slice-library':
        slice_('library_manifest.json')
    elif cmd == 'slice-variety':
        slice_('variety_manifest.json')
    elif cmd == 'variety':
        variety()
    else:
        {'sets': sets, 'slice': slice_, 'library': library}[cmd]()
