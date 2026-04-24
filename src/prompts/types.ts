// Prompt Template Types

export interface GenreTemplate {
  id: string;
  name: string;
  description: string;
  type: 'instrumental' | 'vocal' | 'both';

  // Core elements
  genres: string[];
  subGenres: string[];
  moods: string[];
  tempos: TempoRange[];
  instruments: string[];

  // Context
  useCases: string[];
  atmospheres: string[];

  // Constraints
  negativePrompts: string[];

  // Optional: for vocal tracks
  vocalStyles?: string[];
  lyricThemes?: string[];
  language?: string; // e.g., 'Spanish', 'English' - for lyrics generation
}

export interface TempoRange {
  label: string;
  minBpm: number;
  maxBpm: number;
}

export interface GeneratedPrompt {
  id: string;
  genreTemplateId: string;
  prompt: string;
  title: string;
  type: 'instrumental' | 'vocal';
  components: {
    genre: string;
    subGenre: string;
    mood: string;
    tempo: string;
    instruments: string[];
    useCase: string;
    atmosphere?: string;
    negative: string[];
    // Vocal-specific components
    vocalStyle?: string;
    lyricTheme?: string;
    language?: string; // e.g., 'Spanish', 'English' - for lyrics generation
  };
  createdAt: Date;
}

export interface PromptBatch {
  id: string;
  genreTemplateId: string;
  count: number;
  prompts: GeneratedPrompt[];
  createdAt: Date;
}
