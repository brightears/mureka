#!/usr/bin/env node

import { Command } from 'commander';
import ora from 'ora';
import { config } from 'dotenv';
import { createClientFromEnv } from './api/mureka-client.js';
import { PromptGenerator, formatPromptForDisplay } from './prompts/generator.js';
import { setTitlePrefix, getUsedTitleCount, getTotalVocabularySize, generateUniqueTitle } from './prompts/title-generator.js';
import { loadTemplate, listTemplates, savePromptBatch, listPromptBatches, loadPromptBatch } from './prompts/template-loader.js';
import { BatchRunner } from './jobs/batch-runner.js';
import { Downloader } from './jobs/downloader.js';
import { getDatabase } from './db/tracks.js';
import { MurekaModel } from './api/types.js';
import { uploadAndFineTune, checkFineTuningStatus, scanFolders } from './jobs/finetune-uploader.js';
import { ReferenceBatchGenerator } from './jobs/reference-batch-generator.js';

// Load environment variables
config();

const program = new Command();

program
  .name('mureka')
  .description('Automated bulk music generation using Mureka API')
  .version('1.0.0');

// Generate prompts command
program
  .command('prompts')
  .description('Generate and manage prompts')
  .argument('<action>', 'Action: create, list, show')
  .argument('[genre]', 'Genre template ID (for create/show)')
  .option('-c, --count <number>', 'Number of prompts to generate', '50')
  .option('-s, --systematic', 'Generate systematic combinations instead of random')
  .option('-p, --prefix <prefix>', 'Title prefix (default: MU)', 'MU')
  .action(async (action, genre, options) => {
    // Set title prefix if specified
    if (options.prefix) {
      setTitlePrefix(options.prefix);
    }
    const generator = new PromptGenerator();

    if (action === 'list') {
      console.log('\nAvailable genre templates:');
      const templates = listTemplates();
      if (templates.length === 0) {
        console.log('  No templates found. Create one in src/prompts/templates/');
      } else {
        templates.forEach((t) => console.log(`  - ${t}`));
      }

      console.log('\nSaved prompt batches:');
      const batches = listPromptBatches();
      if (batches.length === 0) {
        console.log('  No saved batches. Generate some with: mureka prompts create <genre>');
      } else {
        batches.forEach((b) => console.log(`  - ${b}`));
      }
      return;
    }

    if (action === 'create') {
      if (!genre) {
        console.error('Error: Genre template ID required');
        process.exit(1);
      }

      const spinner = ora(`Loading template: ${genre}`).start();
      try {
        const template = loadTemplate(genre);
        spinner.succeed(`Loaded template: ${template.name}`);

        const count = parseInt(options.count);
        spinner.start(`Generating ${count} prompts...`);

        const batch = options.systematic
          ? generator.generateSystematic(template, count)
          : generator.generateBatch(template, count);

        spinner.succeed(`Generated ${batch.count} unique prompts`);

        const filePath = savePromptBatch(batch, genre);
        console.log(`\nSaved to: ${filePath}`);

        console.log('\nSample prompts:');
        batch.prompts.slice(0, 3).forEach((p, i) => {
          console.log(`\n--- Prompt ${i + 1} ---`);
          console.log(formatPromptForDisplay(p));
        });
      } catch (error) {
        spinner.fail((error as Error).message);
        process.exit(1);
      }
      return;
    }

    if (action === 'show') {
      if (!genre) {
        console.error('Error: Batch filename required');
        process.exit(1);
      }

      try {
        const batch = loadPromptBatch(genre);
        console.log(`\nBatch: ${genre}`);
        console.log(`Total prompts: ${batch.count}`);
        console.log(`Created: ${batch.createdAt}`);

        console.log('\nPrompts:');
        batch.prompts.forEach((p, i) => {
          console.log(`\n--- Prompt ${i + 1} ---`);
          console.log(formatPromptForDisplay(p));
        });
      } catch (error) {
        console.error((error as Error).message);
        process.exit(1);
      }
      return;
    }

    console.error(`Unknown action: ${action}`);
    process.exit(1);
  });

