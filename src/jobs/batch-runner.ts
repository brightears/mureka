import { randomUUID } from 'crypto';
import pLimit from 'p-limit';
import { MurekaClient } from '../api/mureka-client.js';
import { GenerationJob, BatchJob, Song, MurekaModel, GenerationChoice } from '../api/types.js';
import { GeneratedPrompt, PromptBatch } from '../prompts/types.js';
import { TracksDatabase, getDatabase } from '../db/tracks.js';
import { generateUniqueTitle } from '../prompts/title-generator.js';

const MAX_PARALLEL = 5; // $1000 tier allows 5 concurrent requests
const POLL_DELAY = 5000;

// Convert API choice to Song format for compatibility
function choiceToSong(choice: GenerationChoice, title: string): Song {
  return {
    song_id: choice.id,
    title: title,
    version: 1,
    duration_milliseconds: choice.duration,
    genres: [],
    moods: [],
    mp3_url: choice.url,
    flac_url: choice.flac_url,
    wav_url: choice.wav_url,
    cover: '',
    share_link: '',
    machine_audit_state: '',
    credit_type: '',
  };
}

export interface BatchRunnerConfig {
  client: MurekaClient;
  db?: TracksDatabase;
  maxParallel?: number;
  onProgress?: (completed: number, total: number, failed: number) => void;
  onTrackComplete?: (song: Song, prompt: string) => void;
  onError?: (error: Error, prompt: string) => void;
}

export interface BatchResult {
  batchJobId: string;
  totalRequested: number;
  completed: number;
  failed: number;
  tracks: Song[];
}

export class BatchRunner {
  private client: MurekaClient;
  private db: TracksDatabase;
  private maxParallel: number;
  private onProgress?: (completed: number, total: number, failed: number) => void;
  private onTrackComplete?: (song: Song, prompt: string) => void;
  private onError?: (error: Error, prompt: string) => void;

  constructor(config: BatchRunnerConfig) {
    this.client = config.client;
    this.db = config.db || getDatabase();
    this.maxParallel = config.maxParallel || MAX_PARALLEL;
    this.onProgress = config.onProgress;
    this.onTrackComplete = config.onTrackComplete;
    this.onError = config.onError;
  }

  /**
   * Run a batch generation from a prompt batch
   */
  async runBatch(
    promptBatch: PromptBatch,
    genre: string,
    model: MurekaModel = 'auto'
  ): Promise<BatchResult> {
    const batchJobId = randomUUID();
    const tracks: Song[] = [];
    let completed = 0;
    let failed = 0;

    // Create batch job in database
    this.db.createBatchJob({
      id: batchJobId,
      genre,
      totalTracks: promptBatch.count,
      completedTracks: 0,
      failedTracks: 0,
      status: 'running',
      createdAt: new Date(),
      prompts: promptBatch.prompts.map((p) => p.prompt),
    });

    // Create generation jobs
    for (const prompt of promptBatch.prompts) {
      const job: GenerationJob = {
        id: randomUUID(),
        type: prompt.type === 'vocal' ? 'song' : 'instrumental',
        prompt: prompt.prompt,
        title: prompt.title,
        model,
        status: 'pending',
        createdAt: new Date(),
        retryCount: 0,
      };
      this.db.createGenerationJob(job, batchJobId);
    }

    // Run generations with concurrency limit
    const limit = pLimit(this.maxParallel);
    const tasks = promptBatch.prompts.map((prompt) =>
      limit(async () => {
        try {
          const result = await this.generateTrack(prompt, batchJobId, model);
          completed++;

          for (const song of result) {
            tracks.push(song);
            this.onTrackComplete?.(song, prompt.prompt);
          }

          this.db.updateBatchJobProgress(batchJobId, completed, failed, 'running');
          this.onProgress?.(completed, promptBatch.count, failed);
        } catch (error) {
          failed++;
          if (error instanceof Error) {
            this.onError?.(error, prompt.prompt);
          } else {
            this.onError?.(new Error(JSON.stringify(error)), prompt.prompt);
          }
          this.db.updateBatchJobProgress(batchJobId, completed, failed, 'running');
          this.onProgress?.(completed, promptBatch.count, failed);
        }
      })
    );

    await Promise.all(tasks);

    // Update final status
    const finalStatus = failed === promptBatch.count ? 'completed' : 'completed';
    this.db.updateBatchJobProgress(batchJobId, completed, failed, finalStatus);

    return {
      batchJobId,
      totalRequested: promptBatch.count,
      completed,
      failed,
      tracks,
    };
  }

