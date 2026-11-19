import * as THREE from 'three';

/**
 * The turning leaf: a dense sheet bent at runtime, and the deformation that
 * lets paper pieces ride on it as real geometry.
 * Owned by the Interaction agent (docs/INTERACTION.md).
 *
 * Book space is BookScene's `group` space: X across the spread (gutter at 0,
 * right page positive), Y up, Z toward the visitor. The leaf is described by
 * a grid over the right page: u runs from the gutter to the fore-edge, v from
 * the head (-Z) to the front edge (+Z). Every row is a cross-section bent by
 * a tangent-angle field, so the sheet keeps its length (it never stretches)
 * and both endpoints match the bound pages exactly: at rest it lies 0.006
 * above the right page, landed it is the mirror image over the left page.
 */

export const LEAF_NU = 72;
export const LEAF_NV = 18;
/** Rest height of the leaf above the page it lies on. */
export const LEAF_LIFT = 0.006;
/** Half the paper thickness (front and back faces sit either side of the mid-surface). */
const HALF_THICKNESS = 0.0014;
/** Tallest folded stack of paper pieces above the page (docs/PIPELINE.md: Y up to .32). */
const STACK = 0.11;
const SHADOW_COLUMNS = 192;

export type RestSurface = { x0: number; x1: number; z0: number; z1: number; y: Float32Array };

const smoothstep = (a: number, b: number, x: number) => {
  const t = Math.min(1, Math.max(0, (x - a) / (b - a)));
  return t * t * (3 - 2 * t);
};

/**
 * How far each part of the sheet has turned (0 resting on its source page,
 * 1 landed on the other), for travel progress L. The S-curve: the sheet comes
 * out of the binding a little behind the body, and the fore-edge leads while
 * the page lifts, then trails as it falls over and catches up on landing.
 * `grab` (0 head .. 1 front edge) is the row the hand holds; it leads most.
 */
export function curlWeight(u: number, v: number, L: number, grab = 0.85) {
  const l = Math.min(1, Math.max(0, L));
  const tip = smoothstep(0.18, 1, u);
  const root = 1 - smoothstep(0, 0.24, u);
  const twist = 1 + 0.3 * (0.5 - Math.min(1, Math.abs(v - grab) * 1.6));
  const w = l + 0.115 * Math.sin(2 * Math.PI * l) * tip * twist - 0.07 * Math.sin(Math.PI * l) * root;
  return Math.min(1, Math.max(0, w));
}

/** Travel progress whose held fore-edge row has turned by `target` (0..1). */
export function travelForTip(target: number, grab = 0.85) {
  let lo = 0, hi = 1;
  for (let i = 0; i < 24; i++) {
    const mid = (lo + hi) / 2;
    if (curlWeight(1, grab, mid, grab) < target) lo = mid; else hi = mid;
  }
  return (lo + hi) / 2;
}

/** Shared deformation uniforms for every chapter material (see deformMaterial). */
export function makeLeafUniforms() {
  return {
    uLeafFrame: { value: null as THREE.DataTexture | null },
    uLeafGrid: { value: new THREE.Vector4(0.02, 2.42, -1.54, 1.54) },
    uLeafDims: { value: new THREE.Vector2(LEAF_NU + 1, LEAF_NV + 1) },
    uBook: { value: new THREE.Matrix4() },
    uBookInv: { value: new THREE.Matrix4() },
    uLeafShadow: { value: null as THREE.DataTexture | null },
    uLeafShadowOn: { value: 0 },
    /** 0..1: how far pieces riding on the leaf have been seated onto its front face. */
    uLeafSeat: { value: 0 },
    /** The same for the reading panel lying on the leaf's back. */
    uLeafSeatBack: { value: 0 },
  };
}
export type LeafUniforms = ReturnType<typeof makeLeafUniforms>;

