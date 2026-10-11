#!/usr/bin/env python3
"""Write complete Ableton Live sets (.als) for the pilot arrangements: one MIDI track per part with the right
Suite-pack instrument (or Kontakt Festive Bells) already loaded, the notes as an arrangement clip, mix levels,
reverb sends, tempo, meter and the loop brace set to the song, so Live only has to open the set and export it.

An .als is gzipped XML. Every instrument (incl. Kontakt with its saved Sleigh Bells state) is copied from
templates/instrument-library.als, a set saved by Live 12.4.6 that is also the base (A-Reverb / B-Delay returns).

Usage: python3 tools/xmas/als.py [pilot_id ...]      -> ~/Downloads/Christmas Ableton/<Playlist>/<id> .../<name>.als
"""
import gzip, math, os, re, sys
from arrange import PILOTS, build, OUT

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(HERE, 'templates', 'instrument-library.als')

# part name -> (instrument-library track, volume dB, reverb send dB, colour index, note remap, rack chain selector)
# The library set holds every instrument once, loaded by Live itself (rack presets cannot be pasted from .adg files:
# their layers are stored differently). Chain selector picks a rack articulation, e.g. Glockenspiel 0-41 plastic
# hits, 42-84 brass hits, 85-127 brass rolls.
PARTS = {
    'Piano': ('Grand Piano Equal Mellow Solo', -1, -13, 1, None, None),
    'Upright Bass': ('Upright Close Bass', -4, -24, 17, None, None),
    'Brushes': ('Jazz Brush Kit', -9, -18, 26, {44: 42, 51: 50}, None),
    'Violins 1': ('Violin Section Legato', 0, -9, 5, None, None),
    'Violins 2': ('Violin Section', -4, -10, 6, None, None),
    'Violas': ('Viola Section', -4, -10, 7, None, None),
    'Cellos': ('Cello Section', -3, -10, 8, None, None),
    'Basses': ('Double Bass Section', -6, -12, 9, None, None),
    'Harp': ('Harp Concert', -6, -10, 20, None, None),
    'Celesta': ('Glockenspiel', -11, -8, 14, None, 20),
    'Drums': ('Towel Kit', -7, -30, 26, {46: 44}, None),
    'Keys (electric piano)': ('Basic Suitcase Speakers', -5, -18, 3, None, None),
    'Bass': ('Electric Damped Bass', -5, -40, 17, None, None),
    'Lead (melody)': ('Basic Suitcase Speakers', -3, -16, 1, None, None),
    'Bells (glockenspiel or celesta)': ('Glockenspiel', -12, -10, 14, None, 63),
    'Sleigh Bells': ('1-Kontakt 8', -19, -14, 12, {54: 60}, None),
    'Hand Bells': ('21-Kontakt 8', -10, -5, 14, None, None),
    'Vibraphone': ('Vibraphone', -9, -5, 14, None, None),
    'Tubular Bells': ('Tubular Bells', -8, -4, 14, None, None),
    'Vibraphone Bowed': ('Vibraphone Bowed', -8, -4, 14, None, None),
    'Piano Sparkle': ('Grand Piano Equal Mellow Solo', -6, -6, 1, None, None),
}
TRACK_LABEL = {'Celesta': 'Glockenspiel (celesta part)'}


def gz_read(p):
    return gzip.open(p).read().decode('utf-8')


def db(v):
    return 10 ** (v / 20)


class IdGen:
    def __init__(self, start):
        self.n = start
        self.lom = 5000

    def relom(self, xml):
        """Max for Live devices reference Live objects by LomId (MxDIdRef). Copies pasted from the library
        would share those ids and crash Live's Max bridge, so remap them per pasted track (refs stay consistent)."""
        mapping = {}

        def sub(m):
            v = m.group(1)
            if v not in mapping:
                self.lom += 1
                mapping[v] = str(self.lom)
            return f'<LomId Value="{mapping[v]}" />'
        return re.sub(r'<LomId Value="([1-9]\d*)" />', sub, xml)

    def renumber(self, xml):
        """Give every automation/modulation target and pointee in pasted device XML a fresh unique id."""
        def sub(m):
            self.n += 1
            return f'<{m.group(1)} Id="{self.n}"'
        return re.sub(r'<(\w*Target(?:s\.\d+)?|Pointee) Id="\d+"', sub, xml)


