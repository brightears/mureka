import { randomUUID } from 'crypto';
import { GenreTemplate, GeneratedPrompt, PromptBatch, TempoRange } from './types.js';
import { generateUniqueTitle } from './title-generator.js';

/**
 * Generates Mureka-optimized prompts from genre templates
 */
export class PromptGenerator {
  /**
   * Generate a single random prompt from a template
   */
  generatePrompt(template: GenreTemplate, type?: 'instrumental' | 'vocal'): GeneratedPrompt {
    const effectiveType = type || (template.type === 'both' ? 'instrumental' : template.type);

    // Random selection helpers
    const pick = <T>(arr: T[]): T => arr[Math.floor(Math.random() * arr.length)];
    const pickMultiple = <T>(arr: T[], min: number, max: number): T[] => {
      const count = min + Math.floor(Math.random() * (max - min + 1));
      const shuffled = [...arr].sort(() => Math.random() - 0.5);
      return shuffled.slice(0, Math.min(count, arr.length));
    };

    // Select components
    const genre = pick(template.genres);
    const subGenre = pick(template.subGenres);
    const mood = pick(template.moods);
    const tempo = pick(template.tempos);
    const instruments = pickMultiple(template.instruments, 2, 4);
    const useCase = pick(template.useCases);
    const atmosphere = template.atmospheres.length > 0 ? pick(template.atmospheres) : undefined;
    const negative = template.negativePrompts;

    // Vocal-specific components
    const vocalStyle = template.vocalStyles && template.vocalStyles.length > 0
      ? pick(template.vocalStyles)
      : undefined;
    const lyricTheme = template.lyricThemes && template.lyricThemes.length > 0
      ? pick(template.lyricThemes)
      : undefined;

    // Build tempo string
    const tempoStr = this.formatTempo(tempo);

    // Build prompt string
    const promptParts: string[] = [
      `${genre}, ${subGenre}`,
      mood,
      tempoStr,
      instruments.join(', '),
      useCase,
    ];

    // Add vocal style for vocal tracks
    if (effectiveType === 'vocal' && vocalStyle) {
      promptParts.push(vocalStyle);
    }

    if (atmosphere) {
      promptParts.push(atmosphere);
    }

    if (negative.length > 0) {
      promptParts.push(negative.join(', '));
    }

    const prompt = promptParts.join(', ');

    // Generate title
    const title = this.generateTitle(template, mood, subGenre);

    return {
      id: randomUUID(),
      genreTemplateId: template.id,
      prompt,
      title,
      type: effectiveType,
      components: {
        genre,
        subGenre,
        mood,
        tempo: tempoStr,
        instruments,
        useCase,
        atmosphere,
        negative,
        vocalStyle,
        lyricTheme,
        language: template.language,
      },
      createdAt: new Date(),
    };
  }

  /**
   * Generate a batch of unique prompts
   */
  generateBatch(template: GenreTemplate, count: number, type?: 'instrumental' | 'vocal'): PromptBatch {
    const prompts: GeneratedPrompt[] = [];
    const usedPromptHashes = new Set<string>();

    // Note: Title uniqueness is now global (persisted across all batches)
    // Each title is used only ONCE ever, never repeated

    // Generate unique prompts
    let attempts = 0;
    const maxAttempts = count * 10; // Prevent infinite loops

    while (prompts.length < count && attempts < maxAttempts) {
      const prompt = this.generatePrompt(template, type);
      const hash = this.hashPrompt(prompt);

      if (!usedPromptHashes.has(hash)) {
        usedPromptHashes.add(hash);
        prompts.push(prompt);
      }

      attempts++;
    }

    if (prompts.length < count) {
      console.warn(
        `Could only generate ${prompts.length}/${count} unique prompts. ` +
          `Consider adding more variety to the template.`
      );
    }

    return {
      id: randomUUID(),
      genreTemplateId: template.id,
      count: prompts.length,
      prompts,
      createdAt: new Date(),
    };
  }

  /**
   * Generate systematic prompts covering all combinations
   */
  generateSystematic(
    template: GenreTemplate,
    maxCount: number,
    type?: 'instrumental' | 'vocal'
  ): PromptBatch {
    const effectiveType = type || (template.type === 'both' ? 'instrumental' : template.type);
    const prompts: GeneratedPrompt[] = [];

    // Generate combinations systematically
    for (const genre of template.genres) {
      for (const subGenre of template.subGenres) {
        for (const mood of template.moods) {
          for (const tempo of template.tempos) {
            if (prompts.length >= maxCount) break;

            // Pick random instruments for variety
            const instruments = this.pickRandom(template.instruments, 2, 3);
            const useCase = this.pickRandom(template.useCases, 1, 1)[0];
            const atmosphere =
              template.atmospheres.length > 0
                ? this.pickRandom(template.atmospheres, 1, 1)[0]
                : undefined;

            const tempoStr = this.formatTempo(tempo);

            const promptParts: string[] = [
              `${genre}, ${subGenre}`,
              mood,
              tempoStr,
              instruments.join(', '),
              useCase,
            ];

            if (atmosphere) promptParts.push(atmosphere);
            if (template.negativePrompts.length > 0) {
              promptParts.push(template.negativePrompts.join(', '));
            }

            const prompt: GeneratedPrompt = {
              id: randomUUID(),
              genreTemplateId: template.id,
              prompt: promptParts.join(', '),
              title: this.generateTitle(template, mood, subGenre),
              type: effectiveType,
              components: {
                genre,
                subGenre,
                mood,
                tempo: tempoStr,
                instruments,
                useCase,
                atmosphere,
                negative: template.negativePrompts,
              },
              createdAt: new Date(),
            };

            prompts.push(prompt);
          }
        }
      }
    }

    return {
      id: randomUUID(),
      genreTemplateId: template.id,
      count: prompts.length,
      prompts,
      createdAt: new Date(),
    };
  }

  private formatTempo(tempo: TempoRange): string {
    const bpm = tempo.minBpm + Math.floor(Math.random() * (tempo.maxBpm - tempo.minBpm + 1));
    return `${tempo.label} tempo ${bpm} BPM`;
  }

  private generateTitle(template: GenreTemplate, mood: string, subGenre: string): string {
    // Use the new AI-style unique title generator
    return generateUniqueTitle(template.id, mood, subGenre);
  }

  private pickRandom<T>(arr: T[], min: number, max: number): T[] {
    const count = min + Math.floor(Math.random() * (max - min + 1));
    const shuffled = [...arr].sort(() => Math.random() - 0.5);
    return shuffled.slice(0, Math.min(count, arr.length));
  }

  private hashPrompt(prompt: GeneratedPrompt): string {
    return `${prompt.components.genre}|${prompt.components.subGenre}|${prompt.components.mood}|${prompt.components.tempo}|${prompt.components.instruments.sort().join(',')}`;
  }
}

/**
 * Format a prompt for display
 */
export function formatPromptForDisplay(prompt: GeneratedPrompt): string {
  return `
Title: ${prompt.title}
Type: ${prompt.type}
Prompt: ${prompt.prompt}
Components:
  Genre: ${prompt.components.genre} / ${prompt.components.subGenre}
  Mood: ${prompt.components.mood}
  Tempo: ${prompt.components.tempo}
  Instruments: ${prompt.components.instruments.join(', ')}
  Use Case: ${prompt.components.useCase}
  ${prompt.components.atmosphere ? `Atmosphere: ${prompt.components.atmosphere}` : ''}
  Negative: ${prompt.components.negative.join(', ')}
`.trim();
}
