/**
 * Fine-Tuning Uploader
 * Uploads reference tracks and starts fine-tuning task
 */

import * as fs from 'fs';
import * as path from 'path';
import { execSync } from 'child_process';
import { MurekaClient } from '../api/mureka-client.js';
import { FineTuningResponse, UploadProgress } from '../api/types.js';

// Duration limits for fine-tuning (in seconds)
const MIN_DURATION = 30;
const MAX_DURATION = 270;
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

interface TrackInfo {
  path: string;
  name: string;
  duration: number;
  size: number;
  valid: boolean;
  reason?: string;
}

interface UploadResult {
  uploadId: string;
  totalFiles: number;
  uploadedFiles: number;
  skippedFiles: number;
  failedFiles: number;
  tracks: TrackInfo[];
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
 * Scan folders for valid audio files
 */
export function scanFolders(folders: string[]): TrackInfo[] {
  const tracks: TrackInfo[] = [];

  for (const folder of folders) {
    if (!fs.existsSync(folder)) {
      console.error(`Folder not found: ${folder}`);
      continue;
    }

    const files = fs.readdirSync(folder);
    for (const file of files) {
      const ext = path.extname(file).toLowerCase();
      if (ext !== '.mp3' && ext !== '.m4a') {
        continue;
      }

      const filePath = path.join(folder, file);
      const stats = fs.statSync(filePath);
      const duration = getAudioDuration(filePath);

      const track: TrackInfo = {
        path: filePath,
        name: file,
        duration,
        size: stats.size,
        valid: true,
      };

      // Validate
      if (duration < MIN_DURATION) {
        track.valid = false;
        track.reason = `Too short: ${duration.toFixed(1)}s (min ${MIN_DURATION}s)`;
      } else if (duration > MAX_DURATION) {
        track.valid = false;
        track.reason = `Too long: ${duration.toFixed(1)}s (max ${MAX_DURATION}s)`;
      } else if (stats.size > MAX_FILE_SIZE) {
        track.valid = false;
        track.reason = `Too large: ${(stats.size / 1024 / 1024).toFixed(1)}MB (max 10MB)`;
      }

      tracks.push(track);
    }
  }

  return tracks;
}

/**
 * Upload tracks and start fine-tuning
 */
export async function uploadAndFineTune(
  client: MurekaClient,
  folders: string[],
  modelSuffix: string,
  onProgress?: (progress: UploadProgress) => void
): Promise<{ uploadResult: UploadResult; fineTuningTask?: FineTuningResponse }> {
  console.log('\n📁 Scanning folders for audio files...');
  const allTracks = scanFolders(folders);

  const validTracks = allTracks.filter((t) => t.valid);
  const invalidTracks = allTracks.filter((t) => !t.valid);

  console.log(`\n📊 Scan Results:`);
  console.log(`   Total files: ${allTracks.length}`);
  console.log(`   Valid: ${validTracks.length}`);
  console.log(`   Invalid: ${invalidTracks.length}`);

  if (invalidTracks.length > 0) {
    console.log(`\n⚠️  Skipped files:`);
    for (const track of invalidTracks) {
      console.log(`   - ${track.name}: ${track.reason}`);
    }
  }

  if (validTracks.length < 100) {
    console.error(`\n❌ Not enough valid tracks. Need at least 100, found ${validTracks.length}`);
    return {
      uploadResult: {
        uploadId: '',
        totalFiles: allTracks.length,
        uploadedFiles: 0,
        skippedFiles: invalidTracks.length,
        failedFiles: 0,
        tracks: allTracks,
      },
    };
  }

  // Create upload
  console.log(`\n📤 Creating upload for ${validTracks.length} tracks...`);
  const upload = await client.createUpload(`cny-finetune-${Date.now()}`);
  console.log(`   Upload ID: ${upload.id}`);

  const progress: UploadProgress = {
    uploadId: upload.id,
    totalFiles: validTracks.length,
    uploadedFiles: 0,
    failedFiles: 0,
    skippedFiles: invalidTracks.length,
  };

  // Upload each file
  console.log(`\n📤 Uploading files...`);
  let failedFiles = 0;

  for (let i = 0; i < validTracks.length; i++) {
    const track = validTracks[i];
    progress.currentFile = track.name;

    if (onProgress) {
      onProgress({ ...progress });
    }

    try {
      process.stdout.write(`   [${i + 1}/${validTracks.length}] ${track.name}...`);
      await client.addUploadPart(upload.id, track.path);
      progress.uploadedFiles++;
      console.log(' ✓');
    } catch (error) {
      progress.failedFiles++;
      failedFiles++;
      console.log(` ✗ ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  // Complete upload
  console.log(`\n📦 Completing upload...`);
  const completedUpload = await client.completeUpload(upload.id);
  console.log(`   Status: ${completedUpload.status}`);
  console.log(`   Parts: ${completedUpload.parts.length}`);

  const uploadResult: UploadResult = {
    uploadId: upload.id,
    totalFiles: allTracks.length,
    uploadedFiles: progress.uploadedFiles,
    skippedFiles: invalidTracks.length,
    failedFiles,
    tracks: allTracks,
  };

  // Start fine-tuning
  if (progress.uploadedFiles >= 100) {
    console.log(`\n🎯 Starting fine-tuning task...`);
    console.log(`   Model suffix: ${modelSuffix}`);
    const fineTuning = await client.createFineTuning(upload.id, modelSuffix);
    console.log(`   Task ID: ${fineTuning.id}`);
    console.log(`   Status: ${fineTuning.status}`);
    console.log(`   Base model: ${fineTuning.model}`);
    console.log(`\n⏳ Fine-tuning started. This typically takes ~3 hours.`);
    console.log(`   Check status with: npm run dev -- finetune status ${fineTuning.id}`);

    return { uploadResult, fineTuningTask: fineTuning };
  } else {
    console.log(`\n❌ Not enough files uploaded (${progress.uploadedFiles}). Need at least 100.`);
    return { uploadResult };
  }
}

/**
 * Check fine-tuning status
 */
export async function checkFineTuningStatus(
  client: MurekaClient,
  taskId: string
): Promise<FineTuningResponse> {
  const status = await client.queryFineTuning(taskId);

  console.log(`\n📊 Fine-Tuning Status:`);
  console.log(`   Task ID: ${status.id}`);
  console.log(`   Status: ${status.status}`);
  console.log(`   Base Model: ${status.model}`);

  if (status.created_at) {
    console.log(`   Created: ${new Date(status.created_at * 1000).toLocaleString()}`);
  }

  if (status.finished_at) {
    console.log(`   Finished: ${new Date(status.finished_at * 1000).toLocaleString()}`);
  }

  if (status.status === 'succeeded' && status.fine_tuned_model) {
    console.log(`\n✅ Fine-tuned model ready: ${status.fine_tuned_model}`);
    console.log(`   Use in templates: "model": "${status.fine_tuned_model}"`);
  }

  if (status.status === 'failed') {
    console.log(`\n❌ Training failed!`);
    if (status.failed_reason) {
      console.log(`   Reason: ${status.failed_reason}`);
    } else {
      console.log(`   No failure reason provided by API`);
    }
  }

  return status;
}
