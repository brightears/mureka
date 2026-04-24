import {
  GenerateInstrumentalRequest,
  GenerateSongRequest,
  GenerateLyricsRequest,
  GenerationResponse,
  LyricsResponse,
  MurekaError,
  MurekaModel,
  CreateUploadRequest,
  UploadResponse,
  UploadPartResponse,
  CreateFineTuningRequest,
  FineTuningResponse,
  FileUploadPurpose,
  UploadFileResponse,
  GenerateWithReferenceRequest,
  GenerateWithInstrumentalRequest,
} from './types.js';
import * as fs from 'fs';
import * as path from 'path';

const DEFAULT_BASE_URL = 'https://api.mureka.ai';
const DEFAULT_TIMEOUT = 300000; // 5 minutes
const MIN_REQUEST_INTERVAL = 3000; // 3 seconds between requests
const MAX_RETRIES = 3;
const POLL_INTERVAL = 5000; // 5 seconds between status checks

interface MurekaClientConfig {
  apiKey: string;
  baseUrl?: string;
  timeout?: number;
  maxParallel?: number;
}

export class MurekaClient {
  private apiKey: string;
  private baseUrl: string;
  private timeout: number;
  private lastRequestTime = 0;
  private activeRequests = 0;
  private maxParallel: number;

  constructor(config: MurekaClientConfig) {
    this.apiKey = config.apiKey;
    this.baseUrl = config.baseUrl || DEFAULT_BASE_URL;
    this.timeout = config.timeout || DEFAULT_TIMEOUT;
    this.maxParallel = config.maxParallel || 10;
  }

  private async waitForRateLimit(): Promise<void> {
    const now = Date.now();
    const timeSinceLastRequest = now - this.lastRequestTime;

    if (timeSinceLastRequest < MIN_REQUEST_INTERVAL) {
      const waitTime = MIN_REQUEST_INTERVAL - timeSinceLastRequest;
      await this.sleep(waitTime);
    }

    // Wait if we're at max parallel requests
    while (this.activeRequests >= this.maxParallel) {
      await this.sleep(1000);
    }
  }

