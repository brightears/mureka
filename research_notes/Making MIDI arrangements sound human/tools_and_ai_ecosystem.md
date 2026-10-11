# Tools and AI Ecosystem for Agent-Driven Composition, Humanization and Rendering in Ableton (as of 2026-10-10)

Method note: GitHub metadata (stars, last push date, license, archived flag) was pulled live from the GitHub API on 2026-10-10 via `gh api repos/<owner>/<repo>`; Hugging Face licenses were pulled from the HF model API the same day. "Last push" is the repo's `pushed_at`, a reasonable proxy for last commit. Local machine check (same day): Ableton Live 12 Suite **12.4.6**, Apple **M4 Pro**, Python 3.14.6 (Homebrew), `uv`, `ffmpeg` and `fluidsynth` already installed; **Kontakt 8** (AU + VST3) and **Surge XT** (AU) plugins installed. No REAPER, MuseScore or Pianoteq installed.

## 1. Ableton control: MCP servers, AbletonOSC, pylive, Live API, .als libraries, Max for Live / Extensions. Can anything render audio headlessly?

### Takeaway
Several tools give an agent good live control of Ableton: create tracks, write notes, load browser devices, and in some forks clip automation and freeze/flatten. None of them exports audio. Live's Python Remote Script API has no documented render or bounce call; the one MCP that advertises export returns "501 unsupported", and the new Ableton Extensions SDK (JS/TS, Live 12.4.5+ beta, Suite only) has no confirmed export API. For Ableton, export still means the GUI Export dialog (computer use or OS scripting) or real-time capture. For automation at scale, the better bets are a separate offline render path (Section 5) or REAPER (Section 4).