const deformChunk = /* glsl */`
#define LEAF_REST_LIFT ${LEAF_LIFT.toFixed(4)}
#define LEAF_HALF_THICKNESS ${HALF_THICKNESS.toFixed(4)}
uniform highp sampler2D uLeafFrame;
uniform vec4 uLeafGrid;
uniform vec2 uLeafDims;
uniform mat4 uBookInv;
uniform float uLeafMode;
uniform float uLeafSeat;
uniform float uLeafSeatBack;
vec4 leafFetch(int block, vec2 g) {
  vec2 f = clamp(g, vec2(0.0), uLeafDims - 1.0);
  ivec2 a = ivec2(floor(f));
  ivec2 b = min(a + 1, ivec2(uLeafDims) - 1);
  vec2 t = f - vec2(a);
  int o = block * int(uLeafDims.y);
  vec4 p00 = texelFetch(uLeafFrame, ivec2(a.x, a.y + o), 0);
  vec4 p10 = texelFetch(uLeafFrame, ivec2(b.x, a.y + o), 0);
  vec4 p01 = texelFetch(uLeafFrame, ivec2(a.x, b.y + o), 0);
  vec4 p11 = texelFetch(uLeafFrame, ivec2(b.x, b.y + o), 0);
  return mix(mix(p00, p10, t.x), mix(p01, p11, t.x), t.y);
}
// Mode 1: hinged to the leaf's front (the right page) and riding on it.
// Mode 2: left on the right page, pressed flat where the leaf lies on it.
// Mode 3: lying on the leaf's back (the left page side): the reading panel and its writing.
void leafApply(inout vec3 p, inout vec3 n) {
  if (uLeafMode < 0.5) return;
  bool onBack = uLeafMode > 2.5;
  mat4 toBook = uBookInv * modelMatrix;
  vec3 b = (toBook * vec4(p, 1.0)).xyz;
  vec3 bn = mat3(toBook) * n;
  // The back is described from the left page, mirrored onto the leaf's own grid.
  if (onBack) { b.x = -b.x; bn.x = -bn.x; }
  vec2 span = vec2(uLeafGrid.y - uLeafGrid.x, uLeafGrid.w - uLeafGrid.z);
  vec2 g = (vec2(b.x, b.z) - uLeafGrid.xz) / span * (uLeafDims - 1.0);
  vec2 gc = clamp(g, vec2(0.0), uLeafDims - 1.0);
  vec4 P = leafFetch(0, g);
  vec4 N = leafFetch(1, g);
  vec4 T = leafFetch(2, g);
  vec4 RN = leafFetch(3, g);
  vec3 rn = normalize(RN.xyz);
  vec3 rt = normalize(leafFetch(4, g).xyz);
  vec3 rb = normalize(cross(rt, rn));
  vec3 restP = vec3(uLeafGrid.x + gc.x / (uLeafDims.x - 1.0) * span.x, P.w, uLeafGrid.z + gc.y / (uLeafDims.y - 1.0) * span.y);
  vec3 d = b - restP;
  float along = dot(d, rt), height = dot(d, rn), across = dot(d, rb);
  // Heights above the bound page (the leaf rests LIFT above it).
  float onPage = height + LEAF_REST_LIFT;
  float seated = max(onPage, 0.0) + LEAF_HALF_THICKNESS + 0.0005;
  vec3 cp = restP, ct = rt, cn = rn, cb = rb;
  if (uLeafMode < 1.5) {
    cp = P.xyz; ct = normalize(T.xyz); cn = normalize(N.xyz); cb = normalize(cross(ct, cn));
    // Seat the piece on the leaf's front face, then press it flat as the leaf closes on the other page.
    height = mix(height, seated, uLeafSeat) * N.w;
  } else if (onBack) {
    cp = P.xyz; ct = normalize(T.xyz); cn = -normalize(N.xyz); cb = normalize(cross(ct, -cn));
    height = mix(height, seated, uLeafSeatBack) * RN.w;
  } else {
    // Under the leaf: pressed towards the page, never through the sheet.
    height = onPage * T.w - LEAF_REST_LIFT;
  }
  vec3 moved = cp + along * ct + height * cn + across * cb;
  vec3 turned = dot(bn, rt) * ct + dot(bn, rn) * cn + dot(bn, rb) * cb;
  mat4 fromBook = inverse(toBook);
  p = (fromBook * vec4(moved, 1.0)).xyz;
  n = mat3(fromBook) * turned;
}
`;

/**
 * Let a chapter material's geometry follow the leaf. `mode` is the rig's own
 * uniform (0 at rest, 1 on the leaf, 2 pressed under it). Chains any existing hook.
 */
