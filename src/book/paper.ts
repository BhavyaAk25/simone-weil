import * as THREE from 'three';
import type { Chapter } from '../types';

/**
 * The raised writing panel, typeset as a book page (verso: the gutter is on the right).
 * Layout units are a 1536 x 1746 page; the canvas is drawn at 4/3 that size so the
 * loupe and 2x screens stay crisp. `userData.textLayout` reports the measured fit.
 */
const PAGE_W = 1536;
const PAGE_H = 1746;
const SCALE = 4 / 3;
const OUTER = 138;            // left margin (outer edge of a verso)
const GUTTER = 104;           // right margin (toward the spine)
const MEASURE = PAGE_W - OUTER - GUTTER;
const LIMIT = 1590;           // last baseline allowed above the foot margin and folio

const INK = '#211810';
const SOFT = '#6a5844';
const SERIF = '"Cormorant Garamond", Georgia, serif';

type Word = { text: string; font: string; tracking: number; width: number };
type Line = { words: Word[]; width: number };

function measureWord(ctx: CanvasRenderingContext2D, text: string, font: string, tracking: number) {
  ctx.font = font;
  return ctx.measureText(text).width + tracking * Math.max(0, text.length - 1);
}

function drawTracked(ctx: CanvasRenderingContext2D, text: string, x: number, y: number, tracking: number) {
  if (!tracking) { ctx.fillText(text, x, y); return; }
  for (const ch of text) { ctx.fillText(ch, x, y); x += ctx.measureText(ch).width + tracking; }
}

/** Break words into lines no wider than `width`. */
function breakLines(ctx: CanvasRenderingContext2D, words: Word[], width: number, space: number) {
  const lines: Line[] = [];
  let current: Word[] = [];
  let used = 0;
  for (const word of words) {
    const next = current.length ? used + space + word.width : word.width;
    if (next > width && current.length) { lines.push({ words: current, width: used }); current = [word]; used = word.width; }
    else { current.push(word); used = next; }
  }
  if (current.length) lines.push({ words: current, width: used });
  return lines;
}

/** Justified setting: spread the word spaces, except on the last line or when too loose. */
function drawLine(ctx: CanvasRenderingContext2D, line: Line, x: number, y: number, width: number, space: number, justify: boolean) {
  const gaps = line.words.length - 1;
  const natural = line.width;
  let gap = space;
  if (justify && gaps > 0) {
    const stretched = space + (width - natural) / gaps;
    if (stretched < space * 2.3) gap = stretched;
  }
  for (const word of line.words) {
    ctx.font = word.font;
    drawTracked(ctx, word.text, x, y, word.tracking);
    x += word.width + gap;
  }
}

function bodyWords(ctx: CanvasRenderingContext2D, text: string, size: number) {
  const roman = `500 ${size}px ${SERIF}`;
  const caps = `500 ${Math.round(size * 0.74)}px ${SERIF}`;
  // The opening words are set in letterspaced small capitals, as a chapter opening.
  return text.split(/\s+/).map((raw, index): Word => {
    if (index < 3) {
      const text = raw.toUpperCase();
      const tracking = size * 0.07;
      return { text, font: caps, tracking, width: measureWord(ctx, text, caps, tracking) };
    }
    return { text: raw, font: roman, tracking: 0, width: measureWord(ctx, raw, roman, 0) };
  });
}

function quoteWords(ctx: CanvasRenderingContext2D, text: string, size: number) {
  const font = `italic 500 ${size}px ${SERIF}`;
  return text.split(/\s+/).map((raw): Word => ({ text: raw, font, tracking: 0, width: measureWord(ctx, raw, font, 0) }));
}

