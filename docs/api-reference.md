# Mureka API Reference

## Authentication

```
Authorization: Bearer $MUREKA_API_KEY
Base URL: https://api.mureka.ai
API Keys: https://platform.mureka.ai/apiKeys
```

## Two Separate Systems

| Platform | URL | Purpose |
|----------|-----|---------|
| Web Studio | mureka.ai | Manual creation UI (Premier subscription) |
| API Platform | platform.mureka.ai | Programmatic access (separate purchase) |

**Premier subscription does NOT include API access.**

## Pricing

| Tier | Cost | Concurrent Requests |
|------|------|---------------------|
| Test | $30 | 1 (sequential only) |
| Basic | $1,000 | 5 |
| Standard | $3,000 | 15 |
| Business | $5,000 | 25 |

Per-call prices (platform.mureka.ai/pricing, checked 2026-09-23):

| Service | Model | Price |
|---------|-------|-------|
| BGM/Instrumental | mureka-9.5 | $0.15/track |
| BGM/Instrumental | V8 / V9 | $0.045/track |
| BGM/Instrumental | V7.6 | $0.03/track |
| Lyrics-to-song | 9.5 / O2-V8-V9 / V7.6 | $0.15 / $0.045 / $0.03 |
| Prompt-to-song (`song/easy-generate`) | 9.5 / others | $0.50 / $0.30 |
| **Describe song** | analysis model | **$0.10/song** — NOT free; describing every track adds ~67% on top of 9.5 generation |
| Stem export | audio-separation-1 (5 stems) / -2 (12 stems + MIDI) / -3 (vocal+instr) | $0.06 / $0.70 / $0.20 |
| Single track generation (`track/generate`) | V8 | $0.09 |
| Soundtrack (image/video → music) | V9 | $0.10 |
| Music video (`video/generate`) | Seedance 2.x | $0.013–0.62 per output second (10 s mini-model test billed ~$3.48 = ~$0.35/s; the charge posted hours later) |
| Lyrics video | video model | $0.10/video |
| Custom music model | train via sales; up to 200 samples | $0.06/song after training |
| Lyrics | lyric model | $0.009/lyric |

Cost reconciliation 2026-09-14 (Chill Med + Chillout Latin, 490 tracks): 490 × $0.15 gen + 490 × $0.10 describe
= $122.50 of the $128.50 spent. The "9.5 costs more than announced" puzzle was the describe calls.

## Endpoints

### Generate Instrumental

```http
POST /v1/instrumental/generate
Content-Type: application/json

{
  "prompt": "string (max 1024 chars)",
  "title": "string (max 50 chars, optional)",
  "model": "auto | mureka-7.5 | mureka-7.6 | mureka-o2 | mureka-8 | mureka-9",
  "n": "integer (default: 2, max: 3)"
}
```

### Poll for Completion

```http
GET /v1/instrumental/query/{generation_id}
```

Response:
```json
{
  "id": "generation_id",
  "status": "succeeded",
  "choices": [
    {
      "id": "song_id",
      "url": "https://cdn.mureka.ai/.../file.mp3",
      "flac_url": "...",
      "wav_url": "...",
      "duration": 220270
    }
  ]
}
```

### Generate Song (Vocals)

```http
POST /v1/song/generate
{
  "lyrics": "string with [Verse], [Chorus], [Bridge] tags",
  "prompt": "style description",
  "model": "auto | mureka-7.5 | mureka-7.6 | mureka-o2 | mureka-8"
}
```

Poll: `GET /v1/song/query/{generation_id}`

### Generate Lyrics

```http
POST /v1/lyrics/generate
{ "prompt": "Write a song about summer" }
```

### Upload File

```http
POST /v1/files/upload
Content-Type: multipart/form-data

purpose: "reference" | "instrumental" | "vocal" | "melody"
file: @file.mp3
```

### Describe Song (Analyze)

```http
POST /v1/song/describe
{ "url": "https://cdn.mureka.ai/.../track.mp3" }
```

Returns: `instrument[]`, `genres[]`, `tags[]`, `description`

## All Endpoints Summary

### Files
- `POST /v1/files/upload` - Upload reference/vocal/melody file

### Lyrics
- `POST /v1/lyrics/generate` - Generate lyrics
- `POST /v1/lyrics/extend` - Continue existing lyrics

