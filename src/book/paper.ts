import * as THREE from 'three';
import type { Chapter } from '../types';

function lines(ctx: CanvasRenderingContext2D, text: string, maxWidth: number) {
  const output: string[] = [];
  let line = '';
  for (const word of text.split(/\s+/)) {
    const next = line ? `${line} ${word}` : word;
    if (ctx.measureText(next).width > maxWidth && line) { output.push(line); line = word; }
    else line = next;
  }
  if (line) output.push(line);
  return output;
}

export function makePaperText(chapter: Chapter, renderer: THREE.WebGLRenderer) {
  const canvas = document.createElement('canvas');
  canvas.width = 1536;
  canvas.height = 1746;
  const ctx = canvas.getContext('2d')!;
  const left = 90;
  const width = 1356;
  let y = 100;
  ctx.fillStyle = '#5a4734';
  ctx.font = '500 38px Inter';
  ctx.fillText(`${String(chapter.id).padStart(2, '0')}  /  ${chapter.place.toUpperCase()}`, left, y);
  y += 125;
  ctx.fillStyle = '#281d14';
  ctx.font = '500 110px "Cormorant Garamond"';
  for (const line of lines(ctx, chapter.title, width)) { ctx.fillText(line, left, y); y += 112; }
  y += 4;
  ctx.font = '400 37px Inter';
  ctx.fillStyle = '#65513b';
  ctx.fillText(chapter.period, left + 3, y);
  y += 55;
  ctx.fillStyle = '#a38b68';
  ctx.fillRect(left, y, 110, 2);
  y += 90;

  ctx.fillStyle = '#2d2119';
  let bodySize = 81;
  let paragraphLines: string[] = [];
  let quoteLines: string[] = [];
  // Reserve space for the complete quotation and attribution before drawing.
  // Longer paragraphs use a slightly tighter size instead of overlapping the cite.
  for (; bodySize >= 65; bodySize -= 2) {
    ctx.font = `500 ${bodySize}px "Cormorant Garamond"`;
    paragraphLines = lines(ctx, chapter.paragraph, width);
    ctx.font = 'italic 500 78px "Cormorant Garamond"';
    quoteLines = lines(ctx, `“${chapter.quote.text}”`, width);
    if (y + paragraphLines.length * (bodySize + 10) + 55 + quoteLines.length * 86 + 22 <= 1590) break;
  }
  ctx.font = `500 ${bodySize}px "Cormorant Garamond"`;
  for (const line of paragraphLines) { ctx.fillText(line, left, y); y += bodySize + 10; }
  y += 55;

  ctx.fillStyle = '#39281b';
  ctx.font = 'italic 500 78px "Cormorant Garamond"';
  for (const line of quoteLines) { ctx.fillText(line, left, y); y += 86; }
  y += 22;
  ctx.font = '400 34px Inter';
  ctx.fillStyle = '#8c7658';
  ctx.fillText('SIMONE WEIL', left, y);

  ctx.font = '400 32px Inter';
  ctx.textAlign = 'center';
  ctx.fillStyle = '#8c7658';
  ctx.fillText(String(chapter.id * 2 - 1), 768, 1697);
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
  const material = new THREE.MeshBasicMaterial({ map: texture, transparent: true, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -2 });
  const geometry = new THREE.PlaneGeometry(2.05, 2.33);
  const mesh = new THREE.Mesh(geometry, material);
  mesh.name = 'AccessiblePageWriting';
  mesh.userData.textLayout = { bodySize, attributionBaseline: y, fits: y <= 1590 };
  mesh.rotation.x = -Math.PI / 2;
  mesh.position.set(0, 0.010, -1.165);
  mesh.renderOrder = 3;
  return mesh;
}
