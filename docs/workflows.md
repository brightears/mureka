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
