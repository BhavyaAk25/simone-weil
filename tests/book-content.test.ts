import { describe, expect, it } from 'vitest';
import { chapters } from '../src/content/chapters';

describe('complete story manifest', () => {
  it('provides exactly twelve uniquely addressable, ordered spreads', () => {
    expect(chapters).toHaveLength(12);
    expect(chapters.map(chapter => chapter.id)).toEqual(Array.from({ length: 12 }, (_, index) => index + 1));
    for (const key of ['slug', 'scene', 'poster'] as const) expect(new Set(chapters.map(chapter => chapter[key])).size).toBe(12);
  });

  it('keeps every original paragraph within the agreed 45–65 words', () => {
    for (const chapter of chapters) {
      const count = chapter.paragraph.trim().split(/\s+/).length;
      expect(count, chapter.title).toBeGreaterThanOrEqual(45);
      expect(count, chapter.title).toBeLessThanOrEqual(65);
    }
  });

  it('keeps source provenance attached to every short quotation', () => {
    for (const chapter of chapters) {
      expect(chapter.quote.text.trim().split(/\s+/).length, chapter.title).toBeLessThanOrEqual(15);
      for (const value of [chapter.quote.text, chapter.quote.work, chapter.quote.locator, chapter.quote.translation]) expect(value.trim().length, chapter.title).toBeGreaterThan(0);
      expect(new URL(chapter.quote.url).protocol).toBe('https:');
      expect(chapter.quote.translation).toMatch(/translation/i);
      expect(chapter.quote.locator).toMatch(/\d{4}/);
    }
  });

  it('uses local asset paths that remain valid under the GitHub Pages subpath', () => {
    for (const chapter of chapters) {
      expect(chapter.scene).toMatch(/^models\/chapter-\d{2}\.glb$/);
      expect(chapter.poster).toMatch(/^posters\/chapter-\d{2}\.webp$/);
      expect(chapter.slug).toMatch(/^[a-z]+(?:-[a-z]+)*$/);
    }
  });
});
