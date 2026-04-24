/**
 * Generate Nu Jazz Chillhop Instrumental tracks
 * Chillhop influence for more groove, less pure ambient, no saxophone
 */

import { config } from 'dotenv';
config();

import { createClientFromEnv } from '../api/mureka-client.js';
import { generateUniqueTitle } from '../prompts/title-generator.js';
import * as fs from 'fs';
import * as path from 'path';
import { pipeline } from 'stream/promises';
import { Readable } from 'stream';

// Chillhop-influenced nu jazz instrumental prompts - varied lead instruments
const PROMPTS = [
  // Rhodes/Keys lead
  'chillhop, nu jazz instrumental, downtempo groove, fender rhodes lead melody, lo-fi beats, warm electric piano, mellow, 90 BPM, jazzy chords, relaxed, no vocals',
  // Guitar lead
  'chillhop, nu jazz instrumental, downtempo groove, clean jazz guitar lead, nylon guitar melody, lo-fi drums, mellow sophisticated, 95 BPM, warm, no vocals',
  // Synth lead
  'chillhop, nu jazz instrumental, downtempo groove, warm synth melody, lo-fi beats, ambient pads, smooth, 92 BPM, atmospheric, no vocals',
  // Vibraphone lead
  'chillhop, nu jazz instrumental, downtempo groove, vibraphone lead melody, marimba, lo-fi drums, dreamy mellow, 88 BPM, jazzy, no vocals',
  // Piano lead
  'chillhop, nu jazz instrumental, downtempo groove, soft piano melody, lo-fi beats, jazzy chords, intimate, late night feel, 94 BPM, no vocals',
  // Rhodes variation
  'chillhop, nu jazz instrumental, downtempo groove, fender rhodes chords, lo-fi beats, warm mellow, soulful, 91 BPM, jazzy relaxed, no vocals',
  // Guitar variation
  'chillhop, nu jazz instrumental, downtempo groove, nylon guitar melody, lo-fi drums, soft intimate, 93 BPM, mellow, no vocals',
  // Piano variation
  'chillhop, nu jazz instrumental, downtempo groove, acoustic piano lead, lo-fi beats, smooth sophisticated, 89 BPM, late night, no vocals',
];

const OUTPUT_DIR = '/Users/norbert/Library/CloudStorage/GoogleDrive-platzer.norbert@gmail.com/My Drive/Mureka/tracks/Nu Jazz Chillhop';
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

  console.log(`Generating ${count} generations (${count * 2} tracks) of nu jazz chillhop instrumental...`);
  console.log(`Output: ${OUTPUT_DIR}\n`);

  let totalTracks = 0;

  for (let i = 0; i < count; i++) {
    const prompt = PROMPTS[i % PROMPTS.length];
    console.log(`Generation ${i + 1}/${count}...`);
    console.log(`  Using: ${prompt.substring(0, 55)}...`);

    try {
      const response = await client.generateInstrumentalAndWait({
        prompt: prompt,
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
