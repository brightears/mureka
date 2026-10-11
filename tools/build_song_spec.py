"""Build the vocal scale spec from the lyric modules: assemble song structures per style,
screen for phrases from copyrighted holiday songs, check line length, check titles against the
catalog ledger (data/used-titles.json), write data/samples/<out>.json.
Usage: python3 tools/build_song_spec.py <target_count> <out_name>"""
import json, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'data', 'lyrics'))
from christmas_pop_vocal import STYLES, SONGS, REUSED
from christmas_pop_vocal_part2 import SONGS2

BANNED = ["let it snow", "jingle bell rock", "rockin' around", "rocking around", "all i want for christmas",
 "last christmas", "home for christmas", "white christmas", "merry little christmas", "most wonderful time",
 "winter wonderland", "santa claus is com", "rudolph", "frosty", "silver bells", "feliz navidad", "chestnuts",
 "cold outside", "here comes santa", "mistletoe and wine", "wonderful christmastime", "look a lot like",
 "deck the halls", "fa la la", "jingle all the way", "sleigh ride", "holly jolly", "blue christmas",
 "know it's christmas", "happy xmas", "war is over", "merry and bright", "making a list", "checking it twice",
 "naughty or nice", "holy night", "silent night", "let it go", "shake it off", "pretty paper", "little drummer",
 "ring-a-ling", "ring a ling", "jingle bells", "dashing through", "o christmas tree", "christmas time in the city",
 "silver and gold", "underneath the tree", "home for the holidays", "driving home for christmas",
 "do you hear what i hear", "step into christmas", "santa baby", "this christmas, ", "christmas wrapping",
 "feed the world", "simply having", "snow is falling, all around me", "it's christmas time", "mele kalikimaka",
 "hallelujah, hallelujah", "joy to the world", "hark the herald", "o come all ye", "away in a manger",
 "twelve days", "partridge", "we wish you a merry", "the first noel", "good king", "god rest ye"]

# fixes applied to reused (already-approved) sample lyrics after the copyright-phrase screen
REUSED_FIXES = {'VF': [('never let it go', 'hold it close and slow')],
                'V2': [('little silver bells', 'little golden bells')]}

def lines(s): return [l.strip() for l in s.split(' / ') if l.strip()]
def block(tag, s): return f'[{tag}]\n' + '\n'.join(lines(s))

def assemble(style, i, v1, v2, ch, br):
    C, V1, V2, B = block('Chorus', ch), block('Verse', v1), block('Verse', v2), block('Bridge', br)
    out = '[Outro]\n' + lines(ch)[-1]
    alt = i % 2
    if style in ('S1', 'S7', 'S12'):
        parts = (['[Intro]', V1, C, V2, C, B, C, out] if not alt else [V1, V2, C, B, C, out])
    elif style == 'S2':
        parts = ([V1, V2, B, C, out] if not alt else [V1, C, V2, C, B, C])
    elif style in ('S3', 'S11'):
        parts = [C, V1, C, V2, B, C, out]
    elif style == 'S4':
        parts = [V1, C, '[Instrumental]', V2, C, out]
    elif style == 'S8':
        parts = ([V1, V2, C, '[Instrumental]', C, out] if not alt else [V1, C, V2, C, B, C])
    elif style == 'S6':
        parts = [V1, C, V2, C, B, C, C]
    else:  # S5, S9, S10
        parts = ([V1, C, V2, C, B, C, C] if style != 'S5' else [V1, C, V2, C, B, C])
    return '\n\n'.join(parts)

def main(target, out_name):
    songs = []
    for style, title, spec, key in REUSED:
        fam = next(f for f in json.load(open(os.path.join(ROOT, 'data', 'samples', spec)))['families'] if f['key'] == key)
        lyr = fam['lyrics']
        for a, b in REUSED_FIXES.get(key, []): lyr = lyr.replace(a, b).replace(a.capitalize(), b.capitalize())
        songs.append({'style': style, 'title': title, 'lyrics': lyr, 'reused_from': f'{spec}:{key}'})
    for i, (style, title, v1, v2, ch, br) in enumerate(SONGS + SONGS2):
        songs.append({'style': style, 'title': title, 'lyrics': assemble(style, i, v1, v2, ch, br)})
    # screens
    used = set(json.load(open(os.path.join(ROOT, 'data', 'used-titles.json')))['titles'])
    problems, seen = [], set()
    for s in songs:
        low = s['lyrics'].lower()
        hits = [b for b in BANNED if b in low]
        if hits: problems.append(f"BANNED {s['title']}: {hits}")
        longl = [l for l in s['lyrics'].split('\n') if not l.startswith('[') and len(l.split()) > 12]
        if longl: s['long_lines'] = len(longl)
        t = s['title'].lower()
        if t in used: s['title_collision'] = True
        if t in seen: problems.append(f"DUP TITLE {s['title']}")
        seen.add(t)
    from collections import Counter
    by_style = Counter(s['style'] for s in songs)
    # trim to target, keeping styles balanced (drop from the largest style first)
    while len(songs) > target:
        big = max(by_style, key=lambda k: by_style[k]); idx = max(i for i, s in enumerate(songs) if s['style'] == big and 'reused_from' not in s)
        songs.pop(idx); by_style[big] -= 1
    for s in songs:
        st = STYLES[s['style']]; s['prompt'] = st['prompt']; s['gender'] = st['gender']
    json.dump({'playlist': 'Christmas Pop Vocal', 'model': 'mureka-9.5', 'n': 1, 'songs': songs},
              open(os.path.join(ROOT, 'data', 'samples', f'{out_name}.json'), 'w'), indent=1)
    print(f'{len(songs)} songs | per style: {dict(sorted(Counter(s["style"] for s in songs).items(), key=lambda x: int(x[0][1:])))}')
    print('title collisions with catalog:', [s['title'] for s in songs if s.get('title_collision')])
    print('songs with lines >12 words:', [(s['title'], s['long_lines']) for s in songs if s.get('long_lines')])
    print('PROBLEMS:', problems or 'none')

if __name__ == '__main__': main(int(sys.argv[1]), sys.argv[2])
