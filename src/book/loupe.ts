import * as THREE from 'three';

/**
 * The magnifying loupe: a brass-rimmed reading glass on a turned wooden handle,
 * drawn in 3D over the scene. The lens shows the live scene re-rendered
 * through a narrow window of the main camera, so everything behind the book,
 * the room included, is magnified where it really is.
 * Owned by the Interaction agent (docs/INTERACTION.md).
 */
const MARGIN = 1.1; // the magnified view covers a little more than the lens, for the refraction at its rim

type State = { active: boolean; x: number; y: number; radius: number; zoom: number; touch: boolean };

function woodGrain() {
  // Turned walnut: long grain along the handle with faint growth rings, generated once.
  const canvas = document.createElement('canvas');
  canvas.width = 256; canvas.height = 1024;
  const ctx = canvas.getContext('2d')!;
  const gradient = ctx.createLinearGradient(0, 0, 256, 0);
  gradient.addColorStop(0, '#3b2416'); gradient.addColorStop(0.5, '#4d2f1c'); gradient.addColorStop(1, '#3b2416');
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, 256, 1024);
  let seed = 7;
  const random = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
  for (let i = 0; i < 90; i++) {
    const x = random() * 256, width = 0.6 + random() * 2.4, wave = 3 + random() * 9, phase = random() * 6;
    ctx.strokeStyle = random() > 0.5 ? `rgba(24, 12, 6, ${0.18 + random() * 0.3})` : `rgba(122, 78, 44, ${0.12 + random() * 0.2})`;
    ctx.lineWidth = width;
    ctx.beginPath();
    for (let y = 0; y <= 1024; y += 16) ctx.lineTo(x + Math.sin(y / 140 + phase) * wave, y);
    ctx.stroke();
  }
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.wrapS = texture.wrapT = THREE.RepeatWrapping;
  return texture;
}

/** Revolve a profile of [radius, height] points around the Y axis. */
const lathe = (profile: [number, number][], segments = 96) =>
  new THREE.LatheGeometry(profile.map(([r, y]) => new THREE.Vector2(r, y)), segments);

/** A rounded profile: corners [r, y] with a fillet, sampled smoothly. */
function rounded(points: [number, number][], radius: number, steps = 6): [number, number][] {
  const out: [number, number][] = [points[0]];
  for (let i = 1; i < points.length - 1; i++) {
    const [px, py] = points[i - 1], [cx, cy] = points[i], [nx, ny] = points[i + 1];
    const a = Math.hypot(cx - px, cy - py), b = Math.hypot(nx - cx, ny - cy);
    const r = Math.min(radius, a / 2, b / 2);
    const s: [number, number] = [cx + (px - cx) / a * r, cy + (py - cy) / a * r];
    const e: [number, number] = [cx + (nx - cx) / b * r, cy + (ny - cy) / b * r];
    for (let k = 0; k <= steps; k++) {
      const t = k / steps, u = 1 - t;
      out.push([u * u * s[0] + 2 * u * t * cx + t * t * e[0], u * u * s[1] + 2 * u * t * cy + t * t * e[1]]);
    }
  }
  out.push(points[points.length - 1]);
  return out;
}

export class Loupe {
  state: State = { active: false, x: 0, y: 0, radius: 120, zoom: 2.5, touch: false };
  private target?: THREE.WebGLRenderTarget;
  private viewCamera = new THREE.PerspectiveCamera();
  private overlayCamera = new THREE.OrthographicCamera(0, 1, 0, -1, -4000, 4000);
  private overlay = new THREE.Scene();
  private rig = new THREE.Group();
  private handle = new THREE.Group();
  private lens?: THREE.Mesh<THREE.CircleGeometry, THREE.ShaderMaterial>;
  private shadow?: THREE.Mesh<THREE.PlaneGeometry, THREE.ShaderMaterial>;
  private disposables: { dispose(): void }[] = [];
  private angle = -0.7;