  /**
   * Generate a single track and save to database
   */
  private async generateTrack(
    prompt: GeneratedPrompt,
    batchJobId: string,
    model: MurekaModel
  ): Promise<Song[]> {
    let response;

    if (prompt.type === 'instrumental') {
      response = await this.client.generateInstrumentalAndWait({
        prompt: prompt.prompt,
        title: prompt.title,
        model,
      });
    } else {
      // For vocal tracks, generate lyrics first based on lyricTheme
      const lyricTheme = prompt.components.lyricTheme || 'love and life';
      const mood = prompt.components.mood;
      const genre = prompt.components.genre;
      const language = prompt.components.language || 'English';

      // Generate lyrics using the theme with language specification
      const languageInstruction = language !== 'English'
        ? `Write the lyrics entirely in ${language}. `
        : '';
      const lyricsResponse = await this.client.generateLyrics({
        prompt: `${languageInstruction}Write a ${mood} song about "${lyricTheme}" in the style of ${genre}. Include [Verse], [Chorus], and [Bridge] sections. Keep lyrics warm, positive, and suitable for background listening.`,
      });

      // Generate vocal track with the lyrics
      response = await this.client.generateSongAndWait({
        lyrics: lyricsResponse.lyrics,
        prompt: prompt.prompt,
        model,
      });
    }

    // Handle both choices (new API) and songs (legacy) formats
    let songs: Song[] = [];
    if (response.choices && response.choices.length > 0) {
      // First track keeps the original title, additional tracks get unique titles
      songs = response.choices.map((choice, i) => {
        const title = i === 0
          ? prompt.title
          : generateUniqueTitle(prompt.components.genre);
        return choiceToSong(choice, title);
      });
    } else if (response.songs) {
      songs = response.songs;
    }

    // Save tracks to database
    for (const song of songs) {
      this.db.insertTrack({
        song_id: song.song_id,
        batch_job_id: batchJobId,
        genre: prompt.components.genre,
        prompt: prompt.prompt,
        title: song.title,
        duration_ms: song.duration_milliseconds,
        mp3_url: song.mp3_url,
        flac_url: song.flac_url,
        wav_url: song.wav_url,
        cover_url: song.cover || '',
        genres: JSON.stringify(song.genres || []),
        moods: JSON.stringify(song.moods || []),
        model,
        created_at: new Date().toISOString(),
      });
    }

    return songs;
  }

  /**
   * Resume a paused or incomplete batch job
   */
  async resumeBatch(batchJobId: string): Promise<BatchResult> {
    const batchJob = this.db.getBatchJob(batchJobId);
    if (!batchJob) {
      throw new Error(`Batch job not found: ${batchJobId}`);
    }

    const pendingJobs = this.db.getPendingGenerationJobs(batchJobId);
    if (pendingJobs.length === 0) {
      return {
        batchJobId,
        totalRequested: batchJob.totalTracks,
        completed: batchJob.completedTracks,
        failed: batchJob.failedTracks,
        tracks: [],
      };
    }

    const tracks: Song[] = [];
    let completed = batchJob.completedTracks;
    let failed = batchJob.failedTracks;

    this.db.updateBatchJobProgress(batchJobId, completed, failed, 'running');

    const limit = pLimit(this.maxParallel);
    const tasks = pendingJobs.map((job) =>
      limit(async () => {
        try {
          this.db.incrementRetryCount(job.id);

          const response =
            job.type === 'instrumental'
              ? await this.client.generateInstrumentalAndWait({
                  prompt: job.prompt,
                  title: job.title,
                  model: job.model,
                })
              : await this.client.generateSongAndWait({
                  lyrics: job.lyrics || '',
                  prompt: job.prompt,
                  model: job.model,
                });

          const songs = response.songs || [];
          completed++;

          for (const song of songs) {
            tracks.push(song);
            this.db.insertTrack({
              song_id: song.song_id,
              batch_job_id: batchJobId,
              genre: batchJob.genre,
              prompt: job.prompt,
              title: song.title,
              duration_ms: song.duration_milliseconds,
              mp3_url: song.mp3_url,
              cover_url: song.cover,
              genres: JSON.stringify(song.genres),
              moods: JSON.stringify(song.moods),
              model: job.model,
              created_at: new Date().toISOString(),
            });
          }

          this.db.updateGenerationJobStatus(job.id, 'completed');
          this.db.updateBatchJobProgress(batchJobId, completed, failed, 'running');
          this.onProgress?.(completed, batchJob.totalTracks, failed);
        } catch (error) {
          failed++;
          this.db.updateGenerationJobStatus(job.id, 'failed', (error as Error).message);
          this.db.updateBatchJobProgress(batchJobId, completed, failed, 'running');
          this.onError?.(error as Error, job.prompt);
          this.onProgress?.(completed, batchJob.totalTracks, failed);
        }
      })
    );

    await Promise.all(tasks);

    this.db.updateBatchJobProgress(batchJobId, completed, failed, 'completed');

    return {
      batchJobId,
      totalRequested: batchJob.totalTracks,
      completed,
      failed,
      tracks,
    };
  }

  /**
   * Get status of a batch job
   */
  getStatus(batchJobId: string): BatchJob | undefined {
    return this.db.getBatchJob(batchJobId);
  }

  /**
   * List all batch jobs
   */
  listBatchJobs(): BatchJob[] {
    return this.db.listBatchJobs();
  }
}