### Song (Vocals)
- `POST /v1/song/generate` - Generate song with vocals
- `GET /v1/song/query/{task_id}` - Query status
- `POST /v1/song/extend` - Extend existing song
- `POST /v1/song/recognize` - Convert to lyrics with timestamps
- `POST /v1/song/describe` - Analyze song
- `POST /v1/song/stem` - Separate tracks (vocals, instruments)

### Instrumental
- `POST /v1/instrumental/generate` - Generate instrumental
- `GET /v1/instrumental/query/{task_id}` - Query status

### TTS
- `POST /v1/tts/generate` - Text-to-speech
- `POST /v1/tts/podcast` - Podcast-style conversation

### Account
- `GET /v1/account/billing` - Query billing info

## Upload Purposes & Duration

| Purpose | Duration | Format | Use Case |
|---------|----------|--------|----------|
| `reference` | 30 seconds | mp3, m4a | Style reference for songs |
| `instrumental` | 30 seconds | mp3, m4a | Style reference for instrumentals |
| `vocal` | 15-30 seconds | mp3, m4a | Voice cloning |
| `melody` | 5-60 seconds | mp3, m4a, mid | Melody reference |
| `voice` | 5-15 seconds | mp3, m4a | TTS voice cloning |

## Generation Control Options

### Song Generation
| Option | Can Combine With |
|--------|------------------|
| `prompt` | `vocal_id` |
| `reference_id` | `vocal_id` |
| `vocal_id` | `prompt`, `reference_id` |
| `melody_id` | Nothing (standalone) |

### Instrumental Generation
| Option | Can Combine With |
|--------|------------------|
| `prompt` | Nothing (standalone) |
| `instrumental_id` | Nothing (standalone) |

## Models by Endpoint

| Endpoint | Available Models |
|----------|------------------|
| `/v1/song/generate` | `auto`, `mureka-7.5`, `mureka-7.6`, `mureka-o2`, `mureka-8`, `mureka-9` |
| `/v1/instrumental/generate` | `auto`, `mureka-7.5`, `mureka-7.6`, `mureka-o2`, `mureka-8`, `mureka-9` |

**Note:** `auto` resolves to `mureka-9` (V9, released 2026-04-09) for both instrumental and song endpoints — verified empirically 2026-08-10. V9 uses the MusiCoT two-stage architecture (structure plan, then audio) for better coherence.

**mureka-9.5 (V9.5) — whitelisted for our account 2026-08-20 (via Erin @ Mureka).** Marketing pitch: more restrained arrangements, more natural vocals/timbre, truer to prompt, "less AI feel." Works on `/v1/instrumental/generate` with `model: "mureka-9.5"`; `auto` still resolves to `mureka-9`. Early-access pricing (beta until 2026-08-28): Lyrics-to-Song & Instrumental ~$0.045/song (reg $0.15); Prompt-to-Song $0.30/song (reg $0.50) — pricier than V9's $0.03/track, so evaluate cost-vs-quality per playlist (A/B on the next sample round; beta window is the cheap time to test).

**Tested 2026-08-20 on the ultra-ambient brief: V9.5 does NOT fix the pure-ambient gap.** Same drone/underscore prompts that failed on V8/V9 also failed on V9.5 — strong 136 BPM beats (autocorr 0.49-0.54 vs reference 0.24), 15-25 dB too bright above 1 kHz, output tagged IDM/Electronic. "Restrained" ≠ beatless/static. Don't re-spend on ultra-ambient without a model-side change.

## API Changelog Highlights (as of 2026-08)

From the official changelog (`platform.mureka.ai/docs/en/changelog.html`):

| Date | Change |
|------|--------|
| 2026-08-28 | mureka-9.5 enhanced; 9.5 now public in the API enums (no whitelist needed) |
| 2026-08-14 | **Video generation API** (`/v1/video/generate`, `/v1/video/query/{id}`) |
| 2026-07-09 | Music transcription endpoint; soundtrack `audio_start`/`audio_end` params; improved lyrics model |
| 2026-06-25 | Stem API: vocal+instrumental separation; `gender` param on lyrics-to-song |
| 2026-06-15 | Prompt-to-song endpoint (no lyrics needed); `vocal` purpose removed from file upload |
| 2026-05-22 | Lyrics video + remix endpoints |
| 2026-05-11 | Image/video soundtrack generation endpoint |
| 2026-04-09 | **`mureka-9` released** |
| 2026-04-08 | Complementary single-track generation from reference audio |
| 2026-03-02 | `mureka-8` enhanced |
| 2025-09-01 | `n` param for output quantity (default 2, max 3; `n:1` works for cheap single-track probes) |

