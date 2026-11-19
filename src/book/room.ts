import * as THREE from 'three';
import type { GLTF, GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { FullScreenQuad } from 'three/addons/postprocessing/Pass.js';
import { HorizontalBlurShader } from 'three/addons/shaders/HorizontalBlurShader.js';
import { VerticalBlurShader } from 'three/addons/shaders/VerticalBlurShader.js';
import { clamp01 } from './motion';

/**
 * The room around the book: a real walnut desk, the photographed library beyond it,
 * lights, environment, contact shadows and the banker's lamp with its pull chain.
 * Owned by the Room agent (docs/QUALITY-SPEC.md, docs/ROOM-LAMP.md). BookScene calls only
 * the public members.
 */
export type RoomContext = {
  scene: THREE.Scene;
  renderer: THREE.WebGLRenderer;
  camera: THREE.PerspectiveCamera;
  invalidate: () => void;
  reducedMotion: () => boolean;
  lost: () => boolean;
  onLamp?: (on: boolean) => void;
  lampOn?: boolean;
};

const asset = (path: string) => `${import.meta.env.BASE_URL}${path.replace(/^\//, '')}`;

/** The desk's top surface; the book's base rests at -0.045. */
export const DESK_Y = -0.046;
/** The desk's back edge (world Z), a little behind the open book (Z -1.7) and the lamp. */
export const DESK_BACK = -2.95;
const DESK_EDGE_RADIUS = 0.075;
/** Photo row (from the top, 0..1) where the photographed desk's back edge sits. */
const PHOTO_DESK_ROW = 0.585;
const PHOTO_ASPECT = 1672 / 941;
/** Contact-shadow window on the desk (world X/Z), covering the book and the lamp. */
const CONTACT = { x: -0.9, z: -0.45, width: 9.2, depth: 5.4, height: 0.42 };
/** Hidden pick targets live on this layer: raycasts see them, cameras never draw them. */
const PICK_LAYER = 5;

type LampParts = {
  root: THREE.Object3D;
  anchor?: THREE.Object3D;
  chainAnchor?: THREE.Object3D;
  chain?: THREE.Object3D;
  shade?: THREE.Object3D;
  glowUniforms: { level: { value: number }; bulb: { value: THREE.Vector3 } };
  glass: THREE.MeshPhysicalMaterial[];
  opal: THREE.MeshPhysicalMaterial[];
  bulb: THREE.MeshStandardMaterial[];
  own: THREE.MeshStandardMaterial[];
};

type Placement = { x: number; z: number; turn: number };

/** Where the lamp would like to stand: back left of the book, the shade turned towards it. */
const PREFERRED: Placement = { x: -3.65, z: -1.55, turn: 0.9 };

/**
 * The reading camera BookScene settles on (BookScene.updateCamera, without pointer drift).
 * Duplicated here so the lamp can be placed for the reading framing whatever the camera
 * is doing at resize time; keep in step with BookScene if that framing ever changes.
 */
function readingCamera(aspect: number, height: number) {
  const camera = new THREE.PerspectiveCamera(32, aspect, 0.05, 80);
  const verticalFit = Math.sqrt(Math.max(1, 850 / height));
  const horizontalFit = aspect < 1 ? 5.6 : 5.3;
  const distance = Math.max(7.45 * verticalFit, horizontalFit / (2 * Math.tan(THREE.MathUtils.degToRad(16)) * aspect));
  camera.position.set(0.12, 0.53 * distance + 0.65, 0.86 * distance);
  camera.lookAt(0, 0.75, 0);
  camera.updateMatrixWorld();
  return camera;
}

/**
 * Choose the placement nearest PREFERRED that keeps the whole lamp in the reading view:
 * clear of the decorative header (headerFraction of the canvas, from the top), of the left
 * edge, of the book on screen and on the desk, and fully on the desktop. Undefined if none fits.
 */
export function solvePlacement(aspect: number, height: number, headerFraction: number, corners: THREE.Vector3[], footprint: boolean[]): Placement | undefined {
  const camera = readingCamera(aspect, height);
  const v = new THREE.Vector3(), m = new THREE.Matrix4(), q = new THREE.Quaternion(), up = new THREE.Vector3(0, 1, 0);
  const screen = (p: THREE.Vector3) => { v.copy(p).project(camera); return [(v.x + 1) / 2, (1 - v.y) / 2] as const; };
  const [bookBackX, bookBackY] = screen(new THREE.Vector3(-2.62, 0.3, -1.72));
  const [bookFrontX, bookFrontY] = screen(new THREE.Vector3(-2.66, 0.3, 1.72));
  const bookEdgeAt = (y: number) => bookBackX + (bookFrontX - bookBackX) * (y - bookBackY) / (bookFrontY - bookBackY);
  let best: Placement | undefined, bestScore = Infinity;
  const test = (x: number, z: number, turn: number) => {
    const score = Math.hypot(x - PREFERRED.x, (z - PREFERRED.z) * 1.4) + Math.abs(turn - PREFERRED.turn) * 0.6;
    if (score >= bestScore) return;
    q.setFromAxisAngle(up, turn);
    m.compose(new THREE.Vector3(x, DESK_Y, z), q, new THREE.Vector3(1, 1, 1));
    for (const [index, corner] of corners.entries()) {
      const world = v.copy(corner).applyMatrix4(m);
      // Footprint on the desk, behind its edge and left of the book with a hand's gap.
      if (footprint[index] && (world.z < DESK_BACK + 0.08 || world.x > -2.8)) return;
      const [sx, sy] = screen(world);
      if (sx < 0.01 || sy < headerFraction + 0.02 || sy > 0.97) return;
      if (sy > bookBackY && sx > bookEdgeAt(sy) - 0.012) return;
    }
    best = { x, z, turn }; bestScore = score;
  };
  for (let turn = 0.6; turn <= 1.201; turn += 0.15) for (let x = -6.5; x <= -2.9; x += 0.1) for (let z = DESK_BACK + 0.3; z <= 1.2; z += 0.1) test(x, z, turn);
  const coarse = best as Placement | undefined;
  if (coarse) for (let dt = -0.075; dt <= 0.076; dt += 0.075) for (let dx = -0.1; dx <= 0.101; dx += 0.025) for (let dz = -0.1; dz <= 0.101; dz += 0.025) test(coarse.x + dx, coarse.z + dz, coarse.turn + dt);
  return best;
}

/** A desk slab: the long flat top and a rounded back edge, UVs in texture tiles (10 x 5 units). */
function deskGeometry() {
  const r = DESK_EDGE_RADIUS, front = 18, depth = 0.6, left = -18, right = 18;
  const profile: { z: number; y: number; nz: number; ny: number; s: number }[] = [];
  profile.push({ z: front, y: DESK_Y, nz: 0, ny: 1, s: front });
  profile.push({ z: DESK_BACK + r, y: DESK_Y, nz: 0, ny: 1, s: DESK_BACK + r });
  const steps = 10;
  for (let i = 1; i <= steps; i++) {
    const a = (i / steps) * Math.PI / 2;
    profile.push({ z: DESK_BACK + r - r * Math.sin(a), y: DESK_Y - r + r * Math.cos(a), nz: -Math.sin(a), ny: Math.cos(a), s: DESK_BACK + r - r * a });
  }
  const last = profile[profile.length - 1];
  profile.push({ z: DESK_BACK, y: DESK_Y - depth, nz: -1, ny: 0, s: last.s - (depth - r) });
  const positions: number[] = [], normals: number[] = [], uvs: number[] = [], index: number[] = [];
  for (const p of profile) for (const x of [left, right]) {
    positions.push(x, p.y, p.z);
    normals.push(0, p.ny, p.nz);
    uvs.push(x / 10, -p.s / 5);
  }
  for (let i = 0; i < profile.length - 1; i++) {
    const a = i * 2, b = a + 1, c = a + 2, d = a + 3;
    index.push(a, b, d, a, d, c);
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  geometry.setAttribute('normal', new THREE.Float32BufferAttribute(normals, 3));
  geometry.setAttribute('uv', new THREE.Float32BufferAttribute(uvs, 2));
  geometry.setIndex(index);
  return geometry;
}

/**
 * Equirectangular light probe made from the library photograph: the bookcases and window
 * beyond the desk, a dimmer echo behind the viewer, a dark ceiling and the walnut below.
 * Desk, brass and glass reflect this instead of a neutral studio, so they belong to the room.
 */
function libraryProbe(photo: CanvasImageSource & { width: number; height: number }) {
  const W = 1024, H = 512;
  const canvas = document.createElement('canvas');
  canvas.width = W; canvas.height = H;
  const g = canvas.getContext('2d')!;
  const sky = g.createLinearGradient(0, 0, 0, H);
  sky.addColorStop(0, '#120b07');
  sky.addColorStop(0.35, '#2a1b12');
  sky.addColorStop(0.53, '#3a2617');
  sky.addColorStop(0.56, '#2a170d');
  sky.addColorStop(1, '#0d0806');
  g.fillStyle = sky; g.fillRect(0, 0, W, H);
  // Rows above the photographed desk; latitude about -4 to +38 degrees.
  const sh = photo.height * PHOTO_DESK_ROW;
  const horizon = H * (0.5 + 4 / 180), top = H * (0.5 - 38 / 180);
  const span = (x: number, width: number, alpha: number, flip = false) => {
    g.save();
    g.globalAlpha = alpha;
    g.filter = 'blur(2px)';
    if (flip) { g.translate(x + width, 0); g.scale(-1, 1); g.drawImage(photo, 0, 0, photo.width, sh, 0, top, width, horizon - top); }
    else g.drawImage(photo, 0, 0, photo.width, sh, x, top, width, horizon - top);
    g.restore();
  };
  // -Z (beyond the desk) is u = 0.25; the photo spans about 130 degrees there.
  span(W * (0.25 - 0.18), W * 0.36, 1);
  span(W * (0.75 - 0.18), W * 0.36, 0.35, true);
  // Window glow on the left (-X, u = 0 / 1) where the photograph's window is.
  for (const cx of [0, W]) {
    const glow = g.createRadialGradient(cx, H * 0.36, 4, cx, H * 0.36, W * 0.11);
    glow.addColorStop(0, 'rgba(255,214,160,0.95)');
    glow.addColorStop(0.5, 'rgba(230,160,90,0.35)');
    glow.addColorStop(1, 'rgba(120,70,30,0)');
    g.fillStyle = glow; g.fillRect(cx - W * 0.12, 0, W * 0.24, H * 0.7);
  }
  const texture = new THREE.CanvasTexture(canvas);
  texture.mapping = THREE.EquirectangularReflectionMapping;
  texture.colorSpace = THREE.SRGBColorSpace;
  return texture;
}

/** Shader glow for the cased shade: light from the bulb through opal and green glass. */
function glowShader(material: THREE.MeshPhysicalMaterial, uniforms: LampParts['glowUniforms'], tint: string, falloff: number, strength: number, key: string) {
  material.onBeforeCompile = shader => {
    shader.uniforms.lampLevel = uniforms.level;
    shader.uniforms.bulbPosition = uniforms.bulb;
    shader.uniforms.glowTint = { value: new THREE.Color(tint) };
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', '#include <common>\nvarying vec3 vLampWorld;')
      .replace('#include <worldpos_vertex>', '#include <worldpos_vertex>\nvLampWorld = (modelMatrix * vec4(transformed, 1.0)).xyz;');
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <common>', '#include <common>\nvarying vec3 vLampWorld;\nuniform float lampLevel;\nuniform vec3 bulbPosition;\nuniform vec3 glowTint;')
      .replace('#include <emissivemap_fragment>', `#include <emissivemap_fragment>
	{
		// Light scattered by the opal layer, strongest over the bulb and falling off to the ends;
		// seen through more glass at grazing angles, the green deepens.
		float d = distance(vLampWorld, bulbPosition);
		float spread = exp(-d / ${falloff.toFixed(3)});
		float facing = abs(dot(normalize(vViewPosition), normal));
		totalEmissiveRadiance += glowTint * lampLevel * ${strength.toFixed(3)} * spread * mix(0.45, 1.0, facing);
	}`);
  };
  material.customProgramCacheKey = () => `lamp-glow-${key}`;
}

export class Room {
  private lamp?: LampParts;
  private lampLight = new THREE.SpotLight('#ffc98a', 0, 0, 1.16, 0.55, 2);
  /** Light escaping under the shade onto the lamp's own foot and the nearby desk. */
  private lampSpill = new THREE.PointLight('#ffcf98', 0, 1.6, 2);
  private lights?: { hemisphere: THREE.HemisphereLight; sun: THREE.DirectionalLight; bounce: THREE.DirectionalLight };
  private environmentTarget?: THREE.WebGLRenderTarget;
  private probeTarget?: THREE.WebGLRenderTarget;
  private photo?: THREE.Texture;
  private deskMaterial = new THREE.MeshPhysicalMaterial({
    name: 'desk_walnut', color: '#ffffff', roughness: 1, metalness: 0,
    clearcoat: 1, clearcoatRoughness: 0.2, specularIntensity: 0.45, envMapIntensity: 0.9,
    normalScale: new THREE.Vector2(0.55, -0.55),
  });
  private desk = new THREE.Mesh(deskGeometry(), this.deskMaterial);
  // A soft planar reflection of the book and lamp in the polished top, at a quarter of the
  // canvas resolution and blurred: the finish shows them as warm smears, not a mirror.
  private reflection = {
    target: new THREE.WebGLRenderTarget(1, 1, { type: THREE.HalfFloatType }),
    blurTarget: new THREE.WebGLRenderTarget(1, 1, { type: THREE.HalfFloatType }),
    camera: new THREE.PerspectiveCamera(),
    matrix: new THREE.Matrix4(),
    uniforms: { reflectionMap: { value: null as THREE.Texture | null }, reflectionMatrix: { value: new THREE.Matrix4() }, reflectionStrength: { value: 0.85 } },
  };
  private backdrop = new THREE.Mesh(
    new THREE.PlaneGeometry(1, 1),
    new THREE.ShaderMaterial({
      uniforms: {
        map: { value: null as THREE.Texture | null },
        intensity: { value: 0.8 },
        warmth: { value: new THREE.Color(1, 1, 1) },
        uvScale: { value: new THREE.Vector2(1, 1) },
        uvOffset: { value: new THREE.Vector2(0, 0) },
        blur: { value: new THREE.Vector2(0.0016, 0.0028) },
      },
      depthWrite: false,
      vertexShader: 'varying vec2 vUv; void main() { vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
      fragmentShader: `
        uniform sampler2D map; uniform float intensity; uniform vec3 warmth;
        uniform vec2 uvScale; uniform vec2 uvOffset; uniform vec2 blur;
        varying vec2 vUv;
        void main() {
          vec2 uv = vUv * uvScale + uvOffset;
          uv.y = clamp(uv.y, 0.002, 0.998);
          // The library is softly out of focus behind the desk: a small Vogel-disc blur.
          vec3 colour = vec3(0.0);
          for (int i = 0; i < 12; i++) {
            float r = sqrt((float(i) + 0.5) / 12.0);
            float a = float(i) * 2.39996;
            colour += texture2D(map, uv + vec2(cos(a), sin(a)) * r * blur).rgb;
          }
          gl_FragColor = vec4(colour / 12.0 * intensity * warmth, 1.0);
          #include <tonemapping_fragment>
          #include <colorspace_fragment>
        }`,
    }),
  );
  // Contact shadows: the scene's depth just above the desk, seen from below, blurred.
  private contact = {
    target: new THREE.WebGLRenderTarget(1024, 600),
    blurTarget: new THREE.WebGLRenderTarget(1024, 600),
    camera: new THREE.OrthographicCamera(-CONTACT.width / 2, CONTACT.width / 2, CONTACT.depth / 2, -CONTACT.depth / 2, 0, CONTACT.height),
    depth: new THREE.MeshDepthMaterial(),
    horizontal: new FullScreenQuad(new THREE.ShaderMaterial(HorizontalBlurShader)),
    vertical: new FullScreenQuad(new THREE.ShaderMaterial(VerticalBlurShader)),
    plane: new THREE.Mesh(new THREE.PlaneGeometry(CONTACT.width, CONTACT.depth), new THREE.MeshBasicMaterial({
      transparent: true, depthWrite: false, color: '#000000', polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2,
    })),
  };
  private lampOn = false;
  private lampLevel = 0;
  private lampFrom = 0;
  private lampStart = 0;
  private pullStart = 0;
  private clicked = true;
  private raycaster = new THREE.Raycaster();
  private pick = new THREE.Vector2();
  private placement?: Placement;
  private lampCorners: THREE.Vector3[] = [];
  private lampFootprint: boolean[] = [];
  private scratch = { v: new THREE.Vector3(), f: new THREE.Vector3(), color: new THREE.Color(), color2: new THREE.Color(), size: new THREE.Vector2(), zero: new THREE.Matrix4().makeScale(0, 0, 0) };

  constructor(private ctx: RoomContext) {
    this.raycaster.layers.enableAll();
    this.patchDesk();
    this.desk.name = 'Walnut desk';
    this.desk.receiveShadow = true;
    this.desk.frustumCulled = false;
    this.desk.onBeforeRender = (renderer, scene, camera) => this.renderReflection(renderer, scene, camera);
    this.reflection.target.texture.generateMipmaps = this.reflection.blurTarget.texture.generateMipmaps = false;
    this.reflection.uniforms.reflectionMap.value = this.reflection.blurTarget.texture;
    this.backdrop.name = 'Library backdrop';
    this.backdrop.frustumCulled = false;
    this.backdrop.renderOrder = -1000;
    this.backdrop.visible = false;
    this.backdrop.onBeforeRender = (_renderer, _scene, camera) => this.fitBackdrop(camera);
    const { plane, depth, camera, target, blurTarget } = this.contact;
    plane.name = 'Desk contact shadow';
    plane.rotation.x = -Math.PI / 2;
    plane.position.set(CONTACT.x, DESK_Y + 0.0005, CONTACT.z);
    plane.renderOrder = 1;
    plane.material.map = blurTarget.texture;
    plane.material.opacity = 0.9;
    // Seen from below, looking up: the camera's up is world -Z, which flips the image on Z.
    plane.scale.y = -1;
    camera.position.set(CONTACT.x, DESK_Y - 0.002, CONTACT.z);
    camera.rotation.x = Math.PI / 2;
    camera.updateMatrixWorld();
    target.texture.generateMipmaps = blurTarget.texture.generateMipmaps = false;
    depth.depthTest = depth.depthWrite = true;
    depth.side = THREE.DoubleSide;
    depth.onBeforeCompile = shader => {
      shader.uniforms.darkness = { value: 1.25 };
      shader.fragmentShader = `uniform float darkness;\n${shader.fragmentShader.replace(
        'gl_FragColor = vec4( vec3( 1.0 - fragCoordZ ), opacity );',
        // Darkest where a surface touches the desk, fading out over the window's height.
        'float c = 1.0 - fragCoordZ; gl_FragColor = vec4( vec3( 0.0 ), c * c * darkness );',
      )}`;
    };
    if (import.meta.env.DEV) Object.assign(window, { __room: this });
  }

  /** Start loading the room's models and desk textures; resolves when ready (failures are non-fatal). */
  async load(loader: GLTFLoader) {
    const textures = new THREE.TextureLoader();
    const anisotropy = this.ctx.renderer.capabilities.getMaxAnisotropy();
    const map = (name: string, colour = false) => textures.loadAsync(asset(`textures/${name}.webp`)).then(texture => {
      texture.wrapS = texture.wrapT = THREE.RepeatWrapping;
      texture.anisotropy = anisotropy;
      if (colour) texture.colorSpace = THREE.SRGBColorSpace;
      return texture;
    }).catch(error => { console.warn('[book] desk texture', name, error); return undefined; });
    const [lamp, color, normal, rough, coat] = await Promise.all([
      loader.loadAsync(asset('models/lamp.glb')).catch(error => { console.warn('[book] lamp', error); return undefined; }),
      map('desk-color', true), map('desk-normal'), map('desk-rough'), map('desk-coat'),
    ]);
    if (this.ctx.lost()) { [color, normal, rough, coat].forEach(t => t?.dispose()); return; }
    // Tiles: colour 10 x 5 units, pore detail 2.5 x 2.5, polish wear 10 x 10 (desk UVs are in colour tiles).
    if (normal) normal.repeat.set(4, 2);
    if (rough) rough.repeat.set(4, 2);
    if (coat) coat.repeat.set(1, 0.5);
    Object.assign(this.deskMaterial, { map: color ?? null, normalMap: normal ?? null, roughnessMap: rough ?? null, clearcoatRoughnessMap: coat ?? null });
    if (!color) this.deskMaterial.color.set('#4a2e1e');
    this.deskMaterial.needsUpdate = true;
    if (lamp) this.prepareLamp(lamp);
    this.ctx.invalidate();
  }

  /** The photographed library beyond the desk. */
  setBackdrop(texture: THREE.Texture) {
    texture.colorSpace = THREE.SRGBColorSpace;
    texture.wrapS = THREE.ClampToEdgeWrapping;
    texture.wrapT = THREE.ClampToEdgeWrapping;
    this.photo = texture;
    this.backdrop.material.uniforms.map.value = texture;
    this.backdrop.visible = true;
    // The clear colour shows only if the photograph fails; keep it the room's darkest tone.
    this.ctx.scene.background = new THREE.Color('#1c130d');
    if (this.lights) this.buildProbe();
    this.ctx.invalidate();
  }

  resize(_width: number, _height: number) {
    this.positionLamp();
  }

  /**
   * The lamp's bulb is hidden inside its shade, so its mirror image cannot appear in the polished
   * desk as a hot point: keep only a trace of point and spot specular there (the window's stays).
   */
  private patchDesk() {
    this.deskMaterial.onBeforeCompile = shader => {
      const lights = THREE.ShaderChunk.lights_fragment_begin
        .replace('#if ( NUM_POINT_LIGHTS > 0 ) && defined( RE_Direct )', 'roomSpecScale = 0.0;\n#if ( NUM_POINT_LIGHTS > 0 ) && defined( RE_Direct )')
        .replace('#if ( NUM_SUN_LIGHTS > 0 ) && defined( RE_Direct )', 'roomSpecScale = 1.0;\n#if ( NUM_SUN_LIGHTS > 0 ) && defined( RE_Direct )');
      const physical = THREE.ShaderChunk.lights_physical_pars_fragment
        .replace('clearcoatSpecularDirect += ccIrradiance * BRDF_GGX_Clearcoat(', 'clearcoatSpecularDirect += roomSpecScale * ccIrradiance * BRDF_GGX_Clearcoat(')
        .replace('reflectedLight.directSpecular += irradiance * specularBRDF', 'reflectedLight.directSpecular += roomSpecScale * irradiance * specularBRDF');
      Object.assign(shader.uniforms, this.reflection.uniforms);
      shader.vertexShader = shader.vertexShader
        .replace('#include <common>', '#include <common>\nvarying vec3 vDeskWorld;')
        .replace('#include <worldpos_vertex>', '#include <worldpos_vertex>\nvDeskWorld = (modelMatrix * vec4(transformed, 1.0)).xyz;');
      shader.fragmentShader = shader.fragmentShader
        .replace('#include <common>', `#include <common>
float roomSpecScale = 1.0;
varying vec3 vDeskWorld;
uniform sampler2D reflectionMap;
uniform mat4 reflectionMatrix;
uniform float reflectionStrength;`)
        .replace('#include <lights_physical_pars_fragment>', physical)
        .replace('#include <lights_fragment_begin>', lights)
        .replace('#include <opaque_fragment>', `
	{
		// Reflection in the clear coat: Fresnel-weighted, nudged by the pores, fading on worn polish.
		vec4 projected = reflectionMatrix * vec4(vDeskWorld, 1.0);
		vec2 ruv = projected.xy / projected.w + normal.xy * 0.006;
		vec4 mirrored = texture2D(reflectionMap, ruv);
		float cosine = clamp(dot(geometryNormal, geometryViewDir), 0.0, 1.0);
		float fresnel = 0.04 + 0.96 * pow(1.0 - cosine, 5.0);
		float polish = 1.0 - smoothstep(0.12, 0.3, material.clearcoatRoughness);
		outgoingLight += mirrored.rgb * mirrored.a * fresnel * reflectionStrength * mix(0.45, 1.0, polish);
	}
#include <opaque_fragment>`);
    };
    this.deskMaterial.customProgramCacheKey = () => 'room-desk';
    return true;
  }

  /** Lights, environment, the desk, its contact shadows and the backdrop. */
  environment() {
    const { scene, renderer } = this.ctx;
    scene.add(this.desk, this.backdrop, this.contact.plane);

    const pmrem = new THREE.PMREMGenerator(renderer);
    const room = new RoomEnvironment();
    this.environmentTarget = pmrem.fromScene(room, 0.08);
    scene.environment = this.environmentTarget.texture;
    scene.environmentIntensity = 0.45;
    room.dispose();
    pmrem.dispose();

    const hemisphere = new THREE.HemisphereLight('#fff1da', '#5a3a26', 0.8);
    scene.add(hemisphere);
    // Late-afternoon window light from the back left, as in the photograph.
    const sun = new THREE.DirectionalLight('#ffe5c2', 2.6);
    sun.position.set(-3.5, 7, -1.5);
    sun.castShadow = true;
    sun.shadow.mapSize.set(2048, 2048);
    Object.assign(sun.shadow.camera, { left: -6.5, right: 6.5, top: 6.5, bottom: -6.5, near: 0.1, far: 22 });
    sun.shadow.normalBias = 0.003;
    sun.shadow.bias = -0.0001;
    sun.shadow.radius = 3;
    scene.add(sun);
    const bounce = new THREE.DirectionalLight('#f1ddbc', 0.7);
    bounce.position.set(4, 3, 5);
    scene.add(bounce);
    this.lights = { hemisphere, sun, bounce };
    if (this.photo) this.buildProbe();
    this.applyLamp(this.lampLevel);
  }

  private buildProbe() {
    const image = this.photo?.image as (HTMLImageElement | ImageBitmap | undefined);
    if (!image || !image.width) return;
    const pmrem = new THREE.PMREMGenerator(this.ctx.renderer);
    const source = libraryProbe(image);
    this.probeTarget?.dispose();
    this.probeTarget = pmrem.fromEquirectangular(source);
    source.dispose();
    pmrem.dispose();
    this.deskMaterial.envMap = this.probeTarget.texture;
    this.deskMaterial.needsUpdate = true;
    for (const material of this.lamp?.own ?? []) { material.envMap = this.probeTarget.texture; material.needsUpdate = true; }
  }

  /**
   * Keep the photographed room filling the view beyond the desk: a plane far behind it,
   * facing the camera, with the photograph's own desk edge tucked just under the real one.
   * Only the main camera refits it; the loupe and leaf-print cameras see it where it is.
   */
  private fitBackdrop(camera: THREE.Camera) {
    if (camera !== this.ctx.camera) return;
    const cam = this.ctx.camera, { v, f } = this.scratch;
    const distance = cam.far * 0.6;
    const height = 2 * distance * Math.tan(THREE.MathUtils.degToRad(cam.fov / 2));
    const width = height * cam.aspect;
    cam.getWorldDirection(f);
    this.backdrop.position.copy(cam.position).addScaledVector(f, distance);
    this.backdrop.quaternion.copy(cam.quaternion);
    this.backdrop.scale.set(width, height, 1);
    this.backdrop.updateMatrixWorld();
    // Where the desk's back edge crosses the screen, as a fraction from the top.
    v.set(cam.position.x, DESK_Y, DESK_BACK).project(cam);
    const edge = THREE.MathUtils.clamp((1 - v.y) / 2, 0.05, 0.98);
    const pin = edge + 0.012;
    // Photo height as a fraction of the view: never smaller than the approved full-height fit.
    const scale = Math.max(1, pin / PHOTO_DESK_ROW, cam.aspect / PHOTO_ASPECT);
    const top = pin - PHOTO_DESK_ROW * scale;
    const widthFraction = scale * PHOTO_ASPECT / cam.aspect;
    const uniforms = this.backdrop.material.uniforms;
    // Screen (x from left, f from top) -> photo (u, v up): u = (x - 0.5) / wf + 0.5, v = 1 - (f - top) / scale.
    uniforms.uvScale.value.set(1 / widthFraction, 1 / scale);
    uniforms.uvOffset.value.set(0.5 - 0.5 / widthFraction, 1 - (1 - top) / scale);
  }

  /**
   * Mirror the main camera in the desk plane (as three's Reflector does, with an oblique near
   * plane at the desk) and render the scene above the desk into a small target, then blur it.
   * Runs inside the main render, just before the desk is drawn, and only for the main camera.
   */
  private renderReflection(renderer: THREE.WebGLRenderer, scene: THREE.Scene, camera: THREE.Camera) {
    if (camera !== this.ctx.camera || this.ctx.lost()) return;
    const cam = this.ctx.camera, r = this.reflection;
    const size = renderer.getDrawingBufferSize(this.scratch.size);
    const width = Math.max(64, Math.round(size.x / 4)), height = Math.max(64, Math.round(size.y / 4));
    if (r.target.width !== width || r.target.height !== height) { r.target.setSize(width, height); r.blurTarget.setSize(width, height); }
    const normal = new THREE.Vector3(0, 1, 0), point = new THREE.Vector3(0, DESK_Y, 0);
    const eye = new THREE.Vector3().setFromMatrixPosition(cam.matrixWorld);
    if (eye.y <= DESK_Y) return;
    const rotation = new THREE.Matrix4().extractRotation(cam.matrixWorld);
    const look = new THREE.Vector3(0, 0, -1).applyMatrix4(rotation).add(eye);
    const mirror = (p: THREE.Vector3) => p.clone().setY(2 * DESK_Y - p.y);
    const virtual = r.camera;
    virtual.position.copy(mirror(eye));
    virtual.up.set(0, 1, 0).applyMatrix4(rotation).reflect(normal);
    virtual.lookAt(mirror(look));
    virtual.far = cam.far;
    virtual.updateMatrixWorld();
    virtual.projectionMatrix.copy(cam.projectionMatrix);
    r.uniforms.reflectionMatrix.value.set(0.5, 0, 0, 0.5, 0, 0.5, 0, 0.5, 0, 0, 0.5, 0.5, 0, 0, 0, 1)
      .multiply(virtual.projectionMatrix).multiply(virtual.matrixWorldInverse);
    // Oblique near plane at the desk (Lengyel): nothing below the top is reflected.
    const plane = new THREE.Plane().setFromNormalAndCoplanarPoint(normal, point).applyMatrix4(virtual.matrixWorldInverse);
    const clip = new THREE.Vector4(plane.normal.x, plane.normal.y, plane.normal.z, plane.constant);
    const e = virtual.projectionMatrix.elements;
    const q = new THREE.Vector4((Math.sign(clip.x) + e[8]) / e[0], (Math.sign(clip.y) + e[9]) / e[5], -1, (1 + e[10]) / e[14]);
    clip.multiplyScalar(2 / clip.dot(q));
    e[2] = clip.x; e[6] = clip.y; e[10] = clip.z + 1 - 0.003; e[14] = clip.w;
    virtual.projectionMatrixInverse.copy(virtual.projectionMatrix).invert();

    const hidden = [this.desk, this.backdrop, this.contact.plane];
    const visibility = hidden.map(item => item.visible);
    hidden.forEach(item => { item.visible = false; });
    const background = scene.background, autoUpdate = renderer.shadowMap.autoUpdate;
    const clear = renderer.getClearColor(this.scratch.color2), clearAlpha = renderer.getClearAlpha();
    const previous = renderer.getRenderTarget();
    scene.background = null;
    renderer.shadowMap.autoUpdate = false;
    renderer.setClearColor(0x000000, 0);
    renderer.setRenderTarget(r.target);
    renderer.state.buffers.depth.setMask(true);
    renderer.clear();
    renderer.render(scene, virtual);
    const h = this.contact.horizontal.material as THREE.ShaderMaterial, v = this.contact.vertical.material as THREE.ShaderMaterial;
    h.uniforms.tDiffuse.value = r.target.texture; h.uniforms.h.value = 1.6 / width;
    renderer.setRenderTarget(r.blurTarget); this.contact.horizontal.render(renderer);
    v.uniforms.tDiffuse.value = r.blurTarget.texture; v.uniforms.v.value = 1.6 / height;
    renderer.setRenderTarget(r.target); this.contact.vertical.render(renderer);
    h.uniforms.tDiffuse.value = r.target.texture; h.uniforms.h.value = 0.8 / width;
    renderer.setRenderTarget(r.blurTarget); this.contact.horizontal.render(renderer);
    renderer.setRenderTarget(previous);
    renderer.setClearColor(clear, clearAlpha);
    renderer.shadowMap.autoUpdate = autoUpdate;
    scene.background = background;
    hidden.forEach((item, i) => { item.visible = visibility[i]; });
  }

  /** Render the contact-shadow window (call once per frame while the scene changes). */
  private renderContact() {
    const { renderer, scene } = this.ctx;
    const { target, blurTarget, camera, depth, horizontal, vertical, plane } = this.contact;
    const hidden = [this.desk, this.backdrop, plane];
    const visibility = hidden.map(item => item.visible);
    hidden.forEach(item => { item.visible = false; });
    const background = scene.background, override = scene.overrideMaterial;
    const autoUpdate = renderer.shadowMap.autoUpdate, needsUpdate = renderer.shadowMap.needsUpdate;
    const clear = renderer.getClearColor(this.scratch.color), clearAlpha = renderer.getClearAlpha();
    const previous = renderer.getRenderTarget();
    scene.background = null;
    scene.overrideMaterial = depth;
    renderer.shadowMap.autoUpdate = false;
    renderer.shadowMap.needsUpdate = false;
    renderer.setClearColor(0x000000, 0);
    renderer.setRenderTarget(target);
    renderer.clear();
    renderer.render(scene, camera);
    scene.overrideMaterial = override;
    // Two separable blur passes: soft penumbra that widens away from the touching edge.
    const h = horizontal.material as THREE.ShaderMaterial, w = vertical.material as THREE.ShaderMaterial;
    for (const [amount, passes] of [[2.4, 1], [1.2, 1]] as const) {
      for (let i = 0; i < passes; i++) {
        h.uniforms.tDiffuse.value = target.texture; h.uniforms.h.value = amount / target.width;
        renderer.setRenderTarget(blurTarget); horizontal.render(renderer);
        w.uniforms.tDiffuse.value = blurTarget.texture; w.uniforms.v.value = amount / target.height;
        renderer.setRenderTarget(target); vertical.render(renderer);
      }
    }
    h.uniforms.tDiffuse.value = target.texture; h.uniforms.h.value = 0.8 / target.width;
    renderer.setRenderTarget(blurTarget); horizontal.render(renderer);
    renderer.setRenderTarget(previous);
    renderer.setClearColor(clear, clearAlpha);
    renderer.shadowMap.autoUpdate = autoUpdate;
    renderer.shadowMap.needsUpdate = needsUpdate;
    scene.background = background;
    hidden.forEach((item, i) => { item.visible = visibility[i]; });
  }

  /** Brass banker's lamp on the desk, left of the book, with a working pull chain. */
  prepareLamp(gltf: GLTF) {
    const root = gltf.scene;
    root.name = 'Desk lamp';
    const glowUniforms = { level: { value: 0 }, bulb: { value: new THREE.Vector3() } };
    const glass: THREE.MeshPhysicalMaterial[] = [], opal: THREE.MeshPhysicalMaterial[] = [];
    const bulb: THREE.MeshStandardMaterial[] = [], own: THREE.MeshStandardMaterial[] = [];
    const made = new Map<string, THREE.MeshStandardMaterial>();
    const brushed = (colour: string, roughness: number, coat: number) => new THREE.MeshPhysicalMaterial({
      color: colour, metalness: 1, roughness, anisotropy: 0.55, anisotropyRotation: 0,
      clearcoat: coat, clearcoatRoughness: 0.12, envMapIntensity: 1.25,
    });
    const make = (name: string): THREE.MeshStandardMaterial | undefined => {
      if (made.has(name)) return made.get(name);
      let material: THREE.MeshStandardMaterial | undefined;
      if (name === 'lamp_brass') material = brushed('#c9a05a', 0.3, 0.5);
      else if (name === 'lamp_chain') material = brushed('#c8a466', 0.26, 0);
      else if (name === 'lamp_brass_dark') material = brushed('#8a6a3a', 0.42, 0);
      else if (name === 'lamp_glass') {
        // Cased emerald glass: deep, glossy, catching the room; lit, it glows from the opal within.
        const m = new THREE.MeshPhysicalMaterial({
          color: '#0d4a2f', roughness: 0.16, metalness: 0, clearcoat: 1, clearcoatRoughness: 0.03,
          ior: 1.52, specularIntensity: 1, envMapIntensity: 2.2, emissive: '#000000',
        });
        glowShader(m, glowUniforms, '#2f9e5c', 0.24, 1.25, 'glass');
        glass.push(m); material = m;
      } else if (name === 'lamp_opal') {
        const m = new THREE.MeshPhysicalMaterial({ color: '#eee6d6', roughness: 0.42, metalness: 0, sheen: 0.4, sheenColor: '#fff4e0', envMapIntensity: 0.6, side: THREE.DoubleSide });
        glowShader(m, glowUniforms, '#ffe6c0', 0.30, 5.5, 'opal');
        opal.push(m); material = m;
      } else if (name === 'lamp_bulb') {
        const m = new THREE.MeshStandardMaterial({ color: '#fff4dc', roughness: 0.3, emissive: '#ffe0a8', emissiveIntensity: 0 });
        bulb.push(m); material = m;
      } else if (name === 'lamp_felt') {
        material = new THREE.MeshPhysicalMaterial({ color: '#1d2b20', roughness: 1, sheen: 1, sheenColor: '#38513c', sheenRoughness: 0.8 });
      }
      if (material) { material.name = name; made.set(name, material); own.push(material); }
      return material;
    };
    root.traverse(node => {
      if (!(node instanceof THREE.Mesh)) return;
      const source = node.material as THREE.MeshStandardMaterial;
      if (source.name === 'lamp_hit') {
        node.layers.set(PICK_LAYER);
        node.castShadow = node.receiveShadow = false;
        return;
      }
      const material = make(source.name);
      if (material) { node.material = material; source.dispose(); }
      node.castShadow = true;
      node.receiveShadow = true;
      // The lamp's own light sits inside the shade: the shade, socket and bulb must not
      // block it, though they still cast the window's shadow onto the desk.
      // The stem and harp stand directly under the bulb; seen end-on from it, they would throw
      // a hard disc of shadow round the foot that a real (long, horizontal) bulb never makes.
      let group: THREE.Object3D | null = node;
      while (group && !['LampStem', 'LampHarp', 'ChainAnchor'].includes(group.name)) group = group.parent;
      if (['lamp_glass', 'lamp_opal', 'lamp_bulb'].includes(source.name) || group || /^Lamp[ _]chain[ _]guide/.test(node.name)) {
        node.onBeforeShadow = (_r, object, _c, shadowCamera) => {
          if (shadowCamera === this.lampLight.shadow.camera) object.modelViewMatrix.copy(this.scratch.zero);
        };
      }
      if (source.name === 'lamp_bulb') node.castShadow = false;
      // The thin stem's shadow on the foot aliases in the sun's shadow map; the foot keeps its own shading.
      let parent: THREE.Object3D | null = node;
      while (parent && parent.name !== 'LampBase') parent = parent.parent;
      if (parent) node.receiveShadow = false;
    });
    // A sparse cloud of the lamp's own vertices (lamp frame) for the placement solver, with
    // the foot's underside marked as its footprint on the desk.
    root.updateMatrixWorld(true);
    const inverse = root.matrixWorld.clone().invert();
    this.lampCorners = [];
    this.lampFootprint = [];
    root.traverse(node => {
      if (!(node instanceof THREE.Mesh) || !node.layers.isEnabled(0)) return;
      const position = node.geometry.getAttribute('position');
      const step = Math.max(1, Math.floor(position.count / 90));
      const toLamp = inverse.clone().multiply(node.matrixWorld);
      for (let i = 0; i < position.count; i += step) {
        const point = new THREE.Vector3().fromBufferAttribute(position, i).applyMatrix4(toLamp);
        this.lampCorners.push(point);
        this.lampFootprint.push(point.y < 0.02);
      }
    });
    this.ctx.scene.add(root);
    this.lampLight.castShadow = true;
    this.lampLight.shadow.mapSize.set(1024, 1024);
    this.lampLight.shadow.bias = -0.0003;
    this.lampLight.shadow.normalBias = 0.01;
    this.lampLight.shadow.radius = 6;
    this.lampLight.shadow.camera.near = 0.08;
    this.lampLight.shadow.camera.far = 12;
    this.ctx.scene.add(this.lampLight, this.lampLight.target, this.lampSpill);
    this.lamp = {
      root, glowUniforms, glass, opal, bulb, own,
      anchor: root.getObjectByName('LightAnchor'),
      chainAnchor: root.getObjectByName('ChainAnchor'),
      chain: root.getObjectByName('PullChain'),
      shade: root.getObjectByName('LampShade'),
    };
    if (this.probeTarget) for (const material of own) material.envMap = this.probeTarget.texture;
    this.lampOn = Boolean(this.ctx.lampOn);
    this.lampLevel = this.lampFrom = this.lampOn ? 1 : 0;
    this.positionLamp();
    this.applyLamp(this.lampLevel);
  }

  /** Fit the lamp beside the book for this viewport; hide it where it cannot fit (phones). */
  positionLamp() {
    if (!this.lamp) return;
    const canvas = this.ctx.renderer.domElement;
    const width = canvas.clientWidth || 1, height = canvas.clientHeight || 1;
    const aspect = width / height;
    // The decorative header overlaps the top of the canvas; measure it when it is there.
    const header = document.querySelector('.book-header')?.getBoundingClientRect();
    const top = canvas.getBoundingClientRect().top;
    const headerFraction = header ? THREE.MathUtils.clamp((header.bottom - top) / height, 0, 0.4) : 0.1;
    const fit = aspect > 1.15 ? this.placement ?? solvePlacement(aspect, height, headerFraction, this.lampCorners, this.lampFootprint) : undefined;
    // Where it cannot be shown (phones), the lamp still stands just out of view: its light
    // and the dimmed room still answer the Lamp button.
    this.lamp.root.visible = Boolean(fit);
    this.place(fit ?? PREFERRED);
    this.applyLamp(this.lampLevel);
    this.ctx.invalidate();
  }

  private place({ x, z, turn }: Placement) {
    if (!this.lamp) return;
    const root = this.lamp.root;
    root.position.set(x, DESK_Y, z);
    root.rotation.set(0, turn, 0);
    root.updateMatrixWorld(true);
    const origin = this.lamp.anchor ? this.lamp.anchor.getWorldPosition(this.scratch.v).clone() : root.position.clone();
    this.lamp.glowUniforms.bulb.value.copy(origin);
    // The light leaves through the shade's mouth, which leans towards the reader: a virtual
    // source a little below and in front of the bulb, so the stem and foot are lit from the
    // side as by the long bulb and opal lining, not blown out from right above.
    const mouth = new THREE.Vector3(0, -0.1, 0.2).applyAxisAngle(new THREE.Vector3(0, 1, 0), turn);
    this.lampLight.position.copy(origin).add(mouth);
    // About 30 degrees off vertical: an even pool (inverse-square brightest by the foot) that
    // spreads across the left page; the penumbra keeps its rim soft without a hot centre.
    this.lampLight.target.position.set(Math.min(-1.4, x + 1.2), DESK_Y, Math.min(0.2, z + 0.9));
    this.lampLight.target.updateMatrixWorld();
    this.lampSpill.position.copy(origin).add(mouth).add(new THREE.Vector3(0, -0.2, 0));
  }

  /** Room and lamp light for a lamp level between 0 (off) and 1 (on). */
  private applyLamp(level: number) {
    const mix = (off: number, on: number) => off + (on - off) * level;
    if (this.lights) {
      this.lights.hemisphere.intensity = mix(0.8, 0.1);
      this.lights.sun.intensity = mix(2.6, 0.12);
      this.lights.bounce.intensity = mix(0.7, 0.03);
    }
    const uniforms = this.backdrop.material.uniforms;
    uniforms.intensity.value = mix(0.8, 0.13);
    // Lamplight is warmer than the afternoon; the library behind goes amber-brown.
    uniforms.warmth.value.setRGB(1, mix(1, 0.86), mix(1, 0.7));
    this.ctx.scene.environmentIntensity = mix(0.45, 0.05);
    this.deskMaterial.envMapIntensity = mix(0.9, 0.12);
    this.contact.plane.material.opacity = mix(0.9, 0.75);
    for (const material of this.lamp?.own ?? []) {
      if (material.metalness > 0.5) material.envMapIntensity = mix(1.25, 0.22);
    }
    for (const material of this.lamp?.glass ?? []) material.envMapIntensity = mix(2.2, 0.35);
    // The lights stay in the scene at zero instead of toggling visibility: a change in the
    // number of lights would recompile every material, a visible hitch at the click.
    const lit = level > 0.001 && this.lamp ? level : 0;
    this.lampLight.intensity = lit * 30;
    // Off, its shadow map is left alone, but it must exist (receiving materials sample it).
    const shadow = this.lampLight.shadow;
    if (!lit && (shadow.autoUpdate || !shadow.map)) shadow.needsUpdate = true;
    shadow.autoUpdate = lit > 0;
    this.lampSpill.intensity = lit * 0.12;
    if (this.lamp) this.lamp.glowUniforms.level.value = level;
    for (const material of this.lamp?.bulb ?? []) material.emissiveIntensity = level * 9;
  }

  /** True when a point on the stage (-1..1, y down) is over the lamp. */
  lampHit = (x: number, y: number) => {
    if (!this.lamp || this.ctx.lost() || !this.lamp.root.visible) return false;
    this.pick.set(x, -y);
    this.raycaster.setFromCamera(this.pick, this.ctx.camera);
    return this.raycaster.intersectObject(this.lamp.root, true).length > 0;
  };

  /** Pull the chain: it draws out of the socket, clicks, springs back and swings. */
  pullLamp = () => {
    if (!this.lamp || this.ctx.lost()) return;
    const now = performance.now();
    this.pullStart = now;
    this.clicked = false;
    if (this.ctx.reducedMotion()) { this.clicked = true; this.setLampState(!this.lampOn, now); }
    this.ctx.invalidate();
  };

  /** Switch from elsewhere (button, key); the chain still moves. */
  setLamp = (on: boolean) => {
    if (!this.lamp || on === this.lampOn) return;
    this.pullLamp();
  };

  private setLampState(on: boolean, start: number) {
    this.lampOn = on;
    this.lampFrom = this.lampLevel;
    this.lampStart = start;
    this.ctx.onLamp?.(on);
    this.ctx.invalidate();
  }

  /** The chain's pose t ms after a pull: [drop, swing about X, swing about Z], or null when at rest. */
  static chainPose(t: number): [number, number, number] | null {
    const PULL = 150, HOLD = 70;
    const DROP = 0.11;
    if (t < 0) return [0, 0, 0];
    if (t < PULL) {
      const k = t / PULL;
      return [DROP * k * k * (3 - 2 * k), -0.05 * k, 0];
    }
    if (t < PULL + HOLD) return [DROP, -0.05, 0];
    const s = (t - PULL - HOLD) / 1000;
    // Released: the spring takes the slack back with one small overshoot, and the pull
    // swings on its chain like a short pendulum, damped by the socket.
    const drop = DROP * Math.exp(-s * 14) * Math.cos(s * 2 * Math.PI * 3.2);
    const swing = Math.exp(-s / 0.55);
    const x = -0.07 * swing * Math.cos(s * 2 * Math.PI * 1.65);
    const z = 0.022 * swing * Math.sin(s * 2 * Math.PI * 1.65 + 0.6);
    if (s > 3 || (Math.abs(drop) < 1e-4 && swing < 0.02)) return null;
    return [drop, x, z];
  }

  /** Advance the chain, the light and the contact shadows; returns true while still changing. */
  tick(now: number) {
    if (this.lights && !this.ctx.lost()) this.renderContact();
    if (!this.lamp) return false;
    let active = false;
    if (this.pullStart) {
      const t = now - this.pullStart;
      const pose = this.ctx.reducedMotion() ? null : Room.chainPose(t);
      if (!this.clicked && t >= 150) { this.clicked = true; this.setLampState(!this.lampOn, now); }
      const chain = this.lamp.chain, anchor = this.lamp.chainAnchor;
      if (chain && anchor) {
        chain.position.y = -(pose?.[0] ?? 0);
        anchor.rotation.set(pose?.[1] ?? 0, 0, pose?.[2] ?? 0);
      }
      if (pose) active = true; else this.pullStart = 0;
    }
    const target = this.lampOn ? 1 : 0;
    if (this.lampLevel !== target) {
      const span = this.ctx.reducedMotion() ? 1 : this.lampOn ? 650 : 480;
      const t = clamp01((now - this.lampStart) / span);
      // An incandescent filament warms quickly and settles; switching off, it falls away.
      const eased = this.lampOn ? 1 - (1 - t) ** 3 : 1 - (1 - t) ** 2;
      this.lampLevel = t >= 1 ? target : this.lampFrom + (target - this.lampFrom) * eased;
      this.applyLamp(this.lampLevel);
      active = true;
    }
    return active;
  }

  /** Development only: the lamp's bounding box on screen in CSS pixels, padded, for close-ups. */
  lampScreenBox = (pad = 30) => {
    if (!import.meta.env.DEV || !this.lamp) return undefined;
    const box = new THREE.Box3().setFromObject(this.lamp.root);
    const canvas = this.ctx.renderer.domElement.getBoundingClientRect();
    let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
    for (let i = 0; i < 8; i++) {
      const p = new THREE.Vector3(i & 1 ? box.max.x : box.min.x, i & 2 ? box.max.y : box.min.y, i & 4 ? box.max.z : box.min.z).project(this.ctx.camera);
      const sx = canvas.left + (p.x + 1) / 2 * canvas.width, sy = canvas.top + (1 - p.y) / 2 * canvas.height;
      x0 = Math.min(x0, sx); x1 = Math.max(x1, sx); y0 = Math.min(y0, sy); y1 = Math.max(y1, sy);
    }
    const x = Math.max(0, x0 - pad), y = Math.max(0, y0 - pad);
    return { x, y, width: x1 - x0 + pad * 2, height: y1 - y0 + pad * 2 };
  };

  /** Development only: hold the chain at its pose t ms after a pull, for frame inspection. */
  inspectChain = (t: number) => {
    if (!import.meta.env.DEV || !this.lamp?.chain || !this.lamp.chainAnchor) return;
    const pose = Room.chainPose(t) ?? [0, 0, 0];
    this.lamp.chain.position.y = -pose[0];
    this.lamp.chainAnchor.rotation.set(pose[1], 0, pose[2]);
    this.ctx.invalidate();
  };

  /** Development only: move the lamp to try a placement (turn in radians); scale is ignored. */
  inspectLamp = (x: number, z: number, _scale: number, turn: number) => {
    if (!import.meta.env.DEV || !this.lamp) return;
    this.placement = { x, z, turn };
    this.place(this.placement);
    this.ctx.invalidate();
  };

  dispose() {
    this.environmentTarget?.dispose();
    this.probeTarget?.dispose();
    const { target, blurTarget, horizontal, vertical, depth, plane } = this.contact;
    target.dispose(); blurTarget.dispose(); horizontal.dispose(); vertical.dispose(); depth.dispose();
    plane.geometry.dispose(); plane.material.dispose();
    this.reflection.target.dispose(); this.reflection.blurTarget.dispose();
    this.desk.geometry.dispose();
    for (const texture of [this.deskMaterial.map, this.deskMaterial.normalMap, this.deskMaterial.roughnessMap, this.deskMaterial.clearcoatRoughnessMap]) texture?.dispose();
    this.deskMaterial.dispose();
    this.backdrop.geometry.dispose();
    this.backdrop.material.dispose();
  }
}
