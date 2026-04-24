/**
 * Reference-Based Batch Generator
 * Generates new tracks using existing tracks as style references
 * Each reference track produces 4 new tracks (2 generations × 2 tracks each)
 */

import { execSync } from 'child_process';
import * as fs from 'fs';
import * as path from 'path';
import { pipeline } from 'stream/promises';
import { Readable } from 'stream';
import pLimit from 'p-limit';
import { MurekaClient } from '../api/mureka-client.js';
import { GenerationResponse, FileUploadPurpose, MurekaModel } from '../api/types.js';
import { generateUniqueTitle } from '../prompts/title-generator.js';
import {
  tagAudioFile,
  generateAlbumName,
  mapToStandardGenre,
  createMetadataConfig,
} from './metadata-tagger.js';

const MAX_PARALLEL = 5; // $1000 tier allows 5 concurrent requests
const CLIP_DURATION = 30; // Reference clips must be exactly 30 seconds
const TEMP_DIR = '/tmp/mureka-clips';

// Default output path (Google Drive)
const GOOGLE_DRIVE_BASE = path.join(
  process.env.HOME || '',
  'Library/CloudStorage/GoogleDrive-platzer.norbert@gmail.com/My Drive/Mureka/tracks'
);

export interface ReferenceGeneratorConfig {
  client: MurekaClient;
  outputDir?: string;
  maxParallel?: number;
  format?: 'mp3' | 'flac' | 'wav';
  model?: MurekaModel;
  tracksPerReference?: number; // How many tracks to generate per reference (default 4)
  stylePrompt?: string; // Optional style prompt to guide generation (e.g., "smooth jazz, saxophone, mellow")
  onProgress?: (message: string) => void;
  onTrackComplete?: (title: string, outputPath: string) => void;
  onError?: (error: Error, referencePath: string) => void;
}

export interface ReferenceResult {
  referencePath: string;
  referenceId: string;
  tracksGenerated: number;
  outputPaths: string[];
  errors: string[];
}

export interface FolderResult {
  inputFolder: string;
  outputFolder: string;
  totalReferences: number;
  totalTracksGenerated: number;
  failed: number;
  results: ReferenceResult[];
}

/**
 * Get audio duration using macOS afinfo
 */
function getAudioDuration(filePath: string): number {
  try {
    const output = execSync(`afinfo "${filePath}" 2>/dev/null | grep "estimated duration"`, {
      encoding: 'utf-8',
    });
    const match = output.match(/estimated duration:\s*([\d.]+)/);
    return match ? parseFloat(match[1]) : 0;
  } catch {
    return 0;
  }
}

/**
 * Create a 30-second clip from the start of an audio file
 */
export function createReferenceClip(inputPath: string, outputPath: string): void {
  // Ensure temp directory exists
  if (!fs.existsSync(TEMP_DIR)) {
    fs.mkdirSync(TEMP_DIR, { recursive: true });
  }

  // Check if file exists
  if (!fs.existsSync(inputPath)) {
    throw new Error(`Input file not found: ${inputPath}`);
  }

  // Get duration to verify file is long enough
  const duration = getAudioDuration(inputPath);
  if (duration < CLIP_DURATION) {
    throw new Error(`File too short: ${duration.toFixed(1)}s (need at least ${CLIP_DURATION}s)`);
  }

  // Create 30-second clip using ffmpeg
  // -t 30: duration of 30 seconds
  // -acodec libmp3lame: output as MP3
  // -ab 256k: 256kbps bitrate
  execSync(
    `ffmpeg -y -i "${inputPath}" -t ${CLIP_DURATION} -acodec libmp3lame -ab 256k "${outputPath}" 2>/dev/null`,
    { encoding: 'utf-8' }
  );

  if (!fs.existsSync(outputPath)) {
    throw new Error(`Failed to create clip: ${outputPath}`);
  }
}

/**
 * Upload a reference clip and return the reference ID
 */
export async function uploadReference(
  client: MurekaClient,
  clipPath: string,
  purpose: FileUploadPurpose
): Promise<string> {
  const response = await client.uploadFile(clipPath, purpose);
  return response.id;
}

/**
 * Download a track from URL to local path
 */
