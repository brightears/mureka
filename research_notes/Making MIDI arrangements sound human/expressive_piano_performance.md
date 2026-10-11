# Expressive Piano Performance Modeling ("Humanization") for Programmatic MIDI Carol Arrangements

Scope: what skilled pianists measurably do (dynamics, timing, articulation, pedal), the published rule systems and ML models that encode it, and numeric rules a Python generator (note list of start, duration, pitch, velocity, plus tempo map and CC64) can apply before rendering in Ableton Live 12 / Grand Piano.

A sourcing note: several primary PDFs were read in full (Goebl 2001 JASA; Friberg, Bresin & Sundberg 2006 KTH overview; Friberg & Sundberg 1999 JASA final ritard; Bresin 2000 thesis "Virtual Virtuosity"; Dannenberg 2006 ICMC). Where I computed a number from a published formula or figure, the computation is in the Inferences section, not presented as a quote. Numbers I could not source are in Gaps.

---

## 1. Velocity and dynamics: ranges, melody voicing, phrase arches, accents, and what "no dynamics" means in MIDI

### Takeaway
Skilled pianists always play the melody (top voice) clearly louder than every other voice. In Goebl's 22-pianist Bösendorfer data, the melody's hammer velocity is about 1.0 m/s against about 0.5 to 0.8 m/s for the inner and bass voices, so roughly 1.3 to 2 times faster. They also shape loudness over each phrase as an arch: soft at the start, loudest in the middle, soft at the end. "Flat dynamics" in MIDI means constant or near-constant velocity across voices and across a phrase. The fix is structured velocity: a per-voice offset, plus a phrase-level curve, plus small metrical and melodic-tension terms. Random velocity jitter does not fix it.

