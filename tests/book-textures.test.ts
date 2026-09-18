import { afterEach, describe, expect, it } from 'vitest';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { parseGlb, validateImages } from '../scripts/validate-assets.mjs';

const temporary: string[] = [];
afterEach(() => temporary.splice(0).forEach(directory => fs.rmSync(directory, { recursive: true, force: true })));
const png = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a/J8AAAAASUVORK5CYII=', 'base64');
const sha = createHash('sha256').update(png).digest('hex');
function workspace() {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'weil-textures-'));
  temporary.push(directory);
  fs.mkdirSync(path.join(directory, 'public/models'), { recursive: true });
  fs.mkdirSync(path.join(directory, 'public/textures/shared'), { recursive: true });
  return directory;
}
function fixture() {
  // Put the shared image before a sparse accessor and extension view, exercising
  // remapping of references after the image's bufferView has been removed.
  const imageLength = Math.ceil(png.length / 4) * 4;
  const binary = Buffer.alloc(imageLength + 8);
  png.copy(binary); binary.writeFloatLE(0.75, imageLength); binary.writeUInt32LE(7, imageLength + 4);
  const document = {
    asset: { version: '2.0' }, buffers: [{ byteLength: binary.length }],
    bufferViews: [{ buffer: 0, byteOffset: 0, byteLength: png.length },
      { buffer: 0, byteOffset: imageLength, byteLength: 4 }, { buffer: 0, byteOffset: imageLength + 4, byteLength: 4 }],
    images: [{ mimeType: 'image/png', bufferView: 0 }],
    accessors: [{ componentType: 5126, count: 1, type: 'SCALAR', sparse: {
      count: 1, indices: { bufferView: 2, componentType: 5125 }, values: { bufferView: 1 },
    } }],
    extensions: { TEST_payload: { bufferView: 2 } },
  };
  const text = Buffer.from(JSON.stringify(document));
  const json = Buffer.alloc(Math.ceil(text.length / 4) * 4, 32); text.copy(json);
  const header = Buffer.alloc(20); header.writeUInt32LE(0x46546c67, 0); header.writeUInt32LE(2, 4);
  header.writeUInt32LE(28 + json.length + binary.length, 8); header.writeUInt32LE(json.length, 12); header.writeUInt32LE(0x4e4f534a, 16);
  const chunk = Buffer.alloc(8); chunk.writeUInt32LE(binary.length); chunk.writeUInt32LE(0x004e4942, 4);
  return Buffer.concat([header, json, chunk, binary]);
}
const optimize = (directory: string) => JSON.parse(execFileSync('python3', ['scripts/blender/share_textures.py', '--root', directory], { encoding: 'utf8' }));

describe('shared model images', () => {
  it('preserves payloads and sparse/extension references, including mixed fresh exports', () => {
    const directory = workspace(), original = fixture();
    const files = ['one.glb', 'two.glb'].map(name => path.join(directory, 'public/models', name));
    files.forEach(file => fs.writeFileSync(file, original));
    const report = optimize(directory);
    expect(report.files.every((file: { payloadBeforeSha256: string; payloadAfterSha256: string }) => file.payloadBeforeSha256 === file.payloadAfterSha256)).toBe(true);
    expect(fs.readFileSync(path.join(directory, 'public/textures/shared', `${sha}.png`))).toEqual(png);
    const model = parseGlb(fs.readFileSync(files[0]));
    expect(model.json.images[0]).toEqual({ mimeType: 'image/png', uri: `../textures/shared/${sha}.png` });
    expect(model.json.accessors[0].sparse.values.bufferView).toBe(0);
    expect(model.json.accessors[0].sparse.indices.bufferView).toBe(1);
    expect(model.json.extensions.TEST_payload.bufferView).toBe(1);
    validateImages(model, { directory });
    const once = files.map(file => fs.readFileSync(file));
    expect(optimize(directory).glbBytesSaved).toBe(0);
    files.forEach((file, index) => expect(fs.readFileSync(file)).toEqual(once[index]));
    fs.writeFileSync(files[0], original);
    optimize(directory);
    files.forEach((file, index) => expect(fs.readFileSync(file)).toEqual(once[index]));
  });

  it('rejects remote, traversal and mismatched MIME paths', () => {
    for (const uri of ['https://example.com/image.png', '../../secrets.png', `../textures/shared/${sha}.jpg`, `../textures/shared/%2e%2e/${sha}.png`]) {
      expect(() => validateImages({ json: { images: [{ mimeType: 'image/png', uri }] } })).toThrow('canonical shared texture URI');
    }
  });

  it('rejects missing, tampered or linked image files', () => {
    const directory = workspace(), target = path.join(directory, 'public/textures/shared', `${sha}.png`);
    const model = { json: { images: [{ mimeType: 'image/png', uri: `../textures/shared/${sha}.png` }] } };
    expect(() => validateImages(model, { directory })).toThrow();
    fs.writeFileSync(target, 'tampered');
    expect(() => validateImages(model, { directory })).toThrow('hash mismatch');
    fs.unlinkSync(target);
    const outside = path.join(directory, 'outside.png'); fs.writeFileSync(outside, png); fs.symlinkSync(outside, target);
    expect(() => validateImages(model, { directory })).toThrow('inside its bundle');
  });

  it('rejects forged image MIME even when the filename hash matches', () => {
    const directory = workspace(), raw = Buffer.from('not an image');
    const hash = createHash('sha256').update(raw).digest('hex');
    fs.writeFileSync(path.join(directory, 'public/textures/shared', `${hash}.png`), raw);
    expect(() => validateImages({ json: { images: [{ mimeType: 'image/png', uri: `../textures/shared/${hash}.png` }] } }, { directory })).toThrow('MIME type');
  });
});