// Generate command
program
  .command('generate')
  .description('Generate music tracks')
  .argument('<genre>', 'Genre template ID or saved batch filename')
  .option('-c, --count <number>', 'Number of tracks to generate', '10')
  .option('-m, --model <model>', 'Model to use: auto, mureka-7.5', 'auto')
  .option('-p, --prefix <prefix>', 'Title prefix (default: MU)', 'MU')
  .option('--from-batch <filename>', 'Use a saved prompt batch')
  .action(async (genre, options) => {
    // Set title prefix if specified
    if (options.prefix) {
      setTitlePrefix(options.prefix);
    }
    const spinner = ora('Initializing...').start();

    try {
      const client = createClientFromEnv();
      const runner = new BatchRunner({
        client,
        onProgress: (completed, total, failed) => {
          spinner.text = `Progress: ${completed}/${total} completed, ${failed} failed`;
        },
        onTrackComplete: (song) => {
          console.log(`\n  ✓ Generated: ${song.title}`);
        },
        onError: (error, prompt) => {
          const msg = error instanceof Error ? error.message : JSON.stringify(error);
          console.log(`\n  ✗ Failed: ${msg}`);
        },
      });

      let batch;
      if (options.fromBatch) {
        spinner.text = `Loading batch: ${options.fromBatch}`;
        batch = loadPromptBatch(options.fromBatch);
      } else {
        const template = loadTemplate(genre);
        const generator = new PromptGenerator();
        const count = parseInt(options.count);
        spinner.text = `Generating ${count} prompts from template: ${template.name}`;
        batch = generator.generateBatch(template, count);
      }

      spinner.succeed(`Loaded ${batch.count} prompts`);
      spinner.start('Starting generation...');

      const result = await runner.runBatch(batch, genre, options.model as MurekaModel);

      spinner.succeed('Batch complete!');
      console.log(`\n📊 Results:`);
      console.log(`  Total requested: ${result.totalRequested}`);
      console.log(`  Completed: ${result.completed}`);
      console.log(`  Failed: ${result.failed}`);
      console.log(`  Tracks generated: ${result.tracks.length} (2 per generation)`);
      console.log(`  Batch ID: ${result.batchJobId}`);
      console.log(`\nNext: Download tracks with: mureka download ${result.batchJobId}`);
    } catch (error) {
      spinner.fail((error as Error).message);
      process.exit(1);
    }
  });

// Vocal generation command
program
  .command('vocal')
  .description('Generate vocal tracks with AI-generated or custom lyrics')
  .argument('<theme>', 'Theme or topic for the song (e.g., "summer love", "rainy nights")')
  .option('-c, --count <number>', 'Number of songs to generate', '1')
  .option('-s, --style <style>', 'Music style prompt (e.g., "pop ballad, emotional")', 'pop, catchy melody, professional vocals')
  .option('-l, --lyrics <lyrics>', 'Custom lyrics (use [Verse], [Chorus], [Bridge] tags)')
  .option('-p, --prefix <prefix>', 'Title prefix (default: MU)', 'MU')
  .option('--show-lyrics', 'Display generated lyrics before creating song')
  .action(async (theme, options) => {
    if (options.prefix) {
      setTitlePrefix(options.prefix);
    }
    const spinner = ora('Initializing...').start();

    try {
      const client = createClientFromEnv();
      const db = getDatabase();
      const count = parseInt(options.count);

      let completed = 0;
      let failed = 0;
      const tracks: { title: string; songId: string }[] = [];

      for (let i = 0; i < count; i++) {
        try {
          // Step 1: Generate or use provided lyrics
          let lyrics = options.lyrics;
          if (!lyrics) {
            spinner.text = `[${i + 1}/${count}] Generating lyrics for: "${theme}"...`;
            const lyricsResponse = await client.generateLyrics({
              prompt: `Write a song about: ${theme}. Include [Verse], [Chorus], and [Bridge] sections.`,
            });
            lyrics = lyricsResponse.lyrics;

            if (options.showLyrics) {
              spinner.stop();
              console.log(`\n📝 Generated Lyrics:\n${lyrics}\n`);
              spinner.start();
            }
          }

          // Step 2: Generate unique title
          const title = generateUniqueTitle('vocal');

          // Step 3: Generate vocal track
          spinner.text = `[${i + 1}/${count}] Generating vocal track: "${title}"...`;
          const response = await client.generateSongAndWait({
            lyrics,
            prompt: options.style,
          });

          // Step 4: Save tracks to database
          if (response.choices && response.choices.length > 0) {
            const batchJobId = `vocal-${Date.now()}`;

            // Create a batch job entry
            db.createBatchJob({
              id: batchJobId,
              genre: 'vocal',
              totalTracks: response.choices.length,
              completedTracks: response.choices.length,
              failedTracks: 0,
              status: 'completed',
              createdAt: new Date(),
              prompts: [options.style],
            });

            for (let j = 0; j < response.choices.length; j++) {
              const choice = response.choices[j];
              const trackTitle = j === 0 ? title : generateUniqueTitle('vocal');

              db.insertTrack({
                song_id: choice.id,
                batch_job_id: batchJobId,
                genre: 'vocal',
                prompt: `Theme: ${theme}\nStyle: ${options.style}`,
                title: trackTitle,
                duration_ms: choice.duration,
                mp3_url: choice.url,
                flac_url: choice.flac_url,
                wav_url: choice.wav_url,
                cover_url: '',
                genres: JSON.stringify(['vocal']),
                moods: JSON.stringify([]),
                model: 'mureka-8',
                created_at: new Date().toISOString(),
              });

              tracks.push({ title: trackTitle, songId: choice.id });
              console.log(`\n  ✓ Generated: ${trackTitle}`);
            }
          }

          completed++;
        } catch (error) {
          failed++;
          console.log(`\n  ✗ Failed: ${(error as Error).message}`);
        }
      }

      spinner.succeed('Vocal generation complete!');
      console.log(`\n🎤 Results:`);
      console.log(`  Theme: "${theme}"`);
      console.log(`  Style: ${options.style}`);
      console.log(`  Requested: ${count}`);
      console.log(`  Completed: ${completed}`);
      console.log(`  Failed: ${failed}`);
      console.log(`  Tracks generated: ${tracks.length} (2 per generation)`);

      if (tracks.length > 0) {
        console.log(`\nNext: Download tracks with: mureka download all`);
      }
    } catch (error) {
      spinner.fail((error as Error).message);
      process.exit(1);
    }
  });

