import { readFileSync, readdirSync, existsSync, writeFileSync, mkdirSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { GenreTemplate, PromptBatch, GeneratedPrompt } from './types.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const TEMPLATES_DIR = join(__dirname, 'templates');
const PROMPTS_OUTPUT_DIR = join(__dirname, '../../prompts');

/**
 * Load a genre template by ID
 */
export function loadTemplate(templateId: string): GenreTemplate {
  const filePath = join(TEMPLATES_DIR, `${templateId}.json`);

  if (!existsSync(filePath)) {
    throw new Error(`Template not found: ${templateId}`);
  }

  const content = readFileSync(filePath, 'utf-8');
  return JSON.parse(content) as GenreTemplate;
}

/**
 * List all available templates
 */
export function listTemplates(): string[] {
  if (!existsSync(TEMPLATES_DIR)) {
    return [];
  }

  return readdirSync(TEMPLATES_DIR)
    .filter((file) => file.endsWith('.json'))
    .map((file) => file.replace('.json', ''));
}

/**
 * Load all templates
 */
export function loadAllTemplates(): GenreTemplate[] {
  return listTemplates().map(loadTemplate);
}

/**
 * Save a prompt batch to file
 */
export function savePromptBatch(batch: PromptBatch, genre: string): string {
  if (!existsSync(PROMPTS_OUTPUT_DIR)) {
    mkdirSync(PROMPTS_OUTPUT_DIR, { recursive: true });
  }

  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const filename = `${genre}_${timestamp}.json`;
  const filePath = join(PROMPTS_OUTPUT_DIR, filename);

  writeFileSync(filePath, JSON.stringify(batch, null, 2));

  return filePath;
}

/**
 * Load a saved prompt batch
 */
export function loadPromptBatch(filename: string): PromptBatch {
  const filePath = join(PROMPTS_OUTPUT_DIR, filename);

  if (!existsSync(filePath)) {
    throw new Error(`Prompt batch not found: ${filename}`);
  }

  const content = readFileSync(filePath, 'utf-8');
  return JSON.parse(content) as PromptBatch;
}

/**
 * List saved prompt batches
 */
export function listPromptBatches(): string[] {
  if (!existsSync(PROMPTS_OUTPUT_DIR)) {
    return [];
  }

  return readdirSync(PROMPTS_OUTPUT_DIR).filter((file) => file.endsWith('.json'));
}

/**
 * Export prompts to a simple text file (one per line)
 */
export function exportPromptsAsText(prompts: GeneratedPrompt[], outputPath: string): void {
  const lines = prompts.map((p) => `${p.title}\t${p.prompt}`);
  writeFileSync(outputPath, lines.join('\n'));
}