export function deformMaterial(material: THREE.Material, shared: LeafUniforms, mode: { value: number }) {
  if (material.userData.leafDeform) return;
  material.userData.leafDeform = true;
  const previous = material.onBeforeCompile.bind(material);
  const previousKey = material.customProgramCacheKey.bind(material);
  material.onBeforeCompile = (shader, renderer) => {
    previous(shader, renderer);
    Object.assign(shader.uniforms, { uLeafFrame: shared.uLeafFrame, uLeafGrid: shared.uLeafGrid, uLeafDims: shared.uLeafDims, uBookInv: shared.uBookInv, uLeafSeat: shared.uLeafSeat, uLeafSeatBack: shared.uLeafSeatBack, uLeafMode: mode });
    shader.vertexShader = shader.vertexShader.replace('void main() {', `${deformChunk}\nvoid main() {`);
    // Depth materials only mention the normal chunks inside optional blocks.
    if (!(material instanceof THREE.MeshDepthMaterial) && shader.vertexShader.includes('#include <beginnormal_vertex>')) {
      shader.vertexShader = shader.vertexShader
        .replace('#include <beginnormal_vertex>', '#include <beginnormal_vertex>\n\tvec3 leafPosition = position;\n\tleafApply(leafPosition, objectNormal);')
        .replace('#include <begin_vertex>', '#include <begin_vertex>\n\ttransformed = leafPosition;');
    } else {
      shader.vertexShader = shader.vertexShader
        .replace('#include <begin_vertex>', '#include <begin_vertex>\n\t{ vec3 leafNormal = vec3(0.0, 1.0, 0.0); leafApply(transformed, leafNormal); }');
    }
  };
  material.customProgramCacheKey = () => `${previousKey()}|leaf-deform`;
  material.needsUpdate = true;
}

/** Shadow-map material for a deformed mesh, so its shadow bends with it. */
export function deformDepthMaterial(shared: LeafUniforms, mode: { value: number }) {
  const material = new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking, side: THREE.DoubleSide });
  deformMaterial(material, shared, mode);
  return material;
}

/** Fragment hook for the bound pages and the reading panel: the leaf's soft occlusion. */
export function shadePageUnderLeaf(material: THREE.Material, shared: LeafUniforms) {
  const previous = material.onBeforeCompile.bind(material);
  const previousKey = material.customProgramCacheKey.bind(material);
  material.onBeforeCompile = (shader, renderer) => {
    previous(shader, renderer);
    Object.assign(shader.uniforms, { uLeafShadow: shared.uLeafShadow, uLeafShadowOn: shared.uLeafShadowOn, uLeafGrid: shared.uLeafGrid, uBookInv: shared.uBookInv });
    shader.vertexShader = `uniform mat4 uBookInv;\nvarying vec3 vLeafBook;\n${shader.vertexShader}`
      .replace('#include <project_vertex>', '#include <project_vertex>\n\tvLeafBook = (uBookInv * modelMatrix * vec4(transformed, 1.0)).xyz;');
    shader.fragmentShader = `uniform sampler2D uLeafShadow;\nuniform float uLeafShadowOn;\nuniform vec4 uLeafGrid;\nvarying vec3 vLeafBook;\n${shader.fragmentShader}`
      .replace('#include <opaque_fragment>', `
\tif (uLeafShadowOn > 0.5) {
\t\tvec2 leafUv = vec2(vLeafBook.x / uLeafGrid.y * 0.5 + 0.5, (vLeafBook.z - uLeafGrid.z) / (uLeafGrid.w - uLeafGrid.z));
\t\toutgoingLight *= 1.0 - texture2D(uLeafShadow, clamp(leafUv, 0.0, 1.0)).r;
\t}
#include <opaque_fragment>`);
  };
  material.customProgramCacheKey = () => `${previousKey()}|leaf-shade`;
  material.needsUpdate = true;
}

export type LeafState = {
  /** Smallest clearance of the leaf over the reading panel (left page, X < -0.2). */
  panelGap: number;
};