// Lyrics generation command
program
  .command('lyrics')
  .description('Generate lyrics without creating a song')
  .argument('<theme>', 'Theme or topic for the lyrics')
  .option('-o, --output <file>', 'Save lyrics to a file')
  .action(async (theme, options) => {
    const spinner = ora('Generating lyrics...').start();

    try {
      const client = createClientFromEnv();
      const response = await client.generateLyrics({
        prompt: `Write a song about: ${theme}. Include [Verse], [Chorus], and [Bridge] sections.`,
      });

      spinner.succeed('Lyrics generated!');
      console.log('\n📝 Lyrics:\n');
      console.log(response.lyrics);

      if (options.output) {
        const { writeFileSync } = await import('fs');
        writeFileSync(options.output, response.lyrics);
        console.log(`\nSaved to: ${options.output}`);
      }
    } catch (error) {
      spinner.fail((error as Error).message);
      process.exit(1);
    }
  });

// Download command
program
  .command('download')
  .description('Download generated tracks')
  .argument('[target]', 'Batch ID, genre, or "all" for pending downloads', 'all')
  .option('-f, --format <format>', 'Audio format: mp3, flac, wav', 'mp3')
  .option('-a, --album <name>', 'Album name for metadata tags')
  .option('--artist <name>', 'Artist name for metadata tags', 'BMAsia')
  .option('--no-metadata', 'Skip adding metadata tags')
  .action(async (target, options) => {
    const format = options.format as 'mp3' | 'flac' | 'wav';
    const formatLabel = format.toUpperCase();
    const spinner = ora(`Initializing downloader (${formatLabel})...`).start();

    try {
      const downloader = new Downloader({
        format,
        albumName: options.album,
        artist: options.artist,
        addMetadata: options.metadata !== false,
        onProgress: (downloaded, total) => {
          spinner.text = `Downloading ${formatLabel}: ${downloaded}/${total}`;
        },
        onComplete: (track, path) => {
          console.log(`\n  ✓ Downloaded: ${track.title}`);
        },
        onError: (error, track) => {
          console.log(`\n  ✗ Failed: ${track.title} - ${error.message}`);
        },
      });

      let result;
      if (target === 'all') {
        spinner.text = `Downloading all pending tracks as ${formatLabel}...`;
        result = await downloader.downloadPending();
      } else if (target.includes('-')) {
        // Looks like a batch ID (UUID)
        spinner.text = `Downloading batch as ${formatLabel}: ${target}`;
        result = await downloader.downloadBatch(target);
      } else {
        // Assume it's a genre
        spinner.text = `Downloading genre as ${formatLabel}: ${target}`;
        result = await downloader.downloadByGenre(target);
      }

      spinner.succeed(`Download complete! (${formatLabel})`);
      console.log(`\n📊 Results:`);
      console.log(`  Format: ${formatLabel}`);
      console.log(`  Total: ${result.total}`);
      console.log(`  Downloaded: ${result.downloaded}`);
      console.log(`  Failed: ${result.failed}`);
      if (options.metadata !== false) {
        console.log(`  Metadata: Tagged with album "${options.album || 'auto-generated'}"`);
      }
    } catch (error) {
      spinner.fail((error as Error).message);
      process.exit(1);
    }
  });

