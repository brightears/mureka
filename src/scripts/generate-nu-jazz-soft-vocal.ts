/**
 * Generate Nu Jazz Soft Vocal tracks
 * With chillhop influence for more groove, less pure ambient
 */

import { config } from 'dotenv';
config();

import { createClientFromEnv } from '../api/mureka-client.js';
import { generateUniqueTitle } from '../prompts/title-generator.js';
import * as fs from 'fs';
import * as path from 'path';
import { pipeline } from 'stream/promises';
import { Readable } from 'stream';

// Chillhop-influenced nu jazz vocal prompts - varied lead instruments and vocal styles
const STYLE_PROMPTS = [
  // Rhodes/Keys lead - female
  'chillhop, nu jazz vocal, downtempo groove, fender rhodes lead, lo-fi beats, warm electric piano, smooth female vocals, mellow, 90 BPM, jazzy chords, relaxed',
  // Guitar lead - male
  'chillhop, nu jazz vocal, downtempo groove, clean jazz guitar lead, nylon guitar, lo-fi drums, smooth male vocals, mellow sophisticated, 95 BPM, warm',
  // Synth lead - female
  'chillhop, nu jazz vocal, downtempo groove, warm synth melody, lo-fi beats, ambient pads, soulful female vocals, 92 BPM, atmospheric',
  // Vibraphone lead - male
  'chillhop, nu jazz vocal, downtempo groove, vibraphone melody, marimba, lo-fi drums, soft male vocals, dreamy mellow, 88 BPM, jazzy',
  // Piano lead - female
  'chillhop, nu jazz vocal, downtempo groove, soft piano melody, lo-fi beats, jazzy chords, intimate female vocals, late night feel, 94 BPM',
  // Rhodes - male
  'chillhop, nu jazz vocal, downtempo groove, fender rhodes chords, lo-fi beats, warm male vocals, soulful, 91 BPM, jazzy relaxed',
  // Guitar - female
  'chillhop, nu jazz vocal, downtempo groove, nylon guitar melody, lo-fi drums, breathy female vocals, soft intimate, 93 BPM, mellow',
  // Piano - male
  'chillhop, nu jazz vocal, downtempo groove, acoustic piano lead, lo-fi beats, deep male vocals, smooth sophisticated, 89 BPM, late night',
];

const LYRIC_THEMES = [
  'mellow love song, late night city vibes, soft and intimate',
  'peaceful reflection, finding inner calm, gentle journey',
  'rainy afternoon, coffee shop mood, quiet contemplation',
  'starlit evening, dreamy romance, soft whispers',
  'sunrise hope, new beginnings, gentle optimism',
];

const OUTPUT_DIR = '/Users/norbert/Library/CloudStorage/GoogleDrive-platzer.norbert@gmail.com/My Drive/Mureka/tracks/Nu Jazz Soft Vocal';
const GENRE = 'nu jazz';

async function downloadTrack(url: string, outputPath: string): Promise<void> {
  const response = await fetch(url);
  if (!response.ok || !response.body) {
    throw new Error(`Download failed: ${response.status}`);
  }
  const writeStream = fs.createWriteStream(outputPath);
  await pipeline(Readable.fromWeb(response.body as ReadableStream), writeStream);
}

async function main() {
  const count = parseInt(process.argv[2] || '5'); // Number of generations (2 tracks each)
  const client = createClientFromEnv();

  fs.mkdirSync(OUTPUT_DIR, { recursive: true });

  console.log(`Generating ${count} generations (${count * 2} tracks) of nu jazz soft vocal with chillhop influence...`);
  console.log(`Output: ${OUTPUT_DIR}\n`);

  let totalTracks = 0;

  for (let i = 0; i < count; i++) {
    console.log(`Generation ${i + 1}/${count}...`);

    try {
      // Pick theme and style
      const theme = LYRIC_THEMES[i % LYRIC_THEMES.length];
      const stylePrompt = STYLE_PROMPTS[i % STYLE_PROMPTS.length];

      console.log(`  Theme: ${theme}`);
      console.log(`  Style: ${stylePrompt.substring(0, 50)}...`);

      // Generate lyrics
      const lyricsResponse = await client.generateLyrics({ prompt: theme });
      const lyrics = lyricsResponse.lyrics;
      console.log(`  ✓ Lyrics generated`);

      // Generate vocal track
      const response = await client.generateSongAndWait({
        lyrics: lyrics,
        prompt: stylePrompt,
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
