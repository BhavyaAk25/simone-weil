import { describe, expect, it } from 'vitest';
import { parseGlb, sampleBounds } from '../scripts/validate-assets.mjs';

function fixture() {
  const positions = [0.02, 0.24, -1, 2.42, 0.24, -1, 2.42, 0.24, 1];
  const deltas = positions.map((value, index) => index % 3 === 0 ? -2 * value : 0);
  const arrays = [positions, deltas, [0, 1], [0, 1]];
  let byteOffset = 0;
  const bufferViews = arrays.map(values => {
    const result = { buffer: 0, byteOffset, byteLength: values.length * 4 };
    byteOffset += result.byteLength;
    return result;
  });
  const binary = Buffer.alloc(byteOffset);
  arrays.flat().forEach((value, index) => binary.writeFloatLE(value, index * 4));
  const data = {
    asset: { version: '2.0' }, buffers: [{ byteLength: binary.length }], bufferViews,
    accessors: arrays.map((values, index) => ({ bufferView: index, componentType: 5126, count: index < 2 ? values.length / 3 : values.length, type: index < 2 ? 'VEC3' : 'SCALAR' })),
    nodes: [{ name: 'root', translation: [3, 0, 0], children: [1] }, { name: 'TurnPage', mesh: 0 }],
    meshes: [{ weights: [0], primitives: [{ attributes: { POSITION: 0 }, targets: [{ POSITION: 1 }] }] }],
    scenes: [{ nodes: [0] }], scene: 0,
    animations: [{ name: 'turn', channels: [{ sampler: 0, target: { node: 1, path: 'weights' } }], samplers: [{ input: 2, output: 3, interpolation: 'LINEAR' }] }],
  };
  const text = JSON.stringify(data), json = Buffer.from(text.padEnd(Math.ceil(Buffer.byteLength(text) / 4) * 4));
  const glb = Buffer.alloc(12 + 8 + json.length + 8 + binary.length);
  glb.writeUInt32LE(0x46546c67, 0); glb.writeUInt32LE(2, 4); glb.writeUInt32LE(glb.length, 8);
  glb.writeUInt32LE(json.length, 12); glb.writeUInt32LE(0x4e4f534a, 16); json.copy(glb, 20);
  glb.writeUInt32LE(binary.length, 20 + json.length); glb.writeUInt32LE(0x004e4942, 24 + json.length); binary.copy(glb, 28 + json.length);
  return glb;
}

describe('deployable GLB validation', () => {
  it('rejects truncated files and forged declared lengths', () => {
    expect(() => parseGlb(Buffer.alloc(8))).toThrow('Truncated GLB');
    const file = fixture();
    expect(() => parseGlb(file.subarray(0, file.length - 4))).toThrow('declared length');
  });

  it('reads real binary coordinates instead of trusting accessor min/max metadata', () => {
    const glb = parseGlb(fixture());
    glb.json.accessors[0].min = [-999, -999, -999];
    glb.json.accessors[0].max = [999, 999, 999];
    const bounds = sampleBounds(glb, 'turn', 0);
    expect(bounds.min.x).toBeCloseTo(3.02);
    expect(bounds.max.x).toBeCloseTo(5.42);
    expect(bounds.min.y).toBeCloseTo(0.24);
  });

  it('combines hierarchy transforms with interpolated morph weights in both endpoint poses', () => {
    const glb = parseGlb(fixture());
    const end = sampleBounds(glb, 'turn', 1), middle = sampleBounds(glb, 'turn', 0.5);
    expect(end.min.x).toBeCloseTo(0.58);
    expect(end.max.x).toBeCloseTo(2.98);
    expect(middle.min.x).toBeCloseTo(3);
    expect(middle.max.x).toBeCloseTo(3);
  });

  it('rejects out-of-bounds accessor data', () => {
    const glb = parseGlb(fixture());
    glb.json.accessors[0].count = 999;
    expect(() => glb.accessor(0)).toThrow('exceeds buffer view');
  });
});
