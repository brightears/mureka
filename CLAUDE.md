# Mureka Music Automation

CLI tool for bulk AI music generation via Mureka API. Generates royalty-free tracks for commercial use.

## Quick Reference

| Item | Value |
|------|-------|
| Runtime | Node.js 20+, TypeScript, Commander.js |
| Data | JSON files in `data/` (tracks.json, used-titles.json) |
| API Tier | $1,000 Basic (5 concurrent requests) |
| Model | Instrumental `mureka-9`, vocal `mureka-9.5` — always explicit (blind test 2026-09-29) |

## Essential Commands

```bash
npm run dev -- generate <genre> -c <count>   # Generate tracks
npm run dev -- download all --format flac    # Download completed
npm run dev -- status                        # Show statistics
npm run dev -- prompts list                  # List templates
npm run dev -- test                          # Test API connection
```

## CRITICAL Rules (Must Follow)

1. **`-c` = GENERATIONS, not tracks!** Each generation = 2 tracks
   - Want 100 tracks? Use `-c 50`
   - Want 500 tracks? Use `-c 250`

2. **Prompts: SHORT comma-separated tags only**
   - CORRECT: `"jazz, piano, mellow, 80 BPM, no vocals"`
   - WRONG: `"Soft contemporary jazz music with piano..."`

3. **Model (Norbert's blind test 2026-09-29):**
   - **Instrumentals: `mureka-9`** ($0.045/track) — 9 vs 9.5 was indistinguishable in a loudness-matched blind test.
   - **Vocal songs: `mureka-9.5`** ($0.15/song) — other models' voices sound thin.
   - Always pass `model` explicitly (CLI `-m`, scripts `model:`); `auto` = mureka-9 today but can move.
   - **No `/v1/song/describe` calls** ($0.10/track) unless Norbert approves for a specific hard filter.
   - All models available for both endpoints: `auto`, `mureka-7.6`, `mureka-o2`, `mureka-8`, `mureka-9`, `mureka-9.5`

4. **Polling: Use `/query/{id}`** - NOT `/{id}` (404 error)

5. **Status: Check `succeeded`** - NOT `completed`

6. **Reference OR Prompt** - Cannot combine both (API error)

7. **Vietnamese vocals NOT supported** - Use instrumental only

## Code Patterns

- ES modules (`import/export`)
- `p-limit` for concurrency (MAX_PARALLEL = 5)
- JSON storage in `data/*.json`
- Titles must be globally unique (tracked in `used-titles.json`)

## Key Files

| File | Purpose |
|------|---------|
| `src/cli.ts` | Main CLI entry point |
| `src/api/mureka-client.ts` | API wrapper with rate limiting |
| `src/jobs/batch-runner.ts` | Batch orchestration |
| `src/prompts/title-generator.ts` | Unique title generation |
| `src/prompts/templates/*.json` | Genre template definitions |

## Output Layout (per playlist, as of 2026-08-20)

| Where | What |
|-------|------|
| `~/Downloads/<Genre>/` | Samples only (local; user listens) |
| Personal Drive `Mureka/tracks/<Playlist> (flac)/` | THE archived playlist: cleaned lossless FLAC (only artifact there) |
| BMAsia Drive `<Genre>/<Playlist>/` | Production: 96 kbps mono, −16 LUFS ("MP3Gain 91") |

Full 4-stage pipeline (generate → clean FLAC → production prep → BMAsia upload): see @docs/workflows.md "Playlist Production Pipeline". Processing tools live in `tools/audio/`.

## Documentation (Read on Demand)

For detailed information, Claude should read these files when relevant:

- API endpoints, errors, pricing: @docs/api-reference.md
- Prompt engineering, spa music: @docs/prompt-engineering.md
- Genre templates and profiles: @docs/templates.md
- Reference-based workflows: @docs/workflows.md

## Mistakes to Avoid

| DON'T | DO |
|-------|-----|
| `-c 100` expecting 100 tracks | `-c 50` for 100 tracks |
| `model: "mureka-7.6"` or `auto` for instrumental | explicit `model: "mureka-9"` (instrumental) / `"mureka-9.5"` (vocal) |
| `/v1/instrumental/{id}` | `/v1/instrumental/query/{id}` |
| `status === 'completed'` | `status === 'succeeded'` |
| Long sentence prompts | Short comma-separated tags |
| Reference + prompt together | One OR the other |
| Artist names in prompts | Generic style descriptions |

## Output

- Default: Google Drive `~/Library/CloudStorage/GoogleDrive-.../Mureka/tracks/`
- Format: `{genre folder}/{MU - Title}.{mp3|flac|wav}`
- Metadata: Artist=BMAsia, Album=Genre name, auto-tagged on download