def close_of(xml, tag, start):
    """Index just past the </tag> that closes the <tag> opening at `start` (nesting-aware, skips <tag />)."""
    depth, pat = 0, re.compile(rf'<{tag}(?=[\s>/])[^>]*?(/?)>|</{tag}>')
    for m in pat.finditer(xml, start):
        if m.group(0).startswith('</'):
            depth -= 1
            if depth == 0:
                return m.end()
        elif m.group(1) != '/':
            depth += 1
    raise ValueError(f'unclosed <{tag}>')


def library_devices(base):
    """Instrument-library track name (without the 'N-' prefix) -> the XML inside its <Devices>."""
    out = {}
    for m in re.finditer(r'<MidiTrack Id="\d+"', base):
        t = base[m.start():base.index('</MidiTrack>', m.start())]
        name = re.sub(r'^\d+-', '', re.search(r'<EffectiveName Value="([^"]*)"', t).group(1))
        inner = t.index('<DeviceChain>', t.index('</FreezeSequencer>'))
        dv = t.index('<Devices', inner)
        if t.startswith('<Devices />', dv):
            continue
        body = t[dv + len('<Devices>'):close_of(t, 'Devices', dv) - len('</Devices>')]
        out.setdefault(name, body)
        out[re.search(r'<EffectiveName Value="([^"]*)"', t).group(1)] = body  # e.g. '21-Kontakt 8'
    return out


def set_macro(dev, k, value):
    """Set the OUTER rack's macro k (it follows the nested branches, so it is the last match in the device)."""
    tag = re.match(r'\s*<(\w+)', dev).group(1)
    st = dev.index(f'<{tag}')
    en = close_of(dev, tag, st)
    i = dev.rindex(f'<MacroControls.{k}>', st, en)
    j = dev.index('<Manual Value="', i)
    e = dev.index('"', j + len('<Manual Value="'))
    return dev[:j] + f'<Manual Value="{value}' + dev[e:]


EQ_MODE = {'lowcut48': 0, 'lowcut12': 1, 'lowshelf': 2, 'bell': 3, 'notch': 4, 'highshelf': 5, 'highcut12': 6, 'highcut48': 7}
# part -> [(band 0-7, mode, freq Hz, gain dB)]; bands not listed keep EQ Eight defaults (flat)
EQ = {
    'Bells (glockenspiel or celesta)': [(3, 'highshelf', 4000, -6), (7, 'highcut12', 7000, 0)],
    'Celesta': [(3, 'highshelf', 4000, -6), (7, 'highcut12', 7000, 0)],
    'Hand Bells': [(3, 'highshelf', 4500, -5), (7, 'highcut12', 8000, 0)],
    'Vibraphone': [(3, 'highshelf', 4000, -6), (7, 'highcut12', 8000, 0)],
    'Sleigh Bells': [(3, 'highshelf', 6000, -6), (7, 'highcut12', 11000, 0)],
    'Tubular Bells': [(3, 'highshelf', 4000, -6), (7, 'highcut12', 7000, 0)],
    'Vibraphone Bowed': [(3, 'highshelf', 4000, -6), (7, 'highcut12', 8000, 0)],
    'Piano Sparkle': [(3, 'highshelf', 5000, -4), (7, 'highcut12', 9000, 0)],
    'Harp': [(3, 'highshelf', 5000, -3)],
}


def eq_device(lib, bands):
    d = lib['MIDI']  # the library track that holds a lone EQ Eight
    for k, mode, freq, gain in bands:
        i = d.index(f'<Bands.{k}>')
        a0 = d.index('<ParameterA>', i)
        a1 = d.index('</ParameterA>', a0)
        a = d[a0:a1]
        for tag, val in (('IsOn', 'true'), ('Mode', EQ_MODE[mode]), ('Freq', freq), ('Gain', gain)):
            a = re.sub(rf'(<{tag}>\s*<LomId Value="0" />\s*<Manual Value=")[^"]+(")', rf'\g<1>{val}\2', a, count=1)
        d = d[:a0] + a + d[a1:]
    return d


def set_chain(dev, value):
    """Rack articulation: the outer Articulation macro (0) drives the chain selector."""
    return set_macro(dev, 0, value)


