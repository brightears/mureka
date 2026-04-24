# Mureka Prompt Engineering Guide

## Prompt Structure

```
[genre], [sub-genre], [mood], [tempo], [instruments], [use-case], [negative]
```

**CRITICAL: Short comma-separated tags only, NOT long sentences!**

```
CORRECT: "classical, orchestra, Mozart style, strings, relaxing, 70 BPM"
WRONG:   "Soft contemporary classical chamber music rooted in European late-romantic traditions..."
```

## Abstract Descriptions > Specific Brand Names

**CRITICAL: Use abstract descriptive qualities, NOT specific instrument brand/model names.**

Mureka responds much better to descriptive sound qualities than to specific synth/instrument brand names. Named models can trigger wrong genre associations.

```
CORRECT: "filtered warm pad evolving", "soft 909 kick drum", "deep warm bass round smooth"
WRONG:   "Wurlitzer electric piano soulful", "lush analog synth pads Juno style", "deep warm FM bass Yamaha DX style"
```

| DON'T (brand names) | DO (abstract qualities) |
|------|-----|
| `Wurlitzer electric piano` | `warm electric piano chords filtered` |
| `Juno style analog pads` | `warm analog pad chords` |
| `Yamaha DX FM bass` | `deep warm bass round smooth` |
| `Hammond organ riff` | `soft sustained organ pad` |
| `909 style kick drum` | `soft 909 kick drum` (exception: 909 is generic enough) |

Brand names like "Wurlitzer" and "Juno" can trigger wrong genre associations (e.g., jazz instead of deep house). Abstract descriptions give Mureka freedom to match the sound quality without genre confusion.

## Key Elements

### 1. Genre + Sub-genre (Required)
- `chinese traditional, guzheng`
- `electronic, ambient`
- `jazz, bossa nova`

### 2. Mood/Emotion
- peaceful, serene, contemplative
- energetic, uplifting, joyful
- melancholic, somber, reflective

### 3. Tempo
- **Slow**: 60-80 BPM
- **Moderate**: 80-110 BPM
- **Upbeat**: 110-140 BPM

### 4. Instruments
- Chinese: guzheng, erhu, pipa, bamboo flute, yangqin
- Western: piano, strings, violin, cello
- Jazz: piano, upright bass, brushed drums, Rhodes
- Electronic: synth pads, arpeggios

### 5. Negative Prompts
- `no vocals`, `no drums`, `no distortion`

## Example Prompts

### Chinese Instrumental
```
chinese traditional, guzheng, peaceful, slow tempo 70 BPM,
flowing water atmosphere, meditation music, restaurant background,
no vocals, no drums, no modern instruments
```

### Jazz Lounge
```
jazz, piano trio, warm, cozy, 90 BPM, upright bass, brushed drums,
cafe background, no vocals, no synths
```

---

# Creating Minimal/Ambient Spa Music

## Key Techniques

### Use "Sparse" and "Minimal" Language
- **"sparse"** and **"minimal"** reduce arrangement density
- **"solo"** instruments yield fewer layers
- **"single layer only"**, **"one or two sound elements"**
- **"very low energy"**, **"ultra minimal"**

### Effective Negative Prompts for Spa
```
[no vocals], [no drums], [no drum kit], [no percussion], [no beats],
[no rhythm], [no bass], [no bass line], [no orchestra], [no orchestral],
[no full ensemble], [no guitar], [no busy arrangement], [no complex layers],
[no sharp transients], [no sudden changes], [no high energy], [sparse only]
```

### Use Soundscape Terminology
- **"ambient soundscape"** triggers soundscape mode
- **"ethereal"**, **"evolving pads"**, **"field-recorded elements"**
- **"long reverbs"**, **"gentle fades"**, **"smooth crossfades"**

### Instrument Specification for Minimal Output
Instead of just "bamboo flute", use:
- "solo soft bamboo flute phrases very sparse"
- "single soft ambient pad very minimal"
- "warm sustained synth drone single layer only"

### Template Structure for Spa Music
```json
{
  "subGenres": ["minimal ambient soundscape very sparse texture"],
  "moods": ["very sparse and minimal with weightless feel"],
  "instruments": ["solo soft flute phrases very sparse"],
  "atmospheres": ["very sparse arrangement with only one or two sound elements"],
  "negativePrompts": ["[no drums]", "[no orchestra]", "[no busy arrangement]"]
}
```

### Common Mistakes
- Not specifying "solo" before instruments
- Missing "[no orchestra]" or "[no orchestral]"
- Not including "[no busy arrangement]" or "[no complex layers]"
- Using tempo descriptions that imply rhythm (use "breath-like pulse" instead)

### Case Study: New Age Acoustic

When creating truly minimal acoustic music (solo piano or solo guitar only), standard negative prompts like "[no synth]" are insufficient. Mureka may still add strings, flute, harp, cello, and other "acoustic" instruments.

**Solution: Block each instrument explicitly:**

```json
{
  "instruments": [
    "solo piano soft gentle sparse phrases",
    "solo acoustic guitar fingerpicked minimal"
  ],
  "negativePrompts": [
    "no synth", "no electronic",
    "no strings", "no orchestra", "no ensemble",
    "no flute", "no harp", "no cello", "no violin", "no bass",
    "no busy arrangement", "no multiple instruments"
  ]
}
```