// Status command
program
  .command('status')
  .description('Show status and statistics')
  .action(async () => {
    const db = getDatabase();
    const stats = db.getStats();
    const batches = db.listBatchJobs();

    console.log('\n📊 Database Statistics:');
    console.log(`  Total tracks: ${stats.totalTracks}`);
    console.log(`  Total batches: ${stats.totalBatches}`);

    if (Object.keys(stats.genreCounts).length > 0) {
      console.log('\n  Tracks by genre:');
      for (const [genre, count] of Object.entries(stats.genreCounts)) {
        console.log(`    ${genre}: ${count}`);
      }
    }

    if (batches.length > 0) {
      console.log('\n📋 Recent Batch Jobs:');
      batches.slice(0, 5).forEach((batch) => {
        const progress = batch.totalTracks > 0
          ? Math.round((batch.completedTracks / batch.totalTracks) * 100)
          : 0;
        console.log(
          `  [${batch.status}] ${batch.id.slice(0, 8)}... - ${batch.genre} ` +
            `(${batch.completedTracks}/${batch.totalTracks} = ${progress}%)`
        );
      });
    }

    console.log('\n📁 Templates available:');
    listTemplates().forEach((t) => console.log(`  - ${t}`));

    console.log('\n🏷️ Title Generator:');
    console.log(`  Vocabulary size: ${getTotalVocabularySize()} words`);
    console.log(`  Used titles: ${getUsedTitleCount()}`);
  });

// Test connection command
program
  .command('test')
  .description('Test API connection')
  .action(async () => {
    const spinner = ora('Testing Mureka API connection...').start();

    try {
      const client = createClientFromEnv();

      // Try generating lyrics as a simple test
      const response = await client.generateLyrics({
        prompt: 'Write a short test lyric about the moon',
      });

      spinner.succeed('API connection successful!');
      console.log('\nTest lyrics generated:');
      console.log(response.lyrics.slice(0, 200) + '...');
    } catch (error) {
      spinner.fail(`API connection failed: ${(error as Error).message}`);
      process.exit(1);
    }
  });