def clip_xml(name, notes, length, num, den, colour):
    by_pitch = {}
    for s, d, p, v in sorted(notes):
        by_pitch.setdefault(p, []).append((s, d, v))
    keys, nid = [], 1
    for k, p in enumerate(sorted(by_pitch)):
        evs = []
        for s, d, v in by_pitch[p]:
            evs.append(f'<MidiNoteEvent Time="{s:.6f}" Duration="{d:.6f}" Velocity="{v}" VelocityDeviation="0" '
                       f'OffVelocity="64" Probability="1" IsEnabled="true" NoteId="{nid}" />')
            nid += 1
        keys.append(f'<KeyTrack Id="{k}"><Notes>{"".join(evs)}</Notes><MidiKey Value="{p}" /></KeyTrack>')
    L = f'{length:.6f}'
    return f'''<MidiClip Id="0" Time="0"><LomId Value="0" /><LomIdView Value="0" /><CurrentStart Value="0" /><CurrentEnd Value="{L}" />
<Loop><LoopStart Value="0" /><LoopEnd Value="{L}" /><StartRelative Value="0" /><LoopOn Value="false" /><OutMarker Value="{L}" /><HiddenLoopStart Value="0" /><HiddenLoopEnd Value="{L}" /></Loop>
<Name Value="{name}" /><Annotation Value="" /><Color Value="{colour}" /><LaunchMode Value="0" /><LaunchQuantisation Value="0" />
<TimeSignature><TimeSignatures><RemoteableTimeSignature Id="0"><Numerator Value="{num}" /><Denominator Value="{den}" /><Time Value="0" /></RemoteableTimeSignature></TimeSignatures></TimeSignature>
<Envelopes><Envelopes /></Envelopes><ScrollerTimePreserver><LeftTime Value="0" /><RightTime Value="{L}" /></ScrollerTimePreserver>
<TimeSelection><AnchorTime Value="0" /><OtherTime Value="0" /></TimeSelection><Legato Value="false" /><Ram Value="false" />
<GrooveSettings><GrooveId Value="-1" /></GrooveSettings><Disabled Value="false" /><VelocityAmount Value="0" />
<FollowAction><FollowTime Value="4" /><IsLinked Value="false" /><LoopIterations Value="1" /><FollowActionA Value="0" /><FollowActionB Value="0" /><FollowChanceA Value="100" /><FollowChanceB Value="0" /><JumpIndexA Value="1" /><JumpIndexB Value="1" /><FollowActionEnabled Value="true" /></FollowAction>
<Grid><FixedNumerator Value="1" /><FixedDenominator Value="16" /><GridIntervalPixel Value="20" /><Ntoles Value="2" /><SnapToGrid Value="true" /><Fixed Value="false" /></Grid>
<FreezeStart Value="0" /><FreezeEnd Value="0" /><IsWarped Value="true" /><TakeId Value="0" />
<Notes><KeyTracks>{"".join(keys)}</KeyTracks><PerNoteEventStore><EventLists /></PerNoteEventStore><NoteProbabilityGroups />
<ProbabilityGroupIdGenerator><NextId Value="1" /></ProbabilityGroupIdGenerator><NoteIdGenerator><NextId Value="{nid}" /></NoteIdGenerator></Notes>
<BankSelectCoarse Value="-1" /><BankSelectFine Value="-1" /><ProgramChange Value="-1" /><NoteEditorFoldInZoom Value="-1" /><NoteEditorFoldInScroll Value="-1" />
<NoteEditorFoldOutZoom Value="-1" /><NoteEditorFoldOutScroll Value="0" /><NoteEditorFoldScaleZoom Value="-1" /><NoteEditorFoldScaleScroll Value="-1" />
<ScaleInformation><Root Value="0" /><Name Value="0" /></ScaleInformation><IsInKey Value="false" /><NoteSpellingPreference Value="0" />
<AccidentalSpellingPreference Value="3" /><PreferFlatRootNote Value="false" />
<ExpressionGrid><FixedNumerator Value="1" /><FixedDenominator Value="16" /><GridIntervalPixel Value="20" /><Ntoles Value="2" /><SnapToGrid Value="false" /><Fixed Value="false" /></ExpressionGrid></MidiClip>'''


def bake_pedal(notes, ccs):
    """Sustain pedal (CC64) folded into note lengths: a note released while the pedal is down rings until the pedal
    lifts (or until the same key is struck again). Avoids clip-envelope plumbing; samplers sound the same."""
    downs, state, start = [], False, 0.0
    for t, num, val in sorted(ccs):
        if num != 64:
            continue
        if val >= 64 and not state:
            state, start = True, t
        elif val < 64 and state:
            state = False
            downs.append((start, t))
    out = []
    by_pitch = {}
    for n in sorted(notes):
        by_pitch.setdefault(n[2], []).append(n)
    for p, ns in by_pitch.items():
        for i, (s, d, _, v) in enumerate(ns):
            end = s + d
            for a, b in downs:
                if a <= end < b:
                    end = b
                    break
            if i + 1 < len(ns):
                end = min(end, ns[i + 1][0] - 0.01)
            out.append((s, max(0.03, end - s), p, v))
    return out


