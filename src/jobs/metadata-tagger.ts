/**
 * Metadata tagger for MP3 and FLAC files
 * Adds ID3 tags to MP3 and Vorbis comments to FLAC
 */

import NodeID3 from 'node-id3';
import { exec } from 'child_process';
import { promisify } from 'util';
import { AudioFormat } from '../api/types.js';

const execAsync = promisify(exec);

export interface TrackMetadataOptions {
  title: string;
  artist?: string;
  album?: string;
  genre?: string;
  date?: string; // ISO date format: YYYY-MM-DD
  albumArtist?: string;
}

export interface MetadataConfig {
  artist: string;
  albumArtist: string;
  defaultGenre?: string;
}

const DEFAULT_CONFIG: MetadataConfig = {
  artist: 'BMAsia',
  albumArtist: 'BMAsia',
};

/**
 * Add metadata tags to an audio file
 */
export async function tagAudioFile(
  filePath: string,
  format: AudioFormat,
  metadata: TrackMetadataOptions,
  config: MetadataConfig = DEFAULT_CONFIG
): Promise<void> {
  const fullMetadata: TrackMetadataOptions = {
    ...metadata,
    artist: metadata.artist || config.artist,
    albumArtist: metadata.albumArtist || config.albumArtist,
    date: metadata.date || new Date().toISOString().split('T')[0], // YYYY-MM-DD
    genre: metadata.genre || config.defaultGenre,
  };

  switch (format) {
    case 'mp3':
      await tagMp3File(filePath, fullMetadata);
      break;
    case 'flac':
      await tagFlacFile(filePath, fullMetadata);
      break;
    case 'wav':
      // WAV has limited metadata support, skip for now
      break;
  }
}

/**
 * Tag MP3 file with ID3v2 tags
 */
async function tagMp3File(filePath: string, metadata: TrackMetadataOptions): Promise<void> {
  const tags: NodeID3.Tags = {
    title: metadata.title,
    artist: metadata.artist,
    album: metadata.album,
    date: metadata.date, // ID3v2.4 uses TDRC for date
    genre: metadata.genre,
    performerInfo: metadata.albumArtist,
  };

  // Also set year from date for compatibility
  if (metadata.date) {
    tags.year = metadata.date.substring(0, 4);
  }

  const success = NodeID3.write(tags, filePath);
  if (!success) {
    throw new Error(`Failed to write ID3 tags to ${filePath}`);
  }
}

/**
 * Tag FLAC file with Vorbis comments using metaflac
 */
async function tagFlacFile(filePath: string, metadata: TrackMetadataOptions): Promise<void> {
  // Build metaflac command to remove existing tags and add new ones
  const tags: string[] = [];

  if (metadata.title) tags.push(`TITLE=${metadata.title}`);
  if (metadata.artist) tags.push(`ARTIST=${metadata.artist}`);
  if (metadata.album) tags.push(`ALBUM=${metadata.album}`);
  if (metadata.albumArtist) tags.push(`ALBUMARTIST=${metadata.albumArtist}`);
  if (metadata.date) tags.push(`DATE=${metadata.date}`);
  if (metadata.genre) tags.push(`GENRE=${metadata.genre}`);

  // First remove all existing tags, then add new ones
  const removeCmd = `metaflac --remove-all-tags "${filePath}"`;
  const addCmd = tags.map(tag => `--set-tag="${tag}"`).join(' ');
  const fullCmd = `${removeCmd} && metaflac ${addCmd} "${filePath}"`;

  try {
    await execAsync(fullCmd);
  } catch (error) {
    throw new Error(`Failed to write FLAC tags to ${filePath}: ${(error as Error).message}`);
  }
}

/**
 * Generate album name from genre/template (Title Case)
 */
export function generateAlbumName(genre: string, _format?: AudioFormat): string {
  // Convert to Title Case (e.g., "cafe-jazz" -> "Cafe Jazz")
  return genre
    .split(/[-_\s]+/)
    .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ');
}

/**
 * Map template genre to standard music genre tag
 */
export function mapToStandardGenre(templateGenre: string): string {
  const lowerGenre = templateGenre.toLowerCase();

  if (lowerGenre.includes('jazz')) return 'Jazz';
  if (lowerGenre.includes('chinese') || lowerGenre.includes('asian')) return 'World';
  if (lowerGenre.includes('ambient')) return 'Ambient';
  if (lowerGenre.includes('lounge')) return 'Jazz';
  if (lowerGenre.includes('classical')) return 'Classical';
  if (lowerGenre.includes('electronic')) return 'Electronic';
  if (lowerGenre.includes('chill')) return 'Chillout';

  return 'Instrumental';
}

/**
 * Create metadata config with custom settings
 */
export function createMetadataConfig(overrides?: Partial<MetadataConfig>): MetadataConfig {
  return {
    ...DEFAULT_CONFIG,
    ...overrides,
  };
}