  constructor(private renderer: THREE.WebGLRenderer, private scene: THREE.Scene, private camera: THREE.PerspectiveCamera,
    private element: HTMLElement, private invalidate: () => void) {}

  get active() { return this.state.active; }

  /** Show the loupe at stage pixel (x, y), or hide it. `touch` floats it above a finger, handle down. */
  set = (active: boolean, x = this.state.x, y = this.state.y, radius = this.state.radius, touch = this.state.touch) => {
    Object.assign(this.state, { active, x, y, radius, touch });
    if (active && !this.lens) this.build();
    this.invalidate();
  };

  private build() {
    // The glass: the magnified view with a little refraction, colour fringe, vignette and reflection at the rim.
    const lensMaterial = new THREE.ShaderMaterial({
      uniforms: { map: { value: null }, margin: { value: MARGIN } },
      depthTest: false,
      depthWrite: false,
      vertexShader: 'varying vec2 vUv; void main() { vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
      fragmentShader: /* glsl */`
        uniform sampler2D map;
        uniform float margin;
        varying vec2 vUv;
        vec3 view(vec2 c) { return texture2D(map, c / margin * 0.5 + 0.5).rgb; }
        void main() {
          vec2 c = vUv * 2.0 - 1.0;
          float d = length(c);
          // A plano-convex lens: nearly distortion-free in the middle, bending light more towards the rim.
          vec2 bent = c * (1.0 - 0.035 * d * d - 0.075 * pow(d, 8.0));
          // Lateral colour: red and blue land slightly apart at the rim.
          float fringe = 0.0045 * pow(d, 6.0);
          vec3 colour = vec3(view(bent * (1.0 + fringe)).r, view(bent).g, view(bent * (1.0 - fringe)).b);
          // Glass: a breath of warmth, light falling off towards the rim and the dark ground edge.
          colour *= vec3(1.0, 0.992, 0.975);
          colour *= 1.0 - 0.22 * smoothstep(0.62, 1.0, d);
          colour *= 1.0 - 0.45 * smoothstep(0.955, 1.0, d);
          // Reflections of the room's window: a soft broad sheen and a thin bright arc at the upper left.
          vec2 w = c - vec2(-0.36, 0.42);
          float sheen = exp(-dot(w * vec2(1.0, 1.7), w * vec2(1.0, 1.7)) * 5.5);
          float arc = smoothstep(0.83, 0.9, d) * smoothstep(0.98, 0.92, d) * pow(max(0.0, dot(normalize(c + 1e-5), vec2(-0.62, 0.78))), 6.0);
          float lower = smoothstep(0.86, 0.95, d) * smoothstep(1.0, 0.95, d) * pow(max(0.0, dot(normalize(c + 1e-5), vec2(0.6, -0.8))), 8.0);
          colour += vec3(1.0, 0.97, 0.9) * (0.07 * sheen + 0.32 * arc + 0.08 * lower);
          gl_FragColor = vec4(colour, 1.0);
          #include <tonemapping_fragment>
          #include <colorspace_fragment>
        }`,
    });
    // The magnified view is rendered linear into a half-float target, so the lens applies
    // tone mapping and the output colour space once, exactly as the main frame does.
    this.lens = new THREE.Mesh(new THREE.CircleGeometry(1, 128), lensMaterial);
    this.lens.renderOrder = 1;

    // A soft shadow of rim and handle on the page, offset away from the window light.
    const shadowMaterial = new THREE.ShaderMaterial({
      uniforms: { angle: { value: this.angle }, strength: { value: 0.3 } },
      transparent: true,
      depthTest: false,
      depthWrite: false,
      vertexShader: 'varying vec2 vP; void main() { vP = position.xy; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
      fragmentShader: /* glsl */`
        uniform float angle;
        uniform float strength;
        varying vec2 vP;
        float capsule(vec2 p, vec2 a, vec2 b, float r) {
          vec2 pa = p - a, ba = b - a;
          float h = clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0);
          return length(pa - ba * h) - r;
        }
        void main() {
          vec2 p = vP - vec2(0.16, -0.24);
          float ring = abs(length(p) - 1.08) - 0.07;
          vec2 dir = vec2(cos(angle), sin(angle));
          float grip = capsule(p, dir * 1.15, dir * 2.85, 0.14);
          float shape = min(ring, grip);
          float shade = 1.0 - smoothstep(-0.06, 0.22, shape);
          // The glass itself casts only a faint shadow, brighter at its centre where it focuses light.
          float glass = (1.0 - smoothstep(0.9, 1.05, length(p))) * 0.25;
          gl_FragColor = vec4(0.06, 0.035, 0.02, strength * max(shade, glass));
        }`,
    });
    this.shadow = new THREE.Mesh(new THREE.PlaneGeometry(7, 7), shadowMaterial);
    this.shadow.renderOrder = 0;

    const brass = new THREE.MeshPhysicalMaterial({ name: 'loupe brass', side: THREE.DoubleSide, color: '#c99c50', metalness: 1, roughness: 0.24, clearcoat: 0.35, clearcoatRoughness: 0.18, envMapIntensity: 1.25 });
    const darkBrass = new THREE.MeshPhysicalMaterial({ name: 'loupe brass, inner', side: THREE.DoubleSide, color: '#7d5c2c', metalness: 1, roughness: 0.4, envMapIntensity: 0.9 });
    const grain = woodGrain();
    const wood = new THREE.MeshPhysicalMaterial({ name: 'loupe walnut', map: grain, color: '#ffffff', roughness: 0.42, clearcoat: 0.7, clearcoatRoughness: 0.22, sheen: 0.2, sheenColor: '#8a5a34', envMapIntensity: 0.8 });

    // Bezel: a turned brass ring with a bevelled face, a rolled outer edge and a dark seat for the glass.
    const bezel = new THREE.Mesh(lathe(rounded([
      [0.975, -0.05], [0.975, 0.04], [1.03, 0.115], [1.14, 0.125], [1.175, 0.06], [1.17, -0.07], [1.0, -0.08],
    ], 0.035, 8), 160), brass);
    const seat = new THREE.Mesh(lathe([[0.965, 0.0], [0.985, 0.045], [1.0, 0.05]], 160), darkBrass);
    for (const ring of [bezel, seat]) { ring.rotation.x = Math.PI / 2; this.rig.add(ring); }

    // Handle, along +Y of its own group: brass neck and collar, ferrule, turned walnut grip, brass end cap.
    const neck = new THREE.Mesh(lathe(rounded([
      [0, 1.13], [0.07, 1.13], [0.065, 1.27], [0.1, 1.29], [0.1, 1.33], [0.075, 1.35], [0.075, 1.4], [0, 1.4],
    ], 0.012, 4), 48), brass);
    const ferrule = new THREE.Mesh(lathe(rounded([
      [0, 1.39], [0.112, 1.39], [0.118, 1.42], [0.105, 1.445], [0.118, 1.47], [0.118, 1.58], [0.105, 1.6], [0.118, 1.625], [0.112, 1.65], [0, 1.65],
    ], 0.01, 4), 64), brass);
    const grip = new THREE.Mesh(lathe(rounded([
      [0, 1.64], [0.108, 1.64], [0.13, 1.7], [0.116, 1.76], [0.128, 1.82], [0.15, 2.1], [0.152, 2.3], [0.135, 2.55], [0.11, 2.68], [0.118, 2.72], [0.1, 2.76], [0, 2.77],
    ], 0.03, 6), 64), wood);
    grip.geometry.attributes.uv.array.forEach((_, i, array) => { if (i % 2 === 1) (array as Float32Array)[i] *= 2.5; });
    const cap = new THREE.Mesh(lathe(rounded([[0, 2.765], [0.08, 2.765], [0.085, 2.79], [0.05, 2.82], [0, 2.825]], 0.015, 4), 48), brass);
    this.handle.add(neck, ferrule, grip, cap);
    this.rig.add(this.handle);

    // Light from the window at the upper left, a warm fill, and the room's own reflections.
    const key = new THREE.DirectionalLight('#fff1dc', 2.4);
    key.position.set(-0.6, 0.8, 1);
    const rim = new THREE.DirectionalLight('#ffd9a8', 0.8);
    rim.position.set(0.8, -0.5, 0.6);
    this.overlay.add(new THREE.HemisphereLight('#fff4e2', '#3a2416', 0.7), key, rim, this.shadow, this.lens, this.rig);

    this.disposables.push(lensMaterial, shadowMaterial, brass, darkBrass, wood, grain, this.lens.geometry, this.shadow.geometry,
      bezel.geometry, seat.geometry, neck.geometry, ferrule.geometry, grip.geometry, cap.geometry);
  }