def set_value(xml, tag, value, start=0):
    """Set <tag ...><Manual Value=..."/> (first one at or after `start`)."""
    i = xml.index(f'<{tag}>', start)
    j = xml.index('<Manual Value="', i)
    k = xml.index('"', j + len('<Manual Value="'))
    return xml[:j] + f'<Manual Value="{value}' + xml[k:]


def envelope_xml(eid, pointee, events):
    ev = ''.join(f'<FloatEvent Id="{k + 1}" Time="{b:.5f}" Value="{v:.5f}" />' for k, (b, v) in enumerate(events))
    return (f'<AutomationEnvelope Id="{eid}"><EnvelopeTarget><PointeeId Value="{pointee}" /></EnvelopeTarget>'
            f'<Automation><Events><FloatEvent Id="0" Time="-63072000" Value="{events[0][1]:.5f}" />{ev}</Events>'
            '<AutomationTransformViewState><IsTransformPending Value="false" /><TimeAndValueTransforms />'
            '</AutomationTransformViewState></Automation></AutomationEnvelope>')


def target_id(track_xml, target):
    """AutomationTarget id of the mixer volume ('vol') or of macro k of the first device (('macro', k))."""
    if target == 'vol':
        i = track_xml.index('<Volume>', track_xml.index('<Mixer>'))
    else:  # the outer rack's macros follow its (nested) branches, so take the last match inside the first device
        inner = track_xml.index('<DeviceChain>', track_xml.index('</FreezeSequencer>'))
        dv = track_xml.index('<Devices>', inner) + len('<Devices>')
        tag = re.match(r'\s*<(\w+)', track_xml[dv:]).group(1)
        start = track_xml.index(f'<{tag}', dv)
        end = close_of(track_xml, tag, start)
        i = track_xml.rindex(f'<MacroControls.{target[1]}>', start, end)
    return re.search(r'<AutomationTarget Id="(\d+)"', track_xml[i:i + 2000]).group(1)


def make_track(proto, tid, label, colour, device, clip, vol_db, send_db, ids, pan=None, autom=()):
    t = re.sub(r'^<MidiTrack Id="\d+"', f'<MidiTrack Id="{tid}"', proto)
    t = re.sub(r'<EffectiveName Value="[^"]*" />', f'<EffectiveName Value="{label}" />', t, count=1)
    t = re.sub(r'<UserName Value="[^"]*" />', f'<UserName Value="{label}" />', t, count=1)
    t = re.sub(r'<Color Value="\d+" />', f'<Color Value="{colour}" />', t, count=1)
    ms = t.index('<MainSequencer>')
    ev = t.index('<ArrangerAutomation>', ms)
    ev = t.index('<Events />', ev)
    t = t[:ev] + '<Events>' + clip + '</Events>' + t[ev + len('<Events />'):]
    fz = t.index('<FreezeSequencer')
    inner = t.index('<DeviceChain>', t.index('</FreezeSequencer>', fz))
    dv = t.index('<Devices />', inner)
    t = t[:dv] + '<Devices>' + device + '</Devices>' + t[dv + len('<Devices />'):]
    mx = t.index('<Mixer>')
    t = set_value(t, 'Volume', f'{db(vol_db):.6f}', mx)
    sd = t.index('<TrackSendHolder Id="0">', mx)
    t = set_value(t, 'Send', f'{max(db(send_db), 0.0003162277571):.6f}', sd)
    if pan is not None:
        t = set_value(t, 'Pan', f'{pan:.3f}', mx)
    t = ids.relom(ids.renumber(t))
    if autom:
        envs = ''.join(envelope_xml(k, target_id(t, tgt), evs) for k, (tgt, evs) in enumerate(autom))
        i = t.index('<AutomationEnvelopes>')
        j = t.index('<Envelopes />', i)
        t = t[:j] + '<Envelopes>' + envs + '</Envelopes>' + t[j + len('<Envelopes />'):]
    return t


def make_set(pid):
    cfg = PILOTS[pid]
    folder, secs, song, segs = build(pid, preview=False)
    out = os.path.join(folder, cfg['file'] + '.als')
    end = write_set(song, out)
    return out, end, song


