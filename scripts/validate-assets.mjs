import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { Box3, Matrix4, Quaternion, Vector3 } from 'three';

const componentReaders = {
  5120: ['getInt8', 1], 5121: ['getUint8', 1], 5122: ['getInt16', 2],
  5123: ['getUint16', 2], 5125: ['getUint32', 4], 5126: ['getFloat32', 4],
};
const widths = { SCALAR: 1, VEC2: 2, VEC3: 3, VEC4: 4, MAT2: 4, MAT3: 9, MAT4: 16 };
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const assert = (condition, message) => { if (!condition) throw new Error(message); };

/** Decode the deployable binary, without trusting its sidecar manifest. */
export function parseGlb(bytes) {
  assert(bytes.length >= 20, 'Truncated GLB header');
  assert(bytes.readUInt32LE(0) === 0x46546c67, 'Invalid GLB magic');
  assert(bytes.readUInt32LE(4) === 2, 'GLB must use glTF 2.0');
  assert(bytes.readUInt32LE(8) === bytes.length, 'GLB declared length differs from actual bytes');
  let json, binary;
  for (let cursor = 12; cursor < bytes.length;) {
    assert(cursor + 8 <= bytes.length, 'Truncated GLB chunk header');
    const length = bytes.readUInt32LE(cursor), type = bytes.readUInt32LE(cursor + 4);
    assert(length % 4 === 0 && cursor + 8 + length <= bytes.length, 'Invalid GLB chunk bounds');
    const chunk = bytes.subarray(cursor + 8, cursor + 8 + length);
    if (type === 0x4e4f534a) { assert(!json, 'Duplicate GLB JSON chunk'); json = JSON.parse(chunk.toString('utf8').trim()); }
    if (type === 0x004e4942) { assert(!binary, 'Duplicate GLB binary chunk'); binary = chunk; }
    cursor += 8 + length;
  }
  assert(json?.asset?.version === '2.0' && binary, 'Missing glTF 2.0 JSON or binary');
  assert(json.buffers?.length === 1 && !json.buffers[0].uri, 'GLB must embed one binary buffer');
  assert(json.buffers[0].byteLength <= binary.length, 'Binary buffer is too short');
  const accessors = new Map();
  function readValues(viewIndex, offset, count, width, componentType, stride) {
    const view = json.bufferViews?.[viewIndex], reader = componentReaders[componentType];
    assert(view && reader && view.buffer === 0, 'Invalid accessor buffer view or component type');
    assert((view.byteOffset ?? 0) + view.byteLength <= binary.length, 'Buffer view exceeds binary');
    const [method, size] = reader, step = stride ?? size * width;
    assert(step >= size * width, 'Accessor byte stride is too small');
    assert(offset + Math.max(0, count - 1) * step + (count ? size * width : 0) <= view.byteLength, 'Accessor exceeds buffer view');
    const data = new DataView(binary.buffer, binary.byteOffset, binary.byteLength), result = [];
    for (let i = 0; i < count; i++) for (let j = 0; j < width; j++) result.push(data[method]((view.byteOffset ?? 0) + offset + i * step + j * size, true));
    return result;
  }
  function accessor(index) {
    if (accessors.has(index)) return accessors.get(index);
    const spec = json.accessors?.[index], width = widths[spec?.type];
    assert(spec && width && Number.isInteger(spec.count) && spec.count >= 0, `Invalid accessor ${index}`);
    const values = spec.bufferView === undefined ? new Array(spec.count * width).fill(0)
      : readValues(spec.bufferView, spec.byteOffset ?? 0, spec.count, width, spec.componentType, json.bufferViews[spec.bufferView].byteStride);
    if (spec.sparse) {
      const sparse = spec.sparse;
      const indices = readValues(sparse.indices.bufferView, sparse.indices.byteOffset ?? 0, sparse.count, 1, sparse.indices.componentType);
      const replacements = readValues(sparse.values.bufferView, sparse.values.byteOffset ?? 0, sparse.count, width, spec.componentType);
      indices.forEach((target, row) => {
        assert(target < spec.count, 'Sparse accessor index out of range');
        for (let j = 0; j < width; j++) values[target * width + j] = replacements[row * width + j];
      });
    }
    assert(values.every(Number.isFinite), `Non-finite accessor ${index}`);
    accessors.set(index, values);
    return values;
  }
  return { json, binary, accessor };
}

