"""Public-domain carol data: melody + harmony, checked bar by bar on load.

Only PUBLIC-DOMAIN tunes belong here. Never add copyrighted holiday songs (White Christmas, Let It Snow,
Winter Wonderland, Rudolph, Frosty, Sleigh Ride, Jingle Bell Rock, Last Christmas, ...).

Melody: 'Pitch:beats' tokens (beats in quarter notes), 'r' = rest, trailing '~' ties into the next note,
'|' separates bars. With a pickup, the first bar is the pickup and the last bar is shortened by it.
Chords: '|' bars; 'Sym:beats', or bare 'Sym' tokens that share the rest of the bar evenly.
Every tune is validated on import, so a transcription slip raises instead of sounding wrong.
"""
from fractions import Fraction as F
from theory import midi, parse_chord


class Tune:
    def __init__(self, name, title, key, bar_len, pickup, mel, chords, source):
        self.name, self.title, self.key, self.source = name, title, key, source
        self.bar_len, self.pickup = F(bar_len), F(pickup)
        self.melody, self.n_bars = parse_mel(mel, self.bar_len, self.pickup, name)
        self.chords = parse_chords(chords, self.bar_len, self.n_bars, self.pickup, name)

    @property
    def length(self):
        return self.n_bars * self.bar_len

    def transposed(self, t):
        c = object.__new__(Tune)
        c.__dict__.update(self.__dict__)
        c.melody = [(p + t if p is not None else None, s, d) for p, s, d in self.melody]
        c.chords = [(ch.transposed(t), s, d) for ch, s, d in self.chords]
        return c


def parse_mel(s, bar_len, pickup, name):
    bars = [b.split() for b in s.split('|')]
    notes, t, tie = [], -pickup, False
    for i, bar in enumerate(bars):
        want = pickup if (pickup and i == 0) else (bar_len - pickup if (pickup and i == len(bars) - 1) else bar_len)
        got = F(0)
        for tok in bar:
            p, d = tok.split(':')
            nxt_tie = d.endswith('~')
            d = F(d.rstrip('~'))
            pitch = None if p == 'r' else midi(p)
            if tie and notes and notes[-1][0] == pitch:
                notes[-1] = (pitch, notes[-1][1], notes[-1][2] + d)
            else:
                notes.append((pitch, t, d))
            tie, t, got = nxt_tie, t + d, got + d
        if got != want:
            raise ValueError(f'{name}: melody bar {i} has {got} beats, expected {want}: {" ".join(bar)}')
    notes = [n for n in notes if n[0] is not None]
    return notes, len(bars) - (1 if pickup else 0)


def parse_chords(s, bar_len, n_bars, pickup, name):
    bars = [b.split() for b in s.split('|')]
    if len(bars) != n_bars:
        raise ValueError(f'{name}: {len(bars)} chord bars for {n_bars} melody bars')
    out = []
    for i, bar in enumerate(bars):
        start = i * bar_len
        fixed = sum(F(t.split(':')[1]) for t in bar if ':' in t)
        loose = [t for t in bar if ':' not in t]
        share = (bar_len - fixed) / len(loose) if loose else 0
        t = start
        for tok in bar:
            sym, d = (tok.split(':')[0], F(tok.split(':')[1])) if ':' in tok else (tok, share)
            out.append((parse_chord(sym), t, d))
            t += d
        if t - start not in (bar_len, bar_len - pickup):
            raise ValueError(f'{name}: chord bar {i} has {t - start} beats: {" ".join(bar)}')
        if t - start != bar_len:  # final bar shortened by the pickup: let the last chord ring the full bar
            ch, s0, d = out[-1]
            out[-1] = (ch, s0, d + bar_len - (t - start))
    return out