async function downloadTrack(url: string, outputPath: string): Promise<void> {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Download failed: ${response.status} ${response.statusText}`);
  }

  if (!response.body) {
    throw new Error('No response body');
  }

  // Ensure directory exists
  const dir = path.dirname(outputPath);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }

  const writeStream = fs.createWriteStream(outputPath);
  await pipeline(Readable.fromWeb(response.body as ReadableStream), writeStream);
}

/**
 * Generate tracks using a reference
 */
async function generateWithReference(
  client: MurekaClient,
  referenceId: string,
  type: 'vocal' | 'instrumental',
  lyrics: string | null,
  genre: string,
  outputFolder: string,
  format: 'mp3' | 'flac' | 'wav',
  model: MurekaModel,
  stylePrompt?: string,
  onTrackComplete?: (title: string, outputPath: string) => void
): Promise<string[]> {
  const outputPaths: string[] = [];

  let response: GenerationResponse;

  if (type === 'instrumental') {
    response = await client.generateWithInstrumentalAndWait({
      instrumental_id: referenceId,
      prompt: stylePrompt,
      model,
      n: 2,
    });
  } else {
    if (!lyrics) {
      throw new Error('Lyrics required for vocal generation');
    }
    response = await client.generateWithReferenceAndWait({
      reference_id: referenceId,
      lyrics,
      prompt: stylePrompt,
      model,
      n: 2,
    });
  }

  // Process each generated track
  const choices = response.choices || [];
  for (const choice of choices) {
    const title = generateUniqueTitle(genre);
    const ext = format;

    // Get the right URL for the format
    let url: string | undefined;
    switch (format) {
      case 'flac':
        url = choice.flac_url || choice.url;
        break;
      case 'wav':
        url = choice.wav_url || choice.url;
        break;
      default:
        url = choice.url;
    }

    if (!url) {
      console.warn(`No ${format.toUpperCase()} URL available for track, skipping`);
      continue;
    }

    const outputPath = path.join(outputFolder, `${title}.${ext}`);
    await downloadTrack(url, outputPath);

    // Add metadata
    try {
      const metadataConfig = createMetadataConfig({
        artist: 'BMAsia',
        albumArtist: 'BMAsia',
      });
      const album = generateAlbumName(genre, format);
      const standardGenre = mapToStandardGenre(genre);

      await tagAudioFile(outputPath, format, {
        title,
        album,
        genre: standardGenre,
      }, metadataConfig);
    } catch (tagError) {
      console.warn(`Warning: Failed to tag ${title}: ${(tagError as Error).message}`);
    }

    outputPaths.push(outputPath);
    onTrackComplete?.(title, outputPath);
  }

  return outputPaths;
}

/**
 * Process a single reference track
 */
export async function processReference(
  client: MurekaClient,
  referencePath: string,
  type: 'vocal' | 'instrumental',
  genre: string,
  outputFolder: string,
  format: 'mp3' | 'flac' | 'wav' = 'flac',
  model: MurekaModel = 'auto',
  tracksPerReference: number = 4,
  stylePrompt?: string,
  onProgress?: (message: string) => void,
  onTrackComplete?: (title: string, outputPath: string) => void
): Promise<ReferenceResult> {
  const result: ReferenceResult = {
    referencePath,
    referenceId: '',
    tracksGenerated: 0,
    outputPaths: [],
    errors: [],
  };

  const fileName = path.basename(referencePath);
  const clipPath = path.join(TEMP_DIR, `clip-${Date.now()}.mp3`);

  try {
    // Step 1: Create 30-second clip
    onProgress?.(`Creating clip for: ${fileName}`);
    createReferenceClip(referencePath, clipPath);

    // Step 2: Upload clip
    onProgress?.(`Uploading: ${fileName}`);
    const purpose: FileUploadPurpose = type === 'instrumental' ? 'instrumental' : 'reference';
    result.referenceId = await uploadReference(client, clipPath, purpose);
    onProgress?.(`Uploaded as ${purpose}: ${result.referenceId}`);

    // Step 3: Generate lyrics if vocal track
    let lyrics: string | null = null;
    if (type === 'vocal') {
      onProgress?.(`Generating CNY lyrics...`);
      const lyricsResponse = await client.generateLyrics({
        prompt: `Write a Chinese New Year blessing song with warm wishes for prosperity,
happiness, and good fortune. Include [Verse], [Chorus], and [Bridge] sections.
Themes: spring festival celebration, family reunion, red envelopes, lion dance,
new beginnings, good luck, abundance. Keep it joyful, festive, and uplifting.`,
      });
      lyrics = lyricsResponse.lyrics;
    }

    // Step 4: Generate tracks (2 generations × 2 tracks = 4 tracks per reference)
    const generationsNeeded = Math.ceil(tracksPerReference / 2);
    for (let i = 0; i < generationsNeeded; i++) {
      onProgress?.(`Generating tracks (${i + 1}/${generationsNeeded})...`);
      try {
        const paths = await generateWithReference(
          client,
          result.referenceId,
          type,
          lyrics,
          genre,
          outputFolder,
          format,
          model,
          stylePrompt,
          onTrackComplete
        );
        result.outputPaths.push(...paths);
        result.tracksGenerated += paths.length;
      } catch (genError) {
        result.errors.push(`Generation ${i + 1} failed: ${(genError as Error).message}`);
      }
    }
  } catch (error) {
    result.errors.push((error as Error).message);
  } finally {
    // Clean up temp clip
    if (fs.existsSync(clipPath)) {
      fs.unlinkSync(clipPath);
    }
  }

  return result;
}

/**
 * Scan a folder for audio files
 */
function scanFolder(folderPath: string): string[] {
  if (!fs.existsSync(folderPath)) {
    throw new Error(`Folder not found: ${folderPath}`);
  }

  const files = fs.readdirSync(folderPath);
  const audioFiles: string[] = [];

  for (const file of files) {
    const ext = path.extname(file).toLowerCase();
    if (['.mp3', '.m4a', '.wav', '.flac', '.aac'].includes(ext)) {
      audioFiles.push(path.join(folderPath, file));
    }
  }

  return audioFiles.sort();
}

/**
 * Process an entire folder of reference tracks
 */
export async function processFolder(
  config: ReferenceGeneratorConfig,
  inputFolder: string,
  outputFolder: string,
  type: 'vocal' | 'instrumental'
): Promise<FolderResult> {
  const { client, maxParallel = MAX_PARALLEL, format = 'flac', model = 'auto', tracksPerReference = 4, stylePrompt } = config;

  // Determine genre from folder name
  const genre = path.basename(inputFolder).replace(/\s*\(\d+\)\s*$/, '').trim();

  // Construct full output path
  const fullOutputFolder = config.outputDir
    ? path.join(config.outputDir, outputFolder)
    : path.join(GOOGLE_DRIVE_BASE, outputFolder);

  // Ensure output folder exists
  if (!fs.existsSync(fullOutputFolder)) {
    fs.mkdirSync(fullOutputFolder, { recursive: true });
  }

  const result: FolderResult = {
    inputFolder,
    outputFolder: fullOutputFolder,
    totalReferences: 0,
    totalTracksGenerated: 0,
    failed: 0,
    results: [],
  };

  // Scan for audio files
  const audioFiles = scanFolder(inputFolder);
  result.totalReferences = audioFiles.length;

  config.onProgress?.(`Found ${audioFiles.length} reference tracks in ${path.basename(inputFolder)}`);
  config.onProgress?.(`Output folder: ${fullOutputFolder}`);
  config.onProgress?.(`Type: ${type}, Format: ${format}, Tracks per reference: ${tracksPerReference}`);

  // Process with concurrency limit
  const limit = pLimit(maxParallel);
  const tasks = audioFiles.map((audioFile, index) =>
    limit(async () => {
      config.onProgress?.(`\n[${index + 1}/${audioFiles.length}] Processing: ${path.basename(audioFile)}`);

      const refResult = await processReference(
        client,
        audioFile,
        type,
        genre,
        fullOutputFolder,
        format,
        model,
        tracksPerReference,
        stylePrompt,
        config.onProgress,
        config.onTrackComplete
      );

      result.results.push(refResult);
      result.totalTracksGenerated += refResult.tracksGenerated;

      if (refResult.errors.length > 0) {
        result.failed++;
        config.onError?.(new Error(refResult.errors.join('; ')), audioFile);
      }

      config.onProgress?.(
        `Completed: ${path.basename(audioFile)} → ${refResult.tracksGenerated} tracks`
      );
    })
  );

  await Promise.all(tasks);

  return result;
}

/**
 * Reference Batch Generator class for CLI integration
 */
export class ReferenceBatchGenerator {
  private config: ReferenceGeneratorConfig;

  constructor(config: ReferenceGeneratorConfig) {
    this.config = config;
  }

  /**
   * Process a single reference track and generate new tracks
   */
  async processReference(
    referencePath: string,
    type: 'vocal' | 'instrumental',
    genre: string,
    outputFolder: string
  ): Promise<ReferenceResult> {
    return processReference(
      this.config.client,
      referencePath,
      type,
      genre,
      outputFolder,
      this.config.format || 'flac',
      this.config.model || 'auto',
      this.config.tracksPerReference || 4,
      this.config.onProgress,
      this.config.onTrackComplete
    );
  }

  /**
   * Process an entire folder of reference tracks
   */
  async processFolder(
    inputFolder: string,
    outputFolder: string,
    type: 'vocal' | 'instrumental'
  ): Promise<FolderResult> {
    return processFolder(this.config, inputFolder, outputFolder, type);
  }
}