def write_set(song, out, reverb=None):
    """Write `song` (arrange.Song or v2.Song2) as a complete Live set. Song2 extras honoured: tempo_events,
    autom {track: [(target, [(beat, value)])]}, pan {track: -1..1}; reverb = (decay ms, pre-delay ms)."""
    base = gz_read(BASE)
    num = int(song.bar_len)
    den = 4
    end = math.ceil((song.end + 2 * song.bar_len) / song.bar_len) * song.bar_len  # + reverb tail
    ids = IdGen(int(re.search(r'<NextPointeeId Value="(\d+)"', base).group(1)) + 1000)

    ts, te = base.index('<Tracks>'), base.index('</Tracks>')
    tracks = base[ts + len('<Tracks>'):te]
    i = tracks.index('<MidiTrack Id="13"')
    proto = tracks[i:tracks.index('</MidiTrack>', i) + len('</MidiTrack>')]
    returns = tracks[tracks.index('<ReturnTrack'):]
    lib = library_devices(base)
    new = []
    for n, (name, trk) in enumerate(song.tracks.items()):
        libname, vol, send, colour, remap, chain = PARTS[name]
        device = lib[libname]
        if isinstance(chain, dict):  # {macro index: value}
            for k, v in chain.items():
                device = set_macro(device, k, v)
        elif chain is not None:
            device = set_chain(device, chain)
        if name in EQ:  # second device in the chain: its list id must differ from the instrument's
            device = device + re.sub(r'^(\s*<\w+) Id="\d+"', r'\1 Id="1"', eq_device(lib, EQ[name]), count=1)
        notes = trk['notes']
        if trk['cc']:
            notes = bake_pedal(notes, trk['cc'])
        if remap:
            notes = [(s, d, remap.get(p, p), v) for s, d, p, v in notes]
        label = TRACK_LABEL.get(name, name)
        clip = clip_xml(label, notes, end, num, den, colour)
        new.append(make_track(proto, 100 + n, label, colour, device, clip, vol, send, ids,
                              getattr(song, 'pan', {}).get(name), getattr(song, 'autom', {}).get(name, ())))
    xml = base[:ts] + '<Tracks>' + '\n'.join(new) + '\n' + returns + base[te:]

    xml = set_value(xml, 'Tempo', f'{song.tempo}')
    tsig = (num - 1) + 99 * int(math.log2(den))
    xml = re.sub(r'(<TimeSignature>\s*<LomId Value="0" />\s*<Manual Value=")\d+(")', rf'\g<1>{tsig}\2', xml, count=1)
    mt = xml.index('<MainTrack')  # the arrangement plays the main track's tempo/meter envelopes, not the dials
    me = xml.index('</AutomationEnvelopes>', mt)
    env = re.sub(r'(<EnumEvent Id="0" Time="-63072000" Value=")\d+(")', rf'\g<1>{tsig}\2', xml[mt:me], count=1)
    env = re.sub(r'(<FloatEvent Id="0" Time="-63072000" Value=")[^"]+(")', rf'\g<1>{song.tempo}\2', env, count=1)
    tev = getattr(song, 'tempo_events', None)
    if tev:  # tempo map (rubato / ritardando) as arrangement tempo automation
        pts = ''.join(f'<FloatEvent Id="{k + 1}" Time="{b:.4f}" Value="{v:.3f}" />' for k, (b, v) in enumerate(tev))
        env = re.sub(r'(<FloatEvent Id="0" Time="-63072000" Value="[^"]+" />)', lambda m: m.group(1) + pts, env, count=1)
    xml = xml[:mt] + env + xml[me:]
    tr = xml.index('<Transport>')
    xml = xml[:tr] + re.sub(r'<LoopStart Value="[^"]*" />', '<LoopStart Value="0" />',
                            re.sub(r'<LoopLength Value="[^"]*" />', f'<LoopLength Value="{end}" />',
                                   xml[tr:tr + 800], count=1), count=1) + xml[tr + 800:]
    xml = re.sub(r'(<LiveSet>.*?<TimeSelection>\s*<AnchorTime Value=")[^"]*("\s*/>\s*<OtherTime Value=")[^"]*(")',
                 rf'\g<1>0\g<2>{end}\3', xml, count=1, flags=re.S)
    xml = re.sub(r'<NextPointeeId Value="\d+" />', f'<NextPointeeId Value="{ids.n + 10}" />', xml, count=1)
    if reverb:  # return A (Reverb): decay and pre-delay
        ra = xml.index('<ReturnTrack')
        rv = xml.index('<Reverb', ra)
        xml = set_value(xml, 'DecayTime', f'{reverb[0]}', rv)
        xml = set_value(xml, 'PreDelay', f'{reverb[1]}', rv)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with gzip.open(out, 'wb') as f:
        f.write(xml.encode('utf-8'))
    return end


if __name__ == '__main__':
    for pid in sys.argv[1:] or PILOTS:
        out, end, song = make_set(pid)
        print(f'{pid}: {len(song.tracks)} tracks, {end:.0f} beats @ {song.tempo} BPM -> {out}')