// Fine-tuning command
program
  .command('finetune')
  .description('Fine-tune a custom model from reference tracks')
  .argument('<action>', 'Action: upload, status, scan')
  .argument('[value]', 'Folder paths (comma-separated) for upload, or task ID for status')
  .option('-s, --suffix <suffix>', 'Model name suffix (lowercase, numbers, hyphens only)', 'custom-model')
  .action(async (action, value, options) => {
    const spinner = ora('Initializing...').start();

    try {
      const client = createClientFromEnv();

      if (action === 'scan') {
        spinner.text = 'Scanning folders...';
        if (!value) {
          spinner.fail('Please provide folder paths (comma-separated)');
          process.exit(1);
        }

        const folders = value.split(',').map((f: string) => f.trim());
        spinner.stop();

        const tracks = scanFolders(folders);
        const valid = tracks.filter((t) => t.valid);
        const invalid = tracks.filter((t) => !t.valid);

        console.log('\n📊 Scan Results:');
        console.log(`   Total files: ${tracks.length}`);
        console.log(`   Valid for fine-tuning: ${valid.length}`);
        console.log(`   Invalid: ${invalid.length}`);

        if (invalid.length > 0) {
          console.log('\n⚠️  Invalid files:');
          invalid.forEach((t) => console.log(`   - ${t.name}: ${t.reason}`));
        }

        if (valid.length >= 100) {
          console.log(`\n✅ Ready for fine-tuning! Run:`);
          console.log(`   npm run dev -- finetune upload "${value}" -s your-model-name`);
        } else {
          console.log(`\n❌ Need at least 100 valid tracks (have ${valid.length})`);
        }
        return;
      }

      if (action === 'status') {
        if (!value) {
          spinner.fail('Please provide a task ID');
          process.exit(1);
        }

        spinner.text = `Checking fine-tuning status: ${value}`;
        spinner.stop();
        await checkFineTuningStatus(client, value);
        return;
      }

      if (action === 'upload') {
        if (!value) {
          spinner.fail('Please provide folder paths (comma-separated)');
          process.exit(1);
        }

        const folders = value.split(',').map((f: string) => f.trim());
        spinner.stop();

        const result = await uploadAndFineTune(client, folders, options.suffix, (progress) => {
          process.stdout.write(
            `\r   Progress: ${progress.uploadedFiles}/${progress.totalFiles} uploaded, ${progress.failedFiles} failed`
          );
        });

        if (result.fineTuningTask) {
          console.log(`\n✅ Fine-tuning started!`);
          console.log(`   Task ID: ${result.fineTuningTask.id}`);
          console.log(`   Check status: npm run dev -- finetune status ${result.fineTuningTask.id}`);
        }
        return;
      }

      spinner.fail(`Unknown action: ${action}. Use: scan, upload, or status`);
      process.exit(1);
    } catch (error) {
      spinner.fail((error as Error).message);
      process.exit(1);
    }
  });

// Reference-based generation command
program
  .command('reference-generate')
  .description('Generate tracks using reference audio files')
  .argument('<input-folder>', 'Folder containing reference audio files')
  .argument('<output-folder>', 'Output folder name (will be created in Google Drive/Mureka/tracks/)')
  .option('-t, --type <type>', 'Type: vocal or instrumental', 'instrumental')
  .option('-f, --format <format>', 'Output format: mp3, flac, wav', 'flac')
  .option('-m, --model <model>', 'Model: auto, mureka-7.5', 'auto')
  .option('-n, --tracks-per-ref <number>', 'Tracks to generate per reference (default 4)', '4')
  .option('-p, --parallel <number>', 'Max parallel requests', '5')
  .option('-s, --style <prompt>', 'Style prompt to guide generation (e.g., "smooth jazz, saxophone, mellow")')
  .action(async (inputFolder, outputFolder, options) => {
    const spinner = ora('Initializing reference generator...').start();

    try {
      const client = createClientFromEnv();

      const generator = new ReferenceBatchGenerator({
        client,
        maxParallel: parseInt(options.parallel),
        format: options.format as 'mp3' | 'flac' | 'wav',
        model: options.model as MurekaModel,
        tracksPerReference: parseInt(options.tracksPerRef),
        stylePrompt: options.style,
        onProgress: (message) => {
          spinner.text = message;
        },
        onTrackComplete: (title, outputPath) => {
          console.log(`\n  ✓ Created: ${title}`);
        },
        onError: (error, referencePath) => {
          console.log(`\n  ✗ Failed: ${referencePath} - ${error.message}`);
        },
      });

      const type = options.type as 'vocal' | 'instrumental';
      spinner.succeed(`Starting ${type} generation from: ${inputFolder}`);

      const result = await generator.processFolder(inputFolder, outputFolder, type);

      console.log(`\n\n📊 Reference Generation Results:`);
      console.log(`  Input folder: ${result.inputFolder}`);
      console.log(`  Output folder: ${result.outputFolder}`);
      console.log(`  References processed: ${result.totalReferences}`);
      console.log(`  Tracks generated: ${result.totalTracksGenerated}`);
      console.log(`  Failed: ${result.failed}`);
      console.log(`  Format: ${options.format.toUpperCase()}`);

      if (result.failed > 0) {
        console.log(`\n⚠️  Some references failed. Check the errors above.`);
      } else {
        console.log(`\n✅ All references processed successfully!`);
      }
    } catch (error) {
      spinner.fail((error as Error).message);
      process.exit(1);
    }
  });

program.parse();
