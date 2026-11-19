import * as THREE from 'three';
import { GLTFLoader, type GLTF } from 'three/addons/loaders/GLTFLoader.js';
import type { BookSnapshot, Chapter } from '../types';
import { ENTER_DURATION, TURN_DURATION, TURN_LEAF_START, clamp01, interval, entrancePose, incomingWriting, progressForTravel, turnPose, validDestination } from './motion';
import { Leaf, deformDepthMaterial, deformMaterial, makeLeafFrontMaterial, makeLeafUniforms, sampleRestSurface, shadePageUnderLeaf, travelForTip } from './leaf';
import { makePaperText } from './paper';
import { FrameLoop } from './frameLoop';
import { Room } from './room';
import { Loupe } from './loupe';
import { loadBookTextures, prepareMaterials, type BookTextures } from './materials';

/** mode: 0 at rest, 1 riding on the leaf, 2 pressed under it (see leaf.ts). */
type Rig = { gltf: GLTF; mixer: THREE.AnimationMixer; action?: THREE.AnimationAction; mode: { value: number } };
type Writing = ReturnType<typeof makePaperText>;
/** Leaf clearance over the reading panel below which the panel hides under the leaf's print. */
const PANEL_CLEARANCE = 0.03;
/** A click turn holds the page near its front corner. */
const CLICK_GRAB = 0.85;
type Options = {
  chapters: Chapter[];
  initialChapter?: number;
  reducedMotion: boolean;
  onChange: (snapshot: BookSnapshot) => void;
  onRustle: () => void;
  /** The desk lamp was switched by its pull chain (or setLamp). */
  onLamp?: (on: boolean) => void;
  lampOn?: boolean;
};

const asset = (path: string) => `${import.meta.env.BASE_URL}${path.replace(/^\//, '')}`;
const axisY = new THREE.Vector3(0, 1, 0);
const axisX = new THREE.Vector3(1, 0, 0);
const initialRotation = new THREE.Quaternion().setFromAxisAngle(axisY, Math.PI / 2)
  .multiply(new THREE.Quaternion().setFromAxisAngle(axisX, -Math.PI / 2));
const coverRotation = new THREE.Quaternion().setFromAxisAngle(axisX, Math.PI / 2);
const flatRotation = new THREE.Quaternion();

export class BookScene {
  private renderer: THREE.WebGLRenderer;
  private scene = new THREE.Scene();
  private camera = new THREE.PerspectiveCamera(32, 1, 0.05, 80);
  private group = new THREE.Group();
  private loader = new GLTFLoader();
  private book?: GLTF;
  private bookMixer?: THREE.AnimationMixer;
  private openAction?: THREE.AnimationAction;
  private readingAction?: THREE.AnimationAction;
  private readingHinge?: THREE.Object3D;
  private turnPage?: THREE.Object3D;
  private currentRig?: Rig;
  private nextRig?: Rig;
  private text?: Writing;
  private nextText?: Writing;
  private leaf?: Leaf;
  private leafUniforms = makeLeafUniforms();
  /** A second reading panel that lies on the leaf's back while it turns, with its writing. */
  private leafHinge = new THREE.Group();
  private leafPanelMode = { value: 0 };
  private manual = false;
  /** Drag: the turn progress the hand asks for, and the progress the page has reached. */
  private manualTarget = 0;
  private manualProgress = 0;
  private manualSettling = false;
  private dragStart = 0;
  private grab = CLICK_GRAB;
  private grabX = 0;
  private dragPlane = new THREE.Plane(new THREE.Vector3(0, 1, 0), -0.3);
  private raycaster = new THREE.Raycaster();
  private resumeProgress = 0;
  private revertFrom: number | null = null;
  private revertStart = 0;
  private cache = new Map<number, Promise<Rig>>();
  private textures: THREE.Texture[] = [];
  private released = new WeakSet<object>();
  private graphicsLost = false;
  private textIndex = -1;
  private inspectionProgress: number | null = null;
  private observer: ResizeObserver;
  private loop = new FrameLoop(now => this.tick(now));
  private hiddenAt: number | null = null;
  private disposed = false;
  private lastFrame = 0;
  private motionStart = 0;
  private nextIndex = 0;
  private direction = 1;
  private entry = 0;
  private turningProgress = 0;
  private pointer = new THREE.Vector2();
  private cameraOffset = new THREE.Vector2();
  private look = new THREE.Vector3();
  // The book is held: it tilts after the hand on a soft spring, lifting off the
  // desk as it does, and its paper pieces flex a little with the motion.
  private basePosition = new THREE.Vector3();
  private baseQuaternion = new THREE.Quaternion();
  private tilt = new THREE.Vector2();
  private tiltVelocity = new THREE.Vector2();
  private flex = 0;
  private flexVelocity = 0;
  private tiltQuaternion = new THREE.Quaternion();
  private tiltEuler = new THREE.Euler();
  private bookTextures: BookTextures = {};
  /** A faint light that follows the pointer, so the paper's sheen moves with the hand. */
  private sheenLight = new THREE.PointLight('#fff1dc', 0, 7, 2);
  private sheenPosition = new THREE.Vector3();
  private room: Room;
  private loupe: Loupe;
  private metrics = { totalFrames: 0, frames: 0, seconds: 0, fps: 0, drawCalls: 0, triangles: 0, longestFrameMs: 0 };
  private motionFrames: number[] = [];
  state: BookSnapshot = { phase: 'loading', chapter: 0, progress: 0 };

