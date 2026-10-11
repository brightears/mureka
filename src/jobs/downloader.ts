import { createWriteStream, existsSync, mkdirSync, renameSync, statSync, unlinkSync } from 'fs';
import { randomBytes } from 'crypto';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { pipeline } from 'stream/promises';
import { Readable } from 'stream';
import pLimit from 'p-limit';
import { TracksDatabase, getDatabase } from '../db/tracks.js';
import { TrackMetadata, AudioFormat } from '../api/types.js';
import {
  tagAudioFile,
  generateAlbumName,
  mapToStandardGenre,
  MetadataConfig,
  createMetadataConfig,
} from './metadata-tagger.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Default to Google Drive if available, otherwise local output folder
const GOOGLE_DRIVE_PATH = join(
  process.env.HOME || '',
  'Library/CloudStorage/GoogleDrive-platzer.norbert@gmail.com/My Drive/Mureka/tracks'
);
const LOCAL_OUTPUT_DIR = join(__dirname, '../../output/tracks');
const DEFAULT_OUTPUT_DIR = process.env.OUTPUT_DIR ||
  (existsSync(dirname(GOOGLE_DRIVE_PATH)) ? GOOGLE_DRIVE_PATH : LOCAL_OUTPUT_DIR);
const MAX_PARALLEL_DOWNLOADS = 5;

// Any completed audio file smaller than this is an error body, not a track
// (a real Mureka MP3/FLAC is megabytes). Guards both fresh downloads and the
// resume skip below.
const MIN_AUDIO_BYTES = 100_000;

export interface DownloadConfig {
  db?: TracksDatabase;
  outputDir?: string;
  maxParallel?: number;
  format?: AudioFormat;
  // Metadata options
  albumName?: string;
  artist?: string;
  addMetadata?: boolean;
  onProgress?: (downloaded: number, total: number) => void;
  onComplete?: (track: TrackMetadata, localPath: string) => void;
  onError?: (error: Error, track: TrackMetadata) => void;
}

export interface DownloadResult {
  total: number;
  downloaded: number;
  failed: number;
  paths: string[];
}

export class Downloader {
  private db: TracksDatabase;
  private outputDir: string;
  private maxParallel: number;
  private format: AudioFormat;
  private albumName?: string;
  private artist?: string;
  private addMetadata: boolean;
  private metadataConfig: MetadataConfig;
  private onProgress?: (downloaded: number, total: number) => void;
  private onComplete?: (track: TrackMetadata, localPath: string) => void;
  private onError?: (error: Error, track: TrackMetadata) => void;

  constructor(config: DownloadConfig = {}) {
    this.db = config.db || getDatabase();
    this.outputDir = config.outputDir || DEFAULT_OUTPUT_DIR;
    this.maxParallel = config.maxParallel || MAX_PARALLEL_DOWNLOADS;
    this.format = config.format || 'mp3';
    this.albumName = config.albumName;
    this.artist = config.artist;
    this.addMetadata = config.addMetadata !== false; // Default to true
    this.metadataConfig = createMetadataConfig({
      artist: config.artist,
      albumArtist: config.artist,
    });
    this.onProgress = config.onProgress;
    this.onComplete = config.onComplete;
    this.onError = config.onError;

    // Ensure output directory exists
    if (!existsSync(this.outputDir)) {
      mkdirSync(this.outputDir, { recursive: true });
    }
  }

  /**
   * Download all tracks that haven't been downloaded yet
   */
  async downloadPending(): Promise<DownloadResult> {
    const tracks = this.db.getTracksNotDownloaded();
    return this.downloadTracks(tracks);
  }

  /**
   * Download tracks for a specific batch job
   */
  async downloadBatch(batchJobId: string): Promise<DownloadResult> {
    const tracks = this.db.getTracksByBatchJob(batchJobId).filter((t) => !t.local_path);
    return this.downloadTracks(tracks);
  }

  /**
   * Download tracks for a specific genre
   */
  async downloadByGenre(genre: string): Promise<DownloadResult> {
    const tracks = this.db.getTracksByGenre(genre).filter((t) => !t.local_path);
    return this.downloadTracks(tracks);
  }

  /**
   * Download a list of tracks
   */
  async downloadTracks(tracks: TrackMetadata[]): Promise<DownloadResult> {
    const paths: string[] = [];
    let downloaded = 0;
    let failed = 0;

    const limit = pLimit(this.maxParallel);
    const tasks = tracks.map((track) =>
      limit(async () => {
        try {
          const localPath = await this.downloadTrack(track);
          paths.push(localPath);
          downloaded++;
          this.onComplete?.(track, localPath);
          this.onProgress?.(downloaded, tracks.length);
        } catch (error) {
          failed++;
          this.onError?.(error as Error, track);
          this.onProgress?.(downloaded, tracks.length);
        }
      })
    );

    await Promise.all(tasks);

    return {
      total: tracks.length,
      downloaded,
      failed,
      paths,
    };
  }