function duration(glb, animation) {
  return Math.max(...animation.samplers.map(sampler => glb.accessor(sampler.input).at(-1)));
}

/** Sample baked transform and morph channels, then evaluate actual mesh vertices. */
export function sampleBounds(glb, animationName, progress, { include, exclude = [], checkVertex } = {}) {
  const { json, accessor } = glb;
  const pose = json.nodes.map(node => ({
    position: new Vector3().fromArray(node.translation ?? [0, 0, 0]),
    rotation: new Quaternion().fromArray(node.rotation ?? [0, 0, 0, 1]),
    scale: new Vector3().fromArray(node.scale ?? [1, 1, 1]),
    weights: [...(node.weights ?? json.meshes?.[node.mesh]?.weights ?? [])],
  }));
  const samples = typeof animationName === 'string' ? { [animationName]: progress } : animationName;
  for (const [name, fraction] of Object.entries(samples ?? {})) {
    const animation = json.animations?.find(item => item.name === name);
    assert(animation, `Missing animation ${name}`);
    const time = duration(glb, animation) * fraction;
    for (const channel of animation.channels) {
      const sampler = animation.samplers[channel.sampler], times = accessor(sampler.input), values = accessor(sampler.output);
      const width = channel.target.path === 'weights' ? pose[channel.target.node].weights.length : channel.target.path === 'rotation' ? 4 : 3;
      assert(width > 0, 'Animation has no morph targets');
      assert((sampler.interpolation ?? 'LINEAR') !== 'CUBICSPLINE', 'Validator requires baked LINEAR/STEP channels');
      let start = 0;
      while (start < times.length - 1 && times[start + 1] <= time) start++;
      const end = Math.min(start + 1, times.length - 1);
      const alpha = end === start || sampler.interpolation === 'STEP' ? 0 : Math.max(0, Math.min(1, (time - times[start]) / (times[end] - times[start])));
      const from = values.slice(start * width, (start + 1) * width), to = values.slice(end * width, (end + 1) * width);
      const target = pose[channel.target.node];
      if (channel.target.path === 'rotation') target.rotation.fromArray(from).slerp(new Quaternion().fromArray(to), alpha).normalize();
      else {
        const sampled = from.map((value, i) => value + (to[i] - value) * alpha);
        if (channel.target.path === 'weights') target.weights = sampled;
        else target[channel.target.path === 'translation' ? 'position' : 'scale'].fromArray(sampled);
      }
    }
  }
  const bounds = new Box3(), vertex = new Vector3();
  function visit(index, parent, ancestry) {
    assert(!ancestry.has(index), 'Cycle in glTF node graph');
    const node = json.nodes[index];
    assert(node, `Missing node ${index}`);
    const next = new Set(ancestry).add(index), p = pose[index];
    const local = node.matrix ? new Matrix4().fromArray(node.matrix) : new Matrix4().compose(p.position, p.rotation, p.scale);
    const world = parent.clone().multiply(local);
    if (node.mesh !== undefined && !exclude.includes(node.name) && (!include || include.includes(node.name))) {
      for (const primitive of json.meshes[node.mesh].primitives) {
        const positions = accessor(primitive.attributes.POSITION);
        const morphs = (primitive.targets ?? []).map(target => target.POSITION === undefined ? null : accessor(target.POSITION));
        for (let offset = 0; offset < positions.length; offset += 3) {
          vertex.fromArray(positions, offset);
          morphs.forEach((deltas, target) => {
            if (deltas && p.weights[target]) { vertex.x += deltas[offset] * p.weights[target]; vertex.y += deltas[offset + 1] * p.weights[target]; vertex.z += deltas[offset + 2] * p.weights[target]; }
          });
          vertex.applyMatrix4(world);
          if (checkVertex) checkVertex(vertex, node.name);
          bounds.expandByPoint(vertex);
        }
      }
    }
    for (const child of node.children ?? []) visit(child, world, next);
  }
  for (const index of json.scenes?.[json.scene ?? 0]?.nodes ?? []) visit(index, new Matrix4(), new Set());
  assert(!bounds.isEmpty(), 'No visible mesh vertices found');
  return bounds;
}