/** The sheet itself: front (lit paper), back (the print of the left half) and edges. */
export class Leaf {
  readonly group = new THREE.Group();
  readonly frame: THREE.DataTexture;
  readonly shadow: THREE.DataTexture;
  readonly front: THREE.Mesh;
  readonly back: THREE.Mesh;
  readonly edge: THREE.Mesh;
  /** Leaf points, row-major (v outer, u inner), xyz. */
  private points = new Float32Array((LEAF_NU + 1) * (LEAF_NV + 1) * 3);
  private normals = new Float32Array((LEAF_NU + 1) * (LEAF_NV + 1) * 3);
  private tangents = new Float32Array((LEAF_NU + 1) * (LEAF_NV + 1) * 3);
  private restAngle = new Float32Array(LEAF_NU * (LEAF_NV + 1));
  private restLength = new Float32Array(LEAF_NU * (LEAF_NV + 1));
  private gapRow = new Float32Array(SHADOW_COLUMNS);
  private shadeRow = new Float32Array(SHADOW_COLUMNS);
  private frontPositions: THREE.BufferAttribute;
  private frontNormals: THREE.BufferAttribute;
  private backPositions: THREE.BufferAttribute;
  private backNormals: THREE.BufferAttribute;
  private edgePositions: THREE.BufferAttribute;
  private edgeNormals: THREE.BufferAttribute;
  state: LeafState = { panelGap: 1 };

  constructor(readonly rest: RestSurface, materials: { front: THREE.Material; back: THREE.Material; edge: THREE.Material },
    frontUv?: (x: number, z: number) => [number, number], backUv?: (x: number, z: number) => [number, number]) {
    const nu = LEAF_NU, nv = LEAF_NV, count = (nu + 1) * (nv + 1);
    // Frame texture: 5 blocks of (nu+1) x (nv+1) texels; see deformChunk.
    const frameData = new Float32Array((nu + 1) * (nv + 1) * 5 * 4);
    this.frame = new THREE.DataTexture(frameData, nu + 1, (nv + 1) * 5, THREE.RGBAFormat, THREE.FloatType);
    this.frame.minFilter = this.frame.magFilter = THREE.NearestFilter;
    const shadowData = new Uint8Array(SHADOW_COLUMNS * (nv + 1) * 4);
    this.shadow = new THREE.DataTexture(shadowData, SHADOW_COLUMNS, nv + 1, THREE.RGBAFormat, THREE.UnsignedByteType);
    this.shadow.minFilter = this.shadow.magFilter = THREE.LinearFilter;

    // Rest cross-sections: segment angles and lengths along every row.
    for (let j = 0; j <= nv; j++) for (let i = 0; i < nu; i++) {
      const dx = (rest.x1 - rest.x0) / nu, dy = this.restY(i + 1, j) - this.restY(i, j);
      this.restAngle[j * nu + i] = Math.atan2(dy, dx);
      this.restLength[j * nu + i] = Math.hypot(dx, dy);
    }

    // Faces share one grid; the attributes are rewritten every frame of a turn.
    const index: number[] = [];
    for (let j = 0; j < nv; j++) for (let i = 0; i < nu; i++) {
      const a = j * (nu + 1) + i, b = a + 1, c = a + nu + 1, d = c + 1;
      index.push(a, c, b, b, c, d);
    }
    const uvFront = new Float32Array(count * 2), uvBack = new Float32Array(count * 2), restXZ = new Float32Array(count * 2);
    for (let j = 0; j <= nv; j++) for (let i = 0; i <= nu; i++) {
      const k = j * (nu + 1) + i, x = this.x(i), z = this.z(j);
      const [fu, fv] = frontUv ? frontUv(x, z) : [i / nu, 1 - j / nv];
      uvFront[k * 2] = fu; uvFront[k * 2 + 1] = fv;
      // The back is the left page's paper where the leaf lands on it.
      const [bu, bv] = backUv ? backUv(-x, z) : [1 - i / nu, 1 - j / nv];
      uvBack[k * 2] = bu; uvBack[k * 2 + 1] = bv;
      restXZ[k * 2] = x; restXZ[k * 2 + 1] = z;
    }
    const face = (uv: Float32Array, flip: boolean) => {
      const geometry = new THREE.BufferGeometry();
      geometry.setIndex(flip ? index.map((_, n) => index[n - (n % 3) + [0, 2, 1][n % 3]]) : index);
      const position = new THREE.BufferAttribute(new Float32Array(count * 3), 3).setUsage(THREE.DynamicDrawUsage);
      const normal = new THREE.BufferAttribute(new Float32Array(count * 3), 3).setUsage(THREE.DynamicDrawUsage);
      geometry.setAttribute('position', position);
      geometry.setAttribute('normal', normal);
      geometry.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
      geometry.setAttribute('leafRest', new THREE.BufferAttribute(restXZ, 2));
      return geometry;
    };
    const frontGeometry = face(uvFront, false), backGeometry = face(uvBack, true);
    this.frontPositions = frontGeometry.attributes.position as THREE.BufferAttribute;
    this.frontNormals = frontGeometry.attributes.normal as THREE.BufferAttribute;
    this.backPositions = backGeometry.attributes.position as THREE.BufferAttribute;
    this.backNormals = backGeometry.attributes.normal as THREE.BufferAttribute;
    this.front = new THREE.Mesh(frontGeometry, materials.front);
    this.back = new THREE.Mesh(backGeometry, materials.back);
    // The cut edges: fore-edge, head and tail, as thin strips between the faces.
    const rim: [number, number][] = [];
    for (let j = 0; j <= nv; j++) rim.push([nu, j]);
    const edgeCount = (nv + 1 + 2 * (nu + 1)) * 2;
    const edgeGeometry = new THREE.BufferGeometry();
    this.edgePositions = new THREE.BufferAttribute(new Float32Array(edgeCount * 3), 3).setUsage(THREE.DynamicDrawUsage);
    this.edgeNormals = new THREE.BufferAttribute(new Float32Array(edgeCount * 3), 3).setUsage(THREE.DynamicDrawUsage);
    edgeGeometry.setAttribute('position', this.edgePositions);
    edgeGeometry.setAttribute('normal', this.edgeNormals);
    const edgeIndex: number[] = [];
    const strip = (start: number, length: number, flip: boolean) => {
      for (let n = 0; n < length - 1; n++) {
        const a = start + n * 2, b = a + 1, c = a + 2, d = a + 3;
        edgeIndex.push(...(flip ? [a, c, b, b, c, d] : [a, b, c, b, d, c]));
      }
    };
    strip(0, nv + 1, false);
    strip((nv + 1) * 2, nu + 1, false);
    strip((nv + 1 + nu + 1) * 2, nu + 1, true);
    edgeGeometry.setIndex(edgeIndex);
    this.edge = new THREE.Mesh(edgeGeometry, materials.edge);
    for (const mesh of [this.front, this.back, this.edge]) { mesh.frustumCulled = false; this.group.add(mesh); }
    this.front.castShadow = true;
    this.front.receiveShadow = true;
    this.back.castShadow = false;
    this.back.receiveShadow = true;
    this.edge.castShadow = false;
    this.group.name = 'Turning leaf';
    this.group.visible = false;
    this.writeRestFrame();
  }

