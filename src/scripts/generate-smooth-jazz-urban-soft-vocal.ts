/**
 * Generate Smooth Jazz Urban Soft Vocal tracks using prompt-based generation
 */

import { config } from 'dotenv';
config();

import { createClientFromEnv } from '../api/mureka-client.js';
import { generateUniqueTitle } from '../prompts/title-generator.js';
import * as fs from 'fs';
import * as path from 'path';
import { pipeline } from 'stream/promises';
import { Readable } from 'stream';

const STYLE_PROMPT = 'smooth jazz vocal, urban R&B influence, soft mellow groove, contemporary jazz, soulful vocals, electric piano rhodes, smooth saxophone, clean guitar, groovy bass line, soft drums, downtempo 95 BPM, sophisticated, romantic';
const LYRIC_THEMES = [
  'romantic love song, smooth and sophisticated, city nights',
  'soulful ballad about finding peace and happiness',
  'smooth R&B love song, tender moments, late night vibes',
  'contemporary jazz song about dreams and aspirations',
  'mellow love song, soft and intimate, moonlit evening',
];
const OUTPUT_DIR = '/Users/norbert/Library/CloudStorage/GoogleDrive-platzer.norbert@gmail.com/My Drive/Mureka/tracks/Smooth Jazz Urban Soft Vocal';
const GENRE = 'smooth jazz';

async function downloadTrack(url: string, outputPath: string): Promise<void> {
  const response = await fetch(url);
  if (!response.ok || !response.body) {
    throw new Error(`Download failed: ${response.status}`);
  }
  const writeStream = fs.createWriteStream(outputPath);
  await pipeline(Readable.fromWeb(response.body as ReadableStream), writeStream);
}

async function main() {
  const count = parseInt(process.argv[2] || '3'); // Number of generations (2 tracks each)
  const client = createClientFromEnv();

  fs.mkdirSync(OUTPUT_DIR, { recursive: true });

  console.log(`Generating ${count} generations (${count * 2} tracks) of smooth jazz urban soft vocal...`);
  console.log(`Style: ${STYLE_PROMPT}`);
  console.log(`Output: ${OUTPUT_DIR}\n`);

  let totalTracks = 0;

  for (let i = 0; i < count; i++) {
    console.log(`Generation ${i + 1}/${count}...`);
    try {
      // Pick a random lyric theme
      const theme = LYRIC_THEMES[i % LYRIC_THEMES.length];
      console.log(`  Generating lyrics for: ${theme}`);

      // Generate lyrics
      const lyricsResponse = await client.generateLyrics({ prompt: theme });
      const lyrics = lyricsResponse.lyrics;
      console.log(`  ✓ Lyrics generated`);

      // Generate vocal track
      const response = await client.generateSongAndWait({
        lyrics: lyrics,
        prompt: STYLE_PROMPT,
        model: 'auto'
      });

      for (const choice of response.choices || []) {
        const title = generateUniqueTitle(GENRE);
        const outputPath = path.join(OUTPUT_DIR, `${title}.flac`);
        console.log(`  Downloading: ${title}`);
        await downloadTrack(choice.flac_url || choice.url, outputPath);
        console.log(`  ✓ Created: ${title}`);
        totalTracks++;
      }
    } catch (error) {
      console.error(`  ✗ Failed: ${(error as Error).message}`);
    }
  }

  console.log(`\nDone! Generated ${totalTracks} tracks.`);
}

main().catch(console.error);
