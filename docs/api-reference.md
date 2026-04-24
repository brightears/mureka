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

| Service | Price |
|---------|-------|
| BGM/Instrumental | $0.03/track |
| Song (vocals) | $0.03-$0.05/track |
| Lyrics | $0.009/lyric |

## Endpoints

### Generate Instrumental

```http
POST /v1/instrumental/generate
Content-Type: application/json

{
  "prompt": "string (max 1024 chars)",
  "title": "string (max 50 chars, optional)",
  "model": "auto | mureka-7.5",
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
| `/v1/song/generate` | `auto`, `mureka-7.5`, `mureka-7.6`, `mureka-o2`, `mureka-8` |
| `/v1/instrumental/generate` | `auto`, `mureka-7.5`, `mureka-7.6`, `mureka-o2`, `mureka-8` |

**Note:** `auto` now resolves to `mureka-8` (V8) for both instrumental and song endpoints. V8 is the latest model with improved quality, vocal realism, and structural coherence.

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