  x(i: number) { return this.rest.x0 + (this.rest.x1 - this.rest.x0) * i / LEAF_NU; }
  z(j: number) { return this.rest.z0 + (this.rest.z1 - this.rest.z0) * j / LEAF_NV; }
  restY(i: number, j: number) { return this.rest.y[j * (LEAF_NU + 1) + i]; }
  /** Height of a bound page surface at |X|, row j (the leaf rests LEAF_LIFT above it). */
  private pageY(x: number, j: number) {
    const f = (Math.abs(x) - this.rest.x0) / (this.rest.x1 - this.rest.x0) * LEAF_NU;
    const i = Math.min(LEAF_NU - 1, Math.max(0, Math.floor(f))), t = Math.min(1, Math.max(0, f - i));
    return this.restY(i, j) * (1 - t) + this.restY(i + 1, j) * t - LEAF_LIFT;
  }

  private writeRestFrame() {
    // The rest frame is the bent sheet at travel 0, so a piece riding on the
    // resting leaf is exactly where it was on the page.
    this.bend(0, 1, 0.85);
    const data = this.frame.image.data as Float32Array, block = (LEAF_NU + 1) * (LEAF_NV + 1) * 4;
    for (let k = 0; k < (LEAF_NU + 1) * (LEAF_NV + 1); k++) {
      for (let c = 0; c < 3; c++) {
        data[3 * block + k * 4 + c] = this.normals[k * 3 + c];
        data[4 * block + k * 4 + c] = this.tangents[k * 3 + c];
      }
    }
    this.update(0, 1);
  }

  /**
   * Bend the sheet. `travel` runs 0..1 from the source page to the other side;
   * `direction` 1 turns right to left (forward), -1 left to right.
   */
  update(travel: number, direction: 1 | -1, grab = 0.85) {
    this.bend(travel, direction, grab);
    this.writeGeometry();
    this.writeFrameAndShadow();
  }