The key is using "solo" + instrument name, plus blocking each potential ensemble instrument individually.

---

# Vocal Generation

## Supported Languages (10 only)
Chinese, English, Japanese, Korean, Portuguese, Spanish, German, French, Italian, Russian

**Vietnamese is NOT supported** - use instrumental only.

## Style Options
- `pop, catchy melody, upbeat, summer anthem`
- `ballad, emotional, piano, strings`
- `rock, energetic, guitar, drums`
- `R&B, smooth, soulful vocals`
- `country, acoustic guitar, storytelling`

## Commands

```bash
# Generate with auto-lyrics
npm run dev -- vocal "summer beach vibes" -s "pop, upbeat, catchy"

# Show lyrics before generating
npm run dev -- vocal "heartbreak" --show-lyrics

# Custom lyrics
npm run dev -- vocal "custom" -l "[Verse] My lyrics here [Chorus] And chorus"

# Lyrics only (no song)
npm run dev -- lyrics "summer adventure" -o lyrics.txt
```

---

# Classical Music Tips

Mureka defaults to violin for classical. To get variety, use instrument-specific prompts:

| Instrument | Prompt Pattern |
|------------|----------------|
| Solo Piano | `classical solo piano, Mozart Beethoven piano sonata, elegant melodic, major key, cheerful, 72 BPM, concert hall, no orchestra, no strings, no violin` |
| Brass | `classical brass ensemble, Mozart style, French horn, trumpet, no strings, no violin, no piano` |
| Woodwind | `classical woodwind ensemble, flute, clarinet, oboe, no strings, no violin, no piano, no brass` |
| String Quartet | `classical chamber music, Haydn style, string quartet, light, cheerful, 72 BPM` |

**Key discoveries:**
- "no violin" does NOT work for orchestra/concerto prompts
- Must use "solo piano" or specific ensemble types
- "major key" and "cheerful" help avoid sad output

---

# Avoiding Unwanted Saxophone

## The Problem

Mureka's training data heavily associates saxophone with certain terms. Even with "no saxophone" in negative prompts, these trigger terms will add saxophone to tracks.

## Jazz-Associated Terms That Trigger Saxophone

| Term | Triggers Sax | Replace With |
|------|--------------|--------------|
| lounge | Yes | ambient, electronica |
| sophisticated | Yes | refined, elegant |
| mellow | Yes | warm, smooth |
| Rhodes | Yes | warm synth keys |
| smooth | Sometimes | soft, gentle |

## Solution: Complete Term Replacement

Simply adding "no saxophone" does NOT work if trigger terms are present. You must:

1. **Replace ALL jazz-associated terms** in genres, subGenres, moods, instruments
2. **Use aggressive negative prompts**: `no saxophone, no sax, no jazz, no smooth jazz, no wind instruments, no brass, no trumpet, no clarinet`
3. **Use electronic/ambient terminology** instead of lounge/jazz terminology

## Example: Chillout Lounge (Fixed)

**WRONG** (will have saxophone):
```
chillout lounge, sophisticated, mellow, Rhodes electric piano, warm atmosphere
```

**CORRECT** (no saxophone):
```
downtempo chillout, warm and atmospheric, dreamy and hypnotic, warm synth keys, ambient electronica, no saxophone, no jazz, no wind instruments, no brass
```

## Key Learning

The negative prompt alone cannot override strong associations in Mureka's training data. You must change the positive prompt terms to avoid triggering those associations in the first place.

---

# Genre Tag Associations

## Terms That Trigger Wrong Genres

Mureka's training data creates strong associations between certain genre tags and output styles. Using the wrong genre tag will produce the wrong genre regardless of other prompt elements.

| Genre Tag Used | What Mureka Produces | Use Instead |
|----------------|---------------------|-------------|
| `neo soul` | Smooth jazz | `chillhop`, `lo-fi hip-hop soul` |
| `jazztronica` + jazz terms | Smooth jazz | `broken beat electronic`, `nu jazz electronic` |
| `deep house` + brand names | Jazz or EDM | Abstract descriptions only |

## "Live" and "Real" Prefixes

For genres requiring authentic acoustic instrument sounds (electro swing, neo soul, Italian traditional), prefix instruments with **"live"**, **"real"**, or **"authentic"**:

```
CORRECT: "live brass horn stabs", "real trumpet melody", "authentic ragtime piano"
WRONG:   "brass horns", "trumpet", "ragtime piano"
```

This technique was proven effective in the electro-swing template and applied to Italian traditional and neo soul templates.

## Vocal Track Folder Separation

When creating vocal variants of existing templates, use a distinct genre name in the `genres` array to ensure tracks download to separate folders:

```json
// Instrumental template
"genres": ["progressive house"]

// Vocal template - different genre name for separate folder
"genres": ["progressive house vocal"]
```

## Language Support for Vocals

Add `"language": "Italian"` (or Spanish, etc.) to vocal templates. The batch runner prepends language instructions to the lyrics generation prompt automatically. Supported: Chinese, English, Japanese, Korean, Portuguese, Spanish, German, French, Italian, Russian.
