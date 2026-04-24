/**
 * Generate Nu Jazz Soft tracks using prompt-based generation
 * WITHOUT "jazz" term - using electronic/downtempo terminology instead
 */

import { config } from 'dotenv';
config();

import { createClientFromEnv } from '../api/mureka-client.js';
import { generateUniqueTitle } from '../prompts/title-generator.js';
import * as fs from 'fs';
import * as path from 'path';
import { pipeline } from 'stream/promises';
import { Readable } from 'stream';

// Electronic/downtempo prompts WITHOUT "jazz" - varied lead instruments
const PROMPTS = [
  // Rhodes/Keys lead
  'downtempo electronic, fender rhodes lead melody, warm electric piano solo, broken beat, programmed drums, deep bass, ambient synth pads, chillout lounge, 90 BPM, mellow atmospheric, no vocals',
  // Guitar lead
  'downtempo electronic, clean electric guitar lead, nylon guitar melody, soft synth layers, broken beat groove, deep bass, ambient pads, chillout, 95 BPM, mellow sophisticated, no vocals',
  // Synth lead
  'downtempo electronic, analog synth lead melody, warm synth solo, ambient pads, broken beat drums, deep electronic bass, chillout groove, 92 BPM, atmospheric futuristic, no vocals',
  // Vibraphone lead
  'downtempo electronic, vibraphone lead melody, marimba, kalimba, soft electric piano chords, broken beat, ambient textures, deep bass, chillout lounge, 88 BPM, dreamy mellow, no vocals',
  // Flute lead
  'downtempo electronic, soft flute lead melody, bamboo flute solo, rhodes piano chords, synth pads, broken beat drums, deep bass, ambient electronic, chillout, 90 BPM, organic atmospheric, no vocals',
  // Piano lead
  'downtempo electronic, acoustic piano lead melody, soft piano solo, synth textures, broken beat, electronic drums, deep bass, ambient pads, 94 BPM, late night atmospheric, no vocals',
];

const OUTPUT_DIR = '/Users/norbert/Library/CloudStorage/GoogleDrive-platzer.norbert@gmail.com/My Drive/Mureka/tracks/Nu Jazz Soft';
const GENRE = 'downtempo';

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

  console.log(`Generating ${count} generations (${count * 2} tracks) of downtempo electronic (no jazz term)...`);
  console.log(`Output: ${OUTPUT_DIR}\n`);

  let totalTracks = 0;

  for (let i = 0; i < count; i++) {
    // Rotate through different prompts for variety
    const prompt = PROMPTS[i % PROMPTS.length];
    console.log(`Generation ${i + 1}/${count}...`);
    console.log(`  Using: ${prompt.substring(0, 60)}...`);

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