  private bend(travel: number, direction: 1 | -1, grab: number) {
    const nu = LEAF_NU, nv = LEAF_NV, { x0 } = this.rest;
    const p = this.points, nrm = this.normals, tan = this.tangents;
    for (let j = 0; j <= nv; j++) {
      const v = j / nv;
      // The root swings through a tiny arc at the spine.
      const w0 = this.weight(0, v, travel, direction, grab);
      let px = x0 * Math.cos(Math.PI * w0), py = this.restY(0, j) + x0 * Math.sin(Math.PI * w0);
      const z = this.z(j);
      for (let i = 0; i <= nu; i++) {
        const k = (j * (nu + 1) + i) * 3;
        p[k] = px; p[k + 1] = py; p[k + 2] = z;
        if (i === nu) break;
        const r = this.restAngle[j * nu + i];
        const w = this.weight((i + 0.5) / nu, v, travel, direction, grab);
        const angle = r + (Math.PI - 2 * r) * w;
        const length = this.restLength[j * nu + i];
        px += Math.cos(angle) * length;
        py += Math.sin(angle) * length;
      }
    }
    // Tangent along u, binormal along v, normal = binormal x tangent (+Y at rest).
    const t = new THREE.Vector3(), b = new THREE.Vector3(), n = new THREE.Vector3();
    for (let j = 0; j <= nv; j++) for (let i = 0; i <= nu; i++) {
      const k = (j * (nu + 1) + i) * 3;
      const i0 = Math.max(0, i - 1), i1 = Math.min(nu, i + 1), j0 = Math.max(0, j - 1), j1 = Math.min(nv, j + 1);
      const a0 = (j * (nu + 1) + i0) * 3, a1 = (j * (nu + 1) + i1) * 3, b0 = (j0 * (nu + 1) + i) * 3, b1 = (j1 * (nu + 1) + i) * 3;
      t.set(p[a1] - p[a0], p[a1 + 1] - p[a0 + 1], p[a1 + 2] - p[a0 + 2]).normalize();
      b.set(p[b1] - p[b0], p[b1 + 1] - p[b0 + 1], p[b1 + 2] - p[b0 + 2]).normalize();
      n.crossVectors(b, t).normalize();
      t.crossVectors(n, b).normalize();
      nrm[k] = n.x; nrm[k + 1] = n.y; nrm[k + 2] = n.z;
      tan[k] = t.x; tan[k + 1] = t.y; tan[k + 2] = t.z;
    }
  }

  private weight(u: number, v: number, travel: number, direction: number, grab: number) {
    const w = curlWeight(u, v, travel, grab);
    return direction > 0 ? w : 1 - w;
  }

  private writeGeometry() {
    const p = this.points, nrm = this.normals, count = (LEAF_NU + 1) * (LEAF_NV + 1);
    const fp = this.frontPositions.array as Float32Array, fn = this.frontNormals.array as Float32Array;
    const bp = this.backPositions.array as Float32Array, bn = this.backNormals.array as Float32Array;
    for (let k = 0; k < count * 3; k += 3) {
      for (let c = 0; c < 3; c++) {
        fp[k + c] = p[k + c] + nrm[k + c] * HALF_THICKNESS;
        bp[k + c] = p[k + c] - nrm[k + c] * HALF_THICKNESS;
        fn[k + c] = nrm[k + c];
        bn[k + c] = -nrm[k + c];
      }
    }
    // Edges: fore-edge (u = 1), head (v = 0), tail (v = 1); outward normal = the edge direction.
    const ep = this.edgePositions.array as Float32Array, en = this.edgeNormals.array as Float32Array;
    let e = 0;
    const put = (i: number, j: number, ox: number, oy: number, oz: number) => {
      const k = (j * (LEAF_NU + 1) + i) * 3;
      for (const side of [1, -1]) {
        ep[e] = p[k] + nrm[k] * HALF_THICKNESS * side; ep[e + 1] = p[k + 1] + nrm[k + 1] * HALF_THICKNESS * side; ep[e + 2] = p[k + 2] + nrm[k + 2] * HALF_THICKNESS * side;
        en[e] = ox; en[e + 1] = oy; en[e + 2] = oz;
        e += 3;
      }
    };
    const tan = this.tangents;
    for (let j = 0; j <= LEAF_NV; j++) { const k = (j * (LEAF_NU + 1) + LEAF_NU) * 3; put(LEAF_NU, j, tan[k], tan[k + 1], tan[k + 2]); }
    for (let i = 0; i <= LEAF_NU; i++) put(i, 0, 0, 0, -1);
    for (let i = 0; i <= LEAF_NU; i++) put(i, LEAF_NV, 0, 0, 1);
    for (const attribute of [this.frontPositions, this.frontNormals, this.backPositions, this.backNormals, this.edgePositions, this.edgeNormals]) attribute.needsUpdate = true;
  }

