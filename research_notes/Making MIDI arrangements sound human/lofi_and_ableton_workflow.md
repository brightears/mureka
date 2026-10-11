# Lo-fi / Chillhop Production Technique and Ableton Live 12 Workflow for Polished MIDI Arrangements

Scope note: Sources found are mostly manufacturer manuals (Ableton), platform docs (Spotify), and producer/education blogs (Native Instruments, Mode Audio, Attack Magazine, Splice, Yamaha, Violet Recording, Music Guy Mixing). Forum posts are flagged. Many tutorials give settings only in screenshots or video, so hard numbers are sparser than the questions ask for. Where I derived numbers (e.g. swing in ms) the math is shown under Inferences.

## 1. Lo-fi / chillhop drums: tempo, swing, velocity, ghost notes, "drunk" timing, fills, sample processing

### Takeaway
Lo-fi/chillhop sits at about 60-90 BPM, with 2-3 sparse drum elements, swing in the 54-62% MPC range (roughly 15-45 ms of delay on the offbeat 16th at 80 BPM), ghost notes at about 30-40% velocity, and drums low-passed hard (around 2-3 kHz). "Looseness" works when it is systematic per instrument (e.g. hats straight-ish, snare slightly early or late, kick late), not uniform random jitter.

### Cited Findings
**Tempo**
- Chillhop tempos are "usually between 70 and 90 bpm" — [Yamaha Hub](https://hub.yamaha.com/proaudio/recording/how-to-create-lo-fi)
- Lo-fi generally sits at 60-90 BPM; NI's tutorial beat is 65 BPM; most lo-fi tracks run about 1-3 minutes — [Native Instruments blog](https://blog.native-instruments.com/lo-fi-hip-hop/)
- Lo-fi hip hop "tends to sit anywhere in the 60-80 BPM range" vs ~90-100 BPM for traditional hip hop; example beat at 74 BPM — [Mode Audio](https://modeaudio.com/magazine/lofi-hip-hop-5-production-essentials)
- Point Blank's lo-fi chord tutorial sets the project to 84 BPM — [Magnetic Mag / Point Blank](https://magneticmag.com/2022/09/point-blank-tutorial-how-to-make-lo-fi-hip-hop-chords-in-ableton-live/)

**Swing**
- MPC swing ranges from 50% (straight) to 75% (extreme shuffle). One guide's chart: ~54% modern hip-hop/R&B, ~58% classic boom-bap / 90s hip-hop, ~62% heavy shuffle for neo-soul and jazz-influenced styles — [Audeobox MPC Drum Programming](https://www.audeobox.com/learn/mpc-software/mpc-drum-programming/)
- MPC2000XL forum: 55-65% for a solid hip-hop/funk groove; a described Madlib-style method sets 8th-note swing ~55%, programs kick and hats there, then switches to 16ths for snares and other 16th hits (gives a looser feel than 16th-only swing) (forum, unverified) — [MPC-Forums](https://www.mpc-forums.com/viewtopic.php?p=412257)
- "Somewhere between 55% and 65% swing helps the groove feel played rather than programmed" — [Violet Recording](https://violetrecording.com/how-to-make-lofi-beats/)
- Attack Magazine: 50% = straight; 52% barely audible but adds subtle feel; 64% clearly swung; 73% pronounced. Below 50% is "negative" swing (rushed/anticipatory). Swing can be applied to leads, chops, bass, not just drums; different grooves/amounts can go on different elements — [Attack Magazine](https://www.attackmagazine.com/technique/tutorials/going-off-grid-what-is-swing-and-how-to-add-it/)
- Ableton forum user: MPC swing "seems to sound better when snare and claps have groove pool on them at least" (forum opinion) — [Ableton Forum](https://forum.ableton.com/viewtopic.php?p=1731735)
- A blog estimates Dilla beats often started with subtle swing of ~53-56% on 8th notes (author notes debate over exact methods) — [RouteNote Create](https://create.routenote.com/blog/wp-json/wp/v2/posts/17309) (via search summary; not fetched)

**"Drunk"/Dilla timing**
- Dan Charnas' *Dilla Time* (as summarised by the LRB) describes a key snare displacement of ~5/192 of a measure, ~65 ms from the strict grid — [London Review of Books](https://www.lrb.co.uk/the-paper/v44/n20/francis-gooding/basement-beats) (figure not verified against the book)
- Charnas' core idea: fusing swung and straight time simultaneously — hats might suggest straight time, kicks lean late, snares land early — [The Pier](https://thepier.org/twenty-years-of-dilla-time-how-j-dilla-rewrote-the-feel-of-popular-music/)
- Ethan Hein's audio-to-MIDI analysis of a classic funk groove: the anticipated (early) backbeat snare gives the groove drive; the hi-hat on beat 2 drags; kick and snare offbeats swing by different amounts, and swing amount varies between bars — [Ethan Hein](https://ethanhein.com/wp/2022/dilla-time-in-chameleon/)
- Mode Audio pulls kicks off the grid "just a touch"; notes some tracks stay fully quantised — [Mode Audio](https://modeaudio.com/magazine/lofi-hip-hop-5-production-essentials)
- Lo-fi drum parts are "typically looser rhythmically than in other genres", not quantized precisely — [Violet Recording](https://violetrecording.com/how-to-make-lofi-beats/)

**Pattern and density**
- Use 2 or 3 drum elements: snare/rim on 2 and 4, kick on beat 1 plus one or two syncopated spots, hat/shaker/percussion as the third — [Mode Audio](https://modeaudio.com/magazine/lofi-hip-hop-5-production-essentials)
- Boom-bap-influenced: kick on 1 and 3, snare on 2 and 4; avoid busy parts like 16th-note hats — [Violet Recording](https://violetrecording.com/how-to-make-lofi-beats/)
- In chillhop, drums are "relatively simple" and often don't start until after several intro measures of unaccompanied chords — [Yamaha Hub](https://hub.yamaha.com/proaudio/recording/how-to-create-lo-fi)

**Velocity and ghost notes**
- Starting point: full velocity on accents, ~60-70% on regular hits, ~30-40% on ghost notes; ghost notes on the 16th just before beats 2 and 4; "if you can clearly identify them as separate hits, they are too loud"; hand-draw velocity curves over a phrase rather than pure randomize — [Soundbridge](https://soundbridge.io/en/drum-programming-tips-for-producers-of-all-levels) (via search summary)
- A promotional forum post claims Dilla-style backbeat softened to ~82% and 62-72% swing — product marketing, not verified — [MPC-Forums](https://www.mpc-forums.com/viewtopic.php?p=1903072)

**Drum sound processing**
- Low-pass each kit element deeply, cutoff "down to around 2kHz or so", or a high-shelf cut above 2 kHz for subtler effect — [Mode Audio](https://modeaudio.com/magazine/lofi-hip-hop-5-production-essentials)
- NI: gentle low-pass curve from 3.12 kHz on drums; high-pass at 20 Hz to remove vinyl-plugin sub rumble; "dusty" kits with soft thumpy kick, loose snare, acoustic hats — [Native Instruments](https://blog.native-instruments.com/lo-fi-hip-hop/)
- Drum samples can be made by running analog drum machine sounds through reel-to-reel tape — [Mode Audio](https://modeaudio.com/magazine/lofi-hip-hop-5-production-essentials)
- Pitching a bounced loop down an octave = half speed; a fifth down = 2/3 BPM; then compress, overdrive, filter and resample for lo-fi grit (forum) — [Elektronauts](https://www.elektronauts.com/t/lofi-sample-loop-trick-by-multiplying-dividing-pitch/84208)

**Fills/variation**
- Bring in one element at a time over 4- or 8-bar phrases; remove/reintroduce parts as they get repetitive; reverse crash as ear candy into sections — [Native Instruments](https://blog.native-instruments.com/lo-fi-hip-hop/)
- Ableton forum user: a groove template just repeats, so add randomness on top for variation across a track — [Ableton Forum / search summary](https://forum.ableton.com/viewtopic.php?p=1731742)

### Inferences
- **Swing-to-ms formula (derived):** for 16th swing, delay of the offbeat 16th = (S/100 - 0.5) x (30000 / BPM) ms. At 80 BPM (16th-pair = 375 ms): 54% = 15 ms, 56% = 22.5 ms, 58% = 30 ms, 60% = 37.5 ms, 62% = 45 ms, 66.7% (triplet) = 62.5 ms. At 85 BPM: 54% = 14, 58% = 28, 62% = 42 ms. At 72 BPM: 58% = 33 ms. For 8th-note swing replace 30000 with 60000: at 80 BPM, 55% = 37.5 ms, 58% = 60 ms.
- **Diagnosis of the current beat:** "straight 8th hats with offbeats delayed ~30 ms" at 80 BPM equals only ~54% 8th-note swing (30/750) — mild, which is fine, but if only hats are swung while kick, EP and melody remain dead straight, parts disagree on the grid, which can read as "off rhythm". Adding uniform random jitter to every part compounds this. Better: one shared groove (e.g. 16th swing 56-58%) on drums, bass, keys and melody, plus small *systematic* per-voice offsets (kick +5-10 ms late, snare -5 to +10 ms, hats at groove), with random jitter limited to ±3-5 ms or none.
- **Velocity rule set (derived from the 100/65/35% guidance above, mapped to MIDI 0-127):** kick downbeat 105-115, kick syncopated 85-95; snare backbeat 100-110, snare ghost 30-45; hat accents (on-beats) 80-95, offbeats 55-70, occasional hat ghosts 35-45; vary each per-bar by a hand-drawn curve (e.g. bar 4/8 slightly lifted) rather than flat random.
- Kick on 1 and 2.5 + snare 2/4 is a valid pattern; variation should come from moving a second kick (e.g. "a" of 2, "and" of 3, or 4.5 pickup) every 4th/8th bar and dropping a hat or snare in bar 8 into a fill (snare ghost roll, open hat on 4.5).
- Lowering tempo to 70-75 BPM with a half-time feel is in-genre; 80 BPM itself is not the problem — sources cover 60-90.

### Gaps
- No primary measurement of per-instrument ms offsets in lo-fi tracks; the 65 ms Dilla figure is secondhand.
- No authoritative source for specific hi-hat velocity numbers in lo-fi; values above are a general drum-programming guideline.
- No source found giving fill frequency rules specific to lo-fi beyond "4- or 8-bar phrases".

## 2. Chords, keys, and melody treatment (voicings, comping, Rhodes expression, flipping a known melody)

### Takeaway
Use 2-4 chord loops of 7th/9th chords (maj7, m7, m9, maj9, dominant 7 extensions) in close, mid-register voicings on electric piano, comped in simple rhythms with loose timing; process keys with downsampling, saturation, pitch wobble and low-pass. For a well-known melody, the genre approach is to treat it like a sample: chop, pitch, re-time and fragment it, not to play it straight top to bottom.

### Cited Findings
- Replace triads with major 7ths, minor 7ths and 9ths; loops of 2-4 chords on warm electric piano or sampled from records; common progressions I-vi-ii-V (Cmaj7-Am7-Dm7-G7) and ii-V-I (Dm7-G7-Cmaj7), each chord held 1-2 bars — [Flat.io blog](https://blog.flat.io/lofi-chord-progressions/)
- Add a 9th to the vi chord for color; start with 7ths then add 9ths and 11ths; two-chord VI-i loops create "a chilled, cyclical and relaxing atmosphere" — [Native Instruments lo-fi chords](https://blog.native-instruments.com/lo-fi-chord-progressions/)
- NI tutorial progression: VI-i-V7 in A minor (F, Am, E7) with extensions on an electric-keys instrument; downsampling + saturation preset on keys — [Native Instruments](https://blog.native-instruments.com/lo-fi-hip-hop/)
- Elephorm cheatsheet lists vi-V-I-IV (Am7-Gsus4-Cmaj7-Fmaj7) as chillhop/nostalgic (paywalled, summary only) — [Elephorm](https://www.elephorm.com/formation/audio-mao/guide-de-production-du-beatmaker-le-cheatsheet-par-style/harmonie-melodie-et-arrangement-lo-fi-chill-et-ambient)
- Example Rhodes loop: F#maj7-Bmaj7-A#m7-G#m9-G#m7 at 90 BPM — [Looperman](https://www.looperman.com/loops/detail/261737/chill-lofi-chords-free-90bpm-lo-fi-rhodes-piano-loop)
- Simple, pop-oriented 2-4 chord progressions in simple rhythms; a keys loop recorded at 110 BPM slowed to 74 BPM via time-compression adds lo-fi character; keys sidechained to kick — [Mode Audio](https://modeaudio.com/magazine/lofi-hip-hop-5-production-essentials)
- Leave melody timing unquantized for a "janky" out-of-time feel; use a counter-melody on a second instrument; melodic parts sent to reverb and delay — [Native Instruments](https://blog.native-instruments.com/lo-fi-hip-hop/)
- Chorus-Ensemble's Vibrato mode gives tape-warble pitch variation; Warmth dial for grit — [Mode Audio](https://modeaudio.com/magazine/how-to-produce-a-lofi-sound-in-any-daw)
- Simpler Slice mode chops at Transient/Beat/Region/Manual; Simpler creates no MIDI timing, you program the trigger rhythm — [RouteNote](https://routenote.com/blog/how-to-chop-samples-in-ableton/); [MusicRadar](https://www.musicradar.com/tuition/tech/how-to-chop-beats-with-ableton-simplers-new-slice-mode-632939)
- Sample flip definition and practice (chopping and rearranging a known source into a new phrase) — [Melodics](https://melodics.com/blog/what-is-a-sample-flip)

### Inferences
- **Voicing rules for MIDI generation (music-theory derived, not from a single source):** keep chord tones in ~C3-C5 (MIDI 48-72); left hand root (or root+7th) an octave below; right hand 3-7-9 or 7-9-3 close voicing; omit 5th. Examples in C: Cmaj9 = C2 | E3 B3 D4 (G optional); Am9 = A1 | C3 G3 B3 (or G3 B3 C4 E4); Dm9 = D2 | F3 C4 E4; G13 = G1 | F3 B3 E4; Fmaj9 = F2 | A3 E4 G4. Voice-lead so the top note moves by step or stays.
- **Christmas application:** Jingle Bells in F could use Fmaj9 - Dm9 - Gm9 - C13(sus) loops; harmonise the melody's long notes with these, not I-IV-V triads.
- **Comping:** rather than block hits always on 1 and "and of 3", vary: anticipate chord changes by a 16th or 8th (push into the next bar), hold whole notes in intro/breakdown, add a short re-strike on "a of 2". Strum chords 10-30 ms bottom-up (Live 12 Strum transformation) and spread velocity across chord tones (top note +10, inner voices -10).
- **EP expression:** velocity range roughly 50-100 with phrase-level shaping; tremolo/auto-pan at 1/4 or 1/8 synced, low depth; Chorus-Ensemble vibrato for wobble. (No source gave exact EP velocity numbers.)
- **Melody flip:** play the carol's hook only (e.g. "Jingle bells, jingle bells") as a 1-2 bar motif, displaced rhythmically (start on the "and", lengthen the last note, drop notes), double an octave up on glockenspiel or bells at -12 dB only on repeats, and answer it with a chord stab or counter-line (call-and-response). Present the full melody once, mid-track, and otherwise fragments. Rendering the melody, bouncing it, pitching it down and re-slicing in Simpler is the authentic "sample" route.

### Gaps
- No source found giving Rhodes velocity ranges or tremolo settings specifically for lo-fi.
- No published tutorial found on flipping public-domain carols in lo-fi style specifically.

## 3. Bass: patterns, sub vs upright, sidechain/ducking

### Takeaway
Bass in lo-fi is simple: chord roots in a basic rhythm on a warm sub, low-passed at ~150 Hz or below; some tracks omit bass entirely and let keys and kick carry the low end. Keys (and optionally the whole mix) are ducked by the kick via sidechain.

### Cited Findings
- Play a simple bass or sub that outlines chord roots in a basic rhythm; low-pass "right back to 150Hz or less" — [Mode Audio](https://modeaudio.com/magazine/lofi-hip-hop-5-production-essentials)
- Kick as sidechain key for keys; author also sidechains the rest of the mix to the kick — [Mode Audio](https://modeaudio.com/magazine/lofi-hip-hop-5-production-essentials)
- NI tutorial track has no dedicated bass; if added, play chord roots on a warm sub patch — [Native Instruments](https://blog.native-instruments.com/lo-fi-hip-hop/)
- Attack Magazine chillout beat: a heavily reverbed bass hit accents the first beat of each bar — [Attack Magazine](https://www.attackmagazine.com/technique/beat-dissected/chillout-beat-raw-strip-hop/)

### Inferences
- Root-only bass becomes "school-kid" if it hits on every chord onset with flat velocity. Improve with: root on 1, a passing 5th/octave or chromatic approach note on the "a" of 4 into the next chord, note lengths shorter than the chord (gaps), velocity 85-105.
- Sidechain amount for background music should be subtle: roughly 2-4 dB of ducking on keys/bass with fast attack and ~100-200 ms release (derived; no source gave numbers).
- Upright-bass samples suit the cafe/lounge Christmas brief; a sine sub suits the beat-tape feel. Either way, cap the bass low-pass around 150-400 Hz depending on whether pluck definition is wanted.

### Gaps
- No source gave numeric sidechain depth (dB) or release times for lo-fi.

## 4. Arrangement and form for a ~3-minute lo-fi track

### Takeaway
Form is loop-based and simple: intro of 4-8 bars (chords + texture, filtered or no drums), main loop that slowly gains or swaps layers every 4-8 bars, a breakdown where drums drop out, return, outro. Change comes from switching elements on and off, filter automation, and subtle ear candy, not from new harmony.

### Cited Findings
- Lo-fi structure is intentionally simple and repetitive; typical: intro, main loop that builds slightly, sometimes a breakdown, return to core groove — [Native Instruments](https://blog.native-instruments.com/lo-fi-hip-hop/)
- Intro of just chords and crackle; drop full drums and bass for main section; pull drums for a stripped-back bridge/breakdown — [Violet Recording](https://violetrecording.com/how-to-make-lofi-beats/)
- Chillhop form: Intro (4-8 bars) - A - B - Breakdown - A - Outro; lo-fi hip-hop as a 4- or 8-bar loop with elements switched on/off — [Elephorm cheatsheet](https://www.elephorm.com/formation/audio-mao/guide-de-production-du-beatmaker-le-cheatsheet-par-style/cheatsheet-de-production-lo-fi-chill-et-ambient)
- Drums often don't start until after several intro measures of unaccompanied chords — [Yamaha Hub](https://hub.yamaha.com/proaudio/recording/how-to-create-lo-fi)
- Keep the core to 3-4 elements; add 1-2 extra parts or background synths at points to guide flow — [Mode Audio](https://modeaudio.com/magazine/lofi-hip-hop-5-production-essentials)
- Automate a low-pass filter cutoff slowly across 8 or 16 bars for movement — [Violet Recording (lo-fi music)](https://violetrecording.com/how-to-make-lofi-music/)
- Reverse crash as ear candy into sections; introduce one element at a time over 4- or 8-bar phrases — [Native Instruments](https://blog.native-instruments.com/lo-fi-hip-hop/)
- Lo-fi tracks typically 1-3 minutes — [Native Instruments](https://blog.native-instruments.com/lo-fi-hip-hop/)

### Inferences
- **A 3:00 template at 80 BPM (1 bar = 3.0 s, 60 bars):** Intro 8 bars (keys + crackle, drums low-passed ~500 Hz or kick/rim only) -> A1 8 bars (full drums, bass, melody fragment) -> A2 8 bars (add counter-line/bells, hats open up) -> B 8 bars (chord variation or melody on different instrument) -> Breakdown 8 bars (drums out, filtered keys, melody snippet) -> A3 16 bars (full + variation, kick pattern change) -> Outro 4 bars (tape-stop or filter close, crackle tail). At 75 BPM, 60 bars = 3:12.
- Rule: each 8-bar boundary changes at least one layer; bar 8 of each section carries a fill or drop-out (e.g. drums cut on beat 4 of bar 8); no section runs more than 16 bars unchanged.
- For background (hotel/cafe) use, keep risers, tape stops and drop-outs subtle and few (1-2 per track); sudden silences can be distracting in venues.

### Gaps
- No source quantified how many layers change per section in commercial lo-fi.

## 5. Texture: vinyl, tape wow/flutter, low-pass, saturation (Ableton devices and settings)

### Takeaway
Typical Ableton chain: Saturator -> Redux/Vinyl Distortion -> Auto Filter (LP) -> Chorus-Ensemble (vibrato) -> Reverb. Keep degradation "felt more than heard"; low-pass drums ~2-3 kHz, high-pass vinyl noise ~20 Hz; pitch wobble via Chorus-Ensemble Vibrato or Frequency Shifter LFO.

### Cited Findings
- Redux: Downsample set to Soft, nudge up until the top end is noticeably aliased; Frequency Shifter for tape wobble with LFO Amount ~5 Hz and Rate ~2-3 Hz; Vinyl Distortion Crackle for background noise "but don't overdo it"; adjust Pinch frequency for color; small reverb Size (e.g. bathroom) — [Splice](https://splice.com/blog/lo-fi-piano-ableton/)
- Sound on Sound: Redux = bit-depth reduction and downsampling; Erosion = modulated very short delay with noise or sine; Erosion (noise) adds the most noise, Redux bit reduction close second; Vinyl (Tracing mode) and Saturator create the clearest peaks with least noise — [Sound on Sound](https://www.soundonsound.com/techniques/ableton-live-distortion)
- Chorus-Ensemble Vibrato mode for tape warble; Warmth for grit — [Mode Audio](https://modeaudio.com/magazine/how-to-produce-a-lofi-sound-in-any-daw)
- Community chain: Saturator -> Redux/Vinyl Distortion -> Auto Filter (LP) -> Chorus-Ensemble -> Reverb (community suggestion) — [skillsmp](https://skillsmp.com/ar/creators/korben00/ableton-producer-skills/skills-ableton-fx-chain)
- Every texture layer (tape hiss, field recordings, tape wobble, saturation) should sit "just below conscious hearing" — [Violet Recording](https://violetrecording.com/how-to-make-lofi-beats/)
- Over-processing is the common mistake; degradation should be felt more than heard; low-pass to sound "like it's playing from another room" — [Violet Recording](https://violetrecording.com/how-to-make-lofi-music/)
- Deep low-pass (~2 kHz) on each element pushes sounds back and softens transients; apply low-pass to most other parts too — [Mode Audio](https://modeaudio.com/magazine/lofi-hip-hop-5-production-essentials)
- Bandpass "telephone filter" as a final touch — [Splice/Origin Sound](https://splice.com/blog/?p=6189) (via search summary)
- Add vinyl crackle, tape hiss, or field recordings (soft rain, water) — [Mode Audio](https://modeaudio.com/magazine/lofi-hip-hop-5-production-essentials)

### Inferences
- **Starter settings to implement (derived; tune by ear):** Keys: Saturator Analog Clip, Drive +3 to +6 dB, Dry/Wet 30-50%; Redux bit depth 10-12 bits or downsample mild; Auto Filter LP 12 dB/oct at 3-5 kHz; Chorus-Ensemble Vibrato, rate ~0.5-1 Hz, low amount; reverb send with 1.5-2.5 s decay, pre-delay 20-30 ms, high-cut ~5 kHz. Drums: Drum Buss or Saturator light, LP 2.5-3.5 kHz, HP 30 Hz. Vinyl crackle return at -30 to -24 dBFS relative to mix (always below conscious hearing). Bass: LP 150-300 Hz.
- Roar (Live 12) and Hybrid Reverb are capable but no sourced lo-fi settings were found; Saturator/Redux/Vinyl Distortion/Chorus-Ensemble cover the sourced techniques.
- For hotel/cafe background use, go lighter than streaming lo-fi on crackle and bit-crush: listeners hear it at low volume for hours, and noise can read as "bad audio".

### Gaps
- No source gave numeric Roar, Hybrid Reverb, Echo or Erosion settings for lo-fi.
- No source gave a crackle level in dB.

## 6. Ableton Live 12 features: Groove Pool, MIDI Tools, note chance/velocity deviation, scale mode

### Takeaway
Live 12 ships MPC/SP-1200 swing grooves in the Core Library ("Swing and Groove"), applied via the Groove Pool with Base, Quantize, Timing, Random and Velocity; Commit writes the timing into MIDI. Live 12 MIDI Transformations (Strum, Ornament, Span, Recombine, Velocity Shaper, etc.) and Generators (Rhythm, Seed, Stacks, Shape, Euclidean) act destructively on clip notes; per-note Chance and Velocity Deviation give live variation every loop pass.

### Cited Findings
**Groove Pool**
- Base = timing resolution grooves are measured against (e.g. 1/4, 1/8); Quantize 0-100% snaps notes to Base before groove; Timing = how strongly the groove's timing affects the clip; Random adds random timing per voice (low values humanize); Velocity -100 to +100 (negative inverts groove's velocity pattern); Global Amount scales Timing/Random/Velocity, up to 130%; Commit writes MIDI note positions (Warp Markers for audio) and sets clip groove to None; grooves can be extracted from audio or MIDI clips — [Ableton Live 12 Manual, Using Grooves](https://www.ableton.com/en/manual/using-grooves/)
- Ableton's groove library includes grooves from the Akai MPC and E-mu SP-1200; find under Packs > Core Library > Swing and Groove; the number in the name is the swing % (e.g. "Swing 16th 64" = 64%); global groove amount must be 100% or swing is reduced — [Attack Magazine](https://www.attackmagazine.com/technique/tutorials/going-off-grid-what-is-swing-and-how-to-add-it/); [search summary incl. ask.audio](https://ask.audio/articles/all-about-groove-in-ableton-live)
- Grooves are timing data; drag to a MIDI track to see the notes — [Gearspace / search summary](https://gearspace.com/threads/groove-pools.1453884/)
- The grid moves, not the notes: notes look straight in the piano roll but play swung (until committed) — [Attack Magazine](https://www.attackmagazine.com/technique/tutorials/going-off-grid-what-is-swing-and-how-to-add-it/)

**MIDI Transformations and Generators (Live 12)**
- Transformations: Arpeggiate, Chop, Connect, Glissando (MPE), LFO (MPE), Ornament (Flam or Grace Notes with Position, Velocity, Chance, Amount), Quantize (with Amount), Recombine, Span (Legato/Tenuto/Staccato, Offset, Variation), Strum (Strum Low/High up to one grid step at ±100%, Tension), Time Warp, Velocity Shaper (M4L; envelope breakpoints, Min/Max velocity, Loop, Rotate, Division) — [Ableton Live 12 Manual, MIDI Tools](https://www.ableton.com/en/live-manual/12/midi-tools/)
- Generators: Rhythm (Steps up to 16, Density, Velocity, Accent, Accent Frequency/Offset), Seed (pitch/duration/velocity ranges, voices, density), Shape, Stacks (chord pads, root, inversion, duration; custom .stacks banks), Euclidean (M4L, up to 4 voices) — [Ableton Live 12 Manual, MIDI Tools](https://www.ableton.com/en/live-manual/12/midi-tools/)
- Transformations replace selected notes; generators add/replace notes; Auto Apply on by default; third-party M4L tools go in User Library "Max Transformations"/"Max Generators" folders — [Ableton Live 12 Manual, MIDI Tools](https://www.ableton.com/en/live-manual/12/midi-tools/)

**Per-note expression and editing**
- Chance per note 0-100%; Play All / Play One groups; randomize chance with a range — [Ableton Live 12 Manual, Editing MIDI](https://www.ableton.com/en/live-manual/12/editing-midi/)
- Velocity Deviation per note: random value chosen each playback (e.g. velocity 60 with +20 plays 60-80); Velocity Ramp; Velocity Randomize; Release Velocity lane — [Ableton Live 12 Manual, Editing MIDI](https://www.ableton.com/en/live-manual/12/editing-midi/)
- Humanize: randomizes note starts by up to a quarter of a grid division with an Amount slider — [Ableton Live 12 Manual, Editing MIDI](https://www.ableton.com/en/live-manual/12/editing-midi/)
- Scale Mode per clip (root + scale); Fit to Scale; scale-aware transpose/invert — [Ableton Live 12 Manual, Editing MIDI](https://www.ableton.com/en/live-manual/12/editing-midi/)

### Inferences
- **Programmatic route:** since MIDI tools are interactive and destructive, the generator (Python) should bake the equivalent results into notes (strum offsets, flams, velocity curves, swing) and use .als-level fields only for things Live evaluates at playback: per-note Probability and VelocityDeviation, and a clip Groove reference. From prior knowledge of the .als XML (gzip), MIDI notes are `MidiNoteEvent` elements with attributes including Time, Duration, Velocity, VelocityDeviation, OffVelocity, Probability, IsEnabled — this is unverified against an official schema and should be checked by saving a Live 12 set and inspecting it.
- **Suggested use:** Velocity Deviation of +/-8 to 12 on hats and ghost snares; Chance 60-80% on hat ghost notes and extra kick hits (bar-to-bar variation without writing new bars); Chance 100% on backbeat snare and downbeat kick. Groove: an MPC 16th swing ~56-58 with Timing 70-100%, Random 0-5%, Velocity 0-20%, Quantize 0% applied to drums, bass, keys and melody so everything shares a grid.
- Live's Humanize (up to 1/4 grid division) at a 1/16 grid at 80 BPM is up to ~47 ms each way — too large at high amounts; keep Amount low (~10-20%, i.e. ±5-10 ms).

### Gaps
- Exact list/names of MPC groove files in Live 12 Core Library not verified from a primary listing.
- No free Max for Live lo-fi device list verified in this research.
- .als field names not verified from an official source.

## 7. Mixing/mastering chain and loudness for background music; avoiding the amateur sound

### Takeaway
Spotify normalizes to -14 LUFS integrated and asks for true peak below -1 dBTP; Apple Music reportedly normalizes to -16 LUFS. Gentle glue on drums/mix (Ableton Glue Compressor 2:1, ~10 ms attack, 1-3 dB gain reduction) plus deep filtering and restraint on texture are the sourced mix moves. For in-venue background music, a consistent -16 to -14 LUFS master with preserved dynamics fits.

### Cited Findings
- Spotify plays back at -14 LUFS; recommends mastering to -14 LUFS integrated with true peak below -1 dBTP (below -2 dBTP if louder than -14 LUFS); Premium Loud = -11 LUFS, Quiet = -19 LUFS — [Spotify for Artists](https://support.spotify.com/artists/article/loudness-normalization/)
- Apple Music normalizes to -16 LUFS following AES TD1008 (secondary sources; no Apple primary doc found) — [Production Expert](https://www.production-expert.com/production-expert-1/apple-choose-16lufs-loudness-level-for-apple-music-heres-why); [Meterplugs, Mar 2022](https://www.meterplugs.com/blog/2022/03/23/apple-switch-to-lufs.html)
- Ableton Glue Compressor offers fixed 2:1, 4:1 and 10:1 ratios — [Music Guy Mixing](https://www.musicguymixing.com/?p=1417); [ProRec](https://ProRec.com/?p=4878)
- Drum bus: 2:1 as lightest option, ~1-2 dB average gain reduction, ~3 ms attack suggested — [Music Guy Mixing](https://www.musicguymixing.com/drum-bus-compression/); eMastered suggests 10 ms attack, 0.1 s release, 4:1, 2-3 dB GR — [eMastered](https://emastered.com/blog/glue-compressor)
- Fast attack can dull drum transients — [ProRec](https://ProRec.com/?p=4878)
- Forum: masters for streaming should not be quieter than -14 LUFS (forum opinion) — [Loopy Pro forum](https://forum.loopypro.com/discussion/comment/1313109/)
- Bob Katz attributed (secondhand) ~14 dB crest factor sounding good on vinyl, 12 dB for many digital releases — [Gearspace](https://gearspace.com/threads/vinyl-dynamic-range-or-lufs-targets.1429601/)
- EQ cuts starting at -3 to -6 dB depending on brightness (lo-fi acoustic) — [Acoustica forum](https://discourse.acoustica.com/?p=19830)
- Gentle compression smooths jarring dynamics; very subtle reverb glues chopped material — [Computer Music via PressReader / search summary](https://www.pressreader.com/australia/computer-music/20181228/282127817576259)

### Inferences
- **Chain to implement in Live 12 (derived):** per-track EQ Eight HP (kick 30 Hz, keys 120-150 Hz, melody 200 Hz, crackle 200 Hz) and LP as in section 5 -> drum group Glue Compressor 2:1, attack 10 ms, release Auto, 1-2 dB GR, Drum Buss light -> master: EQ Eight gentle (-1 to -2 dB shelf above 10 kHz if harsh), Glue Compressor 2:1, attack 30 ms, release Auto, 1-2 dB GR, Utility for mono below ~120 Hz, Limiter ceiling -1.0 dBTP (true peak mode), target -16 to -14 LUFS integrated, short-term range ~2-4 LU across sections.
- Background music for hotels/cafes is played at low level for hours; lower loudness (-16 LUFS) with intact dynamics is gentler than streaming-loud masters, and consistent loudness across a catalog matters more than peak loudness.
- "Amateur" tells relevant to the producer's critique: every part on the same flat velocity; melody stated literally from start to end; all parts entering together with no arrangement arc; harmonically plain triads; uniform random jitter instead of a shared groove; full-bandwidth bright sounds without low-pass shaping.

### Gaps
- No primary source for background-music-specific (in-venue) loudness targets; -16 to -14 LUFS is extrapolated from streaming specs.
- No authoritative Ableton-published mastering chain for lo-fi found.