## Task Statuses

| Status | Description |
|--------|-------------|
| `preparing` | Initializing |
| `queued` | In queue |
| `running` | Processing |
| `streaming` | Playback available |
| `succeeded` | Complete |
| `failed` | Failed (check `failed_reason`) |
| `timeouted` | Timed out |
| `cancelled` | Cancelled |

## Error Codes

| Code | Cause | Solution |
|------|-------|----------|
| 400 | Invalid parameters | Check docs |
| 401 | Invalid API key | Fix key |
| 403 | Unsupported region | Use supported region |
| 429 | Rate limit/quota | Slow down or buy credits |
| 500 | Server error | Retry |
| 503 | Overloaded | Retry later |

## Fine-Tuning - NOT AVAILABLE

Fine-tuning is an enterprise service ($10-20k USD), NOT an API feature. The endpoints exist but are non-functional. Use reference-based generation instead.

## Technical Support

Email: api-support@mureka.ai (responds within 24 hours)

## Rate Limits

- Generation time: ~45 seconds average
- Track length: Up to 5 minutes
- Output: 2 variations per generation

## New Capabilities Explored (2026-09-23)

- **Agent Skill** (plan feature) = Skywork's open `skywork-music-maker` skill (github.com/SkyworkAI/Skywork-Skills),
  a generic SKILL.md + `mureka.py` wrapper for Claude Code/Codex/OpenClaw. Defaults to vocal songs and `mureka-8`,
  last synced 2026-04. Our repo's CLI + pipeline already covers more; do NOT install it here (its defaults contradict our rules).
  The nav "MCP server" link = github.com/SkyworkAI/Mureka-mcp, unchanged since 2025-05.
- **Stem separation** `POST /v1/song/stem {url, model}` — synchronous (~8 s for 90 s audio), returns `zip_url` of WAVs
  (`drums, bass, other, vocals, instrumental, song`). Accepts cdn URLs or `data:audio/mp3;base64,...` (≤10 MB, mp3/m4a).
  Test on a Chill Med track: drum stem removed cleanly (high band −6 dB), but the pulse stayed 0.67 (vs 0.83) because
  bass + rhythm guitar carry the groove. Useful to delete a stray drum kit; not a fix for arrangement-level groove.
- **Single track generation** `POST /v1/track/generate {song_id|upload_audio_id, generate_type, prompt}` — adds a
  harmonized track (Guitar, Keyboard, Strings, Synth, Percussion, Brass, Woodwinds, Bass, Drums, Vocals, FX, Instrumental).
  No accordion type. Returns a song task → poll `/v1/song/query/{id}`.
- **Music video** `POST /v1/video/generate` — Seedance models (`doubao-seedance-2-5-260628` default, `-2-0-`, `-2-0-fast-`,
  `-2-0-mini-`). Feed `song_id` (choice id of an instrumental generated in the last 30 days) + `audio_start/audio_end` ms,
  `prompt`, `ratio`, `resolution`, `generate_audio:false`, `watermark:false`. Also text/image/video-to-video via `content[]`.
  Poll `/v1/video/query/{id}` (statuses queued/running/succeeded/failed/expired); `video_url` valid 24 h — download at once.
  Test: 10 s, mini model, "480p" requested → 1920×1080 H.264 with the track's audio muxed in, ~2 min wall time, billed ~$3.48 (posted late — check balance the next day, not right after). Scale check: at that rate 1 minute of video ≈ $21, a full 3-minute track video ≈ $63; higher resolution / the default Seedance 2.5 can cost more (up to $0.62/s ≈ $112 per 3 min).
- **Lyrics video** `POST /v1/lyrics-video/generate` — $0.10, template layouts, instrumentals by time range only.
- **Custom music model** — fine-tuning is now a sales-assisted product (up to 200 samples, then $0.06/song).
- Other new endpoints: `song/easy-generate` (prompt-to-song + style enum), `song/remix`, `song/region-edit`,
  `song/vocal-clone`, `song/transcribe` (MusicXML/PDF), chunked `uploads/create|add|complete` for large files,
  `stream:true` on instrumental generate for playback while generating.