  /** Render the magnified window and the glass itself after the main frame. */
  render() {
    if (!this.state.active || !this.lens || !this.shadow) return;
    const width = this.element.clientWidth, height = this.element.clientHeight;
    const { x, y, radius, zoom, touch } = this.state;
    // Render at the canvas's own density (crisp on 2x screens), with a margin for the refraction.
    const ratio = this.renderer.getPixelRatio();
    const pixels = Math.min(2048, Math.ceil(radius * 2 * MARGIN * ratio));
    if (!this.target || this.target.width !== pixels) {
      this.target?.dispose();
      this.target = new THREE.WebGLRenderTarget(pixels, pixels, { type: THREE.HalfFloatType, samples: 4 });
      this.lens.material.uniforms.map.value = this.target.texture;
    }
    const span = radius * 2 * MARGIN / zoom;
    this.viewCamera.copy(this.camera);
    this.viewCamera.setViewOffset(width, height, x - span / 2, y - span / 2, span, span);
    this.viewCamera.updateProjectionMatrix();
    // A screen-space photograph behind the scene must be cropped to the same window.
    const background = this.scene.background instanceof THREE.Texture && !(this.scene.background as THREE.CubeTexture).isCubeTexture
      ? this.scene.background : null;
    const saved = background ? { offset: background.offset.clone(), repeat: background.repeat.clone() } : null;
    if (background && saved) {
      background.offset.set(saved.offset.x + saved.repeat.x * (x - span / 2) / width, saved.offset.y + saved.repeat.y * (1 - (y + span / 2) / height));
      background.repeat.set(saved.repeat.x * span / width, saved.repeat.y * span / height);
    }
    const previous = this.renderer.getRenderTarget();
    this.renderer.setRenderTarget(this.target);
    this.renderer.render(this.scene, this.viewCamera);
    this.renderer.setRenderTarget(previous);
    if (background && saved) { background.offset.copy(saved.offset); background.repeat.copy(saved.repeat); }

    // The glass, in stage pixels (y up is negative), scaled by its radius.
    Object.assign(this.overlayCamera, { left: 0, right: width, top: 0, bottom: -height });
    this.overlayCamera.updateProjectionMatrix();
    // Held from below and to the right by a mouse hand; straight below the lens above a finger.
    this.angle = touch ? -1.32 : -0.72;
    this.handle.rotation.set(0, 0, this.angle - Math.PI / 2);
    // The grip comes up toward the eye a little, so its turned shape catches the light.
    this.handle.rotateX(0.32);
    this.shadow.material.uniforms.angle.value = this.angle;
    this.rig.position.set(x, -y, 0);
    this.rig.scale.setScalar(radius);
    this.lens.position.set(x, -y, 0);
    this.lens.scale.setScalar(radius);
    this.shadow.position.set(x, -y, 0);
    this.shadow.scale.setScalar(radius);
    this.overlay.environment = this.scene.environment;
    const autoClear = this.renderer.autoClear;
    this.renderer.autoClear = false;
    this.renderer.clearDepth();
    this.renderer.render(this.overlay, this.overlayCamera);
    this.renderer.autoClear = autoClear;
  }

  dispose() {
    this.target?.dispose();
    this.disposables.forEach(item => item.dispose());
  }
}