  private writeFrameAndShadow() {
    const nu = LEAF_NU, nv = LEAF_NV, p = this.points, nrm = this.normals, tan = this.tangents;
    const data = this.frame.image.data as Float32Array, block = (nu + 1) * (nv + 1) * 4;
    const shadow = this.shadow.image.data as Uint8Array;
    const { x1 } = this.rest;
    let panelGap = 1;
    for (let j = 0; j <= nv; j++) {
      // Lowest clearance of the sheet over every column of the spread, this row.
      const gap = this.gapRow.fill(1e3);
      for (let i = 0; i < nu; i++) {
        const a = (j * (nu + 1) + i) * 3, b = a + 3;
        const xa = p[a], xb = p[b];
        const lo = Math.min(xa, xb), hi = Math.max(xa, xb);
        const c0 = Math.max(0, Math.ceil(((lo / x1) * 0.5 + 0.5) * (SHADOW_COLUMNS - 1)));
        const c1 = Math.min(SHADOW_COLUMNS - 1, Math.floor(((hi / x1) * 0.5 + 0.5) * (SHADOW_COLUMNS - 1)));
        for (let c = c0; c <= c1; c++) {
          const x = ((c / (SHADOW_COLUMNS - 1)) - 0.5) * 2 * x1;
          const f = hi > lo ? (x - xa) / (xb - xa) : 0;
          const y = p[a + 1] + (p[b + 1] - p[a + 1]) * f;
          gap[c] = Math.min(gap[c], y - this.pageY(x, j));
        }
      }
      for (let c = 0; c < SHADOW_COLUMNS; c++) {
        const x = ((c / (SHADOW_COLUMNS - 1)) - 0.5) * 2 * x1;
        if (x < -0.2) panelGap = Math.min(panelGap, gap[c]);
        // Soft occlusion: none where the sheet touches (it covers the page there), deepest a little above it.
        const g = gap[c];
        this.shadeRow[c] = g > 50 ? 0 : 0.34 * (1 - Math.exp(-Math.max(0, g) / 0.035)) * Math.exp(-g / 0.9);
      }
      // A soft penumbra: blur along X.
      for (let c = 0; c < SHADOW_COLUMNS; c++) {
        let sum = 0, weight = 0;
        for (let d = -6; d <= 6; d++) {
          const q = c + d;
          if (q < 0 || q >= SHADOW_COLUMNS) continue;
          const k = Math.exp(-(d * d) / 18);
          sum += this.shadeRow[q] * k; weight += k;
        }
        shadow[(j * SHADOW_COLUMNS + c) * 4] = Math.round(255 * Math.min(1, sum / weight));
      }
      for (let i = 0; i <= nu; i++) {
        const k = j * (nu + 1) + i, o = k * 4, q = k * 3;
        // Pieces riding on the sheet are pressed flat as it comes down on the other page.
        let attached = 1;
        if (nrm[q + 1] < -0.02) {
          const clearance = (p[q + 1] - this.pageY(p[q], j)) / -nrm[q + 1];
          attached = Math.min(1, Math.max(0, (clearance - 0.004) / STACK));
        }
        // Pieces on the right page are pressed flat where the sheet lies on them.
        const column = Math.round(((this.x(i) / x1) * 0.5 + 0.5) * (SHADOW_COLUMNS - 1));
        const under = Math.min(1, Math.max(0, (gap[column] - 0.004) / STACK));
        data[o] = p[q]; data[o + 1] = p[q + 1]; data[o + 2] = p[q + 2]; data[o + 3] = this.restY(i, j);
        data[block + o] = nrm[q]; data[block + o + 1] = nrm[q + 1]; data[block + o + 2] = nrm[q + 2]; data[block + o + 3] = attached;
        data[2 * block + o] = tan[q]; data[2 * block + o + 1] = tan[q + 1]; data[2 * block + o + 2] = tan[q + 2]; data[2 * block + o + 3] = under;
        // The panel on the leaf's back is pressed flat when the back faces down onto a page.
        let backed = 1;
        if (nrm[q + 1] > 0.02) {
          const clearance = (p[q + 1] - this.pageY(p[q], j)) / nrm[q + 1];
          backed = Math.min(1, Math.max(0, (clearance - 0.004) / STACK));
        }
        data[3 * block + o + 3] = backed;
      }
    }
    this.state = { panelGap };
    this.frame.needsUpdate = true;
    this.shadow.needsUpdate = true;
  }

