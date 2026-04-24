/**
 * Generate tracks using the winning prompt with unique titles and proper metadata
 */

import { config } from 'dotenv';
config();

import { createClientFromEnv } from '../api/mureka-client.js';
import { generateUniqueTitle } from '../prompts/title-generator.js';
import { tagAudioFile } from '../jobs/metadata-tagger.js';
import { TracksDatabase } from '../db/tracks.js';
import { createWriteStream, mkdirSync, existsSync } from 'fs';
import { dirname } from 'path';
import pLimit from 'p-limit';

// Vietnamese Tết - Festive V-pop instrumental
const WINNING_PROMPT = "Vietnamese pop instrumental, festive spring celebration, upbeat dance pop, bright synth, catchy melody, happy cheerful, major key, 125 BPM, Asian pop, Lunar New Year festival, no vocals, no sad, no minor key";

const OUTPUT_DIR = process.env.OUTPUT_DIR ||
  `${process.env.HOME}/Library/CloudStorage/GoogleDrive-platzer.norbert@gmail.com/My Drive/Mureka/tracks`;

const GENRE = "Vietnamese Tết";
const ALBUM = "Vietnamese Tết";
const ARTIST = "BMAsia";
const FORMAT = "flac";

async function downloadFile(url: string, outputPath: string): Promise<void> {
  const dir = dirname(outputPath);
  if (!existsSync(dir)) {
    mkdirSync(dir, { recursive: true });
  }

  const response = await fetch(url);
  if (!response.ok) throw new Error(`Download failed: ${response.status}`);

  const buffer = await response.arrayBuffer();
  const { writeFileSync } = await import('fs');
  writeFileSync(outputPath, Buffer.from(buffer));
}

async function main() {
  const count = parseInt(process.argv[2] || '50', 10);
  console.log(`Generating ${count} batches (${count * 2} tracks)...`);
  console.log(`Prompt: "${WINNING_PROMPT.substring(0, 70)}..."`);
  console.log('');

  const client = createClientFromEnv();
  const db = new TracksDatabase();
  const limit = pLimit(5); // 5 concurrent requests

  const batchId = crypto.randomUUID();
  let completed = 0;
  let failed = 0;

  const tasks: Promise<void>[] = [];

  for (let i = 0; i < count; i++) {
    tasks.push(limit(async () => {
      try {
        // Generate two unique titles for this batch
        const title1 = generateUniqueTitle(GENRE);
        const title2 = generateUniqueTitle(GENRE);

        // Call API and wait for completion
        const result = await client.generateInstrumentalAndWait({ prompt: WINNING_PROMPT });

        if (!result.choices || result.choices.length === 0) {
          console.log(`  ✗ Batch ${i + 1} no choices returned`);
          failed++;
          return;
        }

        // Process both tracks
        const titles = [title1, title2];
        for (let j = 0; j < result.choices.length && j < 2; j++) {
          const choice = result.choices[j];
          const title = titles[j];

          // Download
          const url = FORMAT === 'flac' ? choice.flac_url :
                      FORMAT === 'wav' ? choice.wav_url : choice.url;

          const genreFolder = `${GENRE} (${FORMAT})`;
          const outputPath = `${OUTPUT_DIR}/${genreFolder}/${title}.${FORMAT}`;

          await downloadFile(url, outputPath);

          // Tag metadata
          await tagAudioFile(outputPath, FORMAT as 'flac' | 'mp3' | 'wav', {
            title,
            artist: ARTIST,
            album: ALBUM,
            genre: 'Classical',
            date: new Date().toISOString().split('T')[0],
          });

          // Save to database
          db.insertTrack({
            song_id: choice.id,
            batch_job_id: batchId,
            genre: GENRE,
            prompt: WINNING_PROMPT,
            title,
            duration_ms: choice.duration || 0,
            mp3_url: choice.url,
            flac_url: choice.flac_url,
            wav_url: choice.wav_url,
            cover_url: '',
            genres: '[]',
            moods: '[]',
            model: result.model || 'auto',
            local_path: outputPath,
            downloaded_at: new Date().toISOString(),
          });

          console.log(`  ✓ ${title}`);
        }
        completed++;
      } catch (error) {
        console.error(`  ✗ Batch ${i + 1} error:`, error instanceof Error ? error.message : error);
        failed++;
      }
    }));
  }

  await Promise.all(tasks);

  console.log(`\n✔ Complete!`);
  console.log(`  Batches: ${completed} completed, ${failed} failed`);
  console.log(`  Tracks: ${completed * 2} generated`);
  console.log(`  Batch ID: ${batchId}`);
}

main().catch(console.error);
