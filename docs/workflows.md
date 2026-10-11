# Workflows

## Reference-Based Generation (Recommended)

Instead of fine-tuning ($10-20k), use reference files to guide style.

### Step 1: Prepare Reference (30 seconds clip)

```bash
ffmpeg -i "reference-track.mp3" -t 30 -acodec libmp3lame -ab 256k reference-30s.mp3
```

### Step 2: Upload Reference

**For Songs (vocals):**
```bash
curl https://api.mureka.ai/v1/files/upload \
  -H "Authorization: Bearer $MUREKA_API_KEY" \
  -F purpose="reference" \
  -F file="@reference-30s.mp3"
# Returns: {"id": "117900453085185", ...}
```

**For Instrumentals:**
```bash
curl https://api.mureka.ai/v1/files/upload \
  -H "Authorization: Bearer $MUREKA_API_KEY" \
  -F purpose="instrumental" \
  -F file="@reference-30s.mp3"
# Returns: {"id": "117900509708289", ...}
```

### Step 3: Generate with Reference ID

**Song:**
```bash
curl https://api.mureka.ai/v1/song/generate \
  -H "Authorization: Bearer $MUREKA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"lyrics": "[Verse]...", "reference_id": "117900453085185"}'
```

**Instrumental:**
```bash
curl https://api.mureka.ai/v1/instrumental/generate \
  -H "Authorization: Bearer $MUREKA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"instrumental_id": "117900509708289"}'
```

### Reference vs Fine-Tuning

| Aspect | Reference-Based | Fine-Tuning |
|--------|-----------------|-------------|
| Tracks needed | 1 (30 seconds) | 100-200 |
| Setup time | Instant | ~3 hours |
| Cost | Free (included) | $10-20k USD |
| Copyright issues | None | Fails with commercial music |
| Availability | API | Enterprise service only |

**IMPORTANT:** Cannot combine reference + prompt (API error). Use one OR the other.

---

## Batch Generation

### Using Templates

```bash
# List available templates
npm run dev -- prompts list

# Generate from template (-c = generations, NOT tracks)
npm run dev -- generate cafe-jazz -c 50    # = 100 tracks

# Generate vocal tracks
npm run dev -- generate cafe-jazz-vocal -c 50
```

### Using Custom Scripts

For rapid iteration on specific prompts:

```bash
# Edit WINNING_PROMPT, GENRE, ALBUM in the script
npx tsx src/scripts/generate-winning-prompt.ts 50  # 100 tracks
```

---

## Download Workflow

```bash
# Download all pending (default MP3)
npm run dev -- download all

# Download as FLAC (lossless)
npm run dev -- download all --format flac

# Download as WAV (uncompressed)
npm run dev -- download all --format wav

# Download specific batch
npm run dev -- download <batch-id>

# Custom metadata
npm run dev -- download all --artist "Custom Artist" --album "Album Name"

# Skip metadata tagging
npm run dev -- download all --no-metadata
```

Output folders by format:
- MP3: `{genre}/`
- FLAC: `{genre} (flac)/`
- WAV: `{genre} (wav)/`

---

## Title & Metadata

### Title Format
`MU - {Unique Title}` (e.g., "MU - Golden Horizon")

### Title Uniqueness
- 1,467 unique words in vocabulary
- Each title used EXACTLY ONCE globally
- Persisted in `data/used-titles.json`
- Two tracks per generation get different titles

### Metadata Tags
| Field | Value |
|-------|-------|
| Title | `MU - {Title}` |
| Artist | `BMAsia` |
| Album | Genre in Title Case |
| Genre | Standard genre |
| Date | ISO date |

### CLI Options
```bash
--prefix "BM"           # Custom prefix (default: MU)
--artist "Artist Name"  # Custom artist
--album "Album Name"    # Custom album
--no-metadata           # Skip tagging
```

---

## Testing & Status

```bash
# Test API connection
npm run dev -- test

# Show statistics
npm run dev -- status
```

---

## Architecture

```
src/
├── api/
│   ├── mureka-client.ts    # API wrapper, rate limiting
│   └── types.ts            # TypeScript interfaces
├── prompts/
│   ├── generator.ts        # Prompt generation
│   ├── title-generator.ts  # Unique title generation
│   ├── template-loader.ts  # Template loading
│   └── templates/          # Genre JSON files
├── jobs/
│   ├── batch-runner.ts     # Batch orchestration
│   ├── downloader.ts       # Download manager
│   └── metadata-tagger.ts  # ID3 tagging
├── db/tracks.ts            # JSON-based storage
└── cli.ts                  # CLI entry point

data/
├── tracks.json             # Track database
├── batch-jobs.json         # Batch history
├── generation-jobs.json    # Job records
└── used-titles.json        # Title tracking
```

---

## YouTube Reference Analysis (client sends a link)

When a client sends a YouTube link as a style reference, turn it into Mureka prompts
with this pipeline (proven 2026-08-20 on the "Flying" / Soothing Relaxation spa brief):

### 1. Get the audio locally