  dispose() {
    for (const mesh of [this.front, this.back, this.edge]) mesh.geometry.dispose();
    this.frame.dispose();
    this.shadow.dispose();
  }
}

/** Sample a page mesh's top surface on the leaf grid (heights + LEAF_LIFT). */
export function sampleRestSurface(page: THREE.Mesh, toBook: THREE.Matrix4, bounds: { x0: number; x1: number; z0: number; z1: number }): RestSurface {
  const probe = new THREE.Mesh(page.geometry, new THREE.MeshBasicMaterial({ side: THREE.DoubleSide }));
  probe.matrixAutoUpdate = false;
  probe.matrix.copy(toBook);
  probe.matrixWorld.copy(toBook);
  const raycaster = new THREE.Raycaster();
  const down = new THREE.Vector3(0, -1, 0);
  const y = new Float32Array((LEAF_NU + 1) * (LEAF_NV + 1));
  const hits: THREE.Intersection[] = [];
  let last = 0.2;
  for (let j = 0; j <= LEAF_NV; j++) for (let i = 0; i <= LEAF_NU; i++) {
    const x = bounds.x0 + (bounds.x1 - bounds.x0) * i / LEAF_NU, z = bounds.z0 + (bounds.z1 - bounds.z0) * j / LEAF_NV;
    // Probe just inside the outer edges, where rounded corners could miss.
    const px = Math.min(x, bounds.x1 - 0.004), pz = Math.min(Math.max(z, bounds.z0 + 0.004), bounds.z1 - 0.004);
    raycaster.set(new THREE.Vector3(px, 5, pz), down);
    hits.length = 0;
    probe.raycast(raycaster, hits);
    if (hits.length) last = Math.min(...hits.map(hit => hit.distance)) * -1 + 5;
    y[j * (LEAF_NU + 1) + i] = last + LEAF_LIFT;
  }
  probe.material.dispose();
  return { ...bounds, y };
}

/**
 * Each face of the leaf is its page's own paper: a clone of the page material,
 * with the gutter shading taken from where each point rests, fading while the
 * sheet is away from the gutter (`gutter` 1 lying on either page).
 */
export function makeLeafFrontMaterial(page: THREE.Material, gutter: { value: number }) {
  const material = page.clone();
  material.side = THREE.FrontSide;
  const previous = page.onBeforeCompile.bind(page);
  material.onBeforeCompile = (shader, renderer) => {
    previous(shader, renderer);
    shader.uniforms.uLeafGutter = gutter;
    shader.vertexShader = `attribute vec2 leafRest;\nvarying vec2 vLeafRest;\n${shader.vertexShader}`
      .replace('#include <project_vertex>', '#include <project_vertex>\n\tvLeafRest = leafRest;');
    shader.fragmentShader = `uniform float uLeafGutter;\nvarying vec2 vLeafRest;\n${shader.fragmentShader}`
      .replace('#include <opaque_fragment>', `
\tfloat leafGutter = abs(vLeafRest.x);
\tfloat leafGutterShade = 1.0 - uLeafGutter * (0.38 * exp(-leafGutter / 0.075) + 0.11 * exp(-leafGutter / 0.38));
\tfloat leafEdgeTone = max(smoothstep(2.08, 2.43, leafGutter), smoothstep(1.32, 1.56, abs(vLeafRest.y)));
\toutgoingLight *= leafGutterShade * mix(vec3(1.0), vec3(0.965, 0.925, 0.855), leafEdgeTone * 0.6);
#include <opaque_fragment>`);
  };
  const previousKey = page.customProgramCacheKey.bind(page);
  material.customProgramCacheKey = () => `${previousKey()}|leaf-face`;
  return material;
}