  private sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  private async request<T>(
    endpoint: string,
    method: 'GET' | 'POST' = 'GET',
    body?: unknown
  ): Promise<T> {
    await this.waitForRateLimit();

    this.activeRequests++;
    this.lastRequestTime = Date.now();

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.timeout);

      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        method,
        headers: {
          Authorization: `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json',
        },
        body: body ? JSON.stringify(body) : undefined,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorText = await response.text();
        let errorMessage = `HTTP ${response.status}`;
        try {
          const errorJson = JSON.parse(errorText);
          // Handle nested error objects
          const msg = errorJson.message || errorJson.error;
          if (typeof msg === 'string') {
            errorMessage = msg;
          } else if (msg && typeof msg === 'object') {
            errorMessage = JSON.stringify(msg);
          } else {
            errorMessage = JSON.stringify(errorJson);
          }
        } catch {
          errorMessage = errorText || errorMessage;
        }

        throw new MurekaError(errorMessage, response.status);
      }

      return (await response.json()) as T;
    } finally {
      this.activeRequests--;
    }
  }

  private async requestWithRetry<T>(
    endpoint: string,
    method: 'GET' | 'POST' = 'GET',
    body?: unknown,
    retries = MAX_RETRIES
  ): Promise<T> {
    let lastError: Error | null = null;

    for (let attempt = 0; attempt <= retries; attempt++) {
      try {
        return await this.request<T>(endpoint, method, body);
      } catch (error) {
        lastError = error as Error;

        if (error instanceof MurekaError) {
          // Don't retry on 4xx errors (except 429)
          if (error.status >= 400 && error.status < 500 && error.status !== 429) {
            throw error;
          }
        }

        if (attempt < retries) {
          // Exponential backoff: 1s, 2s, 4s, 8s...
          const backoff = Math.pow(2, attempt) * 1000;
          console.log(`Request failed, retrying in ${backoff}ms... (attempt ${attempt + 1}/${retries})`);
          await this.sleep(backoff);
        }
      }
    }

    throw lastError;
  }

  /**
   * Generate instrumental/background music
   */
  async generateInstrumental(
    request: GenerateInstrumentalRequest
  ): Promise<GenerationResponse> {
    if (request.prompt.length > 1000) {
      throw new MurekaError('Prompt must be 1000 characters or less', 400);
    }
    if (request.title && request.title.length > 50) {
      throw new MurekaError('Title must be 50 characters or less', 400);
    }

    // Valid model values: "auto" (resolves to mureka-8/V8), "mureka-8", "mureka-7.6", "mureka-7.5", "mureka-o2"
    const body: { prompt: string; title?: string; model: string } = {
      prompt: request.prompt,
      model: request.model || 'auto',
    };
    if (request.title) {
      body.title = request.title;
    }

    return this.requestWithRetry<GenerationResponse>(
      '/v1/instrumental/generate',
      'POST',
      body
    );
  }

  /**
   * Generate song with vocals
   */
  async generateSong(request: GenerateSongRequest): Promise<GenerationResponse> {
    // Valid model values: "auto", "mureka-7.5", "mureka-7.6", "mureka-o2", "mureka-8" (V8 beta)
    // Default to mureka-8 (V8) for enhanced quality
    const body: { lyrics: string; prompt: string; model: string } = {
      lyrics: request.lyrics,
      prompt: request.prompt,
      model: request.model || 'mureka-8',
    };
    return this.requestWithRetry<GenerationResponse>('/v1/song/generate', 'POST', body);
  }

  /**
   * Generate lyrics from a prompt
   */
  async generateLyrics(request: GenerateLyricsRequest): Promise<LyricsResponse> {
    return this.requestWithRetry<LyricsResponse>('/v1/lyrics/generate', 'POST', request);
  }

  /**
   * Poll for generation completion
   */
  async waitForCompletion(
    generationId: string,
    type: 'instrumental' | 'song' = 'instrumental',
    maxWaitMs = this.timeout
  ): Promise<GenerationResponse> {
    const startTime = Date.now();
    // Correct endpoint: /v1/{type}/query/{id}
    const endpoint = type === 'instrumental'
      ? `/v1/instrumental/query/${generationId}`
      : `/v1/song/query/${generationId}`;

    while (Date.now() - startTime < maxWaitMs) {
      const response = await this.requestWithRetry<GenerationResponse>(endpoint, 'GET');

      // API returns 'succeeded' not 'completed'
      if (response.status === 'succeeded' || response.status === 'completed') {
        return response;
      }

      if (response.status === 'failed') {
        throw new MurekaError(`Generation failed: ${generationId}`, 500);
      }

      await this.sleep(POLL_INTERVAL);
    }

    throw new MurekaError(`Generation timed out: ${generationId}`, 408);
  }

  /**
   * Generate instrumental and wait for completion
   */
  async generateInstrumentalAndWait(
    request: GenerateInstrumentalRequest
  ): Promise<GenerationResponse> {
    const response = await this.generateInstrumental(request);
    return this.waitForCompletion(response.id, 'instrumental');
  }

  /**
   * Generate song and wait for completion
   */
  async generateSongAndWait(request: GenerateSongRequest): Promise<GenerationResponse> {
    const response = await this.generateSong(request);
    return this.waitForCompletion(response.id, 'song');
  }

  /**
   * Get current active request count
   */
  getActiveRequests(): number {
    return this.activeRequests;
  }

  /**
   * Check if we can make more requests
   */
  canMakeRequest(): boolean {
    return this.activeRequests < this.maxParallel;
  }

  // ============================================
  // Fine-Tuning API Methods
  // ============================================

  /**
   * Create an upload object for fine-tuning
   */
  async createUpload(name: string): Promise<UploadResponse> {
    const body: CreateUploadRequest = {
      upload_name: name,
      purpose: 'fine-tuning',
    };
    return this.requestWithRetry<UploadResponse>('/v1/uploads/create', 'POST', body);
  }

  /**
   * Add a file part to an upload (multipart/form-data)
   * Requirements: MP3 or M4A, 30-270 seconds, max 10MB
   */
  async addUploadPart(uploadId: string, filePath: string): Promise<UploadPartResponse> {
    await this.waitForRateLimit();
    this.activeRequests++;
    this.lastRequestTime = Date.now();

    try {
      const fileBuffer = fs.readFileSync(filePath);
      const fileName = path.basename(filePath);

      // Create form data manually for Node.js
      const boundary = '----FormBoundary' + Math.random().toString(36).substring(2);

      const header = [
        `--${boundary}`,
        `Content-Disposition: form-data; name="upload_id"`,
        '',
        uploadId,
        `--${boundary}`,
        `Content-Disposition: form-data; name="file"; filename="${fileName}"`,
        `Content-Type: audio/mpeg`,
        '',
        '',
      ].join('\r\n');

      const footer = `\r\n--${boundary}--\r\n`;

      const headerBuffer = Buffer.from(header, 'utf-8');
      const footerBuffer = Buffer.from(footer, 'utf-8');
      const bodyBuffer = Buffer.concat([headerBuffer, fileBuffer, footerBuffer]);

      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.timeout);

      const response = await fetch(`${this.baseUrl}/v1/uploads/add`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${this.apiKey}`,
          'Content-Type': `multipart/form-data; boundary=${boundary}`,
        },
        body: bodyBuffer,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorText = await response.text();
        throw new MurekaError(`Upload failed: ${errorText}`, response.status);
      }

      return (await response.json()) as UploadPartResponse;
    } finally {
      this.activeRequests--;
    }
  }

  /**
   * Complete an upload after all parts are added
   */
  async completeUpload(uploadId: string): Promise<UploadResponse> {
    return this.requestWithRetry<UploadResponse>('/v1/uploads/complete', 'POST', {
      upload_id: uploadId,
    });
  }

  /**
   * Create a fine-tuning task
   * @param uploadId - The completed upload ID
   * @param suffix - Model name suffix (max 32 chars, lowercase + numbers + hyphens)
   */
  async createFineTuning(uploadId: string, suffix: string): Promise<FineTuningResponse> {
    // Validate suffix
    if (suffix.length > 32) {
      throw new MurekaError('Suffix must be 32 characters or less', 400);
    }
    if (!/^[a-z0-9-]+$/.test(suffix)) {
      throw new MurekaError('Suffix must contain only lowercase letters, numbers, and hyphens', 400);
    }

    const body: CreateFineTuningRequest = {
      upload_id: uploadId,
      suffix,
    };
    return this.requestWithRetry<FineTuningResponse>('/v1/finetuning/create', 'POST', body);
  }

  /**
   * Query fine-tuning task status
   */
  async queryFineTuning(taskId: string): Promise<FineTuningResponse> {
    return this.requestWithRetry<FineTuningResponse>(`/v1/finetuning/query/${taskId}`, 'GET');
  }

  /**
   * Wait for fine-tuning to complete (can take hours)
   */
  async waitForFineTuning(
    taskId: string,
    onProgress?: (status: FineTuningResponse) => void,
    pollIntervalMs = 60000 // Check every minute
  ): Promise<FineTuningResponse> {
    while (true) {
      const response = await this.queryFineTuning(taskId);

      if (onProgress) {
        onProgress(response);
      }

      if (response.status === 'succeeded') {
        return response;
      }

      if (response.status === 'failed' || response.status === 'timeouted' || response.status === 'cancelled') {
        throw new MurekaError(
          `Fine-tuning ${response.status}: ${response.failed_reason || 'Unknown error'}`,
          500
        );
      }

      await this.sleep(pollIntervalMs);
    }
  }

  // ============================================
  // Reference-Based Generation API Methods
  // ============================================

  /**
   * Upload a file for reference-based generation
   * @param filePath - Path to audio file (MP3 or M4A, must be exactly 30 seconds)
   * @param purpose - Upload purpose: 'reference' for songs, 'instrumental' for BGM
   */
  async uploadFile(filePath: string, purpose: FileUploadPurpose): Promise<UploadFileResponse> {
    await this.waitForRateLimit();
    this.activeRequests++;
    this.lastRequestTime = Date.now();

    try {
      const fileBuffer = fs.readFileSync(filePath);
      const fileName = path.basename(filePath);

      // Determine content type
      const ext = path.extname(filePath).toLowerCase();
      const contentType = ext === '.m4a' ? 'audio/mp4' : 'audio/mpeg';

      // Create multipart form data
      const boundary = '----FormBoundary' + Math.random().toString(36).substring(2);

      const header = [
        `--${boundary}`,
        `Content-Disposition: form-data; name="purpose"`,
        '',
        purpose,
        `--${boundary}`,
        `Content-Disposition: form-data; name="file"; filename="${fileName}"`,
        `Content-Type: ${contentType}`,
        '',
        '',
      ].join('\r\n');

      const footer = `\r\n--${boundary}--\r\n`;

      const headerBuffer = Buffer.from(header, 'utf-8');
      const footerBuffer = Buffer.from(footer, 'utf-8');
      const bodyBuffer = Buffer.concat([headerBuffer, fileBuffer, footerBuffer]);

      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.timeout);

      const response = await fetch(`${this.baseUrl}/v1/files/upload`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${this.apiKey}`,
          'Content-Type': `multipart/form-data; boundary=${boundary}`,
        },
        body: bodyBuffer,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorText = await response.text();
        throw new MurekaError(`Upload failed: ${errorText}`, response.status);
      }

      return (await response.json()) as UploadFileResponse;
    } finally {
      this.activeRequests--;
    }
  }

  /**
   * Generate song with reference track (for vocal tracks)
   * @param request - Generation request with reference_id and lyrics
   */
  async generateWithReference(request: GenerateWithReferenceRequest): Promise<GenerationResponse> {
    const body: Record<string, unknown> = {
      reference_id: request.reference_id,
      lyrics: request.lyrics,
      model: request.model || 'auto',
      n: request.n || 2,
    };
    if (request.prompt) {
      body.prompt = request.prompt;
    }
    return this.requestWithRetry<GenerationResponse>('/v1/song/generate', 'POST', body);
  }

  /**
   * Generate instrumental with reference track (for BGM)
   * @param request - Generation request with instrumental_id
   */
  async generateWithInstrumental(request: GenerateWithInstrumentalRequest): Promise<GenerationResponse> {
    const body: Record<string, unknown> = {
      instrumental_id: request.instrumental_id,
      model: request.model || 'auto',
      n: request.n || 2,
    };
    if (request.prompt) {
      body.prompt = request.prompt;
    }
    return this.requestWithRetry<GenerationResponse>('/v1/instrumental/generate', 'POST', body);
  }

  /**
   * Generate with reference and wait for completion
   */
  async generateWithReferenceAndWait(request: GenerateWithReferenceRequest): Promise<GenerationResponse> {
    const response = await this.generateWithReference(request);
    return this.waitForCompletion(response.id, 'song');
  }

  /**
   * Generate with instrumental reference and wait for completion
   */
  async generateWithInstrumentalAndWait(request: GenerateWithInstrumentalRequest): Promise<GenerationResponse> {
    const response = await this.generateWithInstrumental(request);
    return this.waitForCompletion(response.id, 'instrumental');
  }
}

/**
 * Create a client from environment variables
 */
export function createClientFromEnv(): MurekaClient {
  const apiKey = process.env.MUREKA_API_KEY;
  if (!apiKey) {
    throw new Error('MUREKA_API_KEY environment variable is required');
  }

  return new MurekaClient({
    apiKey,
    baseUrl: process.env.MUREKA_API_URL,
    timeout: process.env.GENERATION_TIMEOUT_SECONDS
      ? parseInt(process.env.GENERATION_TIMEOUT_SECONDS) * 1000
      : undefined,
    maxParallel: process.env.MAX_PARALLEL_JOBS
      ? parseInt(process.env.MAX_PARALLEL_JOBS)
      : undefined,
  });
}