export function makePaperText(chapter: Chapter, renderer: THREE.WebGLRenderer) {
  const canvas = document.createElement('canvas');
  canvas.width = Math.round(PAGE_W * SCALE);
  canvas.height = Math.round(PAGE_H * SCALE);
  const ctx = canvas.getContext('2d')!;
  ctx.scale(SCALE, SCALE);
  ctx.textBaseline = 'alphabetic';
  const left = OUTER;
  const right = PAGE_W - GUTTER;

  // Running head: chapter on the outer side, the place toward the gutter.
  ctx.fillStyle = SOFT;
  ctx.font = `600 38px ${SERIF}`;
  drawTracked(ctx, `CHAPTER ${chapter.id}`, left, 152, 38 * 0.18);
  const place = chapter.place.toUpperCase();
  const placeWidth = measureWord(ctx, place, `600 38px ${SERIF}`, 38 * 0.18);
  drawTracked(ctx, place, right - placeWidth, 152, 38 * 0.18);

  // Title and dates.
  let y = 330;
  ctx.fillStyle = INK;
  const titleSize = chapter.title.length > 22 ? 96 : 106;
  ctx.font = `500 ${titleSize}px ${SERIF}`;
  const titleLines = breakLines(ctx, chapter.title.split(/\s+/).map(text => ({ text, font: ctx.font, tracking: 0, width: ctx.measureText(text).width })), MEASURE, titleSize * 0.26);
  for (const line of titleLines) { drawLine(ctx, line, left - 3, y, MEASURE, titleSize * 0.26, false); y += titleSize * 1.02; }
  y += -titleSize * 1.02 + 72;
  ctx.fillStyle = SOFT;
  ctx.font = `italic 500 48px ${SERIF}`;
  ctx.fillText(chapter.period, left, y);
  y += 44;
  ctx.fillStyle = '#b29a77';
  ctx.fillRect(left, y, 64, 2.5);
  y += 100;
  // Attribution: author and work in small capitals; a long title takes a second line.
  const citeFont = `600 31px ${SERIF}`;
  const citeTracking = 31 * 0.13;
  const quoteGap = 128;
  const fullCite = `SIMONE WEIL · ${chapter.quote.work.toUpperCase()}`;
  const citeParts = measureWord(ctx, fullCite, citeFont, citeTracking) <= MEASURE - 152 ? [fullCite] : ['SIMONE WEIL', chapter.quote.work.toUpperCase()];

  // Body and quotation: choose the largest size at which everything fits the page.
  const bodyTop = y;
  let bodySize = 76;
  let lines: Line[] = [];
  let quoteLines: Line[] = [];
  let quoteSize = 64;
  const quoteIndent = 76;
  const quoteMeasure = MEASURE - quoteIndent * 2;
  const quote = `“${chapter.quote.text}”`;
  let end = 0;
  for (; bodySize >= 62; bodySize -= 2) {
    quoteSize = Math.round(bodySize * 0.9);
    lines = breakLines(ctx, bodyWords(ctx, chapter.paragraph, bodySize), MEASURE, bodySize * 0.25);
    quoteLines = breakLines(ctx, quoteWords(ctx, quote, quoteSize), quoteMeasure, quoteSize * 0.25);
    const leading = bodySize * 1.3;
    end = bodyTop + (lines.length - 1) * leading + quoteGap + (quoteLines.length - 1) * quoteSize * 1.28 + 58 + (citeParts.length - 1) * 40;
    if (end <= LIMIT) break;
  }
  const leading = bodySize * 1.3;
  ctx.fillStyle = INK;
  lines.forEach((line, index) => drawLine(ctx, line, left, y + index * leading, MEASURE, bodySize * 0.25, index < lines.length - 1));
  y += (lines.length - 1) * leading + quoteGap;

  // The quotation is set apart: indented, italic, with a hanging opening mark.
  ctx.fillStyle = '#33261a';
  const hang = measureWord(ctx, '“', `italic 500 ${quoteSize}px ${SERIF}`, 0);
  quoteLines.forEach((line, index) => {
    drawLine(ctx, line, left + quoteIndent - (index === 0 ? hang : 0), y, quoteMeasure, quoteSize * 0.25, false);
    y += quoteSize * 1.28;
  });
  y += 52 - quoteSize * 1.28 + 6;
  ctx.fillStyle = SOFT;
  ctx.font = citeFont;
  citeParts.forEach((part, index) => drawTracked(ctx, part, left + quoteIndent, y + index * 40, citeTracking));
  y += (citeParts.length - 1) * 40;

  // Folio, centred in the foot margin, in the text face.
  ctx.fillStyle = SOFT;
  ctx.font = `500 40px ${SERIF}`;
  ctx.textAlign = 'center';
  ctx.fillText(String(chapter.id * 2 - 1), (left + right) / 2, 1686);
  ctx.textAlign = 'left';

  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
  // The ink is lit with the page, so it dims with the room and the lamp like the paper beneath.
  const material = new THREE.MeshStandardMaterial({
    map: texture, transparent: true, depthWrite: false, roughness: 0.92, metalness: 0,
    polygonOffset: true, polygonOffsetFactor: -2,
  });
  const geometry = new THREE.PlaneGeometry(2.05, 2.33);
  const mesh = new THREE.Mesh(geometry, material);
  mesh.name = 'AccessiblePageWriting';
  mesh.userData.textLayout = { bodySize, quoteSize, bodyLines: lines.length, quoteLines: quoteLines.length, attributionBaseline: y, fits: y <= LIMIT };
  mesh.rotation.x = -Math.PI / 2;
  mesh.position.set(0, 0.010, -1.165);
  mesh.renderOrder = 3;
  return mesh;
}