### Cited Findings
- **Melody is consistently loudest.** In Goebl's study of 22 skilled pianists (Chopin Etude op. 10/3 and Ballade op. 38 on a Bösendorfer SE290), "All pianists played the first voice consistently louder than the other voices. None of the pianists chose another voice to be played as the loudest." — [Goebl 2001, JASA 110(1)](https://iwk.mdw.ac.at/goebl/papers/Goebl_JASA2001_melodyLead.pdf)
- **Magnitude of the melody/accompaniment gap.** In Fig. 6, the mean final hammer velocity (FHV) is about 1.0 to 1.1 m/s for voice 1 (melody). Right-hand inner voices sit around 0.7 to 0.8 m/s and left-hand voices around 0.5 to 0.6 m/s, read from the log-scaled plot. When pianists were asked to emphasise the melody further, its FHV rose from 1.01 to 1.28 m/s while "the accompaniment maintained its dynamic range." — [Goebl 2001](https://iwk.mdw.ac.at/goebl/papers/Goebl_JASA2001_melodyLead.pdf)
- **Within-voice velocity changes over time.** A per-note plot for one pianist (Fig. 9) shows the melody fluctuating between about 0.8 and 1.9 m/s over 9 bars, peaking around the phrase climax, while accompaniment voices stay around 0.4 to 1.0 m/s. In the Etude, the dynamic climax at bar 17 "caused a strong increase in the velocity values." — [Goebl 2001](https://iwk.mdw.ac.at/goebl/papers/Goebl_JASA2001_melodyLead.pdf)
- **Phrase arch (KTH rule).** A phrase is "typically slow/soft in the beginning, fast/loud in the middle and ends slow/soft, modeling a crescendo/accelerando decrescendo/rallentando pattern." The Phrase arch rule extends Todd's model with parameters for structural level, the amount of change at the start and end, the position of the arch maximum, the duration of the last note, and curve shape. "Several instances of the Phrase arch rule acting on different structural levels are applied simultaneously." — [Friberg, Bresin & Sundberg 2006, "Overview of the KTH rule system"](http://www.ac-psych.org/en/download-pdf/volume/2/issue/2/id/15) (DOI [10.2478/v10053-008-0052-x](https://doi.org/10.2478/v10053-008-0052-x))
- **High loud rule.** Sound level increases in proportion to pitch height. Because the highest pitch often sits mid-phrase, this alone produces a phrase-shaped dynamic contour. — [KTH overview 2006](http://www.ac-psych.org/en/download-pdf/volume/2/issue/2/id/15)
- **Melodic charge rule (tonal tension).** Melody notes far from the current chord root on the circle of fifths get increased sound level and duration in proportion to their "charge". For example, F# over a C major chord gets the largest emphasis and C gets none. Melodic charge correlates with Krumhansl-Kessler key profiles (r = 0.86). **Harmonic charge** produces gradual crescendi and rallentandi toward chords far from the key. — [KTH overview 2006](http://www.ac-psych.org/en/download-pdf/volume/2/issue/2/id/15)
- **Todd's model couples tempo and loudness.** Tempo and dynamics are linked through a physical analogy: tempo change is acceleration, dynamics is energy, and intensity is proportional to velocity squared. The model therefore predicts that loudness and tempo rise and fall together over a phrase. — [CCRMA summary of Todd 1992](https://ccrma.stanford.edu/~juanig/articles/towards/Model_Musical_Expression.html); tested against a Schubert Impromptu with mixed success — [Windsor & Clarke 1997](https://continuum-hypothesis.com/music/Windsor-ExpressiveTimingDynamics-1997.pdf)
- **Coupling is not universal.** Repp's Chopin studies found no significant relation between timing strategies and dynamics, which suggests the two are partly independently controlled at a local level. Repp's Träumerei work did find that dynamics tended to rise with pitch and tempo. — summarised in [Windsor & Clarke 1997](https://continuum-hypothesis.com/music/Windsor-ExpressiveTimingDynamics-1997.pdf) and the search summary of [Flossmann & Widmer 2011](https://www.cp.jku.at/research/papers/Flossmann_Widmer_ISPS_2011.pdf)
- **Emotion presets (KTH Table 2).** *Tender*: slow tempo, low sound level, legato, small phrase arch, small final ritardando, small punctuation. *Sad*: slow, low level, legato, large phrase arch, negative duration contrast. *Happy*: somewhat fast, medium level, staccato, small phrase arch, large punctuation, large duration contrast. — [KTH overview 2006](http://www.ac-psych.org/en/download-pdf/volume/2/issue/2/id/15)
- **Velocity-to-loudness mapping is synth-specific.** MIDI does not define a velocity curve. Measured dynamic range (velocity 1 to 127) across commercial synths varies by more than 60 dB, and 20 to 60 dB is typical. Dannenberg proposes a square-law mapping, amplitude = (m·v + b)², with a 60 dB range. — [Dannenberg 2006, "The Interpretation of MIDI Velocity", ICMC](https://www.cs.cmu.edu/~rbd/papers/velocity-icmc2006.pdf)
- **Producer practice: compress and lower velocities.** A Sound on Sound engineer applies a global velocity multiplier of 0.7 to 0.9 to MIDI piano, which both lowers and narrows the range because MIDI keyboards tend to produce harsh, high velocities. He also hand-fixes isolated spikes and left/right-hand imbalance. His example piano patch switches to a harder sample at velocity 100+, which is why he says to check each instrument's velocity response. — [Sound on Sound, "Better MIDI Pianos"](https://www.soundonsound.com/techniques/better-midi-pianos)
- **Brick-wall velocity is the classic tell.** Give the melody note of a chord a stronger velocity than the supporting notes, and avoid every hit sitting at the same level. — [LANDR blog](https://blog.landr.com/how-to-make-midi-instruments-sound-real/)
- **An ML velocity-only humanizer exists.** midihum (XGBoost on about 400 features, trained on 2,579 International Piano-e-Competition performances) rewrites every note's velocity in a MIDI file and leaves timing alone. — [midihum README](https://github.com/erwald/midihum/blob/master/README.md)

### Inferences
- **"No dynamics" in MIDI terms.** There are three failure modes: (a) every note at one velocity, or within a narrow ±5 band; (b) melody and accompaniment at the same level, so the tune does not sing; (c) no phrase-level contour, so bar 1 and the phrase climax are equally loud. All three are visible in a velocity-vs-time plot per voice. Target behaviour, from the Goebl figures: a melody line that clearly sits above the other voices and moves in arches, and accompaniment that is lower and flatter.
- **Suggested velocity budget for soft background piano (pp to mf).** These numbers are a heuristic, not sourced. Calibrate by ear on Ableton Grand Piano, because its velocity curve and layers are undocumented here.
  - Melody: base about 62, phrase-arch range about 52 to 80.
  - Inner voices and chord tones (right hand): melody minus 12 to 20.
  - Bass and left-hand accompaniment: melody minus 15 to 25, with the bass root a few points above left-hand inner notes so harmony stays anchored.
  - The ratio logic: Goebl's melody FHV is about 1.3 to 2 times the accompaniment's. Under a square-law synth curve, a velocity ratio of about 1.3 (for example 65 vs 50) is a few dB. That matches the "clearly but not grossly louder" listening impression; treat the dB figure as approximate.
  - Never exceed about 95 in a soft carol arrangement, and keep below any harder-sample layer switch if the patch has one. This follows the SOS multiplier advice.
- **Phrase dynamic arch (implementable).** For each phrase (typically 2 or 4 bars in carols), multiply or offset melody velocity by an arch with its peak at the melodic high point or about 60 to 70% through the phrase. Use about +8 to +15 velocity at the peak and −5 to −10 at the phrase start and end. Nest a smaller arch (about ±4) at the sub-phrase level, as KTH applies arches at several structural levels. Apply about half the amount to accompaniment so the voices breathe together.
- **Section-level dynamics.** Over the whole carol, plan verse dynamics, for example verse 1 mp, verse 2 slightly fuller, final verse peaking mf, coda softer. A pure local arch repeated identically every 4 bars becomes mechanical in its own way.
- **Metrical accents.** Add about +3 to +6 on beat 1, about +2 on secondary strong beats (beat 3 in 4/4), and nothing on weak beats. Keep it small: KTH lists metrical patterns as a rule group, but the strong cues come from phrase and melody voicing, and big beat accents sound like a beginner's "counting".
- **Melodic charge or tension.** Give non-chord tones (appoggiaturas, suspensions, chromatic notes) about +3 to +8 velocity and a slight lengthening, and give the resolution note slightly less. This is the cheap, high-value part of KTH Melodic charge.
- **High-loud.** Add about +0.3 to +0.5 velocity per semitone above the phrase's median pitch for the melody. This approximates the KTH High loud rule.
- **Density.** When note density rises (running eighths in the accompaniment, thicker chords), lower the per-note velocity of the accompaniment by a few points so the summed loudness does not jump. This is an inference; I found no study quantifying a density-velocity rule.

### Gaps
- No source found giving canonical MIDI velocity values for pp, p, mp and mf on a sampled piano. These are instrument-dependent, as Dannenberg shows, and Ableton Grand Piano's velocity curve and layer split points were not found.
- Repp's (1996b) melody-vs-accompaniment differences in MIDI velocity units (Disklavier) were not retrieved, only their correlation with timing.
- Exact default parameter values of the KTH Phrase arch rule (amount of tempo and level change at k=1, the turn position) were not in the overview. They are in Friberg 1995 / Director Musices docs, which were not fetched.

---

## 2. Timing: melody lead, chord spreading, micro-timing noise, rubato and phrase-level tempo, final ritardando, and random vs. structured deviations

### Takeaway
On a real piano the melody arrives about 20 to 30 ms before the accompaniment. This is mostly a physical side effect of striking it harder, because faster hammers reach the string sooner. A sample player has no hammer travel, so a programmed MIDI file must add the lead explicitly. Phrase-level tempo should follow arches (slightly faster mid-phrase, slower at phrase ends). The final ritardando has a well-validated formula: tempo v(x) = [1 + (w^q − 1)·x]^(1/q), with q = 2 to 3 and final tempo w ≈ 0.3 to 0.5 of the initial tempo. Uncorrelated random jitter is the wrong model. Listeners prefer long-range-correlated (1/f-type) deviations, and KTH's noise rule made performances sound more "human" but not more "musical".

### Cited Findings
**Melody lead and asynchrony**
- The melody "precedes other voices typically by around 30 ms (melody lead)" (Hartmann 1932; Vernon 1937; Palmer 1989, 1996; Repp 1996b). — [Goebl 2001](https://iwk.mdw.ac.at/goebl/papers/Goebl_JASA2001_melodyLead.pdf)
- Palmer (1989): the melody led by about 20 to 30 ms on average. The effect decreased in deliberately "unmusical" performances, and Palmer (1996) found it grew with expressiveness, familiarity and skill. — [Goebl 2001 lit. review](https://iwk.mdw.ac.at/goebl/papers/Goebl_JASA2001_melodyLead.pdf)
- **Measured lead in Goebl's data.** At the hammer-string (sound) level the melody preceded other voices by about 20 to 30 ms. At the finger-key level the within-hand lead was "reduced to about zero". Velocity differences explained about half the variance in asynchronies. — [Goebl 2001](https://iwk.mdw.ac.at/goebl/papers/Goebl_JASA2001_melodyLead.pdf)
- When asked to emphasise the melody, the lead grew to 40 to 50 ms. One pianist habitually led by 40 to 70 ms as a deliberate device. — [Goebl 2001](https://iwk.mdw.ac.at/goebl/papers/Goebl_JASA2001_melodyLead.pdf)
- **Bass anticipation (bass before melody).** Typically about 50 ms, sometimes up to about 180 ms. In one pianist's Etude, five bass leads ran 35 to 185 ms, and "most of the large bass leads occur at metrically important events." Between-hand asynchronies are generally larger, over 50 ms, than within-hand ones. — [Goebl 2001](https://iwk.mdw.ac.at/goebl/papers/Goebl_JASA2001_melodyLead.pdf)
- **Piano action timing.** The time from key press to hammer-string contact runs from about 160 ms at a very soft 0.32 m/s FHV to about 33 ms at 5.12 m/s (Fig. 4/5 TCC). Askenfelt and Jansson report 25 ms (forte) to 160 ms (piano). Repp measured about 110 ms of onset shift between MIDI velocities 30 and 100 on a Disklavier, fitted by a quadratic. — [Goebl 2001](https://iwk.mdw.ac.at/goebl/papers/Goebl_JASA2001_melodyLead.pdf)
- KTH also cites melodic lead as about 20 ms on average. — [KTH overview 2006](http://www.ac-psych.org/en/download-pdf/volume/2/issue/2/id/15)
- **Chord spread (producer practice).** Notes of live-played chords are naturally staggered, often from lowest to highest. Don't hard-quantise. Place each chord cluster so its rhythmic centre, about one third of the way from the first note's onset to the last, sits on the grid. Reduce spread slightly at faster tempi. — [Sound on Sound, "Better MIDI Pianos"](https://www.soundonsound.com/techniques/better-midi-pianos). A chord-tool vendor describes natural strum as "a few milliseconds" between attacks — [Cherry Audio Chord Player](https://store.cherryaudio.com/modules/chord-player)

**Phrase-level tempo (rubato)**
- Phrase arch: slow at the start, faster in the middle, slow at the end, applied simultaneously at several structural levels. — [KTH overview 2006](http://www.ac-psych.org/en/download-pdf/volume/2/issue/2/id/15)
- In 115 commercial recordings of Chopin's Etude op. 10/3 (bars 1 to 5), the dominant timing strategy was "major ritards at the ends of melodic gestures." Others were acceleration within gestures, lengthening of the initial downbeat, and ritards between and within gestures. The first unrotated principal component explained 61.4% of timing variance. — [Repp 1998, JASA](https://www.continuum-hypothesis.com/music/repp1.pdf)
- **Duration contrast rule.** Lengthen long notes and shorten short notes by a fixed number of ms that depends on the IOI. The shorter note of a long-short pair shows a floor of about 100 ms. Negative k values give the opposite: a smoother, calmer effect. Increasing contrast raises perceived "energy". — [KTH overview 2006](http://www.ac-psych.org/en/download-pdf/volume/2/issue/2/id/15)
- **Faster uphill.** Notes in ascending motion are shortened. — [KTH overview 2006](http://www.ac-psych.org/en/download-pdf/volume/2/issue/2/id/15)
- **Punctuation.** Find short melodic fragments, using 13 sub-rules for leaps and long notes in a five-note context. Lengthen the last note of each fragment and insert a micropause after it. — [KTH overview 2006](http://www.ac-psych.org/en/download-pdf/volume/2/issue/2/id/15)
- **Double duration.** In 3/4 and 6/8, half-quarter (2:1) patterns are played with reduced contrast, keeping the summed duration constant. — [KTH overview 2006](http://www.ac-psych.org/en/download-pdf/volume/2/issue/2/id/15)
- **Melodic sync.** To keep all voices synchronised, build a merged voice of all onsets, choosing the note with the highest melodic charge at simultaneities. Apply timing rules to that merged voice and transfer the resulting tempo to all parts, so the short notes govern timing. Letting the accompaniment follow a lead part "led to many practical problems". — [KTH overview 2006](http://www.ac-psych.org/en/download-pdf/volume/2/issue/2/id/15)

**Final ritardando**
- Model: v(x) = [1 + (w^q − 1)·x]^(1/q). Here x is normalised score position (0 at ritard start, 1 at the last note's onset), v is tempo relative to the pre-ritard tempo, w is the final tempo, and q is curvature. q = 2 means constant braking force and q = 3 constant braking power. The listening test gave the highest ratings to q = 2 and q = 3. — [Friberg & Sundberg 1999, JASA 105(3)](https://continuum-hypothesis.com/music/Does_music_performance_allude_to_locomotion_A_mode.pdf); formula restated in [Honing 2005](https://mcg.uva.nl/mcg-2023/papers/honing-2005e.pdf)
- In measured ritardandi, which come from Baroque, motoric pieces, the final tempo w ranged from 32% to 51% of the initial tempo. It did not correlate with pre-ritard tempo (r = 0.02). The model fitted measured ritards with mean r² = 0.98. — [Friberg & Sundberg 1999](https://continuum-hypothesis.com/music/Does_music_performance_allude_to_locomotion_A_mode.pdf)
- Listening-test implementation details:
  - The ritard started at the first note onset at least 1.3 s (in pre-ritard time) before the last note.
  - The penultimate IOI was explicitly normalised to 1/(v_end·v_pre), because the penultimate note dominates the perceived ritard size.
  - The last note was set to 1.25 times the penultimate IOI, unless it was already longer. Long final notes can even be shortened.
  - Example final tempo: v_end = 0.3 in one model variant; v_end = 0.4 is used as an example.

  — [Friberg & Sundberg 1999](https://continuum-hypothesis.com/music/Does_music_performance_allude_to_locomotion_A_mode.pdf)
- KTH uses either Phrase arch or Final ritardando for overall phrasing at the end, because the two overlap. — [KTH overview 2006](http://www.ac-psych.org/en/download-pdf/volume/2/issue/2/id/15)

**Noise: random vs. structured**
- KTH Noise rule: (1) white-noise "motor delay" on each onset and level, with no drift; (2) 1/f "timekeeper" noise scaled by IOI, which gives slow tempo drift. Total deviation follows the JND. Listeners rated performances with noise as more "human" but **not more "musical"** than without. — [KTH overview 2006](http://www.ac-psych.org/en/download-pdf/volume/2/issue/2/id/15)
- For IOIs under 250 ms, timing JNDs do not follow Weber's law, with a lower bound of about 100 ms. KTH deviations are mostly scaled relative to tempo, except Duration contrast and Ensemble swing. — [KTH overview 2006](http://www.ac-psych.org/en/download-pdf/volume/2/issue/2/id/15)
- DAW humanize functions are "essentially random number generators producing only simple uncorrelated fluctuations". Human rhythmic deviations are long-range correlated. Listeners strongly preferred LRC fluctuations: 64% preferred them to random-error versions, and 79% said they sounded more precise. — [Hennig et al. 2011, PLoS ONE 6(10): e26457](https://doi.org/10.1371/journal.pone.0026457); [Harvard Gazette summary](https://news.harvard.edu/gazette/story/2012/07/when-the-beat-goes-off)
- SOS advises against DAW "humanise" as a substitute for real performance timing. — [Sound on Sound](https://www.soundonsound.com/techniques/better-midi-pianos)
- Listeners can detect timing differences of about 20 ms. About 50 ms is a common alignment tolerance. — [AUDITORY list discussion](https://auditory.org/postings/2019/231.html) (secondary, informal)

### Inferences
- **Melody lead must be programmed explicitly for a sampler.** On an acoustic piano the 20 to 30 ms lead emerges from the velocity difference through hammer travel time. A sampled Grand Piano starts every sample at its MIDI onset whatever the velocity, so the effect disappears unless coded. Two options:
  - Simple: shift every melody note that coincides with accompaniment 15 to 30 ms earlier. Use 20 ms as the default and up to 40 ms at expressive peaks. Never exceed about 50 ms within the right hand.
  - Physically motivated: an onset delay derived from Repp's 110 ms span between velocity 30 and 100 with a quadratic fit, delay(v) ≈ 0.0127·(127 − v)² ms. Apply it to all notes, then subtract a constant so the melody lands on the grid. Melody at 75 vs accompaniment at 55 gives about 31 ms lead; 70 vs 60 gives about 16 ms. This automatically ties lead to voicing, which is what Goebl's data show.
- **Bass anticipation.** Occasionally, on strong downbeats or at section starts, about once every 4 to 8 bars rather than constantly, play the bass 30 to 60 ms before the melody. This is a romantic gesture. Use it sparingly in carols.
- **Chord spread.**
  - Block accompaniment chords: spread roughly 5 to 20 ms from bottom to top in total, with smaller spread at faster tempo and for softer, homophonic textures. This is an inference: SOS gives no ms figure, but Goebl's within-hand asynchronies sit within about 30 ms.
  - Deliberate rolled chords (arpeggiando at cadences or big moments): 30 to 80 ms per note.
  - Centre the cluster about one third into the spread, per SOS.
- **Phrase tempo arch (tempo map).**
  - Per 4-bar phrase: start at about 97 to 98% of base tempo, rise to about 101 to 103% mid-phrase, then slow to about 90 to 94% over the last 1 to 2 beats into the phrase-final note. Lengthen the phrase-final note itself by 10 to 25%.
  - Optionally add a micro-breath of 30 to 80 ms (punctuation) before the next phrase's pickup.
  - Apply it at two levels, 4-bar and 8 or 16-bar, with the smaller level about half the depth.
  - Tie velocity to the same curve: faster = louder, per Todd and the KTH phrase arch.
  - These depths are heuristics consistent with the KTH and Repp descriptions, not sourced values. For tender or slow carols the KTH palette says a *small* phrase arch, so keep tempo swings within about ±3 to 5%.
- **Final ritardando (concrete).**
  - Start about 1.3 s, or about 2 to 4 beats at carol tempi, before the final chord's onset. Use q = 2.5 and w = 0.45 to 0.55 for a gentle carol ending; the measured 0.32 to 0.51 is from motoric Baroque, so a lyrical piece may already be slower.
  - Compute v(x) at each onset and set IOI_i = nominal_IOI_i / v(x_i). Force the penultimate IOI to about nominal/w, and make the last note at least 1.25 times the penultimate IOI, or keep its written long value.
  - Use the same curve to reduce velocity by about 5 to 15 into the final cadence (diminuendo), unless the arrangement ends loud.
- **Inner-phrase cadences.** Use a mini version of the same formula over the last 1 to 2 beats, with w of about 0.8 to 0.9.
- **Noise layer (last, smallest).**
  - Onset noise: SD of about 3 to 8 ms, low-passed or 1/f-correlated rather than independent per note.
  - Velocity noise: SD of about 2 to 4 units.
  - Keep notes of a chord correlated, with no independent per-note jitter beyond the spread pattern.
  - This layer only adds "human" texture. KTH shows it does not add musicality; the structured rules above do.
- **Implementation via tempo map vs. note shifts.** Put global and phrase rubato in the tempo map, which Ableton can follow. Put melody lead, chord spread and noise as absolute ms offsets on note onsets. The ms offsets must be converted using the local tempo, otherwise slowing the tempo map scales them up.

### Gaps
- Quantitative standard deviations of onset noise from large datasets (MAESTRO / ASAP) were not found in published form. The KTH paper gives the noise structure but not its SDs.
- Published % tempo depth for phrase-level rubato in lyrical, carol-like music was not found. Repp's Träumerei data (1992) would give it but were not retrieved.
- No source measured chord spread in ms for block chords specifically (apart from melody lead).

---

## 3. Articulation and legato: overlaps, staccato lengths, release velocity

### Takeaway
Pianists' legato is real key overlap, not exact note-to-note abutment. The overlap grows in ms as notes get longer and shrinks as a fraction of the IOI. It is larger in "passionate" playing, smaller in "flat" playing, and larger in descending lines. Natural staccato leaves a silence of about 60% of the IOI, meaning the note sounds about 35 to 40% of its written value. Repeated notes leave about 40% silence.

### Cited Findings
- Definitions: KOT (key overlap time) is the time two successive keys are both down. KDT (key detach time) is the gap with neither down. KOR = KOT/IOI and KDR = KDT/IOI. — [Bresin 2000, "Virtual Virtuosity" (thesis), KTH](https://www.speech.kth.se/music/publications/thesisrb/virtual%20virtuosity%20KTHB.pdf)
- Legato analysis of 2,237 notes from Mozart K 545: a larger IOI gives a lower KOR but a larger absolute KOT. KOR is highest for "passionate", lowest for "flat" and intermediate for "natural" playing. Notes in descending patterns are played more legato than in ascending ones. Bresin's Fig. 1 (KOT vs IOI, comparing Repp 1997, Bresin & Battel, MacKenzie & Van Eerd) spans about 0 to 140 ms of KOT over IOIs of 0 to 1,600 ms; Repp's values are the largest and MacKenzie's the smallest. — [Bresin 2000](https://www.speech.kth.se/music/publications/thesisrb/virtual%20virtuosity%20KTHB.pdf)
- **Score legato rule (Director Musices)**, with DRO = offset-to-onset duration (negative means overlap), IOI in ms:
  - For 0 < K ≤ 1: KOT = (IOI·(−4.3e−6·K − 6.6e−6) + 58.533e−3·K + 113.15e−3)·IOI
  - For 1 < K ≤ 5: KOT = (IOI·(0.5e−6·K − 0.11e−3) + 0.01105·K + 0.16063)·IOI
  - K = 5 is passionate legato, K = 1 natural, K = 0.1 flat.

  — [Bresin 2000](https://www.speech.kth.se/music/publications/thesisrb/virtual%20virtuosity%20KTHB.pdf) (an errata PDF exists on the [thesis page](https://www.speech.kth.se/music/publications/thesisrb/); not checked)
- **Staccato.** KDR is independent of IOI, about 60% for natural performances, higher for bright or light styles and lower (mezzo-staccato) for heavy ones. Across 13 Mozart sonatas KDR ran from 61% (Adagio) to 80% (Menuetto). Isolated staccato notes had the highest KDR. Repeated staccato notes and uphill contours had higher KDR than downhill ones. — [Bresin 2000](https://www.speech.kth.se/music/publications/thesisrb/virtual%20virtuosity%20KTHB.pdf)
- **Score staccato rule.** For 0 < K ≤ 1: KDT = (0.458·K + 0.207)·IOI. For 1 < K ≤ 5: KDT = (0.0216·K + 0.643)·IOI, multiplied by pitch-contour, context and tempo-indication factors (tempo-indication 1, 1.15 or 1.3 depending on marking). K = 5 is staccatissimo, 3 light, 1 natural, 0.6 default staccato, 0.5 heavy, 0.1 mezzostaccato. — [Bresin 2000](https://www.speech.kth.se/music/publications/thesisrb/virtual%20virtuosity%20KTHB.pdf)
- **Repeated notes.** KDR is about 40% of the IOI. Unlike staccato, KDR varies with IOI: KDT is roughly constant across IOIs in natural and heavy playing. — [Bresin 2000](https://www.speech.kth.se/music/publications/thesisrb/virtual%20virtuosity%20KTHB.pdf)
- **Overall articulation rule (KTH).** At k = 1, an articulation ratio (sounding duration/IOI) of 0.75 is applied to all notes longer than 100 ms. — [KTH overview 2006](http://www.ac-psych.org/en/download-pdf/volume/2/issue/2/id/15)
- Key overlap increases non-linearly as tempo slows for scales and arpeggios at IOIs of 100 to 1,000 ms (two-process model). — [Jacobs & Bullock, BU](https://open.bu.edu/items/ee3547df-d786-4b26-a531-e93edb2bf945)
- Caveat on measured touch: neither the Disklavier nor the Bösendorfer SE could capture or reproduce different types of touch. — [Goebl & Bresin 2003, JASA](https://iwk.mdw.ac.at/goebl/papers/Goebl-Bresin_JASA2003_reproAccuracy.pdf)

### Inferences
- **Computed natural legato (K = 1) from Bresin's formula:**

  | IOI | KOR | Overlap |
  |---|---|---|
  | 250 ms | ≈ 0.169 | ≈ 42 ms |
  | 500 ms | ≈ 0.166 | ≈ 83 ms |
  | 1,000 ms | ≈ 0.161 | ≈ 161 ms |

  The 1,000 ms value is above the roughly 140 ms ceiling of Bresin's own Fig. 1, so check the errata. A safe implementation: overlap = clamp(0.10 to 0.15 × IOI, 15 ms, 100 ms) for legato melody, more on descending steps (about ×1.2) and less on ascending (about ×0.9).
- In a sampled piano with the sustain pedal down, legato overlap matters mainly for unpedalled passages and the melody. With pedal, the note-off is masked until the pedal lifts, but overlap still affects re-pedal timing and how the line sounds when the pedal changes.
- **Non-legato or "portato" accompaniment** (for example repeated chords in a carol's left hand): sounding duration about 75 to 85% of IOI (the KTH overall articulation of 0.75). Repeated notes: sounding about 60% of IOI (KDR about 40%).
- **Staccato** (if ever used for "Jingle Bells"-type carols): sounding about 35 to 50% of IOI for natural or light staccato. Shorter in fast or dance tempi, longer in Adagio. Uphill notes slightly shorter than downhill.
- **Release velocity:** I found no evidence that Ableton's Grand Piano responds to MIDI note-off velocity. Set it to a constant, such as 64, unless the instrument documentation says otherwise.

### Gaps
- Repp 1997 (JASA 102: 1878–1890) legato KOT tables in ms were not retrieved directly, only via Bresin's comparison figure.
- No source found on release-velocity handling in Ableton Grand Piano.

---

## 4. Sustain pedal practice: syncopated (legato) pedalling, half-pedal, CC64 programming

### Takeaway
Standard practice is syncopated, or legato, pedalling. The pedal goes up briefly just after each new harmony is struck and comes back down at once, so the new chord is caught while the old one is damped. In CC64 terms: mostly 127, dropping to 0 for a short window just after each chord change. Half-pedal is generally not worth modelling for mainstream production. CC64 interpretation differs between players: some treat any value above 0 as down, others use a threshold near 64.

### Cited Findings
- **CC64 practice.** Value 127 means down and 0 means up. Keep it at 127 most of the time and drop to 0 briefly just after each chord change, then reapply.
  - Lifting too early: the previous chord won't connect smoothly.
  - Lifting too late: the new chord clashes with the old sustain.
  - Up-time too long: sustain is lost. Too short: the previous chord isn't fully damped.

  Pedal most of the time, even where hands could hold the notes. Modelling half-pedal is "overkill" for mainstream productions. — [Sound on Sound, "Better MIDI Pianos"](https://www.soundonsound.com/techniques/better-midi-pianos)
- Syncopated pedalling is described as changing the pedal just after the harmony is played, which preserves legato and avoids harmonic overlap. This is a pedagogy source, not research. — [pedagogy page via search](https://www.elliptic.co/corpus/gen-3040/piano-sonata-in-c-major-d-279-schubert/pianistic-technique.html)
- VirtuosoNet writes sustain as CC64 and notes that players differ: Logic Pro X treats any value above 0 as pedal down, while a Disklavier uses a threshold near 64. A boolean-pedal option exists for output that is too wet. — [VirtuosoNet README](https://github.com/jdasam/virtuosoNet)
- Repp studied pedal timing in 1994/1997 and found deviations from simple proportionality to tempo and effects of musical context. The ms values were not retrieved. — [summary via search, EUSIPCO 2018 paper](https://new.eurasip.org/Proceedings/Eusipco/Eusipco2018/papers/1570437306.pdf)
- Pedal technique "subtly colour[s] the timbre" through the timing and depth of press and release. — [QMUL deep pedal project](https://mat.qmul.ac.uk/projects/deep-pedal)
- MAESTRO MIDI includes sustain, sostenuto and una corda positions as continuous values, so real pedal curves are available for study. — [Hawthorne et al. 2019, MAESTRO](https://arxiv.org/pdf/1810.12247)

### Inferences
- **Programmable recipe.** These are heuristics; tune them by ear on Ableton Grand Piano.
  1. At each harmony change at time t (score time), set CC64 = 0 at t + 20 to 60 ms after the new chord's onset (after any chord spread). Set CC64 = 127 at about 60 to 120 ms after that. At slow tempi lean longer; at fast harmonic rhythm lean shorter.
  2. Keep the pedal down through stepwise melodic passing tones within one harmony. Re-pedal if a melody note clashes strongly, for example a scalar run across a sustained non-chord tone in the bass register.
  3. Put the first pedal-down just after the first note of the piece, never before it, to avoid catching unintended resonance.
  4. Lift the pedal fully (0) after the final chord only at the very end, after the release tail, or fade CC64 down in steps if the instrument supports half-pedal.
  5. If the Grand Piano preset applies sympathetic or pedal-down resonance, a slight "pre-pedal" (down before the first note) may sound more open. Test it.
- Because the pedal masks note-offs, accompaniment note lengths under pedal matter less. Melody note lengths still determine what is heard at each pedal change.
- **Use only 0/127 values** unless you confirm Ableton Grand Piano responds to intermediate CC64 values. Intermediate values may be thresholded, as with the Logic vs Disklavier difference.

### Gaps
- No research source found with measured ms values for pedal-change latency after chord onset (Repp 1996/1997 Psychology of Music / JASA not retrieved).
- Ableton Grand Piano's CC64 behaviour (threshold vs continuous half-pedal, damper-noise samples) was not found.

---

## 5. Research models and code: KTH Director Musices, Todd, Widmer, VirtuosoNet, ScorePerformer, Performance RNN, Basis Mixer, and 2023-2026 score-to-performance systems

### Takeaway
For a carol pipeline the most practical path is to implement a compact KTH-style rule set ourselves: phrase arch, final ritardando, melody voicing and lead, duration contrast, punctuation, articulation, and pedal. It is transparent, controllable and licence-free. The off-the-shelf options are:
- **Pianist Transformer** (2025, Apache-2.0): takes a score MIDI and outputs expressive MIDI with a DAW-ready tempo map and pedal. It is the most directly usable model today.
- **VirtuosoNet**: needs MusicXML. It won RenCon 2025 per its README, and its licence is not stated.
- **ScorePerformer**: CC BY-NC-SA, non-commercial, so not suitable for commercial tracks.
- **Basis Mixer** (built on partitura, Apache-2.0): renders from any partitura-readable score, but ships only a demo model.
- **Performance RNN**: unconditional, so it cannot humanize a given score.

### Cited Findings
**Rule-based**
- KTH rule system: about 30 to 40 parameters, grouped into phrasing (Phrase arch, Final ritardando, High loud), micro-timing (Duration contrast, Faster uphill), metrical patterns (Double duration, Inégales), articulation (Punctuation, Score legato/staccato, Repetition articulation, Overall articulation), tonal tension (Melodic, Harmonic, Chromatic charge), intonation, ensemble timing (Melodic sync, Ensemble swing) and noise. Rules combine additively or multiplicatively. Each has a quantity k, and negative k inverts a rule. Phrase structure and harmony must be supplied manually; only Punctuation finds its own boundaries. Implemented in Director Musices (Lisp, offline) and pDM (real-time). — [KTH overview 2006](http://www.ac-psych.org/en/download-pdf/volume/2/issue/2/id/15); rule list at [KTH performance rules page](https://www.speech.kth.se/music/performance/performance_rules.html)
- Figure 2 of the KTH overview demonstrates the combination of Phrase arch, Duration contrast, Melodic charge (k = 2) and Punctuation (others at k = 1) on a nursery tune. This makes it a ready-made rule palette for a simple tune, analogous to carols. — [KTH overview 2006](http://www.ac-psych.org/en/download-pdf/volume/2/issue/2/id/15)
- Widmer (2002) machine-learned 17 rules for local timing variation from pianist data. — cited in [KTH overview 2006](http://www.ac-psych.org/en/download-pdf/volume/2/issue/2/id/15)
- Todd's model (1985, 1989, 1992): phrase-structure-driven, tempo and dynamics coupled via a kinematic or energy analogy. — [CCRMA summary](https://ccrma.stanford.edu/~juanig/articles/towards/Model_Musical_Expression.html); [Windsor & Clarke 1997](https://continuum-hypothesis.com/music/Windsor-ExpressiveTimingDynamics-1997.pdf)

**Learned models with code**
- **VirtuosoNet (Jeong et al. 2019; maintained repo).**
  - Input: MusicXML (`--xml_path`).
  - Composer conditioning required (16 composers; Bach, Beethoven, Chopin, Haydn, Liszt, Mozart, Ravel and Schubert work best).
  - Outputs a MIDI performance with tempo, velocity, onset deviation and CC64.
  - Pretrained HAN+GRU checkpoint on HuggingFace (`dasaem/virtuosonet`). Its README says this is the RenCon 2025 submission that "placed 1st".
  - Licence not stated on the README.

  — [jdasam/virtuosoNet](https://github.com/jdasam/virtuosoNet)
- **ScorePerformer (Borovik & Viro, ISMIR 2023).** A transformer with hierarchical style encoders (global, bar, beat, onset) and performance-direction control. Colab demo. Alignment and preprocessing code "deliberately not made available". **Licence CC BY-NC-SA 4.0.** — [ilya16/ScorePerformer](https://github.com/ilya16/ScorePerformer); [ISMIR paper](https://archives.ismir.net/ismir2023/paper/000069.pdf)
- **Pianist Transformer (arXiv 2512.02652, Dec 2025).**
  - Self-supervised pre-training on 10B MIDI tokens, then rendering from a score MIDI loaded through the GUI.
  - Outputs a standard MIDI file with "Expressive Tempo Mapping": timing and velocity deviations converted into a tempo track that can be imported into any DAW.
  - Pedal control points per note, with a "Pedal Offset" slider. Runs on CPU, faster on GPU.
  - Checkpoints on HuggingFace and ModelScope. **Licence Apache-2.0.**

  — [arXiv](https://arxiv.org/abs/2512.02652); [project page](https://yhj137.github.io/pianist-transformer-demo/); [GitHub yhj137/PianistTransformer](https://github.com/yhj137/PianistTransformer)
- **DExter (Zhang et al., Applied Sciences 2024)** is a diffusion model. It beat other systems on Chopin, while Basis Mixer and VirtuosoNet did better on Bach and Beethoven. A 2025 paper reports very high, unstable velocity variance. — per search summaries of [arXiv 2406.14850](https://arxiv.org/html/2406.14850) and [arXiv 2509.23878](https://arxiv.org/pdf/2509.23878) (not read in full)
- **Joint rendering and transcription (arXiv 2509.23878, 2025).** Disentangles score content and performance style. Its duration and velocity variances reportedly match human performances closely. — [arXiv 2509.23878](https://arxiv.org/pdf/2509.23878) (snippet only)
- **Basis Mixer (OFAI).** Basis-function modelling of tempo, timing, dynamics and articulation. A `render_piece` script works on any partitura-readable score (MIDI, MusicXML, MEI, kern). The demo model is trained on the Vienna 4x22 corpus and is "not intended to represent the state-of-the-art". — [OFAI/basismixer](https://github.com/OFAI/basismixer). **partitura** (score/performance I/O library) is **Apache-2.0** — [CPJKU/partitura](https://github.com/CPJKU/partitura)
- **Performance RNN (Magenta, 2017).** Unconditional generation of new performances. Event vocabulary: 128 note-on, 128 note-off, 100 time-shifts of 10 ms, 32 velocity bins. Trained on about 1,400 Yamaha e-Competition performances. It does not perform an existing piece. — [Magenta blog](https://magenta.tensorflow.org/performance-rnn)
- **midihum.** Velocity-only humanizer (XGBoost, Piano-e-Competition data). Usage: `python main.py humanize in.mid out.mid`. Best on Baroque, Classical and Romantic solo piano. Licence not stated in README. — [erwald/midihum](https://github.com/erwald/midihum/blob/master/README.md)
- **KAIST expressive piano rendering page** (VirtuosoNet group). — [mac.kaist.ac.kr](https://mac.kaist.ac.kr/expressive_piano_performance_rendering.html)
- **Reviews** (pointers, not read in this session): Widmer & Goebl 2004, "Computational models of expressive music performance: The state of the art", JNMR 33(3), [doi:10.1080/0929821042000317804](https://doi.org/10.1080/0929821042000317804); Cancino-Chacón, Grachten, Goebl & Widmer 2018, "Computational Models of Expressive Music Performance: A Comprehensive and Critical Review", [Frontiers in Digital Humanities](https://www.frontiersin.org/articles/10.3389/fdigh.2018.00025/full)

### Inferences
- **Can any model take our MIDI score and output an expressive MIDI today?**
  - **Pianist Transformer:** yes, natively from MIDI. It has a DAW-friendly tempo map and a permissive Apache-2.0 licence, so it is the top candidate for an A/B test against a hand-coded rule set.
  - **VirtuosoNet:** yes, via MusicXML. Our generator could export MusicXML through music21 or partitura. The licence must be checked before commercial use.
  - **Basis Mixer:** yes, through partitura (MIDI accepted), but the demo model is weak.
  - **midihum:** velocity only.
  - **ScorePerformer:** licence-blocked for commercial use.
- All learned models were trained on classical competition repertoire. Carol arrangements are simpler and homophonic, and models may over-rubato them or apply Romantic mannerisms. A rule system tuned with the "tender" KTH palette (small phrase arch, legato, low level, small final ritard) is likely more controllable for background music.
- A hybrid is attractive: hand-code voicing, lead and pedal, which we know structurally because we generated the parts, and optionally use a model's tempo or velocity curves as one layer.

### Gaps
- Licences for VirtuosoNet, Basis Mixer and midihum were not confirmed (README pages did not state them; LICENSE files not opened).
- DExter code availability was not verified.
- No objective comparison of these models on simple homophonic material such as hymns or carols was found.

---

## 6. Datasets of real pianist deviations (MAESTRO, ASAP, (n)ASAP, Vienna 4x22) and published statistics

### Takeaway
MAESTRO (audio plus MIDI with pedal, about 3 ms alignment), ASAP and (n)ASAP (note-aligned score-to-performance for about 1,062 performances and 7.27M notes), and the Vienna 4x22 corpus (22 pianists, Bösendorfer) are the main resources. Published, ready-to-use deviation statistics (onset SD, velocity distributions per voice) are scarce. The most citable numbers remain those of Goebl 2001 and Repp. To get carol-specific targets, compute statistics yourself from (n)ASAP with partitura.

### Cited Findings
- **ASAP:** 222 scores (MusicXML plus quantised MIDI) aligned with 1,068 performances (over 92 hours), with beat, downbeat, time-signature and key annotations. — [ASAP, ISMIR 2020 (EPFL)](https://infoscience.epfl.ch/record/282307/files/ismir-asap.pdf)
- **(n)ASAP:** note-level alignments for about 7M annotated notes and close to 100 hours. Another count gives 1,062 performances and 7,275,074 notes. Alignments were checked manually, are public on GitHub, and come with the Parangonada correction tool. — [Peter et al., TISMIR 2023](https://transactions.ismir.net/articles/149); [ISMIR 2024 poster](https://ismir2024program.ismir.net/poster_518.html)
- **MAESTRO:** key-strike velocities and sustain, sostenuto and una corda pedal positions, with audio and MIDI aligned to about 3 ms. — [Hawthorne et al. 2019](https://arxiv.org/pdf/1810.12247)
- A 2025 dataset paper reports a negligible velocity-distribution difference between MAESTRO v3 and PianoVAM (Cohen's d = −0.0379), but gives no MAESTRO moments. — [PianoVAM, arXiv 2509.08800](https://arxiv.org/pdf/2509.08800)
- **Vienna 4x22 Piano Corpus** (Goebl): 22 pianists on Chopin op. 10/3, op. 38 and others. Openly published, doi:10.21939/4X22. — [mdw repository](https://repo.mdw.ac.at/projects/IWK/the_vienna_4x22_piano_corpus/index.html); [audio examples](https://iwk.mdw.ac.at/goebl/mp3.html)
- **Repp 1998:** timing in 115 commercial recordings of the Chopin Etude op. 10/3, analysed by PCA. Four strategies, with the first unrotated PC at 61.4% of variance; about 24% of variance was idiosyncratic. — [Repp 1998, JASA](https://www.continuum-hypothesis.com/music/repp1.pdf)

### Inferences
- **A one-day analysis that would give us house numbers:** load (n)ASAP with partitura (Apache-2.0) and filter to slow lyrical pieces, for example Chopin nocturnes, Schumann Kinderszenen and Mozart slow movements. Compute:
  - (a) velocity difference between the top voice and the rest at score-simultaneous onsets;
  - (b) onset asynchrony within chords;
  - (c) local beat-period curves around phrase ends;
  - (d) note-off/next-onset ratios.

  Then fit the parameters of the rules in section 7.

### Gaps
- No published per-voice velocity or onset-SD statistics from MAESTRO or ASAP were found. A secondary claim that MAESTRO velocities are "normally distributed, mostly medium" is unverified.
- No hymn or carol performance dataset was found.

---

## 7. Consolidated, implementable rule set for the Python generator (ordered by expected impact)

### Takeaway
Apply structured, music-aware deviations in this order: (1) voice-specific velocity with melody on top, (2) phrase arches for velocity and tempo together, (3) explicit melody lead and small chord spread, (4) phrase-end lengthening and a formula-based final ritardando, (5) legato overlap and proportional articulation, (6) syncopated CC64, and (7) only then a small correlated noise layer. Each rule maps to a cited finding above.

### Cited Findings
- Melody loudest, about 1.3 to 2 times the hammer velocity of other voices; lead 20 to 30 ms, 40 to 50 ms when emphasised — [Goebl 2001](https://iwk.mdw.ac.at/goebl/papers/Goebl_JASA2001_melodyLead.pdf)
- Phrase arch (tempo and level), High loud, Melodic charge, Duration contrast, Punctuation, Melodic sync, Overall articulation 0.75, Noise (human but not musical), Tender palette — [KTH overview 2006](http://www.ac-psych.org/en/download-pdf/volume/2/issue/2/id/15)
- Final ritard v(x) = [1 + (w^q − 1)x]^(1/q), q = 2 to 3, w = 0.32 to 0.51, start ≥ 1.3 s before the end, last note ≥ 1.25 times the penultimate IOI — [Friberg & Sundberg 1999](https://continuum-hypothesis.com/music/Does_music_performance_allude_to_locomotion_A_mode.pdf)
- Legato KOT formulas and staccato KDR of about 60%; repeated notes about 40% — [Bresin 2000](https://www.speech.kth.se/music/publications/thesisrb/virtual%20virtuosity%20KTHB.pdf)
- Correlated rather than white-noise humanization — [Hennig et al. 2011](https://doi.org/10.1371/journal.pone.0026457)
- CC64 lift just after each chord change; velocity multiplier 0.7 to 0.9; chord centre about one third into the spread — [Sound on Sound](https://www.soundonsound.com/techniques/better-midi-pianos)

### Inferences
These numbers are starting values for soft carol piano. Every value not directly cited above is a heuristic to tune by ear.

1. **Voice roles.** Tag each note as melody, inner, bass or accompaniment-pattern. The generator knows this. Base velocities: melody 62, inner 46, bass 50, broken-chord accompaniment 42. Clamp everything to 30 to 90.
2. **Phrase map.** Mark phrase boundaries every 2 or 4 bars from the carol's text lines, plus 8 or 16-bar sections.
   - Velocity arch: melody gains up to +12 at the phrase peak (the melodic high point, or about 65% through) and −6 at the boundaries. Accompaniment gets half that. Section level adds ±5.
   - Tempo arch: ×0.98 at the start, ×1.02 mid-phrase, ×0.92 over the last beat, and the phrase-final note lengthened by 15%. For gentle carols scale everything by 0.5 to 0.7 (the "tender" palette = small arch).
3. **Local emphasis.**
   - Downbeat: +4 velocity. Beat 3 in 4/4: +2.
   - Non-chord or appoggiatura melody notes: +5 velocity and +5 to 10% length. Resolution note: −3.
   - High-loud: +0.4 velocity per semitone above the phrase median, melody only.
4. **Melody lead.** Melody notes coinciding with accompaniment start 20 ms early, scaled from 10 to 35 ms by the melody-accompaniment velocity gap. Alternatively use delay(v) ≈ 0.0127·(127 − v)² ms on all notes, then re-centre on the melody.
5. **Chord spread.**
   - Accompaniment block chords: spread bottom to top over 6 to 15 ms total, with each chord's shape varied slightly but correlated with its neighbours.
   - Occasional bass anticipation of 30 to 50 ms on strong downbeats of new sections.
   - Rolled chords at the final cadence: 40 to 70 ms per note.
6. **Final ritard.**
   - Over the last 2 to 4 beats (at least 1.3 s), use q = 2.5 and w = 0.5. Set penultimate IOI = nominal/w and final chord ≥ 1.25 times the penultimate IOI, plus a fermata-like hold.
   - Diminuendo of −8 velocity across the ritard.
   - Inner cadences: the same shape with w = 0.85 over 1 to 2 beats.
7. **Articulation.**
   - Legato melody overlap: clamp(0.12 × IOI, 15, 100) ms. ×1.2 on descending steps, ×0.9 ascending.
   - Non-legato accompaniment: 80% of IOI. Repeated notes: 60% of IOI. Staccato: 40% of IOI.
   - Release velocity constant at 64.
8. **Pedal.** At each harmony change: CC64 → 0 at +30 ms after the (spread) chord onset and → 127 at +100 ms. Use only 0/127. First pedal-down just after the first onset. Final release after the last chord's tail.
9. **Noise (last).**
   - Onset: 1/f-correlated with SD 4 ms, for example a sum of 3 to 4 random walks low-passed at different rates, or a Voss-McCartney pink-noise generator.
   - Velocity: SD 2.5, correlated over about 1 beat.
   - The same noise sample applies to all notes of one chord, beyond its spread pattern.
10. **Tempo map in Ableton.** Export rubato as tempo automation, or bake it into note times at a fixed tempo. Convert all ms offsets using the local tempo.
11. **Validation loop.**
    - Render, then plot velocity per voice and IOI-vs-score-position.
    - Check that the melody is always on top, that arches are visible, and that IOI curves show phrase-final bumps rather than white noise.
    - Run blind A/B listening against Pianist Transformer output on the same MIDI.

### Gaps
- Exact optimal parameter values for carol-style material are untested. The values above should be tuned by a short listening test with the producer, for example 3 settings of phrase-arch depth × 2 settings of melody-lead.
- How Ableton Grand Piano's velocity layers, release samples and pedal behaviour interact with these values remains unverified.