```bash
# one-time per session (homebrew python blocks global pip installs)
python3 -m venv /tmp/ytenv && /tmp/ytenv/bin/pip install -q yt-dlp

# metadata first — title/tags/duration already carry style info
/tmp/ytenv/bin/yt-dlp --skip-download --print "%(title)s | %(duration)ss | %(tags.:8)s" "<URL>"

# audio (m4a). If extraction breaks with a JS-runtime warning: brew install deno
/tmp/ytenv/bin/yt-dlp -f "bestaudio[ext=m4a]/bestaudio" -o "ref.%(ext)s" "<URL>"
```

### 2. Signal analysis with ffmpeg (no listening needed)

```bash
# loudness at several offsets — constant LUFS across a 1h+ video = homogeneous style
ffmpeg -ss 120 -t 60 -i ref.m4a -af ebur128 -f null - 2>&1 | grep "I:"
# spectral balance — compare mean_volume of filtered vs full band
ffmpeg -ss 120 -t 30 -i ref.m4a -af "lowpass=f=300,volumedetect"  -f null - 2>&1 | grep mean
ffmpeg -ss 120 -t 30 -i ref.m4a -af "highpass=f=4000,volumedetect" -f null - 2>&1 | grep mean
```
Interpretation: energy concentrated below 300 Hz + nothing above 4 kHz = warm/dark/gentle,
no percussion or brightness (spa profile). High-band energy = cymbals/brightness present.

### 3. Mureka's ears: upload + describe loop

```bash
# 30s clip from a representative section
ffmpeg -ss 120 -t 30 -i ref.m4a -acodec libmp3lame -ab 256k ref-30s.mp3
# upload for reference-based generation
curl https://api.mureka.ai/v1/files/upload -H "Authorization: Bearer $MUREKA_API_KEY" \
  -F purpose="instrumental" -F file="@ref-30s.mp3"     # -> {"id": ...}
```