  /**
   * Download a single track
   */
  async downloadTrack(track: TrackMetadata): Promise<string> {
    const filename = this.generateFilename(track);
    const localPath = join(this.outputDir, filename);

    // Skip if a plausible complete file already exists. The size floor matters:
    // before the atomic tmp+rename below existed, a killed/failed run could
    // leave a truncated file at the final path and this skip made the
    // truncation PERMANENT (the 2026-08 track-health investigation found this
    // was the only way a short file could silently reach the catalog). With
    // atomic renames a final-path file is always a completed download, but the
    // floor still catches historical debris.
    if (existsSync(localPath)) {
      let existingSize = 0;
      try {
        existingSize = statSync(localPath).size;
      } catch {
        existingSize = 0;
      }
      if (existingSize >= MIN_AUDIO_BYTES) {
        this.db.updateTrackLocalPath(track.song_id, localPath);
        return localPath;
      }
      // Too small to be a track — treat as a failed download and redo it.
      try {
        unlinkSync(localPath);
      } catch {
        /* ignore — the rename below overwrites it anyway */
      }
    }

    // Ensure subdirectory exists (if organizing by genre)
    const dir = dirname(localPath);
    if (!existsSync(dir)) {
      mkdirSync(dir, { recursive: true });
    }

    // Get the appropriate URL based on format
    const url = this.getUrlForFormat(track);
    if (!url) {
      throw new Error(`No ${this.format.toUpperCase()} URL available for this track`);
    }

    // Download file
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Failed to download: ${response.status} ${response.statusText}`);
    }

    if (!response.body) {
      throw new Error('No response body');
    }

    // Stream to a temp name in the SAME directory, verify, then atomically
    // rename into place. The final path can therefore never hold a partial
    // file — a crash/kill mid-stream leaves only a .part file that the next
    // run ignores (and re-downloads cleanly). This matters doubly on the
    // Google Drive stream mount, where 5 concurrent writers + a flaky sync
    // made silent truncation a real occurrence.
    const tmpPath = `${localPath}.part-${randomBytes(4).toString('hex')}`;
    try {
      const writeStream = createWriteStream(tmpPath);
      await pipeline(Readable.fromWeb(response.body as ReadableStream), writeStream);

      const written = statSync(tmpPath).size;
      const expected = Number(response.headers.get('content-length') || 0);
      if (expected > 0 && written !== expected) {
        throw new Error(
          `Truncated download for ${track.title}: got ${written} of ${expected} bytes`
        );
      }
      if (written < MIN_AUDIO_BYTES) {
        throw new Error(
          `Download too small to be audio for ${track.title}: ${written} bytes`
        );
      }
      renameSync(tmpPath, localPath);
    } catch (err) {
      try {
        unlinkSync(tmpPath);
      } catch {
        /* already gone */
      }
      throw err;
    }

    // Add metadata tags if enabled
    if (this.addMetadata) {
      try {
        const album = this.albumName || generateAlbumName(track.genre, this.format);
        const genre = mapToStandardGenre(track.genre);

        await tagAudioFile(localPath, this.format, {
          title: track.title,
          album: album,
          genre: genre,
          // Date is automatically added by tagAudioFile
        }, this.metadataConfig);
      } catch (tagError) {
        // Don't fail the download if tagging fails, just log it
        console.warn(`Warning: Failed to tag ${track.title}: ${(tagError as Error).message}`);
      }
    }

    // Update database
    this.db.updateTrackLocalPath(track.song_id, localPath);

    return localPath;
  }

  /**
   * Get the download URL for the specified format
   */
  private getUrlForFormat(track: TrackMetadata): string | undefined {
    switch (this.format) {
      case 'flac':
        return track.flac_url || track.mp3_url; // Fallback to MP3 if FLAC not available
      case 'wav':
        return track.wav_url || track.mp3_url; // Fallback to MP3 if WAV not available
      default:
        return track.mp3_url;
    }
  }

  /**
   * Generate a filename for a track
   * Format: genre-folder/MU - Title.format
   * Note: Song ID removed since titles are globally unique
   */
  private generateFilename(track: TrackMetadata): string {
    // Sanitize genre for folder name
    let genreFolder = this.sanitizeFilename(track.genre);

    // Add format suffix to folder name for non-MP3 formats
    if (this.format !== 'mp3') {
      genreFolder = `${genreFolder} (${this.format})`;
    }

    // Sanitize title for filename (keep the "MU - " prefix from title)
    const title = this.sanitizeFilename(track.title);

    return `${genreFolder}/${title}.${this.format}`;
  }

  /**
   * Sanitize a string for use in filenames
   */
  private sanitizeFilename(str: string): string {
    return str
      .replace(/[<>:"/\\|?*]+/g, '-') // Replace invalid filename chars
      .replace(/\s+/g, ' ') // Normalize whitespace
      .replace(/^[-\s]+|[-\s]+$/g, '') // Trim leading/trailing dashes and spaces
      .slice(0, 100); // Reasonable length limit
  }

  /**
   * Get download statistics
   */
  getStats(): { total: number; downloaded: number; pending: number } {
    const allTracks = this.db.getStats().totalTracks;
    const pending = this.db.getTracksNotDownloaded().length;
    const downloaded = allTracks - pending;

    return { total: allTracks, downloaded, pending };
  }
}
