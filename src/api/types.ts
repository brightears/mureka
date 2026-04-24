// Mureka API Types

// Model types: standard models or fine-tuned "lora:mureka-6:ID:suffix"
export type MurekaModel = 'mureka-8' | 'mureka-o2' | 'mureka-7.6' | 'mureka-7.5' | 'auto' | string;

export type GenerationStatus = 'pending' | 'preparing' | 'processing' | 'completed' | 'succeeded' | 'failed';

// Request types
export interface GenerateInstrumentalRequest {
  prompt: string; // max 1000 chars
  title?: string; // max 50 chars
  model?: MurekaModel;
}

export interface GenerateSongRequest {
  lyrics: string; // with [Verse], [Chorus], [Bridge] tags
  prompt: string; // style description
  model?: MurekaModel;
}

export interface GenerateLyricsRequest {
  prompt: string;
}

// Response types
// Choice from instrumental/song generation
export interface GenerationChoice {
  id: string;
  url: string;           // MP3 URL
  flac_url?: string;     // FLAC URL
  wav_url?: string;      // WAV URL
  duration: number;      // Duration in milliseconds
  index?: number;
}

// Legacy Song interface (for compatibility)
export interface Song {
  song_id: string;
  title: string;
  version: number;
  duration_milliseconds: number;
  genres: string[];
  moods: string[];
  mp3_url: string;
  flac_url?: string;
  wav_url?: string;
  cover: string;
  share_link: string;
  machine_audit_state: string;
  credit_type: string;
}

export interface GenerationResponse {
  id: string;
  created_at: number;
  finished_at?: number;
  model: string;
  status: GenerationStatus;
  trace_id: string;
  choices?: GenerationChoice[];  // Actual API response
  songs?: Song[];                 // Legacy/alternative format
}

export interface LyricsResponse {
  lyrics: string;
}

// Internal types for job management
export interface GenerationJob {
  id: string;
  type: 'instrumental' | 'song';
  prompt: string;
  title?: string;
  lyrics?: string;
  model: MurekaModel;
  status: GenerationStatus;
  createdAt: Date;
  completedAt?: Date;
  songs?: Song[];
  error?: string;
  retryCount: number;
}

export interface BatchJob {
  id: string;
  genre: string;
  totalTracks: number;
  completedTracks: number;
  failedTracks: number;
  status: 'pending' | 'running' | 'completed' | 'paused';
  createdAt: Date;
  prompts: string[];
  generations: GenerationJob[];
}

// Track metadata for database
export interface TrackMetadata {
  id: number;
  song_id: string;
  batch_job_id: string;
  genre: string;
  prompt: string;
  title: string;
  duration_ms: number;
  mp3_url: string;
  flac_url?: string;
  wav_url?: string;
  local_path?: string;
  cover_url: string;
  genres: string;
  moods: string;
  model: string;
  created_at: string;
  downloaded_at?: string;
}

export type AudioFormat = 'mp3' | 'flac' | 'wav';

// API Error
export interface MurekaApiError {
  status: number;
  message: string;
  code?: string;
}

export class MurekaError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string
  ) {
    super(message);
    this.name = 'MurekaError';
  }
}

// ============================================
// Fine-Tuning Types
// ============================================

export type UploadStatus = 'pending' | 'completed' | 'cancelled';
export type FineTuningStatus = 'preparing' | 'queued' | 'running' | 'succeeded' | 'failed' | 'timeouted' | 'cancelled';

// Upload API
export interface CreateUploadRequest {
  upload_name: string;
  purpose: 'fine-tuning';
  bytes?: number;
}

export interface UploadResponse {
  id: string;
  upload_name: string;
  purpose: string;
  bytes: number;
  created_at: number;
  expires_at: number;
  status: UploadStatus;
  parts: string[];
}

export interface UploadPartResponse {
  id: string;
  upload_id: string;
  created_at: number;
}

// Fine-Tuning API
export interface CreateFineTuningRequest {
  upload_id: string;
  suffix: string; // max 32 chars, lowercase + numbers + hyphens
}

export interface FineTuningResponse {
  id: string;
  upload_id: string;
  model: string;
  created_at: number;
  finished_at?: number;
  status: FineTuningStatus;
  failed_reason?: string;
  fine_tuned_model?: string;
}

// Local tracking for upload progress
export interface UploadProgress {
  uploadId: string;
  totalFiles: number;
  uploadedFiles: number;
  failedFiles: number;
  skippedFiles: number; // Too long/short duration
  currentFile?: string;
}

// ============================================
// Reference-Based Generation Types
// ============================================

export type FileUploadPurpose = 'reference' | 'instrumental' | 'vocal' | 'melody' | 'voice' | 'audio' | 'fine-tuning';

export interface UploadFileRequest {
  purpose: FileUploadPurpose;
  file: string; // File path
}

export interface UploadFileResponse {
  id: string;
  purpose: string;
  filename: string;
  bytes: number;
  created_at: number;
}

export interface GenerateWithReferenceRequest {
  reference_id: string;
  lyrics: string;
  prompt?: string;
  model?: MurekaModel;
  n?: number; // Number of tracks (default 2, max 3)
}

export interface GenerateWithInstrumentalRequest {
  instrumental_id: string;
  prompt?: string;
  model?: MurekaModel;
  n?: number; // Number of tracks (default 2, max 3)
}