`/v1/song/describe` does NOT accept YouTube/googlevideo URLs ("input URL parameter is
invalid") — it works on Mureka CDN URLs. So: generate a track (reference- or prompt-based),
then describe the OUTPUT's cdn.mureka.ai URL. The returned instrument[]/genres[]/tags[] are
Mureka's own vocabulary — feed them back into prompts, and use describe as a no-listening
QA check on what a generation actually contains.

### 4. Key lesson: reference-based generation drifts

`instrumental_id` cannot be combined with a prompt, so NO negative prompts are possible.
On the "Flying" test both reference-based tracks drifted to ethereal female vocals +
electronic drums (caught by describe). Prompt-based generation with explicit negatives
matched the reference far better. **Default: use the reference for ANALYSIS (describe,
signal stats, your own listening), then generate with TEXT PROMPTS derived from it.**

### Addendum (2026-08-20): the "pure ambient" generation gap

Systematic finding from the "Flying" spa brief (12+ tracks, all QA'd): **current Mureka
models cannot produce static, beatless, lead-less pure-ambient drone.** Every attempt —
reference-based, prompt-based, template language, bracketed negatives, V9, V8, o2 (400s
on the drone prompt) — injected a beat (strength 0.47-0.74 vs reference 0.24), a lead
instrument, or vocals, and ran 20-30 dB brighter above 1 kHz than the reference.
Acoustic anchors (piano/strings) reliably suppress beats but always add a lead melody.

Implications:
- Our existing spa/sleep templates (deep-sleep-healing, spa-wellness language) likely
  produce beat-contaminated output on current models — re-verify before next spa batch
  (use the QA gate below).
- Ultra-ambient briefs: park until mureka-9.5 (its pitch — restrained, truer-to-prompt —
  is exactly this failure mode), or negotiate style with the client.
- QA gate for any minimal/ambient batch, no listening required:
  1. `/v1/song/describe` on the output CDN URL (instruments list),
  2. beat detector (`scratchpad beatcheck.py` pattern: spectral-flux autocorrelation;
     reference-class ambient ≈ 0.2, injected beats ≥ 0.45),
  3. ffmpeg band fingerprint vs reference (1-2k / 2-4k / 4k+ mean dB).

---

## Playlist Production Pipeline (end-to-end, as of 2026-08-20)

Every playlist runs SAMPLE → REVISE → SCALE → the four stages below. Samples stay in
`~/Downloads/<Genre>/` (local only); the stages apply to the approved SCALE run.

### Stage 1 — Generate (instrumental `mureka-9`, vocal `mureka-9.5`, always explicit)

- **No `/v1/song/describe` calls** (Norbert directive 2026-09-24): $0.10/track, +67% on 9.5. Only with his explicit OK for a hard instrument filter.

- `model` explicit in every request: `mureka-9` for instrumentals, `mureka-9.5` for vocal songs (Norbert's blind test 2026-09-29: 9 vs 9.5 indistinguishable on instrumentals at 1/3.3 the price).
- Generate ~15% over the target track count; the QA ranking uses the overage.
- Titles from the global ledger (`generateUniqueTitle`); track everything in a manifest JSON
  (title, family, generation id, source path) under `data/`.
- Raw FLAC masters (`flac_url`) download to a working folder. They are TEMPORARY —
  discarded after Stage 2 verification (no raw archive on any drive).

### Stage 2 — Clean → the single archived playlist (personal drive)

- `tools/audio/stage2_process.py <manifest> <out_dir> <album> <keep_n> <python>`
- Per track: `clean_track.py` = HPSS transient-strip + background-extraction (for the
  spa-ambient sound; skip the two masks for genres that don't need them) + loudnorm
  I=-17.5 + tags. Output codec follows the output extension — **.flac** for the archive.
- Rank by `beatcheck.py` pulse strength; keep the best `keep_n`.
- Full-band genres (country, chillout, latin...): `tools/audio/stage2_light.py <manifest> <out_dir> <album> <keep_n> [--require FAM:Instrument ...]`
  — no masks, fades + loudnorm + tags only. Selection by describe evidence ONLY if Norbert approved describe for that run (default: no describe → no `--require`, keep_n in manifest order). Two env vars
  are REQUIRED per run: `GENRE_TAG` (ID3 genre, default Country) and `DRIFT_TERMS` (comma list of
  instrument/genre words that disqualify a track; default is the Country list hawaiian,celtic,jazz,ukulele,bossa).
  Describe labels nylon-guitar chillout "Smooth Jazz" routinely — for chillout/latin runs use
  `DRIFT_TERMS=vocal,sax,trumpet,brass,flute,ukulele,hawaiian,trombone,clarinet` (2026-09-14: the Country
  default silently dropped ~45% of an approved batch). Always compare the printed `pass describe-filter`
  count against the manifest before trusting `keep_n`. Pre-sort the manifest by preference (e.g. verified
  accordion first) — the script keeps the first `keep_n` passing entries in manifest order.
- `clean_track.py` applies **micro-fades** (50 ms in / 0.8 s out): Mureka generations can
  start/end at non-zero amplitude, which clicks at every track transition (heard on the
  Beat Breeze sample page, 2026-08-20). QA any batch with a click scan (adjacent-sample
  jumps > 0.25 in ambient material = boundary click; clean batch scans 0).
- Final home: `My Drive/Mureka/tracks/<Playlist> (flac)/` on platzer.norbert@gmail.com
  (Drive for Desktop must be RUNNING). This is the ONLY artifact on the personal drive —
  no 256k MP3 folder, no raw-FLAC folder, no production copy.
- Folder naming follows the historical archive convention: `<Playlist> (flac)`, with
  `(QC)` appended by the team after quality check — don't add `(QC)` yourself.

### Stage 3 — Production files (96k mono, "volume 91")

- `tools/audio/production_prep.py <cleaned_flac_dir> <tmp_out_dir> 5`
- 96 kbps CBR mono MP3, single constant gain per track (no dynamics processing),
  alimiter −1.5 dB, tags preserved.
- **Loudness target = MP3Gain "Target Volume 91.0" measured with the actual ReplayGain
  algorithm** (ffmpeg `replaygain` filter), NOT LUFS — RG's filtered 95th-percentile
  statistic disagrees with integrated LUFS by up to ±1.5 dB on dynamic ambient material
  (the team's MP3Gain check exposed exactly that scatter on the first delivery).
- Calibration (verified against the team's MP3Gain, exact 3.0 dB mono-convention offset):
  `MP3Gain_volume = 92 − ffmpeg_track_gain` → target a FINAL track_gain of **+1.0**.
- The script converges on the ENCODED file (encode → scan → correct, ≤3 passes): both the
  limiter (boosted ambient peaks get shaved) and the 96k encode itself eat a few tenths
  of a dB of the RG statistic. Result: every file scans at 91.0 ± 0.15.
- ffmpeg traps (all three bit us): `-ac 1` applies AFTER `-af`; its stereo→mono pan law is
  hotter than 0.5/0.5 (use in-chain `pan=mono|c0=0.5*c0+0.5*c1` for stereo sources); and
  that same pan HALVES an already-mono file (missing c1 = silence) — scan mono outputs
  with no pan at all.

### Stage 4 — Deliver production files to the BMAsia drive

- Via Google Workspace MCP as norbert@bmasiamusic.com (probe access with `list_drive_items`
  first; auth state can change between sessions).
- Parent: BMAsia "96 kb playlists" folder `1m7x1657Gw9mq6AzXGoFB1GoJpCznQfi5`, organized
  `<Genre>/<Playlist>/` (create the playlist folder with `create_drive_folder`).
- Upload per file: `create_drive_file` with `fileUrl: "file:///...%20..."` (percent-encode
  spaces), `mime_type: audio/mpeg`. Verify first upload byte-for-byte (size vs local),
  then final `list_drive_items` count. Watch for duplicates if any upload path retried.
- The production files live ONLY here (and in local temp during the run).

### Operational cautions

- The Drive folders are actively used by the team: folders get renamed (`(QC)` suffix),
  moved, or removed between sessions. Never assume yesterday's folder state — re-list
  before depending on it. Keeper lists are recoverable from any surviving stage's folder
  (identical basenames across stages).
- Deletions through the Drive mount go to Google Drive trash (30-day recovery).
- Mureka beta pricing for 9.5 ends 2026-08-28 ($0.045 → $0.15/track): flag cost before
  scaling after that date.