TUNES = {t.name: t for t in [
    Tune('silent-night', 'Silent Night', 'C', 3, 0,
         'G4:1.5 A4:.5 G4:1 | E4:3 | G4:1.5 A4:.5 G4:1 | E4:3 | D5:2 D5:1 | B4:3 | C5:2 C5:1 | G4:3 | '
         'A4:2 A4:1 | C5:1.5 B4:.5 A4:1 | G4:1.5 A4:.5 G4:1 | E4:3 | A4:2 A4:1 | C5:1.5 B4:.5 A4:1 | '
         'G4:1.5 A4:.5 G4:1 | E4:3 | D5:2 D5:1 | F5:1.5 D5:.5 B4:1 | C5:3 | E5:3 | C5:1.5 G4:.5 E4:1 | '
         'G4:1.5 F4:.5 D4:1 | C4:3~ | C4:3',
         'C | C | C | C | G7 | G7 | C | C | F | F | C | C | F | F | C | C | G7 | G7 | C | C | C | G7 | C | C',
         'Gruber 1818; checked vs Wikipedia "Silent Night" score (contemporary version)'),
    Tune('o-christmas-tree', 'O Christmas Tree', 'G', 3, .5,
         'D4:.5 | G4:.75 G4:.25 G4:1.5 A4:.5 | B4:.75 B4:.25 B4:1.5 B4:.5 | A4:.5 B4:.5 C5:1 F#4:1 | '
         'A4:1 G4:1 r:.5 D5:.5 | D5:.5 B4:.5 E5:1.5 D5:.5 | D5:.5 C5:.5 C5:1.5 C5:.5 | C5:.5 A4:.5 D5:1.5 C5:.5 | '
         'C5:.5 B4:.5 B4:1 r:.5 D4:.5 | G4:.75 G4:.25 G4:1.5 A4:.5 | B4:.75 B4:.25 B4:1.5 B4:.5 | '
         'A4:.5 B4:.5 C5:1 F#4:1 | A4:1 G4:1 r:.5',
         'G:2 D:1 | G | Am:2 D7:1 | D7:1 G:2 | G7:1 C:2 | D7 | D7 | G | G:2 D:1 | G | Am:2 D7:1 | D7:1 G:2',
         'German folk tune (O Tannenbaum); checked vs Wikipedia "O Tannenbaum" score'),
    Tune('o-come-all-ye-faithful', 'O Come All Ye Faithful', 'G', 4, 1,
         'G4:1 | G4:2 D4:1 G4:1 | A4:2 D4:2 | B4:1 A4:1 B4:1 C5:1 | B4:2 A4:1 G4:1 | G4:2 F#4:1 E4:1 | '
         'F#4:1 G4:1 A4:1 B4:1 | F#4:2 E4:1.5 D4:.5 | D4:4 | D5:2 C5:1 B4:1 | C5:2 B4:2 | A4:1 B4:1 G4:1 A4:1 | '
         'F#4:2 D4:1 G4:1 | G4:1 F#4:1 G4:1 A4:1 | G4:2 D4:1 B4:1 | B4:1 A4:1 B4:1 C5:1 | B4:2 A4:1 B4:1 | '
         'C5:1 B4:1 A4:1 G4:1 | F#4:2 G4:1 C5:1 | B4:2 A4:1.5 G4:.5 | G4:3',
         'G | C:2 D:2 | G:1 D:1 G:1 C:1 | G:2 D:1 Em:1 | Em:2 D:1 A7:1 | D:1 G:1 D:1 G:1 | D/A:2 A7:1.5 D:.5 | D | '
         'G:2 Am:1 G:1 | Am7:2 G:2 | D:1 G:1 Em:1 C:1 | D:3 G:1 | G:1 D:1 G:1 D:1 | G:2 D:1 G:1 | G:1 D:1 G:1 C:1 | '
         'G:2 D:1 G:1 | C:1 G:1 D:1 Em:1 | D:1 D7:1 G:1 C:1 | G/D:2 D7:1.5 G:.5 | G',
         'Adeste Fideles (Wade, 18th c.); checked vs Wikipedia "O Come, All Ye Faithful" score'),
    Tune('away-in-a-manger-uk', 'Away in a Manger', 'F', 3, 1,
         'C4:1 | F4:1 F4:1 G4:.5 A4:.5 | F4:1 F4:1 A4:.5 Bb4:.5 | C5:1 C5:1 D5:1 | Bb4:2 G4:.5 A4:.5 | '
         'Bb4:1 Bb4:1 C5:1 | A4:1 A4:1 F4:.5 A4:.5 | G4:1 D4:1 F4:1 | E4:2 C4:1 | F4:1 F4:1 G4:.5 A4:.5 | '
         'F4:1 F4:1 A4:.5 Bb4:.5 | C5:1 C5:1 D5:1 | Bb4:2 G4:.5 A4:.5 | Bb4:1 Bb4:1 C5:1 | A4:1 A4:1 F4:.5 A4:.5 | '
         'G4:1 D4:1 E4:1 | F4:2',
         'F | F | F:2 Bb:1 | Bb:2 Gm:1 | Bb:2 C7:1 | F | Gm7 | C:2 C7:1 | F | F | F:2 Bb:1 | Bb:2 Gm:1 | '
         'Bb:2 C7:1 | F | Gm7:1 C7:2 | F',
         'Kirkpatrick "Cradle Song" 1895; checked vs Wikipedia "Away in a Manger" score (2nd tune)'),
    Tune('away-in-a-manger-us', 'Away in a Manger', 'F', 3, 1,
         'C5:1 | C5:1.5 Bb4:.5 A4:1 | A4:1.5 G4:.5 F4:1 | F4:1 E4:1 D4:1 | C4:2 C4:1 | C4:1.5 D4:.5 C4:1 | '
         'C4:1 G4:1 E4:1 | D4:1 C4:1 F4:1 | A4:2 C5:1 | C5:1.5 Bb4:.5 A4:1 | A4:1.5 G4:.5 F4:1 | F4:1 E4:1 D4:1 | '
         'C4:2 C4:1 | Bb4:1.5 A4:.5 G4:1 | A4:1 G4:1 F4:1 | G4:1 D4:1 E4:1 | F4:2',
         'F | F | Dm:1 C:1 Bb:1 | F/A | F | C7 | Gm7:1 C7:1 F:1 | F | F | F | Dm:1 C:1 Bb:1 | F/A | '
         'Bb:2 Gm7:1 | F:1 C7:1 Dm:1 | Gm7:2 C7:1 | F',
         'Murray "Mueller" 1887; checked vs Wikipedia "Away in a Manger" score (1st tune)'),
    Tune('hark-the-herald', 'Hark! The Herald Angels Sing', 'F', 4, 0,
         'C4:1 F4:1 F4:1.5 E4:.5 | F4:1 A4:1 A4:1 G4:1 | C5:1 C5:1 C5:1.5 Bb4:.5 | A4:1 G4:1 A4:2 | '
         'C4:1 F4:1 F4:1.5 E4:.5 | F4:1 A4:1 A4:1 G4:1 | C5:1 G4:1 G4:1.5 E4:.5 | E4:1 D4:1 C4:2 | '
         'C5:1 C5:1 C5:1 F4:1 | Bb4:1 A4:1 A4:1 G4:1 | C5:1 C5:1 C5:1 F4:1 | Bb4:1 A4:1 A4:1 G4:1 | '
         'D5:1 D5:1 D5:1 C5:1 | Bb4:1 A4:1 Bb4:2 | G4:1 A4:.5 Bb4:.5 C5:1.5 F4:.5 | F4:1 G4:1 A4:2 | '
         'D5:1.5 D5:.5 D5:1 C5:1 | Bb4:1 A4:1 Bb4:2 | G4:1 A4:.5 Bb4:.5 C5:1.5 F4:.5 | F4:1 G4:1 F4:2',
         'F:3 C:1 | F/A:1 F:1 F/C:1 C:1 | F/A:1 Am:1 Bb:1 Gm/Bb:1 | F/C:1 C:1 F:2 | F:3 C:1 | Dm:1 F/C:1 G7:2 | '
         'Am:1 G/B:1 C:1 C/E:1 | F:1 G7:1 C:2 | C:3 F/A:1 | C7/E:1 F:1 C:2 | C:3 F/A:1 | C7/E:1 F:1 C:2 | Bb | '
         'Gm:1 D7:1 Gm:2 | C7/Bb:2 F/A:1 F:1 | F/C:1 C7:1 F:2 | Bb | Gm:1 D7:1 Gm:1 Gm/F:1 | '
         'C/E:1 C7/Bb:1 F/A:1 F:1 | F/C:1 C7:1 F:2',
         'Mendelssohn 1840; checked vs Wikipedia "Hark! The Herald Angels Sing" score'),
    Tune('joy-to-the-world', 'Joy to the World', 'D', 2, 0,
         'D5:1 C#5:.75 B4:.25 | A4:1.5 G4:.5 | F#4:1 E4:1 | D4:1.5 A4:.5 | B4:1.5 B4:.5 | C#5:1.5 C#5:.5 | D5:2~ | '
         'D5:1.5 D5:.5 | D5:.5 C#5:.5 B4:.5 A4:.5 | A4:.75 G4:.25 F#4:.5 D5:.5 | D5:.5 C#5:.5 B4:.5 A4:.5 | '
         'A4:.75 G4:.25 F#4:.5 F#4:.5 | F#4:.5 F#4:.5 F#4:.5 F#4:.25 G4:.25 | A4:1.5 G4:.25 F#4:.25 | '
         'E4:.5 E4:.5 E4:.5 E4:.25 F#4:.25 | G4:1.5 F#4:.25 E4:.25 | F#4:.5 D5:1 B4:.5 | A4:.75 G4:.25 F#4:.5 G4:.5 | '
         'F#4:1 E4:1 | D4:2',
         'D | D:1.5 G:.5 | D/A:1 A7:1 | D | G | A | D | D | D | D | D | D | D | D/A:1.5 A7:.5 | A7 | A7 | '
         'D:1.5 G:.5 | D/A:1.5 A7:.5 | D/A:1 A7:1 | D',
         'Mason "Antioch" 1839; checked vs Wikipedia "Joy to the World" score'),
    Tune('jingle-bells', 'Jingle Bells', 'C', 4, 0,
         'E4:1 E4:1 E4:2 | E4:1 E4:1 E4:2 | E4:1 G4:1 C4:1.5 D4:.5 | E4:4 | F4:1 F4:1 F4:1.5 F4:.5 | '
         'F4:1 E4:1 E4:1 E4:.5 E4:.5 | E4:1 D4:1 D4:1 E4:1 | D4:2 G4:2 | E4:1 E4:1 E4:2 | E4:1 E4:1 E4:2 | '
         'E4:1 G4:1 C4:1.5 D4:.5 | E4:4 | F4:1 F4:1 F4:1.5 F4:.5 | F4:1 E4:1 E4:1 E4:.5 E4:.5 | '
         'G4:1 G4:1 F4:1 D4:1 | C4:4',
         'C | C | C | C | F | F:1 C:3 | D7 | G7 | C | C | C | C | F | F:1 C:3 | G7 | C',
         'Pierpont 1857, refrain; matches data/melodies/jingle-bells.mid (Mureka repo)'),
    Tune('deck-the-halls', 'Deck the Halls', 'G', 4, 0,
         'D5:1.5 C5:.5 B4:1 A4:1 | G4:1 A4:1 B4:1 G4:1 | A4:.5 B4:.5 C5:.5 A4:.5 B4:1.5 A4:.5 | G4:1 F#4:1 G4:2 | '
         'D5:1.5 C5:.5 B4:1 A4:1 | G4:1 A4:1 B4:1 G4:1 | A4:.5 B4:.5 C5:.5 A4:.5 B4:1.5 A4:.5 | G4:1 F#4:1 G4:2 | '
         'A4:1.5 B4:.5 C5:1 A4:1 | B4:1.5 C5:.5 D5:1 A4:1 | B4:.5 C#5:.5 D5:1 E5:.5 F#5:.5 G5:1 | F#5:1 E5:1 D5:2 | '
         'D5:1.5 C5:.5 B4:1 A4:1 | G4:1 A4:1 B4:1 G4:1 | E5:.5 E5:.5 E5:.5 E5:.5 D5:1.5 C5:.5 | B4:1 A4:1 G4:2',
         'G:3 D7:1 | G | Am:1 D7:1 G:2 | G:1 D7:1 G:2 | G:3 D7:1 | G | Am:1 D7:1 G:2 | G:1 D7:1 G:2 | '
         'Am7:2 D7:2 | G:2 D:2 | Em:1 D:1 A7:2 | D:2 D7:2 | G:3 D7:1 | G | C:2 G/D:1 D7:1 | G:1 D7:1 G:2',
         'Welsh "Nos Galan" (trad.); FROM MEMORY, no score found: needs an ear check'),
    Tune('carol-of-the-bells', 'Carol of the Bells', 'Gm', 4, 0,
         # Leontovych "Shchedryk" (1916) adapted from 3/4 to 4/4 by holding each bar's last note one beat longer
         ' | '.join(['Bb4:1 A4:.5 Bb4:.5 G4:2'] * 8 + ['D5:1 C5:.5 D5:.5 Bb4:2'] * 4 + [
             'G5:1 G5:.5 G5:.5 F5:.5 Eb5:1.5', 'D5:1 D5:.5 D5:.5 C5:.5 Bb4:1.5',
             'C5:1 C5:.5 C5:.5 D5:.5 C5:1.5', 'G4:1 G4:.5 G4:.5 G4:2'] +
             ['D4:.5 E4:.5 F#4:.5 G4:.5 A4:.5 Bb4:1.5', 'C5:.5 D5:.5 C5:1 Bb4:2'] * 2 +
             ['Bb4:1 A4:.5 Bb4:.5 G4:2'] * 4),
         ' | '.join(['Gm9', 'Gm/F', 'Ebmaj7', 'Gm/D'] * 2 + ['Ebmaj7', 'Gm', 'Cm9', 'Gm'] +
                    ['Gm7:2 Cm7:2', 'Gm7', 'Cm9', 'Gm'] + ['D7b13', 'Cm7:2 D7b13:2'] * 2 +
                    ['Gm9', 'Gm/F', 'Ebmaj7', 'Gm/D']),
         'Leontovych "Shchedryk" 1916 (melody only, not the 1936 English arrangement); checked vs Wikipedia score'),
    Tune('god-rest-ye', 'God Rest Ye Merry Gentlemen', 'Em', 4, 1,
         'E4:1 | E4:1 B4:1 B4:1 A4:1 | G4:1 F#4:1 E4:1 D4:1 | E4:1 F#4:1 G4:1 A4:1 | B4:3 E4:1 | '
         'E4:1 B4:1 B4:1 A4:1 | G4:1 F#4:1 E4:1 D4:1 | E4:1 F#4:1 G4:1 A4:1 | B4:3 B4:1 | C5:1 A4:1 B4:1 C5:1 | '
         'D5:1 E5:1 B4:1 A4:1 | G4:1 E4:1 F#4:1 G4:1 | A4:2 G4:1 A4:1 | B4:2 C5:1 B4:1 | B4:1 A4:1 G4:1 F#4:1 | '
         'E4:2 G4:.5 F#4:.5 E4:1 | A4:2 G4:1 A4:1 | B4:1 C5:1 D5:1 E5:1 | B4:1 A4:1 G4:1 F#4:1 | E4:3',
         'Em:2 B:1 B7:1 | Em:1 Bm:1 C:1 G:1 | C:1 B:1 Em:1 Am:1 | B:3 Em:1 | Em:2 B:1 B7:1 | Em:1 Bm:1 C:1 G:1 | '
         'C:1 B:1 Em:1 Am:1 | B:3 E:1 | Am:1 D:1 G:1 C:1 | G7:1 C:1 G:1 B7:1 | Em:1 A7:1 D:1 G:1 | D:2 Em:1 D:1 | '
         'G:2 C:1 G:1 | G:1 D7:1 Em:1 B:1 | Em:3 A7:1 | D:1 D7:1 Em:1 D7:1 | G:1 C:1 G:1 C:1 | G:1 D7:1 Em:1 B:1 | Em',
         'English traditional; checked vs Wikipedia "God Rest Ye Merry, Gentlemen" score'),
]}

if __name__ == '__main__':
    for t in TUNES.values():
        lo, hi = min(p for p, _, _ in t.melody), max(p for p, _, _ in t.melody)
        print(f'{t.name:24} {t.key:3} {t.n_bars:2} bars x {t.bar_len}  range {lo}-{hi}  {t.source}')