  constructor(private element: HTMLElement, private options: Options) {
    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, powerPreference: 'high-performance' });
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.02;
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFShadowMap;
    this.renderer.setClearColor('#30231b');
    this.renderer.domElement.setAttribute('aria-hidden', 'true');
    this.element.append(this.renderer.domElement);
    this.renderer.domElement.addEventListener('webglcontextlost', this.contextLost);
    this.scene.background = new THREE.Color('#30231b');
    this.scene.add(this.group);
    // Always present (at zero when unused): adding a light later would recompile every material.
    this.scene.add(this.sheenLight);
    this.room = new Room({
      scene: this.scene, renderer: this.renderer, camera: this.camera,
      invalidate: () => this.loop.invalidate(), reducedMotion: () => this.options.reducedMotion,
      lost: () => this.disposed || this.graphicsLost, onLamp: options.onLamp, lampOn: options.lampOn,
    });
    this.loupe = new Loupe(this.renderer, this.scene, this.camera, element, () => this.loop.invalidate());
    this.observer = new ResizeObserver(this.resize);
    this.observer.observe(element);
    this.resize();
    document.addEventListener('visibilitychange', this.visibilityChanged);
    this.visibilityChanged();
  }

  async init() {
    try {
      const initialChapter = this.options.initialChapter ?? 0;
      const texturesReady = this.loadTextures();
      // The room's props are decoration: if they fail to load, the book still opens.
      const roomReady = this.room.load(this.loader);
      const bookReady = this.loader.loadAsync(asset('models/book.glb')).then(book => {
        if (this.disposed || this.graphicsLost) this.disposeObject(book.scene);
        else this.book = book;
        return book;
      });
      const [book, initialRig] = await Promise.all([
        bookReady,
        this.loadChapter(initialChapter, texturesReady),
        Promise.all([
        document.fonts.load('400 64px "Cormorant Garamond"'),
        document.fonts.load('500 91px "Cormorant Garamond"'),
        document.fonts.load('italic 500 63px "Cormorant Garamond"'),
        document.fonts.load('500 34px Inter'),
        texturesReady,
        ]),
      ]);
      if (this.disposed || this.graphicsLost) return;
      this.room.environment();
      this.publish({ progress: 0.25 });
      this.prepareMaterials(book.scene);
      await roomReady;
      this.group.add(book.scene);
      this.bookMixer = new THREE.AnimationMixer(book.scene);
      this.openAction = this.action(this.bookMixer, book.animations, 'open');
      this.readingAction = this.action(this.bookMixer, book.animations, 'reading');
      this.readingHinge = book.scene.getObjectByName('ReadingHinge');
      if (!this.openAction || !this.readingAction || !this.readingHinge) throw new Error('The book animations could not be loaded.');
      // The baked TurnPage morph is no longer used: the leaf is bent at runtime.
      this.turnPage = book.scene.getObjectByName('TurnPage');
      this.prepareLeaf(book.scene);
      if (this.turnPage) this.turnPage.visible = false;
      this.preparePages(book.scene);
      await this.precompileLeaf();
      this.sample(this.openAction, 0);
      this.sample(this.readingAction, 0);
      this.bookMixer.update(0);
      this.publish({ progress: 0.65 });
      this.currentRig = initialRig;
      if (this.disposed || this.graphicsLost) return;
      this.group.add(this.currentRig.gltf.scene);
      this.currentRig.gltf.scene.visible = false;
      this.setPopup(this.currentRig, 0);
      this.setText(initialChapter);
      this.text!.visible = false;
      this.poseEntrance(0);
      this.publish({ phase: 'closed', chapter: initialChapter, progress: 1 });
      this.prefetch(initialChapter);
      if (this.options.reducedMotion || this.options.initialChapter !== undefined) this.enter(true);
    } catch (error) {
      if (!this.disposed && !this.graphicsLost) this.publish({ phase: 'error', error: this.errorMessage(error) });
    }
  }

  private errorMessage(error: unknown) {
    const message = error instanceof Error ? error.message : 'The 3D book is unavailable.';
    console.warn('[book]', message);
    return 'The 3D edition could not load. You can still read the illustrated edition.';
  }

  private async loadTextures() {
    const textures = await loadBookTextures(this.renderer, texture => {
      if (this.disposed || this.graphicsLost) texture.dispose();
      else this.textures.push(texture);
    });
    if (this.disposed || this.graphicsLost) return;
    this.bookTextures = textures;
    if (textures.backdrop) this.room.setBackdrop(textures.backdrop);
    this.resize();
  }

  private prepareMaterials(object: THREE.Object3D, cardStock = false) {
    prepareMaterials(object, this.bookTextures, cardStock);
  }

  private action(mixer: THREE.AnimationMixer, clips: THREE.AnimationClip[], name: string) {
    const clip = clips.find(clip => clip.name.toLowerCase() === name || clip.name.toLowerCase().endsWith(`|${name}`));
    if (!clip) return undefined;
    const action = mixer.clipAction(clip);
    action.setLoop(THREE.LoopOnce, 1);
    action.clampWhenFinished = true;
    action.play();
    action.paused = true;
    return action;
  }

  private sample(action: THREE.AnimationAction | undefined, progress: number) {
    if (!action) return;
    action.enabled = true;
    action.paused = true;
    action.time = clamp01(progress) * action.getClip().duration;
  }

  private loadChapter(index: number, materialsReady: Promise<void> = Promise.resolve()): Promise<Rig> {
    const existing = this.cache.get(index);
    if (existing) return existing;
    const promise = this.loader.loadAsync(asset(this.options.chapters[index].scene)).then(async gltf => {
      try { await materialsReady; }
      catch (error) { this.disposeObject(gltf.scene); throw error; }
      if (this.disposed || this.graphicsLost) { this.disposeObject(gltf.scene); throw new Error('Book unavailable'); }
      this.prepareMaterials(gltf.scene, true);
      const mixer = new THREE.AnimationMixer(gltf.scene);
      const action = this.action(mixer, gltf.animations, 'unfold');
      if (!action) { this.disposeObject(gltf.scene); throw new Error(`Missing unfold animation: chapter ${index + 1}`); }
      const rig: Rig = { gltf, mixer, action, mode: { value: 0 } };
      // Every piece can ride on the turning leaf, or be pressed flat beneath it, as real geometry.
      const depth = deformDepthMaterial(this.leafUniforms, rig.mode);
      gltf.scene.traverse(node => {
        if (!(node instanceof THREE.Mesh)) return;
        for (const material of Array.isArray(node.material) ? node.material : [node.material]) deformMaterial(material, this.leafUniforms, rig.mode);
        node.customDepthMaterial = depth;
      });
      this.setPopup(rig, 0);
      // Compile the scene's shaders before it is needed, so its first turn does not stall.
      try { await this.renderer.compileAsync(gltf.scene, this.camera, this.scene); }
      catch { /* compiled lazily instead */ }
      return rig;
    }).catch(error => {
      if (this.cache.get(index) === promise) this.cache.delete(index);
      throw error;
    });
    this.cache.set(index, promise);
    return promise;
  }

  /**
   * Build the runtime leaf over the right page. Its rest shape is sampled from
   * the page mesh itself, so it follows whatever binding the book model has.
   */
  private prepareLeaf(book: THREE.Object3D) {
    const page = this.firstMesh(book.getObjectByName('RightPage'));
    if (!page) return;
    this.group.updateMatrixWorld(true);
    const toBook = new THREE.Matrix4().copy(this.group.matrixWorld).invert().multiply(page.matrixWorld);
    const pageBox = new THREE.Box3().setFromBufferAttribute(page.geometry.attributes.position as THREE.BufferAttribute).applyMatrix4(toBook);
    // The old TurnPage footprint, if present, is the authored leaf size.
    const turn = this.firstMesh(this.turnPage);
    const leafBox = turn ? new THREE.Box3().setFromBufferAttribute(turn.geometry.attributes.position as THREE.BufferAttribute)
      .applyMatrix4(new THREE.Matrix4().copy(this.group.matrixWorld).invert().multiply(turn.matrixWorld)) : undefined;
    const bounds = {
      x0: Math.max(0.012, leafBox?.min.x ?? pageBox.min.x + 0.002),
      x1: Math.min(pageBox.max.x - 0.002, leafBox?.max.x ?? pageBox.max.x - 0.002),
      z0: Math.max(pageBox.min.z + 0.004, leafBox?.min.z ?? pageBox.min.z + 0.01),
      z1: Math.min(pageBox.max.z - 0.004, leafBox?.max.z ?? pageBox.max.z - 0.01),
    };
    const rest = sampleRestSurface(page, toBook, bounds);
    // Each face is its page's own paper, mapped as that page maps it, so the
    // hand-over between page and leaf is invisible. The left page is measured open.
    const pageMaterial = Array.isArray(page.material) ? page.material[0] : page.material;
    const frontUv = this.fitPageUv(page, toBook);
    const left = this.firstMesh(book.getObjectByName('LeftPage'));
    this.sample(this.openAction, 1);
    this.bookMixer?.update(0);
    this.group.updateMatrixWorld(true);
    const leftMaterial = left ? (Array.isArray(left.material) ? left.material[0] : left.material) : pageMaterial;
    const backUv = left ? this.fitPageUv(left, new THREE.Matrix4().copy(this.group.matrixWorld).invert().multiply(left.matrixWorld)) : undefined;
    const edgeColour = pageMaterial instanceof THREE.MeshStandardMaterial ? pageMaterial.color.clone().multiplyScalar(0.92) : new THREE.Color('#cdb894');
    const gutter = { value: 1 };
    this.leaf = new Leaf(rest, {
      front: makeLeafFrontMaterial(pageMaterial, gutter),
      back: makeLeafFrontMaterial(leftMaterial, gutter),
      edge: new THREE.MeshStandardMaterial({ name: 'leaf edge', color: edgeColour, roughness: 0.92, side: THREE.DoubleSide }),
    }, frontUv, backUv);
    this.leafGutter = gutter;
    this.group.add(this.leaf.group);
    // The leaf's own reading panel: a copy of the book's, placed where the real one lies flat.
    const panel = book.getObjectByName('ReadingPanel');
    if (this.readingHinge && panel) {
      this.sample(this.readingAction, 0);
      this.bookMixer?.update(0);
      this.readingHinge.parent?.add(this.leafHinge);
      this.leafHinge.position.copy(this.readingHinge.position);
      this.leafHinge.quaternion.copy(this.readingHinge.quaternion);
      this.leafHinge.scale.copy(this.readingHinge.scale);
      const copy = panel.clone();
      copy.name = 'Leaf reading panel';
      copy.traverse(node => {
        if (!(node instanceof THREE.Mesh)) return;
        node.material = (Array.isArray(node.material) ? node.material[0] : node.material).clone();
        deformMaterial(node.material, this.leafUniforms, this.leafPanelMode);
        node.castShadow = false;
      });
      this.leafHinge.add(copy);
      this.leafHinge.visible = false;
    }
    Object.assign(this.leafUniforms.uLeafGrid.value, { x: rest.x0, y: rest.x1, z: rest.z0, w: rest.z1 });
    this.leafUniforms.uLeafFrame.value = this.leaf.frame;
    this.leafUniforms.uLeafShadow.value = this.leaf.shadow;
  }
  private leafGutter = { value: 1 };

  /** Compile the leaf's shaders now, so the first turn does not stall on them. */
  private async precompileLeaf() {
    if (!this.leaf) return;
    this.leaf.group.visible = this.leafHinge.visible = true;
    try { await this.renderer.compileAsync(this.scene, this.camera); }
    catch { /* compiled lazily instead */ }
    this.leaf.group.visible = this.leafHinge.visible = false;
  }

  private firstMesh(object: THREE.Object3D | undefined) {
    let mesh: THREE.Mesh | undefined;
    object?.traverse(node => { if (!mesh && node instanceof THREE.Mesh) mesh = node; });
    return mesh;
  }

  /** The page's UVs as an affine map of (X, Z), so the leaf's paper grain matches the page beneath. */
  private fitPageUv(page: THREE.Mesh, toBook: THREE.Matrix4) {
    const position = page.geometry.attributes.position, uv = page.geometry.attributes.uv, normal = page.geometry.attributes.normal;
    if (!uv || !normal) return undefined;
    // Least squares on the top-surface vertices: [u v] = [x z 1] M.
    const ata = new THREE.Matrix3().set(0, 0, 0, 0, 0, 0, 0, 0, 0), atu = new THREE.Vector3(), atv = new THREE.Vector3();
    const e = ata.elements, p = new THREE.Vector3(), n = new THREE.Vector3(), normalMatrix = new THREE.Matrix3().getNormalMatrix(toBook);
    let used = 0;
    for (let i = 0; i < position.count; i++) {
      n.fromBufferAttribute(normal, i).applyMatrix3(normalMatrix).normalize();
      if (n.y < 0.9) continue;
      p.fromBufferAttribute(position, i).applyMatrix4(toBook);
      const row = [p.x, p.z, 1];
      for (let a = 0; a < 3; a++) for (let b = 0; b < 3; b++) e[a * 3 + b] += row[a] * row[b];
      atu.addScaledVector(new THREE.Vector3(...row), uv.getX(i));
      atv.addScaledVector(new THREE.Vector3(...row), uv.getY(i));
      used++;
    }
    if (used < 6) return undefined;
    const inverse = ata.clone().invert();
    const mu = atu.applyMatrix3(inverse), mv = atv.applyMatrix3(inverse);
    return (x: number, z: number): [number, number] => [mu.x * x + mu.y * z + mu.z, mv.x * x + mv.y * z + mv.z];
  }

  /** Soft gutter shadow and faint fore-edge toning on the two open pages. */
  private preparePages(book: THREE.Object3D) {
    // The pages stop 0.018 short of the spine on each side; without a fold of
    // paper there, the brown spine leather reads as a rod down the gutter.
    const root = book.getObjectByName('BookRoot');
    if (root) {
      const fold = new THREE.Mesh(
        new THREE.PlaneGeometry(0.06, 3.1).rotateX(-Math.PI / 2),
        new THREE.MeshStandardMaterial({ name: 'gutter fold', color: '#7d6c55', roughness: 0.95 }),
      );
      fold.name = 'Gutter fold';
      fold.position.set(0, 0.199, 0);
      fold.receiveShadow = true;
      root.add(fold);
    }
    for (const name of ['LeftPage', 'RightPage']) {
      const page = book.getObjectByName(name);
      page?.traverse(node => {
        if (!(node instanceof THREE.Mesh) || !(node.material instanceof THREE.MeshStandardMaterial)) return;
        const base = node.material;
        const material = base.clone();
        // Only the page tops take the gutter shade; every page surface takes the leaf's shadow.
        if (base.name.toLowerCase() === 'paper') {
          // Chain the Book agent's hook (material.clone() does not copy it).
          const previous = base.onBeforeCompile.bind(base), previousKey = base.customProgramCacheKey.bind(base);
          material.onBeforeCompile = (shader, renderer) => {
            previous(shader, renderer);
            shader.vertexShader = `varying vec3 vPagePosition;\n${shader.vertexShader}`
              .replace('#include <project_vertex>', '#include <project_vertex>\n\tvPagePosition = transformed;');
            shader.fragmentShader = `varying vec3 vPagePosition;\n${shader.fragmentShader}`
              .replace('#include <opaque_fragment>', `
\tfloat gutterDistance = abs(vPagePosition.x);
\tfloat gutterShade = 1.0 - 0.38 * exp(-gutterDistance / 0.075) - 0.11 * exp(-gutterDistance / 0.38);
\tfloat edgeTone = max(smoothstep(2.08, 2.43, gutterDistance), smoothstep(1.32, 1.56, abs(vPagePosition.z)));
\toutgoingLight *= gutterShade * mix(vec3(1.0), vec3(0.965, 0.925, 0.855), edgeTone * 0.6);
#include <opaque_fragment>`);
          };
          material.customProgramCacheKey = () => `${previousKey()}|bound-page`;
        } else {
          material.onBeforeCompile = base.onBeforeCompile;
          material.customProgramCacheKey = base.customProgramCacheKey;
        }
        shadePageUnderLeaf(material, this.leafUniforms);
        node.material = material;
      });
    }
    // The reading panel lies on the left page: the leaf's shadow passes over it too.
    book.getObjectByName('ReadingPanel')?.traverse(node => {
      if (!(node instanceof THREE.Mesh) || !(node.material instanceof THREE.MeshStandardMaterial)) return;
      node.material = node.material.clone();
      shadePageUnderLeaf(node.material, this.leafUniforms);
    });
  }

  private disposeWriting(writing: Writing | undefined) {
    if (!writing) return;
    writing.removeFromParent();
    writing.material.map?.dispose();
    writing.material.dispose();
    writing.geometry.dispose();
  }

  private makeWriting(index: number) {
    const writing = makePaperText(this.options.chapters[index], this.renderer);
    // The writing can ride on the leaf's back: it follows the leaf like the paper pieces.
    writing.userData.leafMode = { value: 0 };
    deformMaterial(writing.material, this.leafUniforms, writing.userData.leafMode);
    if (this.readingHinge) this.readingHinge.add(writing);
    else {
      writing.position.set(-1.225, 0.26, 0.24);
      this.group.add(writing);
    }
    return writing;
  }

  private setPopup(rig: Rig | undefined, progress: number) {
    if (!rig) return;
    this.sample(rig.action, progress);
    rig.mixer.update(0);
  }

  private setText(index: number) {
    this.textIndex = index;
    this.disposeWriting(this.text);
    this.text = this.makeWriting(index);
  }

  private prefetch(index: number) {
    for (const nearby of [index - 1, index + 1]) {
      if (nearby >= 0 && nearby < this.options.chapters.length) void this.loadChapter(nearby).catch(() => {});
    }
    for (const [cached, promise] of this.cache) {
      if (Math.abs(cached - index) > 1) {
        this.cache.delete(cached);
        void promise.then(rig => { this.group.remove(rig.gltf.scene); rig.mixer.stopAllAction(); this.disposeObject(rig.gltf.scene); }).catch(() => {});
      }
    }
  }

  enter = (immediate = false) => {
    if (this.graphicsLost || (this.state.phase !== 'closed' && this.state.phase !== 'entering')) return;
    if (this.state.phase === 'entering' && !immediate) return;
    this.motionStart = performance.now();
    if (document.hidden) this.hiddenAt = this.motionStart;
    this.publish({ phase: 'entering', progress: 0, error: undefined });
    if (immediate || this.options.reducedMotion) this.finishEntrance();
  };

  private finishEntrance() {
    this.poseEntrance(1);
    this.publish({ phase: 'reading', progress: 1 });
    this.options.onRustle();
  }

  returnToShelf = () => {
    if (this.disposed || this.graphicsLost || this.state.phase !== 'reading' || this.state.chapter !== 0) return;
    this.motionStart = 0;
    this.pointer.set(0, 0);
    this.cameraOffset.set(0, 0);
    this.publish({ phase: 'closed', progress: 1, error: undefined });
    this.poseEntrance(0);
  };

  async goTo(index: number) {
    if (!validDestination(this.state.chapter, index, this.options.chapters.length, this.state.phase !== 'reading')) return;
    this.publish({ phase: 'turning', progress: 0, error: undefined });
    this.nextIndex = index;
    this.turningProgress = 0;
    this.direction = index > this.state.chapter ? 1 : -1;
    this.motionStart = 0;
    this.resumeProgress = 0;
    if (!this.manual) this.grab = CLICK_GRAB;
    try {
      this.nextRig = await this.loadChapter(index);
      if (this.disposed || this.graphicsLost) return;
      this.group.add(this.nextRig.gltf.scene);
      this.nextRig.gltf.scene.visible = false;
      this.nextRig.mode.value = 0;
      this.setPopup(this.nextRig, 0);
      this.disposeWriting(this.nextText);
      this.nextText = this.makeWriting(index);
      this.nextText.visible = false;
      const now = performance.now();
      this.motionStart = now - this.resumeProgress * TURN_DURATION * 1000;
      if (this.manual) this.dragStart = now;
      if (document.hidden) this.hiddenAt = now;
      this.loop.invalidate();
      this.options.onRustle();
      if (this.options.reducedMotion) this.finishTurn();
    } catch (error) {
      console.warn('[book] Chapter load failed', index + 1, error);
      this.manual = false;
      this.revertFrom = null;
      if (!this.disposed && !this.graphicsLost) this.publish({ phase: 'reading', error: 'That chapter could not load. Please try the page again.', progress: 1 });
    }
  }

  /** A stage pixel on the page plane, in book space. */
  private pagePoint(x: number, y: number) {
    const width = this.element.clientWidth || 1, height = this.element.clientHeight || 1;
    this.raycaster.setFromCamera(new THREE.Vector2(x / width * 2 - 1, 1 - y / height * 2), this.camera);
    this.group.updateMatrixWorld();
    const ray = this.raycaster.ray.clone().applyMatrix4(new THREE.Matrix4().copy(this.group.matrixWorld).invert());
    return ray.intersectPlane(this.dragPlane, new THREE.Vector3());
  }

  /**
   * Begin a turn that follows the visitor's drag. (x, y) is where the hand took
   * hold, in stage pixels; the row under it leads the curl. Returns false if no turn starts.
   */
  beginDrag = (direction: 1 | -1, x?: number, y?: number) => {
    if (this.options.reducedMotion || this.graphicsLost || this.state.phase !== 'reading') return false;
    const target = this.state.chapter + direction;
    if (!validDestination(this.state.chapter, target, this.options.chapters.length, false)) return false;
    this.manual = true;
    this.manualTarget = this.manualProgress = 0;
    this.revertFrom = null;
    const point = x !== undefined && y !== undefined ? this.pagePoint(x, y) : null;
    const rest = this.leaf?.rest;
    if (point && rest) {
      this.grab = clamp01((point.z - rest.z0) / (rest.z1 - rest.z0));
      this.grabX = point.x;
    } else {
      this.grab = CLICK_GRAB;
      this.grabX = direction * 1.9;
    }
    void this.goTo(target);
    return true;
  };

  /**
   * Move the held page. With stage coordinates the fore-edge follows the hand
   * across the spread; otherwise `progress` (0..1) is the share of the gesture.
   */
  dragTo = (progress: number, x?: number, y?: number) => {
    if (!this.manual) return;
    let travel = clamp01(progress);
    const point = x !== undefined && y !== undefined ? this.pagePoint(x, y) : null;
    const reach = this.leaf?.rest.x1 ?? 2.42;
    if (point) {
      // The held edge sits where the hand is: its turned angle is the hand's
      // angle about the spine, measured from where the hand took hold.
      const side = this.direction;
      const angle = (value: number) => Math.acos(THREE.MathUtils.clamp(side * value / reach, -1, 1));
      const start = Math.min(angle(this.grabX), Math.PI * 0.9);
      travel = travelForTip(clamp01((angle(point.x) - start) / (Math.PI - start)), this.grab);
    }
    this.manualTarget = travel <= 0 ? 0 : progressForTravel(travel);
    this.loop.invalidate();
  };

  /** Turn progress of the held page (0..1), for the release decision. */
  dragProgress = () => this.manual ? this.manualProgress : this.turningProgress;

  /**
   * Release the page: finish the turn from where it is, or let it fall back.
   * Without an explicit decision, a page past the spine or flicked onward turns.
   * `flick` is the hand's speed in the turning direction, in stage widths per second.
   */
  endDrag = (commit?: boolean, flick = 0) => {
    if (!this.manual) return;
    this.manual = false;
    this.manualSettling = false;
    const progress = this.manualProgress;
    const travel = turnPose(progress).leaf;
    const decided = commit ?? (flick < -0.4 ? false : travel > 0.45 || (flick > 0.4 && progress > TURN_LEAF_START));
    const now = performance.now();
    if (decided) {
      this.resumeProgress = progress;
      if (this.motionStart) this.motionStart = now - progress * TURN_DURATION * 1000;
    } else {
      this.revertFrom = progress;
      this.revertStart = now;
    }
    this.loop.invalidate();
  };

  private applyTurn(t: number) {
    if (!this.nextRig) return;
    const direction = this.direction;
    const pose = turnPose(t, direction);
    const outgoing = this.currentRig, incoming = this.nextRig;
    this.setPopup(outgoing, pose.outgoing);
    this.setPopup(incoming, pose.incoming);
    if (outgoing) outgoing.gltf.scene.visible = pose.showOutgoing;
    incoming.gltf.scene.visible = pose.showIncoming;
    // Forward, the old pieces are hinged to the leaf; backward, the new ones are.
    const leafOn = pose.showLeaf && Boolean(this.leaf);
    if (outgoing) outgoing.mode.value = leafOn ? (direction > 0 ? 1 : 2) : 0;
    incoming.mode.value = leafOn ? (direction > 0 ? 2 : 1) : 0;
    if (this.leaf) {
      this.leaf.group.visible = leafOn;
      if (leafOn) this.leaf.update(pose.leaf, direction > 0 ? 1 : -1, this.grab);
      // Pieces riding on the leaf settle onto its face as it leaves a page and back into place as it lands.
      const leaving = interval(pose.leaf, 0, 0.05), landing = 1 - interval(pose.leaf, 0.95, 1);
      this.leafUniforms.uLeafSeat.value = direction > 0 ? leaving : landing;
      this.leafUniforms.uLeafSeatBack.value = direction > 0 ? landing : leaving;
      // The binding's shade leaves the sheet as it lifts out of the gutter.
      this.leafGutter.value = Math.max(1 - interval(pose.leaf, 0, 0.1), interval(pose.leaf, 0.9, 1));
    }
    this.leafUniforms.uLeafShadowOn.value = leafOn ? 1 : 0;
    this.sample(this.readingAction, pose.reading);
    this.bookMixer?.update(0);
    this.placeWriting(t, leafOn);
    // The panel on the leaf lies exactly where the real one does once landed; the
    // real panel stands proud of the leaf there, so it waits underneath until the leaf clears it.
    if (this.readingHinge) this.readingHinge.visible = !(leafOn && this.leaf && this.leaf.state.panelGap < PANEL_CLEARANCE);
    this.leafHinge.visible = leafOn;
    this.leafPanelMode.value = leafOn ? 3 : 0;
  }

  /**
   * Forward, the new writing lies on the leaf's back and the old stays on the
   * panel beneath; backward, the old writing leaves on the leaf's back and the
   * earlier chapter's is already on the panel. Without the leaf, the panel
   * shows whichever writing the spread has reached.
   */
  private placeWriting(t: number, leafOn: boolean) {
    const direction = this.direction;
    const onLeaf = direction > 0 ? this.nextText : this.text;
    const onPanel = direction > 0 ? this.text : this.nextText;
    const put = (writing: Writing | undefined, parent: THREE.Object3D | undefined, visible: boolean, mode: number) => {
      if (!writing) return;
      if (parent && writing.parent !== parent) parent.add(writing);
      writing.visible = visible;
      writing.material.opacity = 1;
      (writing.userData.leafMode as { value: number }).value = mode;
    };
    if (leafOn) {
      put(onLeaf, this.leafHinge, true, 3);
      put(onPanel, this.readingHinge, true, 0);
    } else {
      const incoming = incomingWriting(t, direction) && this.nextText;
      put(this.text, this.readingHinge, !incoming, 0);
      put(this.nextText, this.readingHinge, Boolean(incoming), 0);
    }
  }

  private restLeaf() {
    if (this.leaf) this.leaf.group.visible = false;
    this.leafUniforms.uLeafShadowOn.value = 0;
    this.leafHinge.visible = false;
    this.leafPanelMode.value = 0;
    if (this.readingHinge) this.readingHinge.visible = true;
    for (const writing of [this.text, this.nextText]) {
      if (!writing) continue;
      if (this.readingHinge && writing.parent !== this.readingHinge) this.readingHinge.add(writing);
      (writing.userData.leafMode as { value: number }).value = 0;
    }
  }

  /** The visitor let go early: return to the spread they were reading. */
  private cancelTurn() {
    if (this.nextRig) {
      this.nextRig.gltf.scene.visible = false;
      this.nextRig.mode.value = 0;
      this.group.remove(this.nextRig.gltf.scene);
      this.nextRig = undefined;
    }
    this.disposeWriting(this.nextText);
    this.nextText = undefined;
    this.revertFrom = null;
    this.manual = false;
    this.motionStart = 0;
    if (this.currentRig) { this.currentRig.gltf.scene.visible = true; this.currentRig.mode.value = 0; }
    this.setPopup(this.currentRig, 1);
    this.restLeaf();
    this.sample(this.readingAction, 1);
    this.bookMixer?.update(0);
    if (this.text) { this.text.visible = true; this.text.material.opacity = 1; }
    this.publish({ phase: 'reading', progress: 1 });
  }

  private finishTurn() {
    if (!this.nextRig) return;
    if (this.currentRig) { this.currentRig.gltf.scene.visible = false; this.currentRig.mode.value = 0; this.group.remove(this.currentRig.gltf.scene); }
    this.currentRig = this.nextRig;
    this.nextRig = undefined;
    this.manual = false;
    this.revertFrom = null;
    this.currentRig.gltf.scene.visible = true;
    this.currentRig.mode.value = 0;
    this.setPopup(this.currentRig, 1);
    this.restLeaf();
    this.sample(this.openAction, 1);
    this.sample(this.readingAction, 1);
    this.bookMixer?.update(0);
    if (this.nextText) {
      this.disposeWriting(this.text);
      this.text = this.nextText;
      this.nextText = undefined;
      this.textIndex = this.nextIndex;
    } else if (this.textIndex !== this.nextIndex) this.setText(this.nextIndex);
    if (this.text) { this.text.visible = true; this.text.material.opacity = 1; }
    this.publish({ phase: 'reading', chapter: this.nextIndex, progress: 1 });
    this.prefetch(this.nextIndex);
  }

  /** True when a stage point (-1..1, y down) is over the lamp. */
  lampHit = (x: number, y: number) => this.room.lampHit(x, y);
  /** Pull the lamp chain. */
  pullLamp = () => this.room.pullLamp();
  setLamp = (on: boolean) => this.room.setLamp(on);

  setPointer = (x: number, y: number) => {
    this.pointer.set(x, y);
    if ((this.state.phase === 'reading' || this.state.phase === 'closed') && !this.options.reducedMotion) this.loop.invalidate();
  };
  setReducedMotion = (reduced: boolean) => {
    this.options.reducedMotion = reduced;
    this.loop.invalidate();
    if (!reduced) return;
    if (this.state.phase === 'closed' || this.state.phase === 'entering') this.enter(true);
    else if (this.state.phase === 'turning' && this.motionStart && this.nextRig) this.finishTurn();
  };
  setInspectionProgress = (value: number | null) => {
    if (import.meta.env.DEV) {
      this.inspectionProgress = value === null ? null : clamp01(value);
      this.loop.invalidate();
    }
  };
  /** Development only: project world points to stage pixels, to place props. */
  inspectProject = (points: [number, number, number][]) => {
    if (!import.meta.env.DEV) return [];
    const w = this.element.clientWidth, h = this.element.clientHeight;
    return points.map(([x, y, z]) => { const v = new THREE.Vector3(x, y, z).project(this.camera); return [Math.round((v.x + 1) / 2 * w), Math.round((1 - v.y) / 2 * h)]; });
  };
  /** Development only: move the lamp to try a placement. */
  inspectLamp = (x: number, z: number, scale: number, turn: number) => this.room.inspectLamp(x, z, scale, turn);
  /** Development only: kept for older inspection scripts; the leaf no longer carries prints. */
  inspectLeafPrints = () => [] as string[];
  /** Development only: the live scene, for frame inspection scripts. */
  inspectScene = () => import.meta.env.DEV ? { scene: this.scene, camera: this.camera, renderer: this.renderer, group: this.group, invalidate: () => this.loop.invalidate(), leaf: this.leaf, uniforms: this.leafUniforms } : undefined;
  inspectContextLoss = () => {
    if (import.meta.env.DEV) this.renderer.getContext().getExtension('WEBGL_lose_context')?.loseContext();
  };
  resetMetrics = () => { this.motionFrames = []; this.metrics.longestFrameMs = 0; };
  getMetrics = () => {
    const sorted = [...this.motionFrames].sort((a, b) => a - b);
    const average = sorted.length ? sorted.reduce((sum, value) => sum + value, 0) / sorted.length : 0;
    return { ...this.metrics, motionSamples: sorted.length, motionFps: average ? Math.round(1000 / average) : 0,
      motionP95Ms: sorted.length ? Math.round(sorted[Math.floor((sorted.length - 1) * .95)]) : 0,
      cachedChapters: this.cache.size, geometries: this.renderer.info.memory.geometries, textures: this.renderer.info.memory.textures,
      viewport: [this.element.clientWidth, this.element.clientHeight], pixelRatio: this.renderer.getPixelRatio(), pageText: this.text?.userData.textLayout, browser: navigator.userAgent };
  };

  /** Apply the current tilt on top of the authored pose. */
  private applyHold() {
    this.tiltEuler.set(this.tilt.y * 0.020, this.tilt.x * 0.030, -this.tilt.x * 0.014, 'YXZ');
    this.tiltQuaternion.setFromEuler(this.tiltEuler);
    this.group.quaternion.copy(this.baseQuaternion).premultiply(this.tiltQuaternion);
    // Lift the book as one edge dips, so it never sinks into the desk.
    const lift = Math.abs(this.tilt.y) * 0.020 * 1.7 + Math.abs(this.tilt.x) * 0.014 * 2.6;
    this.group.position.copy(this.basePosition).add(new THREE.Vector3(0, lift, 0));
  }

  /** Advance the hand's spring; returns true while it is still moving. */
  private tickHold(dt: number) {
    const phase = this.state.phase;
    const holding = !this.options.reducedMotion && (phase === 'reading' || phase === 'closed') && !this.loupe.active;
    const target = holding ? this.pointer : new THREE.Vector2();
    const step = Math.min(dt, 1 / 30);
    if (step <= 0) return this.tilt.lengthSq() > 1e-8 || this.tiltVelocity.lengthSq() > 1e-8;
    // Slightly under-damped: the book settles with the faintest overshoot, like a weight in the hand.
    const stiffness = 38, damping = 10.5;
    const accel = target.clone().sub(this.tilt).multiplyScalar(stiffness).sub(this.tiltVelocity.clone().multiplyScalar(damping));
    this.tiltVelocity.addScaledVector(accel, step);
    this.tilt.addScaledVector(this.tiltVelocity, step);
    // Paper pieces lag behind the board and flex, then spring back upright.
    const drive = this.options.reducedMotion ? 0 : -this.tiltVelocity.length() * 0.02;
    this.flexVelocity += ((drive - this.flex) * 120 - this.flexVelocity * 9) * step;
    this.flex += this.flexVelocity * step;
    this.flex = THREE.MathUtils.clamp(this.flex, -0.035, 0.02);
    const moving = this.tilt.distanceToSquared(target) > 1e-7 || this.tiltVelocity.lengthSq() > 1e-6 || Math.abs(this.flex) > 1e-4 || Math.abs(this.flexVelocity) > 1e-3;
    if (!moving) { this.tilt.copy(target); this.tiltVelocity.set(0, 0); this.flex = this.flexVelocity = 0; }
    this.applyHold();
    if (phase === 'reading' && this.currentRig) this.setPopup(this.currentRig, 1 + Math.min(0, this.flex));
    return moving;
  }

  /** Show the loupe at stage pixel (x, y), or hide it. */
  setLoupe = (active: boolean, x?: number, y?: number, radius?: number, touch?: boolean) => this.loupe.set(active, x, y, radius, touch);

  private poseEntrance(t: number) {
    this.entry = t;
    const pull = interval(t, 0, 0.22);
    const rotate = interval(t, 0.13, 0.34);
    const lower = interval(t, 0.39, 0.54);
    this.group.position.set(THREE.MathUtils.lerp(0.26, -1.25, rotate), 1.78, 0.4 + pull * 0.35);
    this.group.position.lerp(new THREE.Vector3(0, 0, 0), lower);
    this.group.quaternion.copy(initialRotation).slerp(coverRotation, rotate).slerp(flatRotation, lower);
    this.basePosition.copy(this.group.position);
    this.baseQuaternion.copy(this.group.quaternion);
    this.applyHold();
    const pose = entrancePose(t);
    this.sample(this.openAction, pose.cover);
    this.sample(this.readingAction, pose.popup);
    this.bookMixer?.update(0);
    if (this.turnPage) this.turnPage.visible = false;
    this.setPopup(this.currentRig, pose.popup);
    if (this.currentRig) this.currentRig.gltf.scene.visible = pose.showScene;
    if (this.text) {
      this.text.visible = pose.textOpacity > 0;
      this.text.material.opacity = pose.textOpacity;
    }
    this.updateCamera();
  }

  /** Hover the sheen light over the page under the pointer (smoothed with the camera drift). */
  private placeSheenLight() {
    const reading = this.state.phase === 'reading' || this.state.phase === 'turning';
    const on = reading && !this.options.reducedMotion && !this.loupe.active ? 1 : 0;
    this.sheenLight.intensity += (on * 0.9 - this.sheenLight.intensity) * 0.08;
    if (Math.abs(this.sheenLight.intensity - on * 0.9) < 0.002) this.sheenLight.intensity = on * 0.9;
    this.sheenPosition.set(this.cameraOffset.x * 2.3, 2.4, 0.8 + this.cameraOffset.y * 1.3);
    this.sheenLight.position.copy(this.group.localToWorld(this.sheenPosition));
    return this.sheenLight.intensity !== on * 0.9;
  }

  private updateCamera() {
    const aspect = this.camera.aspect;
    const height = this.element.clientHeight || 1000;
    const verticalFit = Math.sqrt(Math.max(1, 850 / height));
    const horizontalFit = aspect < 1 ? 5.6 : 5.3;
    const readingDistance = Math.max(7.45 * verticalFit, horizontalFit / (2 * Math.tan(THREE.MathUtils.degToRad(16)) * aspect));
    const closedPosition = new THREE.Vector3(0.25, 2.2, 11.2);
    const readingPosition = new THREE.Vector3(0.12, 0.53 * readingDistance + 0.65, 0.86 * readingDistance);
    const transition = interval(this.entry, 0.44, 0.78);
    this.camera.position.copy(closedPosition).lerp(readingPosition, transition);
    const moving = !this.options.reducedMotion && this.state.phase === 'reading';
    // Keep the current framing fixed throughout a page turn.
    if (this.state.phase !== 'turning') {
      const target = moving ? this.pointer : new THREE.Vector2();
      this.cameraOffset.lerp(target, 0.035);
      if (this.cameraOffset.distanceToSquared(target) < 0.000001) this.cameraOffset.copy(target);
    }
    this.camera.position.x += this.cameraOffset.x * 0.1;
    this.camera.position.y += this.cameraOffset.y * 0.045;
    this.look.set(0, THREE.MathUtils.lerp(1.65, 0.75, transition), 0);
    this.camera.lookAt(this.look);
  }

  private tick = (now: number) => {
    if (this.disposed || this.graphicsLost) return false;
    const dt = this.lastFrame ? (now - this.lastFrame) / 1000 : 0;
    this.lastFrame = now;
    if (import.meta.env.DEV && this.inspectionProgress === null && dt > 0 && this.motionStart && (this.state.phase === 'entering' || this.state.phase === 'turning')) {
      this.motionFrames.push(dt * 1000);
      if (this.motionFrames.length > 2400) this.motionFrames.shift();
    }
    if (this.state.phase === 'entering') {
      const progress = this.inspectionProgress ?? clamp01((now - this.motionStart) / (ENTER_DURATION * 1000));
      this.poseEntrance(progress);
      if (progress >= 1) this.finishEntrance();
    } else if (this.state.phase === 'turning' && this.motionStart && this.nextRig) {
      let t: number;
      if (this.inspectionProgress !== null) t = this.inspectionProgress;
      else if (this.revertFrom !== null) {
        // Fall back a little faster than a full turn, from wherever the page was released.
        const span = Math.max(0.2, this.revertFrom * TURN_DURATION * 0.6) * 1000;
        t = this.revertFrom * (1 - clamp01((now - this.revertStart) / span));
      } else if (this.manual) {
        // The page follows the hand on a light spring. The reading panel must
        // lie flat before the leaf moves, so that much runs on the clock.
        const clock = clamp01((now - this.dragStart) / (TURN_DURATION * 1000));
        const target = clock < TURN_LEAF_START ? Math.min(clock, Math.max(this.manualTarget, clock)) : Math.max(this.manualTarget, TURN_LEAF_START);
        this.manualProgress += (target - this.manualProgress) * (1 - Math.exp(-Math.min(dt, 0.05) * 22));
        if (Math.abs(target - this.manualProgress) < 1e-4) this.manualProgress = target;
        this.manualSettling = this.manualProgress !== target || clock < TURN_LEAF_START;
        t = this.manualProgress;
      }
      else t = clamp01((now - this.motionStart) / (TURN_DURATION * 1000));
      this.turningProgress = t;
      this.applyTurn(t);
      if (this.revertFrom !== null && t <= 0) this.cancelTurn();
      else if (this.revertFrom === null && !this.manual && t >= 1) this.finishTurn();
    }
    const lampChanging = this.room.tick(now);
    const holding = this.tickHold(dt);
    this.updateCamera();
    const sheen = this.placeSheenLight();
    // Book space for the leaf deformation and its shadow on the pages.
    this.group.updateMatrixWorld();
    this.leafUniforms.uBook.value.copy(this.group.matrixWorld);
    this.leafUniforms.uBookInv.value.copy(this.group.matrixWorld).invert();
    this.renderer.render(this.scene, this.camera);
    this.loupe.render();
    this.metrics.totalFrames++;
    this.metrics.frames++;
    this.metrics.seconds += dt;
    if (dt && (this.state.phase === 'entering' || this.state.phase === 'turning')) this.metrics.longestFrameMs = Math.max(this.metrics.longestFrameMs, Math.round(dt * 1000));
    if (this.metrics.seconds >= 1) {
      this.metrics.fps = Math.round(this.metrics.frames / this.metrics.seconds);
      this.metrics.drawCalls = this.renderer.info.render.calls;
      this.metrics.triangles = this.renderer.info.render.triangles;
      this.metrics.frames = 0;
      this.metrics.seconds = 0;
    }
    const animating = this.inspectionProgress === null && (this.state.phase === 'entering'
      || (this.state.phase === 'turning' && (!this.manual || this.manualSettling) && Boolean(this.motionStart && this.nextRig)));
    const target = !this.options.reducedMotion && this.state.phase === 'reading' ? this.pointer : new THREE.Vector2();
    const settling = this.state.phase !== 'turning' && this.cameraOffset.distanceToSquared(target) > 0.000001;
    if (!animating && !settling && !lampChanging && !holding && !sheen) this.lastFrame = 0;
    return animating || settling || lampChanging || holding || sheen;
  };

  private resize = () => {
    const { width, height } = this.element.getBoundingClientRect();
    if (!width || !height) return;
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, width < 768 ? 1.5 : 1.75));
    this.renderer.setSize(width, height);
    this.room?.resize(width, height);
    this.updateCamera();
    this.loop.invalidate();
  };

  private publish(change: Partial<BookSnapshot>) {
    this.state = { ...this.state, ...change };
    this.options.onChange({ ...this.state });
    this.loop.invalidate();
  }

  private visibilityChanged = () => {
    const now = performance.now();
    if (document.hidden) {
      if (this.hiddenAt === null) this.hiddenAt = now;
      this.loop.setPaused(true);
    } else {
      if (this.hiddenAt !== null && this.motionStart) this.motionStart += now - this.hiddenAt;
      if (this.hiddenAt !== null && this.revertFrom !== null) this.revertStart += now - this.hiddenAt;
      this.hiddenAt = null;
      this.lastFrame = 0;
      this.loop.setPaused(false);
    }
  };

  private contextLost = (event: Event) => {
    event.preventDefault();
    this.graphicsLost = true;
    this.loop.dispose();
    this.publish({ phase: 'error', error: 'The graphics connection was interrupted. The illustrated edition is available below.' });
  };

  private disposeObject(object: THREE.Object3D) {
    object.traverse(node => {
      if (!(node instanceof THREE.Mesh)) return;
      if (!this.released.has(node.geometry)) { node.geometry.dispose(); this.released.add(node.geometry); }
      const materials = Array.isArray(node.material) ? node.material : [node.material];
      for (const material of materials) {
        if (this.released.has(material)) continue;
        for (const value of Object.values(material)) {
          if (value instanceof THREE.Texture && !this.textures.includes(value) && !this.released.has(value)) {
            value.dispose();
            this.released.add(value);
          }
        }
        material.dispose();
        this.released.add(material);
      }
    });
  }

  dispose() {
    this.disposed = true;
    this.loop.dispose();
    this.observer.disconnect();
    document.removeEventListener('visibilitychange', this.visibilityChanged);
    this.renderer.domElement.removeEventListener('webglcontextlost', this.contextLost);
    this.bookMixer?.stopAllAction();
    for (const promise of this.cache.values()) void promise.then(rig => { rig.mixer.stopAllAction(); this.disposeObject(rig.gltf.scene); }).catch(() => {});
    this.cache.clear();
    if (this.text) this.text.material.map?.dispose();
    if (this.nextText) this.nextText.material.map?.dispose();
    this.loupe.dispose();
    this.leaf?.dispose();
    this.disposeObject(this.scene);
    if (this.book) this.disposeObject(this.book.scene);
    this.textures.forEach(texture => texture.dispose());
    this.room.dispose();
    this.renderer.dispose();
    this.renderer.domElement.remove();
  }
}
