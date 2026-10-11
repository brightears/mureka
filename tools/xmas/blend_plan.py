#!/usr/bin/env python3
"""Plan which Christmas overlays go on which Mureka base track, at what level, so they blend in.

Norbert: overlays must "blend in smoothly"; a bright layer (e.g. high vibraphone) "would disrupt the song".
So the level is set per pair from the music itself, not one fixed dB:
  * bells pop out most in a base's QUIET, DARK passages -> measure the base's 2-8 kHz band level at its 25th
    percentile (0.5 s frames) and the overlay's same band at its 90th percentile (its brightest moments)
  * the Mureka mixer (tools/audio/overlay.py) loudness-matches base and overlay, then puts the overlay gain_db
    below; we pick gain_db so the overlay's bright band ends up >= MARGIN dB under the base's quiet bright band
  * clamp per kind: hooks/phrases -18..-12 dB, sleigh loops -19..-15 dB (quieter than the approved pilot mixes)
Variation: per playlist, 1-2 layers per track; carols rotate so neighbouring tracks never share a hook; vibraphone
only as a secondary choice (it is the brighter instrument); keys/tempos must match the base (key guard).

Usage: <python-with-numpy> blend_plan.py <bases_dir> [out_plan.json]
       bases_dir: folders named like 'Christmas Lounge' with base tracks inside (mp3/flac)
Then mix with:  overlay.py <base> <overlay.wav> <out.mp3> <gain_db>  (once per layer, chaining outputs)
"""
import json, os, random, subprocess, sys
import numpy as np

LIB = os.path.expanduser('~/Downloads/Christmas Ableton/overlays')
# repo-relative (tools/xmas/blend_plan.py -> <repo>/tools/audio), so it works from main or any worktree
MUREKA_AUDIO = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'tools', 'audio')
SR, FRAME = 22050, 11025  # 0.5 s frames
MARGIN = 8.0
NOTE = {n: i for i, n in enumerate(['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B'])}