const rounded = box => ({ min: box.min.toArray().map(n => +n.toFixed(4)), max: box.max.toArray().map(n => +n.toFixed(4)) });
const paperHeight = (x, z) => {
  const u = Math.max(0, Math.min(1, (Math.abs(x) - 0.018) / 2.4)), v = (1.55 - z) / 3.1;
  return 0.202 + 0.115 * Math.sin(Math.PI * u) * Math.exp(-1.8 * u) - 0.007 * u * u * Math.cos((v - 0.5) * Math.PI);
};

export function inspectAsset(filename, { directory = root } = {}) {
  const bytes = fs.readFileSync(path.join(directory, 'public/models', filename)), glb = parseGlb(bytes), { json, accessor } = glb;
  const book = filename === 'book.glb', requiredClips = book ? ['open', 'turn', 'reading'] : ['unfold'];
  const names = new Set((json.nodes ?? []).map(node => node.name));
  const requiredNodes = book ? ['BookRoot', 'CoverHinge', 'Spine', 'LeftPage', 'RightPage', 'TurnPage', 'FrontCover', 'BackCover', 'Front title', 'Spine title', 'ReadingHinge', 'ReadingPanel'] : [];
  for (const name of requiredNodes) assert(names.has(name), `Missing required node ${name}`);
  assert(json.meshes?.length > 0 && json.materials?.length > 0, 'Missing geometry or materials');
  for (const material of book ? ['leather', 'brass', 'paper'] : ['paper']) assert(json.materials.some(item => item.name === material), `Missing ${material} material`);
  let primitives = 0, triangles = 0;
  for (const mesh of json.meshes) for (const primitive of mesh.primitives) {
    primitives++;
    assert((primitive.mode ?? 4) === 4, 'Geometry must be triangulated');
    const positions = accessor(primitive.attributes?.POSITION);
    assert(positions.length > 0 && positions.length % 3 === 0, 'Invalid position geometry');
    assert(json.materials[primitive.material], 'Primitive has no valid material');
    const indices = primitive.indices === undefined ? null : accessor(primitive.indices);
    if (indices) assert(indices.every(index => Number.isInteger(index) && index >= 0 && index < positions.length / 3), 'Mesh index exceeds position accessor');
    assert((indices?.length ?? positions.length / 3) % 3 === 0, 'Triangle index count is not divisible by three');
    triangles += (indices?.length ?? positions.length / 3) / 3;
  }
  for (const image of json.images ?? []) assert(image.bufferView !== undefined && !image.uri && ['image/png', 'image/jpeg', 'image/webp'].includes(image.mimeType), 'GLB textures must be embedded browser-supported images');
  const animations = {};
  for (const name of requiredClips) {
    const clip = json.animations?.find(animation => animation.name === name);
    assert(clip?.channels?.length && clip.samplers?.length, `Missing animation ${name}`);
    animations[name] = duration(glb, clip);
    assert(Number.isFinite(animations[name]) && animations[name] > 0 && animations[name] <= 10, `Invalid animation duration ${name}`);
    for (const channel of clip.channels) {
      const sampler = clip.samplers[channel.sampler], node = json.nodes[channel.target.node];
      assert(node && sampler, `Invalid target/sampler in ${name}`);
      assert(['translation', 'rotation', 'scale', 'weights'].includes(channel.target.path), 'Unsupported animation channel');
      const times = accessor(sampler.input), values = accessor(sampler.output), width = channel.target.path === 'weights'
        ? (node.weights ?? json.meshes[node.mesh]?.weights ?? []).length : channel.target.path === 'rotation' ? 4 : 3;
      assert(times.length >= 2 && times[0] === 0 && times.every((time, i) => i === 0 || time > times[i - 1]), `Invalid animation timeline ${name}`);
      assert(['LINEAR', 'STEP'].includes(sampler.interpolation ?? 'LINEAR'), 'Animations must be baked LINEAR/STEP');
      assert(values.length === times.length * width, `Animation channel sample count mismatch in ${name}`);
    }
  }
  // Authoring budgets agreed with the Blender owner, not a claim of phone performance.
  const transferCeiling = book ? 5 : 4;
  assert(bytes.length <= transferCeiling * 1024 * 1024, `GLB exceeds ${transferCeiling} MiB transfer ceiling`);
  assert(primitives <= 256 && triangles <= 250000, 'GLB exceeds 256 primitives / 250k triangles ceiling');
  const report = { file: filename, bytes: bytes.length, meshes: json.meshes.length, primitives, triangles, animations };
  if (book) {
    const open = sampleBounds(glb, { open: 1, reading: 0 }, 0, { exclude: ['TurnPage'] });
    const closed = sampleBounds(glb, { open: 0, reading: 0 }, 0, { exclude: ['TurnPage'] });
    const panelFlat = sampleBounds(glb, { open: 1, reading: 0 }, 0, { include: ['ReadingPanel'] });
    const panelRaised = sampleBounds(glb, { open: 1, reading: 1 }, 0, { include: ['ReadingPanel'] });
    assert(panelFlat.max.y - panelFlat.min.y < 0.03, 'Reading panel is not flat at reading(0)');
    assert(panelRaised.max.y - panelRaised.min.y > 0.68 && panelRaised.max.y - panelRaised.min.y < 0.78, 'Reading panel does not rise to its agreed 18 degree pose');
    assert(panelRaised.min.x >= -2.5 && panelRaised.max.x <= -0.1, 'Reading panel crosses the book footprint or spine');
    const right = sampleBounds(glb, 'turn', 0, { include: ['TurnPage'] });
    const left = sampleBounds(glb, 'turn', 1, { include: ['TurnPage'] });
    assert(open.min.x < -2.3 && open.max.x > 2.3, 'Open cover does not span both pages');
    assert(closed.max.x - closed.min.x < 3 && closed.max.y - closed.min.y < 0.9, 'Closed book is not compact');
    assert(right.min.x >= -0.12 && right.max.x > 2 && left.min.x < -2 && left.max.x <= 0.12, 'TurnPage endpoints do not cross the spine');
    assert(right.max.y - right.min.y < 0.12 && left.max.y - left.min.y < 0.12, 'TurnPage endpoint is not flat');
    Object.assign(report, { open: rounded(open), closed: rounded(closed), turnRight: rounded(right), turnLeft: rounded(left), panelFlat: rounded(panelFlat), panelRaised: rounded(panelRaised) });
  } else {
    const clip = json.animations.find(animation => animation.name === 'unfold');
    const hinges = new Set(clip.channels.filter(channel => channel.target.path === 'rotation').map(channel => channel.target.node));
    const parents = new Map();
    json.nodes.forEach((node, index) => (node.children ?? []).forEach(child => parents.set(child, index)));
    json.nodes.forEach((node, index) => {
      if (node.mesh === undefined) return;
      let current = index;
      while (current !== undefined && !hinges.has(current)) current = parents.get(current);
      assert(current !== undefined, `Mesh ${node.name} has no animated paper hinge`);
    });
    const folded = sampleBounds(glb, 'unfold', 0), opened = sampleBounds(glb, 'unfold', 1);
    assert(folded.min.x >= -2.50 && folded.max.x <= 2.50 && folded.min.z >= -1.64 && folded.max.z <= 1.64, `Folded scenery extends beyond paper: ${JSON.stringify(rounded(folded))}`);
    assert(folded.min.y >= 0.210 && folded.max.y <= 0.323, `Folded scenery is not flush with page: ${JSON.stringify(rounded(folded))}`);
    assert(opened.max.y >= 0.7 && opened.max.y <= 2.403, 'Open scenery has invalid display height');
    for (let step = 0; step <= 20; step++) {
      const bounds = sampleBounds(glb, 'unfold', step / 20, { checkVertex: (vertex, name) => {
        const surface = paperHeight(vertex.x, vertex.z);
        assert(vertex.y >= surface - 0.005, `${name} penetrates curved page at unfold ${step / 20}: vertex Y ${vertex.y.toFixed(4)}, page Y ${surface.toFixed(4)}, X ${vertex.x.toFixed(4)}, Z ${vertex.z.toFixed(4)}`);
      } });
      assert(bounds.min.y >= 0.200, `Scenery falls below the paper's minimum height at ${step / 20}`);
      assert(bounds.min.x >= -2.53 && bounds.max.x <= 2.53 && bounds.min.z >= -1.68 && bounds.max.z <= 1.68, `Scenery swings outside book footprint at ${step / 20}`);
    }
    Object.assign(report, { hinges: hinges.size, folded: rounded(folded), open: rounded(opened) });
  }
  const stem = filename.replace('.glb', '');
  for (const relative of [`public/posters/${stem}.webp`, `assets/source/${stem}.blend`]) assert(fs.statSync(path.join(directory, relative)).size > 100, `Missing or empty companion ${relative}`);
  const poster = fs.readFileSync(path.join(directory, `public/posters/${stem}.webp`));
  assert(poster.toString('ascii', 0, 4) === 'RIFF' && poster.toString('ascii', 8, 12) === 'WEBP' && poster.readUInt32LE(4) + 8 === poster.length, 'Fallback poster is not a complete WebP file');
  const source = fs.readFileSync(path.join(directory, `assets/source/${stem}.blend`));
  assert(source.toString('ascii', 0, 7) === 'BLENDER' || source.readUInt32LE(0) === 0xfd2fb528 || source.readUInt16LE(0) === 0x8b1f, 'Blender source is missing or an unresolved Git LFS pointer');
  return report;
}

