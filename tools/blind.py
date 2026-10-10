"""Turn an A/B model test into a blind listening set.
Input: samples.py results for families keyed '<Genre>-<modelTag>'. Per genre, the two model tags are
randomly mapped to X / Y; each track is loudness-normalized (loudnorm I=-16, same for all) and
metadata-stripped, written to ~/Downloads/<out>/<Genre> X-1.mp3 etc. Key -> <results>.KEY.json
(do not reveal before the listener has chosen).
Usage: python3 tools/blind.py <results.json> <out_rel_to_Downloads>"""
import json, os, random, subprocess, sys
res = json.load(open(sys.argv[1])); out = os.path.expanduser(f'~/Downloads/{sys.argv[2]}'); os.makedirs(out, exist_ok=True)
genres = {}
for k, r in res.items():
    g, tag = k.rsplit('-', 1); genres.setdefault(g, {})[tag] = r
key = {}
for g, tags in sorted(genres.items()):
    order = list(tags); random.SystemRandom().shuffle(order)
    key[g] = {'X': order[0], 'Y': order[1]}
    for letter, tag in (('X', order[0]), ('Y', order[1])):
        for i, t in enumerate(tags[tag]['tracks'], 1):
            dst = os.path.join(out, f'{g} {letter}-{i}.mp3')
            subprocess.run(['ffmpeg', '-v', 'quiet', '-y', '-i', t['file'], '-map_metadata', '-1',
                            '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11', '-ar', '44100', '-ab', '256k', dst], check=True)
json.dump(key, open(sys.argv[1].replace('.json', '.KEY.json'), 'w'), indent=1)
print('blind set ->', out); print(sorted(os.listdir(out)))
