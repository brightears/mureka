import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { TrackMetadata, BatchJob, GenerationJob } from '../api/types.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const DATA_DIR = join(__dirname, '../../data');
const TRACKS_FILE = join(DATA_DIR, 'tracks.json');
const BATCH_JOBS_FILE = join(DATA_DIR, 'batch-jobs.json');
const GENERATION_JOBS_FILE = join(DATA_DIR, 'generation-jobs.json');

interface TracksData {
  tracks: TrackMetadata[];
  nextId: number;
}

interface BatchJobsData {
  jobs: (Omit<BatchJob, 'generations' | 'createdAt'> & { createdAt: string })[];
}

interface GenerationJobsData {
  jobs: (Omit<GenerationJob, 'createdAt' | 'completedAt'> & {
    batchJobId: string;
    createdAt: string;
    completedAt?: string;
  })[];
}

export class TracksDatabase {
  private tracksData: TracksData;
  private batchJobsData: BatchJobsData;
  private generationJobsData: GenerationJobsData;

  constructor() {
    // Ensure data directory exists
    if (!existsSync(DATA_DIR)) {
      mkdirSync(DATA_DIR, { recursive: true });
    }

    this.tracksData = this.loadJson<TracksData>(TRACKS_FILE, { tracks: [], nextId: 1 });
    this.batchJobsData = this.loadJson<BatchJobsData>(BATCH_JOBS_FILE, { jobs: [] });
    this.generationJobsData = this.loadJson<GenerationJobsData>(GENERATION_JOBS_FILE, { jobs: [] });
  }

  private loadJson<T>(filePath: string, defaultValue: T): T {
    if (existsSync(filePath)) {
      const content = readFileSync(filePath, 'utf-8');
      return JSON.parse(content) as T;
    }
    return defaultValue;
  }

  private saveTracks(): void {
    writeFileSync(TRACKS_FILE, JSON.stringify(this.tracksData, null, 2));
  }

  private saveBatchJobs(): void {
    writeFileSync(BATCH_JOBS_FILE, JSON.stringify(this.batchJobsData, null, 2));
  }

  private saveGenerationJobs(): void {
    writeFileSync(GENERATION_JOBS_FILE, JSON.stringify(this.generationJobsData, null, 2));
  }

  // Track operations
  insertTrack(track: Omit<TrackMetadata, 'id'>): number {
    const id = this.tracksData.nextId++;
    const newTrack: TrackMetadata = { id, ...track };
    this.tracksData.tracks.push(newTrack);
    this.saveTracks();
    return id;
  }

  getTrackBySongId(songId: string): TrackMetadata | undefined {
    return this.tracksData.tracks.find((t) => t.song_id === songId);
  }

  getTracksByGenre(genre: string): TrackMetadata[] {
    return this.tracksData.tracks.filter((t) => t.genre === genre);
  }

  getTracksByBatchJob(batchJobId: string): TrackMetadata[] {
    return this.tracksData.tracks.filter((t) => t.batch_job_id === batchJobId);
  }

  updateTrackLocalPath(songId: string, localPath: string): void {
    const track = this.tracksData.tracks.find((t) => t.song_id === songId);
    if (track) {
      track.local_path = localPath;
      track.downloaded_at = new Date().toISOString();
      this.saveTracks();
    }
  }

  getTracksNotDownloaded(): TrackMetadata[] {
    return this.tracksData.tracks.filter((t) => !t.local_path);
  }

  // Batch job operations
  createBatchJob(job: Omit<BatchJob, 'generations'>): void {
    this.batchJobsData.jobs.push({
      ...job,
      createdAt: job.createdAt.toISOString(),
    });
    this.saveBatchJobs();
  }

  getBatchJob(id: string): BatchJob | undefined {
    const job = this.batchJobsData.jobs.find((j) => j.id === id);
    if (!job) return undefined;

    return {
      ...job,
      createdAt: new Date(job.createdAt),
      generations: [],
    };
  }

  updateBatchJobProgress(id: string, completed: number, failed: number, status: BatchJob['status']): void {
    const job = this.batchJobsData.jobs.find((j) => j.id === id);
    if (job) {
      job.completedTracks = completed;
      job.failedTracks = failed;
      job.status = status;
      this.saveBatchJobs();
    }
  }

  listBatchJobs(): BatchJob[] {
    return this.batchJobsData.jobs
      .map((job) => ({
        ...job,
        createdAt: new Date(job.createdAt),
        generations: [],
      }))
      .sort((a, b) => b.createdAt.getTime() - a.createdAt.getTime());
  }

  // Generation job operations
  createGenerationJob(job: GenerationJob, batchJobId: string): void {
    this.generationJobsData.jobs.push({
      ...job,
      batchJobId,
      createdAt: job.createdAt.toISOString(),
      completedAt: job.completedAt?.toISOString(),
    });
    this.saveGenerationJobs();
  }

  updateGenerationJobStatus(id: string, status: string, error?: string): void {
    const job = this.generationJobsData.jobs.find((j) => j.id === id);
    if (job) {
      job.status = status as GenerationJob['status'];
      job.error = error;
      if (status === 'completed' || status === 'failed') {
        job.completedAt = new Date().toISOString();
      }
      this.saveGenerationJobs();
    }
  }

  incrementRetryCount(id: string): void {
    const job = this.generationJobsData.jobs.find((j) => j.id === id);
    if (job) {
      job.retryCount++;
      this.saveGenerationJobs();
    }
  }

  getPendingGenerationJobs(batchJobId: string): GenerationJob[] {
    return this.generationJobsData.jobs
      .filter(
        (j) =>
          j.batchJobId === batchJobId &&
          (j.status === 'pending' || j.status === 'failed') &&
          j.retryCount < 3
      )
      .map((j) => ({
        ...j,
        createdAt: new Date(j.createdAt),
        completedAt: j.completedAt ? new Date(j.completedAt) : undefined,
      }));
  }

  // Stats
  getStats(): { totalTracks: number; totalBatches: number; genreCounts: Record<string, number> } {
    const totalTracks = this.tracksData.tracks.length;
    const totalBatches = this.batchJobsData.jobs.length;

    const genreCounts: Record<string, number> = {};
    for (const track of this.tracksData.tracks) {
      genreCounts[track.genre] = (genreCounts[track.genre] || 0) + 1;
    }

    return { totalTracks, totalBatches, genreCounts };
  }

  close(): void {
    // No-op for JSON storage, but kept for interface compatibility
  }
}

// Singleton instance
let dbInstance: TracksDatabase | null = null;

export function getDatabase(): TracksDatabase {
  if (!dbInstance) {
    dbInstance = new TracksDatabase();
  }
  return dbInstance;
}