export function validateAssets({ milestone = false, directory = root } = {}) {
  const required = ['book.glb', ...Array.from({ length: milestone ? 2 : 12 }, (_, index) => `chapter-${String(index + 1).padStart(2, '0')}.glb`)];
  const reports = [], errors = [];
  for (const file of required) {
    try { reports.push(inspectAsset(file, { directory })); }
    catch (error) { errors.push(`${file}: ${error.message}`); }
  }
  return { mode: milestone ? 'milestone (book + 2 chapters)' : 'release (book + 12 chapters)', reports, errors };
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const result = validateAssets({ milestone: process.argv.includes('--milestone') });
  if (process.argv.includes('--json')) console.log(JSON.stringify(result, null, 2));
  else {
    console.log(`Asset validation: ${result.mode}`);
    for (const item of result.reports) console.log(`PASS ${item.file}: ${(item.bytes / 1048576).toFixed(2)} MiB, ${item.primitives} primitives, ${item.triangles} triangles; clips ${Object.keys(item.animations).join(', ')}`);
    for (const error of result.errors) console.error(`FAIL ${error}`);
    console.log(`${result.reports.length} passed; ${result.errors.length} failed. Structural/pose checks do not establish visual acceptance or physical-device performance.`);
  }
  if (result.errors.length) process.exitCode = 1;
}