def load(path):
    raw = subprocess.run(['ffmpeg', '-v', 'quiet', '-i', path, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'],
                         capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32)


def band_levels(x):
    """Per-frame overall RMS dB and 2-8 kHz band RMS dB."""
    n = len(x) // FRAME
    if n == 0:
        return np.array([-120.0]), np.array([-120.0])
    fr = x[:n * FRAME].reshape(n, FRAME) * np.hanning(FRAME)
    spec = np.abs(np.fft.rfft(fr, axis=1)) ** 2
    f = np.fft.rfftfreq(FRAME, 1 / SR)
    band = spec[:, (f >= 2000) & (f <= 8000)].sum(axis=1)
    total = spec.sum(axis=1)
    db = lambda e: 10 * np.log10(e + 1e-12)
    return db(total), db(band)


CLAMP = {'loop': (-19.0, -15.0), 'phrase': (-18.0, -12.0), 'free': (-18.0, -12.0)}


def gain_for(base_path, ov_path, kind='phrase', cache={}):
    if base_path not in cache:
        tot, band = band_levels(load(base_path))
        act = tot > tot.max() - 40
        cache[base_path] = (float(np.mean(tot[act])), float(np.percentile(band[act], 25)))
    b_loud, b_band_q = cache[base_path]
    tot, band = band_levels(load(ov_path))
    act = tot > tot.max() - 30  # only where the overlay actually sounds
    o_loud, o_band_hi = float(np.mean(tot[act])), float(np.percentile(band[act], 90))
    g = (b_band_q - MARGIN) - (o_band_hi - o_loud + b_loud)
    lo, hi = CLAMP[kind]
    return round(float(np.clip(g, lo, hi)), 1)


def key_sig(name):
    for part in name.replace('.wav', '').split('_'):
        if part.endswith('maj'):
            return NOTE[part[:-3]]
        if part.endswith('min'):
            return (NOTE[part[:-3]] + 3) % 12
    return None


def family(f):
    """Layer family from the file name (drives genre recipes and variety rotation)."""
    n = f['file']
    if n.startswith('sleighbells'):
        return 'sleigh'
    for pre, fam in (('sparkle_', 'sparkle'), ('shimmer_', 'shimmer'), ('bellswell_', 'bellswell'), ('chimes_', 'chimes'),
                     ('harpsweep', 'harpfx'), ('harpglissup', 'harpfx'), ('harpcascade', 'harpfx'), ('harprolling', 'harpfx')):
        if n.startswith(pre):
            return fam
    if '_flip_' in n:
        return 'flip'
    if '_frag_' in n:
        return 'frag'
    return 'free_carol' if f['kind'] == 'free' else 'hook'


INSTS = {'handbells', 'handbellslow', 'vibes', 'piano', 'harp', 'tubular', 'bowedvibes'}


def inst(f):
    return next((t for t in f['file'].replace('.wav', '').split('_') if t in INSTS), 'sleigh')


# genre recipes: (weight, [layer families]); instrument preferences keep each genre's own sound
RECIPES = {
    'Lounge': dict(tempo=80, insts={'vibes', 'handbellslow', 'handbells', 'piano', 'harp'}, recipes=[
        (25, ['flip', 'sleigh']), (20, ['hook', 'sleigh']), (15, ['frag', 'sparkle']), (10, ['flip']),
        (15, ['frag', 'sleigh']), (10, ['sparkle', 'sleigh']), (5, ['sleigh'])]),
    'Jazz': dict(tempo=64, insts={'vibes', 'piano', 'handbells', 'handbellslow'}, recipes=[
        (20, ['hook']), (20, ['frag']), (20, ['frag', 'sleigh']), (15, ['sparkle']), (15, ['hook', 'sleigh']),
        (5, ['sleigh']), (5, [])]),
    'Classical': dict(tempo=None, insts={'harp', 'handbells', 'handbellslow', 'tubular', 'bowedvibes', 'vibes'}, recipes=[
        (30, ['free_carol']), (15, ['chimes']), (15, ['harpfx']), (15, ['shimmer', 'free_carol']), (15, ['free_carol']),
        (5, ['bellswell']), (5, [])]),
    'Acoustic': dict(tempo=None, insts={'handbells', 'handbellslow', 'piano', 'tubular', 'bowedvibes', 'harp'}, recipes=[
        (35, ['free_carol']), (20, ['free_carol']), (15, ['chimes']), (10, ['shimmer']), (10, ['harpfx']), (10, [])]),
}
SLEIGH_OK = {'Lounge': ('eighths', 'sparse', 'quarters', 'build', 'fade', '_80bpm'),
             'Jazz': ('sparse', 'fade', 'build', 'quarters')}


def choose(cat, genre, sig, minor_base, i, rng, usage, recent):
    prof = RECIPES[genre]
    w = [r[0] for r in prof['recipes']]
    fams = rng.choices([r[1] for r in prof['recipes']], weights=w)[0]
    picks = []
    for fam in fams:
        cands = [c for c in cat if family(c) == fam and (prof['tempo'] is None or c['tempo'] in (prof['tempo'], None))
                 and (c['kind'] == 'free') == (prof['tempo'] is None)
                 and (c['key'] is None or key_sig(c['file']) == sig)]
        if fam == 'sleigh':
            cands = [c for c in cands if c['tempo'] == prof['tempo'] and any(t in c['file'] for t in SLEIGH_OK.get(genre, ('',)))]
        else:
            cands = [c for c in cands if inst(c) in prof['insts']]
        if minor_base and fam not in ('free_carol', 'chimes', 'shimmer', 'harpfx', 'bellswell') \
                and any('min' in (c['key'] or '') for c in cands):  # synced hooks: minor carols on minor bases
            cands = [c for c in cands if 'min' in (c['key'] or '') or c['key'] is None]
        cands = [c for c in cands if c['file'] not in recent.get('files', ())] or cands  # never back-to-back
        if not cands:
            continue
        def score(c):
            return (usage.get(c['file'], 0) - (0.5 if minor_base and 'min' in (c['key'] or '') else 0),
                    2 * (c.get('carol') is not None and c.get('carol') in recent['carols']),
                    inst(c) in recent['insts'],
                    rng.random())
        pick = min(cands, key=score)
        usage[pick['file']] = usage.get(pick['file'], 0) + 1
        picks.append(pick)
    recent['files'] = {p['file'] for p in picks}
    recent['carols'] = ([p['carol'] for p in picks if p.get('carol')] + recent['carols'])[:3]
    recent['insts'] = ([inst(p) for p in picks if family(p) != 'sleigh'] + recent['insts'])[:2]
    return picks


def plan(bases_dir, measure=True):
    cat = json.load(open(os.path.join(LIB, 'overlay_catalog.json')))
    out = []
    for pl in sorted(os.listdir(bases_dir)):
        genre = next((g for g in RECIPES if g.lower() in pl.lower()), None)
        if not genre:
            continue
        rng, usage, recent = random.Random(pl), {}, {'carols': [], 'insts': []}
        tracks = sorted(f for f in os.listdir(os.path.join(bases_dir, pl)) if f.lower().endswith(('.mp3', '.flac', '.wav')))
        for i, tr in enumerate(tracks):
            base = os.path.join(bases_dir, pl, tr)
            sig, minor_base = None, 'minor' in tr.lower()
            if measure:
                try:  # measure the key exactly like the mixer's key guard (Mureka repo tools/audio/trackinfo.py)
                    sys.path.insert(0, MUREKA_AUDIO)
                    import trackinfo as ti
                    tonic, qual = ti.key(ti.spectrogram(ti.load(base)))[0].split()
                    sig, minor_base = (NOTE[tonic] if qual == 'major' else (NOTE[tonic] + 3) % 12), qual == 'minor'
                except Exception as e:
                    print('  (key from file name:', e, ')')
            if sig is None:
                for nm, pc in NOTE.items():
                    if f'-{nm}major' in tr:
                        sig = pc
                    elif f'-{nm}minor' in tr:
                        sig = (pc + 3) % 12
            layers = []
            for pick in choose(cat, genre, sig, minor_base, i, rng, usage, recent):
                kind = pick['kind']
                g = gain_for(base, os.path.join(LIB, pick['file']), kind) if measure else CLAMP[kind][1]
                lo, hi = CLAMP[kind]
                g = round(min(hi, max(lo, g + rng.uniform(-2.0, 0.5))), 1)  # a little level variety, never louder
                layers.append(dict(overlay=pick['file'], gain_db=g, kind=kind, family=family(pick)))
            out.append(dict(playlist=pl, base=base, layers=layers))
            print(f"{tr[:44]:44} " + (' + '.join(f"{l['overlay'][:36]} ({l['gain_db']})" for l in layers) or '(plain, no layers)'))
    return out


def simulate(n=200):
    """Variety check without audio: n tracks per genre with random keys -> reuse statistics."""
    cat = json.load(open(os.path.join(LIB, 'overlay_catalog.json')))
    for genre in RECIPES:
        rng, usage, recent = random.Random(genre), {}, {'carols': [], 'insts': []}
        back_to_back, prev, layers_n = 0, set(), []
        for i in range(n):
            sig, minor = rng.choice([(0, False), (5, False), (0, True), (5, True)])
            picks = choose(cat, genre, sig, minor, i, rng, usage, recent)
            names = {p['file'] for p in picks}
            back_to_back += bool(names & prev)
            prev = names
            layers_n.append(len(picks))
        uses = sorted(usage.values(), reverse=True)
        print(f'{genre:9} {n} tracks: {len(usage)} different files used, most-used file x{uses[0]}, '
              f'median x{uses[len(uses) // 2]}, same file on consecutive tracks {back_to_back}x, '
              f'layers/track {dict(sorted({k: layers_n.count(k) for k in set(layers_n)}.items()))}')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'simulate':
        simulate(int(sys.argv[2]) if len(sys.argv) > 2 else 200)
        sys.exit()
    bases = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser('~/Downloads/Christmas/Round 6 - overlay bases')
    res = plan(bases)
    dst = sys.argv[2] if len(sys.argv) > 2 else os.path.join(LIB, 'blend_plan_round6.json')
    json.dump(res, open(dst, 'w'), indent=1)
    print('plan ->', dst)
