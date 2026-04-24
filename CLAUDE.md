# Mureka Music Automation

CLI tool for bulk AI music generation via Mureka API. Generates royalty-free tracks for commercial use.

## Quick Reference

| Item | Value |
|------|-------|
| Runtime | Node.js 20+, TypeScript, Commander.js |
| Data | JSON files in `data/` (tracks.json, used-titles.json) |
| API Tier | $1,000 Basic (5 concurrent requests) |
| Model | `auto` for instrumentals, `mureka-8` (V8 beta) available for songs |

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

3. **Model:**
   - Instrumentals: Use `auto` (resolves to `mureka-8` / V8)
   - Songs (vocals): Use `mureka-8` (V8) - automatically used
   - All models available for both endpoints: `auto`, `mureka-7.5`, `mureka-7.6`, `mureka-o2`, `mureka-8`

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
| `model: "mureka-7.6"` for instrumental | `model: "auto"` for instrumental (resolves to V8) |
| `/v1/instrumental/{id}` | `/v1/instrumental/query/{id}` |
| `status === 'completed'` | `status === 'succeeded'` |
| Long sentence prompts | Short comma-separated tags |
| Reference + prompt together | One OR the other |
| Artist names in prompts | Generic style descriptions |

## Output

- Default: Google Drive `~/Library/CloudStorage/GoogleDrive-.../Mureka/tracks/`
- Format: `{genre folder}/{MU - Title}.{mp3|flac|wav}`
- Metadata: Artist=BMAsia, Album=Genre name, auto-tagged on download