### Cited Findings
**ahujasid/ableton-mcp** (the reference Ableton MCP)
- 3,165 stars, last push 2026-09-22, MIT, active — [GitHub](https://github.com/ahujasid/ableton-mcp)
- Capabilities per README: get session/track info; create and modify MIDI and audio tracks; "Create full song arrangements from start to finish in Arrangement View"; create, edit and trigger clips; control playback; "Load instruments and effects from Ableton's browser"; add notes to MIDI clips; change tempo — [README](https://github.com/ahujasid/ableton-mcp)
- Limitation stated in README: "designed to work with Ableton's default devices and browser items" — [README](https://github.com/ahujasid/ableton-mcp)
- Privacy: anonymous telemetry is **on by default** (install ID, tool names, success, timing; no content). It can be disabled with `ABLETON_MCP_DISABLE_TELEMETRY=true`. Separately, an opt-in "dataset recording" mode collects prompts, MIDI notes, track names and device settings that "may be published as part of an open dataset" — [README](https://github.com/ahujasid/ableton-mcp)
- Third-party guide on its limits: "There's no render-to-WAV tool. It builds and controls the set; you export from Live yourself"; "Third-party devices are hit or miss... Loading specific VST3 presets or unusual racks can fail"; reading notes back out of existing clips is "requested-but-missing"; complex arrangements time out and should be prompted section by section; it is "strongest as a fast scaffolder" — [mcp.directory guide (2026)](https://mcp.directory/blog/ableton-mcp-complete-guide-2026)

**Forks**
- **uisato/ableton-mcp-extended**: 275 stars, last push 2026-05-07, MIT. Adds browser navigation and loading by path/URI, clip automation points ("This feature isn't working perfectly yet"), and optional ElevenLabs TTS via a second MCP — [GitHub](https://github.com/uisato/ableton-mcp-extended)
- **jpoindexter/ableton-mcp**: 55 stars, last push 2026-05-01, MIT. Claims "200+ tools for near-complete Ableton Live Object Model (LOM) coverage": freeze/flatten, clip automation envelopes get/set/clear, rack macros, drum rack pads, browser tree search and load, warp markers, metering, plus built-in "Quantize/humanize timing and velocity" and simple drum/bassline generators. Offers MCP, REST API and Max for Live variants — [GitHub](https://github.com/jpoindexter/ableton-mcp)
- **jon-wrennall/ableton-mcp-extended** (7 stars, 2026-06-09): fuzzy browser search, deep plugin parameter control, device snapshots — [GitHub](https://github.com/jon-wrennall/ableton-mcp-extended)
- **nozomi-koborinai/ableton-osc-mcp** (13 stars, last push 2026-09-29, MIT): MCP layered over AbletonOSC — [GitHub](https://github.com/nozomi-koborinai/ableton-osc-mcp)
- **jterrats/ableton-live-mcp** lists `ableton_export_render` and `ableton_bounce_tracks` tools (master, selected tracks, stems). Per search-result summaries of its docs, its Remote Script bridge "returns explicit 501 unsupported responses for render-backed routes" and points to Max for Live, the Extensions SDK or other automation layers as alternatives. I could not confirm this on the tool page itself — [Glama tool page](https://glama.ai/mcp/servers/jterrats/ableton-live-mcp/tools/ableton_export_render)

**AbletonOSC / pylive**
- **ideoforms/AbletonOSC**: 820 stars, last push 2025-11-19, MIT. OSC API includes `/live/song/create_midi_track`, `/live/song/create_audio_track`, `/live/song/create_return_track`, `/live/song/create_scene`, `/live/clip/add/notes` (pitch, start_time, duration, velocity, mute) and `/live/clip/get/notes`. A grep of the README found no export, render or freeze endpoint — [GitHub](https://github.com/ideoforms/AbletonOSC)
- **ideoforms/pylive**: 631 stars, last push 2025-07-23, no license file per GitHub API. Python query/control of Live (built on AbletonOSC) — [GitHub](https://github.com/ideoforms/pylive)

**Ableton Extensions SDK (new, June 2026)**
- Announced 2 June 2026 as a public beta; "JavaScript-based toolkit"; for Live 12 Suite only; "join the beta program and download the Live 12.4.5 beta" — [Attack Magazine](https://www.attackmagazine.com/news/ableton-extensions-sdk-turns-live-suite-into-an-experimental-development-platform/)
- Official page: "Extensions can interact with tracks, clips, MIDI, devices, tempo, and other parts of a Live Set"; built on Node.js (dev setup needs Node JS v24.16.0 LTS); "available in Live 12 Suite Beta, version 12.4.5 or later"; not in Standard/Intro/Lite. Audio export/render is not mentioned — [ableton.com/live/extensions](https://www.ableton.com/live/extensions)
- SDK docs page: "lets you extend Ableton Live using modern JavaScript and TypeScript"; the detailed API reference is distributed via Centercode (beta portal), not publicly browsable — [ableton.github.io/extensions-sdk](https://ableton.github.io/extensions-sdk)
- Commentary: Extensions are invoked "via a right-click menu from anywhere within a project" and manipulate Set data and workflow, while Max for Live remains the layer for signal flow — [search summary of Fader/Sonicstate/Dubspot coverage](https://www.thefader.com/2026/06/02/ableton-extensions-sdk); [Sonicstate](https://sonicstate.com/news/2026/06/02/ableton-opens-up-java-extensions-sdk-/)

**.als parsing/generation**
- **offlinemark/dawtool**: 223 stars, last push 2024-10-28, license NOASSERTION. Parses .als v8–12 and FL Studio .flp. "Time markers are the only officially supported output", with tempo automation available through internal APIs. It is a parser, not a generator — [GitHub](https://github.com/offlinemark/dawtool)
- A GitHub search for "ableton als parser" returned no repositories. The names in the brief ("ableton-parsing", "alsdiff", "pyableton") were not found by that search — [GitHub search, run 2026-10-10](https://github.com/search?q=ableton+als+parser&type=repositories)

### Inferences
- The current pipeline (gzipped XML editing, then GUI export) is the right shape, and nothing found replaces the export step inside Ableton. MCP/OSC could replace raw XML editing for live, incremental edits. They add value mainly in browser device and preset loading (hard to do correctly in raw XML, because device state blobs are complex), clip automation, and freeze/flatten.
- Freeze, then flatten, then Consolidate gives audio clips inside the set, not a file on disk. Frozen tracks do write audio files into the project's Samples/Processed/Freeze folder (Ableton behaviour from my own knowledge, not verified this session). That could be a "render via freeze" trick: freeze each track through jpoindexter's tool, then collect the freeze WAVs from the project folder and mix them offline. It deserves a quick local test, because it would avoid the Save panel entirely. (Unverified.)
- Real-time capture (route Live's master to a virtual device such as BlackHole and record while the arrangement plays) is another headless-ish path. It runs at 1x speed, which is acceptable for a few tracks but not for bulk production.
- The local Live 12.4.6 appears to meet the Extensions SDK's 12.4.5+ requirement, but it is unclear whether 12.4.6 is a beta build. The SDK runs from a right-click menu, so an external agent probably can't trigger it without extra plumbing (for example, an extension that opens a local socket). Treat it as experimental.
- Recommendation: if staying on Ableton, use **ahujasid/ableton-mcp** for its stability and stars, with telemetry disabled, or **jpoindexter/ableton-mcp** for breadth (freeze, automation). Keep generating notes in Python and push them through the MCP or .als XML. Never ask the MCP to "compose"; its composition quality is just whatever the LLM writes.

### Gaps
- No primary Ableton documentation was found that states outright that the Live API has no export call. The conclusion rests on the absence of such a call in every bridge examined plus third-party statements.
- The Extensions SDK API reference (behind the Centercode beta portal) was not readable, so whether it can export, save the set, or be triggered externally is unknown.
- I found no Reddit or user reports with concrete quality results for AbletonMCP. The only community sentiment found came via the mcp.directory guide.
- Max for Live JS (`LiveAPI`) / Node for Max capabilities were not separately verified this session. From my own knowledge they expose the same LOM as Remote Scripts, so they also have no export.

## 2. Symbolic music generation/arranging models usable today: melody-to-accompaniment, expressive piano, licenses, Apple Silicon feasibility

### Takeaway
The most practical models for "give it our melody/sketch, get a better part back" are the **Anticipatory Music Transformer** (Apache-2.0 weights, accompaniment/infilling), **MIDI-GPT** (MIT, bar-level multitrack infill with density/polyphony controls) and **Composer's Assistant 2** (MIT, multitrack infill, trained only on permissively licensed MIDI, but tied to REAPER). For expressive solo-piano performance, **Aria** (EleutherAI, Apache-2.0, has an MLX backend for Apple Silicon) is the standout. Microsoft Muzic (MuseCoco) and Magenta's classic models are archived; Text2midi, Pop2Piano and Moonbeam are research-grade. None of these is a drop-in "arranger" for commercial background music, and every output still needs curation.

### Cited Findings
**Anticipatory Music Transformer (Stanford CRFM)**
- Repo jthickstun/anticipation: 203 stars, last push 2026-07-19, Apache-2.0 — [GitHub](https://github.com/jthickstun/anticipation)
- Abstract: models offer "the additional capability to perform infilling control tasks, including accompaniment", and human evaluators found it "produces accompaniments with similar musicality to even music composed by humans over a 20-second clip" — [arXiv 2306.08620](https://arxiv.org/abs/2306.08620)
- Weights on HF: `stanford-crfm/music-medium-800k` (apache-2.0, 5,909 downloads) and `stanford-crfm/music-large-800k` (apache-2.0, updated 2024-03-13). Usage goes through HF Transformers `AutoModelForCausalLM` plus the package's `generate()` / `midi_to_events` / `events_to_midi`. The README example calls `.cuda()` — [README](https://github.com/jthickstun/anticipation); [HF](https://huggingface.co/stanford-crfm/music-medium-800k)

**MIDI-GPT (Metacreation Lab, SFU)**
- 107 stars, last push 2026-08-19, MIT. "Fill in missing bars while preserving your existing arrangement"; "Generate new tracks... conditioned on musical attributes"; controls for note density, polyphony and note duration per bar. Models `prism_medium` and `expressive_medium` cover 4/8/12/16 bars with infill and attributes including key signature, pitch range, genre, and "nomml" (expressive timing) on the expressive model. Both are marked "training in progress" — [GitHub](https://github.com/Metacreation-Lab/MIDI-GPT)

**Composer's Assistant 2 (Martin Malandro)**
- Repo m-malandro/composers-assistant-REAPER: 73 stars, last push 2025-06-16, MIT; release v2.1.0. Requires REAPER plus Python 3.9+ with PyTorch and transformers — [GitHub](https://github.com/m-malandro/composers-assistant-REAPER)
- Paper: T5-like model for multi-track infilling at the track-measure level, with rhythmic conditioning, onset density, pitch and "rhythmic interest" controls. Its listening study "does not find a significant difference between real music and music composed in a co-creative fashion with our system" (ISMIR 2024) — [arXiv 2407.14700](https://arxiv.org/abs/2407.14700)
- The original system's "models were trained only on permissively-licensed MIDI files" — [arXiv 2301.12525](https://arxiv.org/abs/2301.12525)

**Aria (EleutherAI): expressive piano**
- 118 stars, last push 2026-05-12, Apache-2.0. LLaMA-3.2-style 1B-parameter model trained on ~60k hours of MIDI transcriptions of expressive solo-piano recordings (ISMIR 2025). Checkpoints: `aria-medium-base`, `aria-medium-gen` (finetuned for generation quality) and `aria-medium-embedding`. Requires Python 3.11+; provides "optimized model implementations for PyTorch (CUDA) and MLX (Apple Silicon)" — [GitHub](https://github.com/EleutherAI/aria); [paper arXiv 2506.23869](https://arxiv.org/abs/2506.23869)
- Limits per README: "performs best when continuing existing piano MIDI files rather than generating music from scratch", is recommended for single-track inputs, is "very sensitive to input quality", and "may memorize or closely reproduce" popular classical works such as Chopin — [README](https://github.com/EleutherAI/aria)
- HF `loubb/aria-medium-base` license apache-2.0 — [HF](https://huggingface.co/loubb/aria-medium-base)

**Other models**
- **SkyTNT/midi-model**: 378 stars, last push 2024-12-31, Apache-2.0; HF `skytnt/midi-model-tv2o-medium` apache-2.0 — [GitHub](https://github.com/SkyTNT/midi-model)
- **Moonbeam** (QMUL): 86 stars, last push 2025-06-12, Apache-2.0. Foundation model trained on 81.6K MIDI files / 18B tokens; the conditional-generation/infilling and unconditional checkpoints are linked as "https://TODO" in the README — [GitHub](https://github.com/guozixunnicolas/Moonbeam-MIDI-Foundation-Model)
- **NotaGen**: 1,236 stars, last push 2025-04-21, MIT (weights MIT on HF). Generates classical sheet music (ABC notation) from "period-composer-instrumentation" prompts; local NotaGen-X inference "may require 8GB of GPU memory"; NotaGen-large needs ≥24GB for training and inference — [GitHub](https://github.com/ElectricAlexis/NotaGen)
- **Text2midi** (AMAAI Lab): 184 stars, last push 2025-02-28, MIT code / apache-2.0 HF weights — [GitHub](https://github.com/AMAAI-Lab/Text2midi)
- **microsoft/muzic** (contains MuseCoco): 4,963 stars, **archived** — [GitHub](https://github.com/microsoft/muzic)
- **magenta/magenta** (Performance RNN, Coconet, Music Transformer, Piano Genie): 19,794 stars, **archived**; **magenta/note-seq** also archived — [GitHub](https://github.com/magenta/magenta); [note-seq](https://github.com/magenta/note-seq)
- **Pop2Piano**: 497 stars, last push 2023-07-11, no license in repo. It takes *audio* in and produces a piano cover — [GitHub](https://github.com/sweetcocoa/pop2piano)
- **Magenta RealTime 2** (audio, not symbolic): 1,819 stars, last push 2026-10-02, Apache-2.0 code; weights `google/magenta-realtime-2` CC-BY-4.0. Ships an AUv3 plugin and a standalone macOS app; `mrt2_small` (230M) and `mrt2_base` (2.4B) both run real-time on **M4 Pro** per its device table — [GitHub](https://github.com/magenta/magenta-realtime); [HF](https://huggingface.co/google/magenta-realtime-2)
- **JazzyGPT2** (DCAI 2025): takes a MIDI lead melody and produces a real-time accompaniment; trained on ~200h of PiJAMA jazz piano; weights and inference code reportedly on GitHub — [CSEM report](https://yoda.csem.ch/items/55ed9015-5f4b-42fb-90b2-96da88e785f3)
- **METEOR** (melody-aware, texture-controllable orchestral accompaniment) — [arXiv 2409.11753](https://arxiv.org/abs/2409.11753v1); code availability unconfirmed
- **SongComposer**: repo `pjlab-aigc/SongComposer` returned 404 on GitHub API (moved or renamed) — [GitHub API check](https://github.com/pjlab-aigc/SongComposer)

### Inferences
- **Melody in, accompaniment out:** Anticipatory Music Transformer is the closest general-purpose fit. The melody becomes the "controls" and the model writes the other events. MIDI-GPT fits an existing multitrack arrangement: infill or regenerate a bar range of one track. Composer's Assistant 2 is strongest on paper (a listening study with parity) but needs REAPER as host. JazzyGPT2 is jazz-specific, which suits BMAsia's cafe/lounge jazz catalog, but it is less established.
- **Expressive (performed) piano MIDI:** Aria (MLX on M4 Pro) for continuation, i.e. prompt with a human-quality few bars. VirtuosoNet / ScorePerformer (Section 3) render a *given score* expressively, which better matches "we have composed notes, make them sound played".
- **Hardware:** Models in the 100M–1B range (Anticipation medium/large, MIDI-GPT, Aria 1B, SkyTNT) should run inference on an M4 Pro with 48GB through PyTorch MPS, CPU or MLX. Several READMEs hard-code `.cuda()`, so expect small patches (`.to("mps")`). NotaGen-X's 8GB GPU figure fits comfortably in unified memory.
- **Commercial use:** The code and weights licenses above (Apache-2.0, MIT, CC-BY-4.0) permit commercial use. Training-data provenance is another matter: Aria was trained on transcriptions of piano recordings, Anticipation on Lakh MIDI. Composer's Assistant is the only one explicitly trained on permissively licensed MIDI. For royalty-free commercial catalog use, Composer's Assistant and handwritten/rule-based generation carry the lowest provenance risk. (A legal judgement is out of scope; flag to the user.)
- **Python 3.14** on this Mac is too new for many ML stacks. Use `uv venv --python 3.11` per model.

### Gaps
- MuPT, MuseCoco weights' current downloadability, the SongComposer new location, and Music Transformer standalone weights were not checked.
- I did not confirm whether JazzyGPT2 and METEOR have public licensed weights.
- Whether Ableton Live 12 hosts AUv3 plugins (relevant to the Magenta RT 2 AUv3) was not verified.
- No hands-on quality comparison of these models on BMAsia-style genres exists in the sources; quality claims are from the papers' own evaluations.

## 3. Expressive performance rendering and MIDI utility libraries

### Takeaway
For score-to-performance rendering, **VirtuosoNet** has momentum (RenCon 2025 first place, pretrained weights via a one-command download), but it has no license file and expects CUDA/MusicXML input. **ScorePerformer** has style controls but withholds its preprocessing code. **partitura** (Apache-2.0, active) is the solid foundation for score/performance handling; **Basis Mixer** is GPL and stale. Off-the-shelf "humanizer" libraries are tiny toys. The useful core MIDI stack is **pretty_midi or symusic** (fast I/O and manipulation), **mido** (low level), **music21** (theory/analysis) and **MidiTok** (only if training models).

### Cited Findings
- **jdasam/virtuosoNet**: 121 stars, last push 2026-05-16, **no license** per GitHub API. "Reads a MusicXML score and generates a human-like expressive performance MIDI"; "The pretrained weights in this repo are the algorithm submitted to RenCon 2025, which ranked 1st in the final evaluation"; `python download_and_test.py` fetches the HF checkpoint; "Requires Python 3.10 and CUDA 11.8 (for GPU)" — [GitHub](https://github.com/jdasam/virtuosoNet); [RenCon 2025 arXiv 2605.02059](https://arxiv.org/abs/2605.02059)
- **ilya16/ScorePerformer** (ISMIR 2023): 43 stars, last push 2025-03-10, license NOASSERTION. Controllable piano performance rendering with style control at the global, bar, beat and onset levels, plus performance-direction classifiers. "The code for the alignment and preprocessing of score and performance data is deliberately not made available"; Colab demo available — [GitHub](https://github.com/ilya16/ScorePerformer)
- **CPJKU/partitura**: 377 stars, last push 2026-08-25, Apache-2.0. Python package for score notation and performance handling (MusicXML, MIDI, MEI, alignment) — [GitHub](https://github.com/CPJKU/partitura)
- **CPJKU/basismixer**: 25 stars, last push 2024-04-19, GPL-3.0; implementation of Basis Function Modeling for expression — [GitHub](https://github.com/CPJKU/basismixer)
- Humanizers: **vincerubinetti/midi-humanizer** (16 stars, MIT, 2025-11-20) "randomize note starts, durations, tempo drift, and velocities"; **uprod/HumanMXA** (AU/VST3 plugin, 2026-09-01) uses "slow Ornstein-Uhlenbeck drift, per-note timing scatter, laid-back feel"; **Hamsterdamm/drums_midi_humanizer** (Python, drums) — [midi-humanizer](https://github.com/vincerubinetti/midi-humanizer); [HumanMXA](https://github.com/uprod/HumanMXA); [drums humanizer](https://github.com/Hamsterdamm/drums_midi_humanizer)
- MIDI libraries (all checked 2026-10-10):
  - **music21** 2,595 stars, last push 2026-10-10, BSD-3 — [GitHub](https://github.com/cuthbertLab/music21)
  - **pretty_midi** 1,043 stars, 2026-10-06, MIT — [GitHub](https://github.com/craffel/pretty-midi)
  - **mido** 1,647 stars, 2026-09-16, MIT — [GitHub](https://github.com/mido/mido)
  - **symusic** 189 stars, 2026-08-11, MIT ("swift and unified toolkit") — [GitHub](https://github.com/Yikai-Liao/symusic)
  - **MidiTok** 904 stars, 2026-09-30, MIT (tokenizers for DL) — [GitHub](https://github.com/Natooz/MidiTok)
  - **miditoolkit** 285 stars, last push 2024-06-10, MIT (slowing) — [GitHub](https://github.com/YatingMusic/miditoolkit)
- Aria's embedding checkpoint can produce "general-purpose piano MIDI embeddings", which could support automated similarity/quality scoring of generated piano MIDI against human references — [Aria README](https://github.com/EleutherAI/aria)

### Inferences
- The judged-amateurish "performance" problem is more likely fixed by **structured** humanization than by random jitter: phrase-level tempo arcs, metric-position velocity accents, voice-dependent timing (melody slightly ahead), and correlated drift such as the Ornstein-Uhlenbeck process HumanMXA uses. The available humanizer libraries are uniform-random and small. Better to implement these rules in our own code on top of pretty_midi/symusic, which is cheap, than to adopt the libraries.
- For piano-centric genres (new-age piano, cafe jazz piano), a promising path: generate a score, export MusicXML with music21/partitura, render it with VirtuosoNet, then render audio with Pianoteq or Kontakt (Section 5). VirtuosoNet's missing license means "all rights reserved" by default, so ask the author before commercial use. Its CUDA requirement suggests trying CPU/MPS inference.
- Replacing the in-house no-library MIDI writer with **pretty_midi** (or **symusic** for speed) costs little and reduces bugs (tempo maps, CC, pitch bend, sustain pedal CC64). **music21** adds chord/key analysis, voice-leading checks and MusicXML export. **mido** is only needed for raw message work.

### Gaps
- I found no maintained, general-purpose (multi-instrument, non-piano) expressive-performance model. All found are piano-only.
- Licensing for the VirtuosoNet pretrained weights on HF was not checked.
- The "Pianoteq-style humanizer" in the brief has no open-source equivalent; Pianoteq itself is commercial (Section 5).

## 4. Claude ecosystem (skills, plugins, MCP) and REAPER / MuseScore / FluidSynth as alternative automation targets

### Takeaway
The Claude-specific music ecosystem is young. The relevant pieces are **glincker/ableton-skills** (12 producer-workflow skills, MIT, pairs with an Ableton MCP), the **PyTheory** Claude Code plugin (theory/composition plus rendering), and a few small skills. **REAPER** looks like a better automation target than Ableton. It has at least six active MCP servers, two of which include `render_project`/`render_stems`; `reapy` gives Python control; a command line renders projects; and it is the only DAW with a published multitrack infill model (Composer's Assistant 2). **MuseScore 4** offers CLI rendering with an "Muse Sounds" sound-profile option. **FluidSynth** (already installed) is the simplest headless path but sounds the most "General MIDI".

### Cited Findings
**Claude skills/plugins**
- **glincker/ableton-skills**: 35 stars, last push 2026-09-23, MIT; "Claude Skills for Ableton Live producers", 12 skills and 4 slash commands; install by `git clone ... ~/.claude/skills/ableton`. Covers voice leading (e.g. "respecting Vln1's range (G3 to G6)"), velocity-curve humanization, mix diagnostics, genre-aware drums. Recommends `uisato/ableton-mcp-extended` as the server and calls ahujasid "stale" (contradicted by ahujasid's 2026-09-22 push) — [GitHub](https://github.com/glincker/ableton-skills)
- **PyTheory** (Kenneth Reitz) ships a Claude Code plugin with six skills: composition ("Score, parts, progressions, melodies, drums, layering, plus rendering to audio and MIDI"), theory, audio→notes/MIDI, MusicXML/LilyPond/ABC export; `pip install pytheory` — [PyTheory Claude docs (git mirror)](https://git.kennethreitz.org/kennethreitz/pytheory/src/branch/master/docs/guide/claude.rst)
- **code-to-music** skill: music21 + FluidR3_GM soundfont + mido, outputs MP3 — [skillselion listing](https://skillselion.com/skills/aiskillstore/marketplace/code-to-music)
- **music-composer** skill on Smithery (mido-based; one install) — [Smithery](https://smithery.ai/skills/paoloquaranta/music-composer)
- **tubone24/midi-mcp-server** (54 stars, 2026-04-12, MIT): MCP that generates MIDI files from text-described notes — [GitHub](https://github.com/tubone24/midi-mcp-server)

**REAPER**
- REAPER MCP servers (GitHub API, 2026-10-10):
  - **bonfire-systems/reaper-mcp**: 152 stars, 2026-10-07, MIT. 60 tools including track templates, MIDI, FX presets, volume/pan automation, and **Rendering: `render_project`, `render_stems`**. Uses python-reapy via REAPER's "distant API"; `pip install reaper-mcp-server` — [GitHub](https://github.com/bonfire-systems/reaper-mcp)
  - **dschuler36/reaper-mcp-server**: 128 stars, 2026-09-02, MIT — [GitHub](https://github.com/dschuler36/reaper-mcp-server)
  - **xDarkzx/Reaper-MCP**: 87 stars, 2026-10-04, Apache-2.0, "181 tools for composition, mixing, mastering" — [GitHub](https://github.com/xDarkzx/Reaper-MCP)
  - **shiehn/total-reaper-mcp**: 84 stars, 2026-08-03, MIT, "100% Reascript Coverage" — [GitHub](https://github.com/shiehn/total-reaper-mcp)
  - **TwelveTake-Studios/reaper-mcp**: 77 stars, 2026-09-29, MIT, 176 tools — [GitHub](https://github.com/TwelveTake-Studios/reaper-mcp)
  - **wretcher207/reaper-daemon**: 16 stars, 2026-10-09 — [GitHub](https://github.com/wretcher207/reaper-daemon)
- bonfire's render tool sets render settings, runs REAPER's render action (`Main_OnCommand 41824`) and checks that the output file exists — [Glama tool page](https://glama.ai/mcp/servers/bonfire-systems/reaper-mcp/tools/render_project)
- **RomeoDespres/reapy**: 153 stars, last push 2024-01-27, MIT (aging but still the base for MCPs) — [GitHub](https://github.com/RomeoDespres/reapy)
- REAPER CLI rendering: a REAPER 3.0.3 changelog lists `-renderproject` ("hides main window from view") — [rekkerd.org changelog](https://rekkerd.org/?p=13329). A v6.64 changelog says "command line and queued renders use the project name" when no render filename is saved — [REAPER old downloads/changelog](https://reaper.FM/download-old.php?ver=6x). A v7 changelog adds a Batch converter option to "copy current settings to clipboard for command line use" — [reaper.fm download](https://reaper.fm/download.php)

**MuseScore**
- MuseScore: 15,218 stars, last push 2026-10-09 — [GitHub](https://github.com/musescore/MuseScore)
- CLI: `-o/--export-to` with format by extension (incl. `.mp3`), `-b/--bitrate`, and `--sound-profile` with values "MuseScore Basic" or "Muse Sounds" for MP3 export. The handbook warns that some docs are carried over from MuseScore 3 — [MuseScore handbook: command line usage](https://handbook.musescore.org/appendix/command-line-usage); [mscore man page](https://mankier.com/1/mscore)

**FluidSynth / sfizz / samples**
- **FluidSynth**: 2,511 stars, last push 2026-10-09, LGPL-2.1, active — [GitHub](https://github.com/FluidSynth/fluidsynth)
- **sfizz** (SFZ player library) and **sfizz-ui** (plugins) are both **archived** (sfizz last push 2025-03-17, sfizz-ui 2025-03-19), BSD-2 — [sfizz](https://github.com/sfztools/sfizz); [sfizz-ui](https://github.com/sfztools/sfizz-ui)
- **VSCO-2 Community Edition** orchestral samples: 676 stars, CC0-1.0, last push 2021-04-06 (static sample set, not abandoned software) — [GitHub](https://github.com/sgossner/VSCO-2-CE)

### Inferences
- **REAPER vs Ableton for automation:** REAPER wins on automation. It has scripted render through the API or CLI with no Save panel, a cheap license, active MCPs, an in-DAW infill model, and plain-text `.rpp` project files that are easier to generate than gzipped `.als` XML (from my own knowledge, not verified this session). Ableton wins on the built-in instruments, racks and Suite sound library the team already relies on. REAPER can't load Ableton's internal devices, but it can host the installed **Kontakt 8** and **Surge XT** plugins. A hybrid is plausible: compose and humanize in Python, render at scale in REAPER or with Pedalboard through Kontakt/Surge, and keep Ableton for hand-finished flagship pieces.
- **glincker/ableton-skills** costs nothing to try and encodes producer heuristics (ranges, velocity curves, high-pass cleanup) that address "amateurish" output. Review its skill contents before adopting, though; with 35 stars it is lightly vetted.
- **MuseScore + Muse Sounds** is a headless path for orchestral, classical and piano content with realistic samples. It suits the classical-relaxation template. Quality and CLI support for Muse Sounds need local testing.
- **sfizz** being archived weakens the "SFZ headless" path. Salamander Grand Piano is available as SF2 for FluidSynth (my own knowledge; license reportedly CC-BY, not verified here).

### Gaps
- I could not reach the official REAPER CLI docs. Exact current syntax for `-renderproject` / `-batchconvert` on macOS needs `reaper -h` locally.
- PyTheory's GitHub location, stars and license were not verified (seen only on a git mirror).
- I found no Claude skill or MCP for Logic Pro in this search (not specifically searched).
- Whether MuseScore CLI can actually use Muse Sounds headless (they are downloaded via Muse Hub) is unconfirmed.

## 5. Headless offline rendering alternatives at scale: DawDreamer, Pedalboard, Pianoteq CLI, sfizz, Carla vs Ableton

### Takeaway
The highest-leverage finding for automation: **Spotify Pedalboard** (GPL-3, 6.3k stars, active) loads **Audio Unit and VST3 instruments on macOS** and renders MIDI to audio offline in Python. That means the already installed **Kontakt 8** and **Surge XT** can render our MIDI without any GUI or Save panel. **DawDreamer** (GPL-3, active) adds graph routing, PPQN automation and Faust. **Pianoteq** offers a documented `--headless --midi --wav` CLI for top-tier modeled piano (commercial). None of these can load Ableton's internal devices or racks; that is the main trade-off.

### Cited Findings
- **spotify/pedalboard**: 6,346 stars, last push 2026-10-07, GPL-3.0 — [GitHub](https://github.com/spotify/pedalboard)
  - `ExternalPlugin` (base of `VST3Plugin` / `AudioUnitPlugin`) has a process overload taking `midi_messages, duration, sample_rate, num_channels=2, buffer_size=8192, reset=True`; "Each MIDI message will be sent to the plugin at its timestamp"; `is_instrument` property "True iff this plugin is not an audio effect and accepts only MIDI input"; instrument support introduced in v0.7.4; "Audio Units are supported on macOS"; VST3 on macOS/Windows/Linux — [Pedalboard API reference](https://spotify.github.io/pedalboard/reference/pedalboard.html)
- **DBraun/DawDreamer**: 1,322 stars, last push 2026-10-02, GPL-3.0; macOS/Windows/Linux. Features: VST instruments and effects "with UI editing and state loading/saving", FAUST instruments, parameter automation "at audio-rate and at pulses-per-quarter-note", MIDI playback in absolute and PPQN time, time-stretching "optionally according to Ableton Live warp markers", rendering multiple processors — [GitHub](https://github.com/DBraun/DawDreamer)
- **Pianoteq CLI**: `--headless`, `--midi FILE`, `--wav FILE` (export then quit), `--preset NAME`, `--list-presets`, `--rate`, `--bit-depth`, `--mono`; example `Pianoteq --preset "U4 Small" --midi foo.mid --wav foo.wav`; folder batch conversion works on Windows — [Modartt forum](https://forum.modartt.com/viewtopic.php?id=11200); [batch export thread](https://forum.modartt.com/viewtopic.php?id=3996)
- **falkTX/Carla** (plugin host): 2,182 stars, last push 2026-06-22, no license detected by API — [GitHub](https://github.com/falkTX/Carla)
- **sfizz**: archived (see Section 4) — [GitHub](https://github.com/sfztools/sfizz)
- **Magenta RT 2** offline (non-real-time) inference is possible on any Apple Silicon Mac via the Python library (audio generation, not MIDI rendering) — [GitHub](https://github.com/magenta/magenta-realtime)

### Inferences
- **Concrete pipeline option (no Ableton GUI):** Python composition, then humanization (pretty_midi/symusic), then Pedalboard `load_plugin("/Library/Audio/Plug-Ins/Components/Kontakt 8.component")` (or Surge XT) per stem, then Pedalboard effects (reverb, compression, EQ; or load third-party AU/VST3 effects), then a mixdown written to FLAC. Everything is scriptable and batchable at faster than real time.
  - The main unknown is **Kontakt patch selection**: Kontakt loads instruments inside its own UI. The likely approach is to configure Kontakt once in a plugin editor, save its state, and restore that state programmatically (DawDreamer documents state loading/saving; Pedalboard exposes `raw_state` per my own knowledge, unverified). Kontakt libraries may also need Native Access authorization on the machine, which is already set up here.
- **What's lost vs Ableton:** Ableton's stock instruments (Drift, Meld, Wavetable, Sampler presets, Drum Racks), its Suite sound packs, groove pool, warping and the arrangement view, which together are much of the current sound. Surge XT (free) and Kontakt Factory content are partial substitutes.
- **Pianoteq** (commercial) is likely the single biggest audio-realism upgrade for piano-led genres because it is modeled and responds to velocity and pedal nuance. Its CLI fits batch rendering directly.
- **DawDreamer vs Pedalboard:** DawDreamer for graphs, sample-accurate automation and buses; Pedalboard for simplicity, AU support confirmed, and a larger maintenance base. GPL-3 on both is fine for internal tooling, and the rendered audio is not encumbered.

### Gaps
- Whether DawDreamer supports Audio Units on macOS (its README mentions VST) was not confirmed; its docs URL redirected to an unverified domain, which I did not follow.
- Whether Kontakt 8 renders correctly offline in Pedalboard/DawDreamer (some protected plugins misbehave without a GUI host) is unverified and needs a local smoke test.
- Pianoteq pricing and licensing for commercial audio output were not checked.

## 6. Overall ranking: what to adopt first (practical inventory)

### Takeaway
Ranked by expected quality or automation gain per unit of effort for this team (Mac, Ableton Suite 12.4.6, Kontakt 8 and Surge XT installed, Python): (1) Pedalboard offline rendering through Kontakt/Surge; (2) pretty_midi/symusic plus music21 replacing in-house MIDI code, with structured humanization rules; (3) Pianoteq CLI for piano genres; (4) an Ableton MCP (ahujasid or jpoindexter) for browser and device loading and a freeze-based render test; (5) Anticipatory Music Transformer / MIDI-GPT for accompaniment and infill; (6) Aria (MLX) and VirtuosoNet for expressive piano; (7) a REAPER trial with bonfire reaper-mcp and Composer's Assistant 2; (8) glincker/ableton-skills as a cheap knowledge layer. Archived or stale (avoid as foundations): Magenta v1, Muzic/MuseCoco, note-seq, sfizz, Pop2Piano, miditoolkit, Basis Mixer.

### Cited Findings
| Rank | Tool | What it adds | Activity (2026-10-10) | License | macOS install | Pipeline fit |
|---|---|---|---|---|---|---|
| 1 | Pedalboard | Offline AU/VST3 instrument + FX rendering from MIDI | 6,346★, 2026-10-07 | GPL-3.0 | `pip install pedalboard` | Replaces GUI export for bulk; [GitHub](https://github.com/spotify/pedalboard), [API](https://spotify.github.io/pedalboard/reference/pedalboard.html) |
| 2 | pretty_midi / symusic / music21 / mido | Robust MIDI I/O, analysis, MusicXML | 1,043★ / 189★ / 2,595★ / 1,647★, all pushed Aug–Oct 2026 | MIT / MIT / BSD-3 / MIT | pip | Replace hand-rolled MIDI writer; [pretty_midi](https://github.com/craffel/pretty-midi), [symusic](https://github.com/Yikai-Liao/symusic), [music21](https://github.com/cuthbertLab/music21), [mido](https://github.com/mido/mido) |
| 3 | Pianoteq CLI | Modeled piano, headless MIDI→WAV | n/a (commercial) | commercial | installer | Piano stems; [forum](https://forum.modartt.com/viewtopic.php?id=11200) |
| 4 | ahujasid/ableton-mcp; jpoindexter/ableton-mcp | Live control, browser loading, automation, freeze | 3,165★ 2026-09-22; 55★ 2026-05-01 | MIT | uv + Remote Script copy | Device/preset loading, freeze-render experiment; [ahujasid](https://github.com/ahujasid/ableton-mcp), [jpoindexter](https://github.com/jpoindexter/ableton-mcp) |
| 5 | Anticipatory Music Transformer | Accompaniment/infill given events | 203★, 2026-07-19 | Apache-2.0 (code + weights) | pip + HF weights; patch `.cuda()` | Melody→accompaniment; [GitHub](https://github.com/jthickstun/anticipation), [arXiv](https://arxiv.org/abs/2306.08620) |
| 5 | MIDI-GPT | Bar-level multitrack infill with density/polyphony controls | 107★, 2026-08-19 | MIT | pip + HF | Regenerate weak bars/tracks; [GitHub](https://github.com/Metacreation-Lab/MIDI-GPT) |
| 6 | Aria | Expressive piano continuation (MLX backend) | 118★, 2026-05-12 | Apache-2.0 | Python 3.11+, uv | Piano performance from a seed; [GitHub](https://github.com/EleutherAI/aria) |
| 6 | VirtuosoNet | MusicXML score → expressive piano MIDI (RenCon 2025 #1) | 121★, 2026-05-16 | none (ask author) | Python 3.10; CUDA preferred | Score→performance; [GitHub](https://github.com/jdasam/virtuosoNet) |
| 7 | REAPER + bonfire reaper-mcp + Composer's Assistant 2 | Scriptable render, infill model in-DAW | 152★ 2026-10-07; CA2 73★ 2025-06-16 | MIT / MIT (REAPER commercial) | REAPER install + reapy distant API | Alternative automation target; [reaper-mcp](https://github.com/bonfire-systems/reaper-mcp), [CA2](https://github.com/m-malandro/composers-assistant-REAPER), [arXiv](https://arxiv.org/abs/2407.14700) |
| 8 | glincker/ableton-skills | Producer heuristics as Claude skills | 35★, 2026-09-23 | MIT | git clone to ~/.claude/skills | Prompt/knowledge layer; [GitHub](https://github.com/glincker/ableton-skills) |
| — | DawDreamer | Graph DAW in Python, PPQN automation, Faust | 1,322★, 2026-10-02 | GPL-3.0 | pip | Alternative to Pedalboard; [GitHub](https://github.com/DBraun/DawDreamer) |
| — | MuseScore 4 CLI | Score→MP3 with Muse Sounds profile | 15,218★, 2026-10-09 | GPL (NOASSERTION in API) | installer | Classical/orchestral headless; [handbook](https://handbook.musescore.org/appendix/command-line-usage) |
| — | FluidSynth + VSCO-2 CE | Simplest headless SF2 render; CC0 orchestral samples | 2,511★ 2026-10-09; VSCO static | LGPL-2.1 / CC0 | already installed (brew) | Quick previews; [FluidSynth](https://github.com/FluidSynth/fluidsynth), [VSCO-2-CE](https://github.com/sgossner/VSCO-2-CE) |
| — | Magenta RT 2 | Real-time audio generation (open weights), AUv3 | 1,819★, 2026-10-02 | Apache-2.0 / CC-BY-4.0 weights | app/AUv3 or Python | Texture/ideas, not MIDI; [GitHub](https://github.com/magenta/magenta-realtime) |
| — | Ableton Extensions SDK | JS/TS add-ons editing Set data | beta since 2026-06 | SDK licence (terms not public) | Live 12.4.5+ beta, Node 24 | Watch; export unconfirmed; [Ableton](https://www.ableton.com/live/extensions) |
| avoid | Magenta v1, Muzic/MuseCoco, note-seq, sfizz/sfizz-ui | — | archived | — | — | [magenta](https://github.com/magenta/magenta), [muzic](https://github.com/microsoft/muzic), [sfizz](https://github.com/sfztools/sfizz) |

### Inferences
- The "amateurish composition" complaint is not fixed by any control tool. MCPs and skills only move notes the LLM chose. The levers that actually change musical quality are: (a) model-assisted infill/accompaniment (Anticipation, MIDI-GPT, CA2) used as a candidate generator with Claude curating; (b) score-aware expressive rendering (VirtuosoNet/Aria for piano); (c) better instruments (Pianoteq, Kontakt libraries) rendered headlessly.
- Suggested first experiment, about half a day: render one existing generated MIDI arrangement through Pedalboard with Kontakt 8 and Surge XT stems, and separately through Pianoteq if trialled. Compare against the current Ableton export. This confirms or rules out the headless path before investing in any model.
- Second experiment: feed an existing melody into the Anticipatory Music Transformer (medium, MPS) and MIDI-GPT infill, and have Norbert blind-judge accompaniments against current in-house output. This matches the team's existing "deliver all samples, Norbert judges" practice.

### Gaps
- No source provides head-to-head quality comparisons of these models on commercial background-music genres. The ranking is a judgement from capabilities, activity and fit, not from measured listening results.
- Install effort estimates come from READMEs; nothing was installed or run in this session.
