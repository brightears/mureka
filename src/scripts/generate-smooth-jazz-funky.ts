/**
 * Generate Smooth Jazz Funky tracks using prompt-based generation
 */

import { config } from 'dotenv';
config();

import { createClientFromEnv } from '../api/mureka-client.js';
import { generateUniqueTitle } from '../prompts/title-generator.js';
import * as fs from 'fs';
import * as path from 'path';
import { pipeline } from 'stream/promises';
import { Readable } from 'stream';

const PROMPT = 'funky smooth jazz, groovy, funk groove, electric bass slap bass, fender rhodes electric piano, clean funky guitar, saxophone lead, synth pads, strong backbeat, syncopated drums, 100 BPM, sophisticated, danceable, no vocals, professional studio recording';
const OUTPUT_DIR = '/Users/norbert/Library/CloudStorage/GoogleDrive-platzer.norbert@gmail.com/My Drive/Mureka/tracks/Smooth Jazz Funky';
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

  console.log(`Generating ${count} generations (${count * 2} tracks) of funky smooth jazz...`);
  console.log(`Prompt: ${PROMPT}`);
  console.log(`Output: ${OUTPUT_DIR}\n`);

  let totalTracks = 0;

  for (let i = 0; i < count; i++) {
    console.log(`Generation ${i + 1}/${count}...`);
    try {
      const response = await client.generateInstrumentalAndWait({
        prompt: PROMPT,
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
