import * as THREE from 'three';
import { GLTFLoader, type GLTF } from 'three/addons/loaders/GLTFLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import type { BookSnapshot, Chapter } from '../types';
import { ENTER_DURATION, TURN_DURATION, clamp01, interval, entrancePose, turnPose, validDestination } from './motion';
import { makePaperText } from './paper';

type Rig = { gltf: GLTF; mixer: THREE.AnimationMixer; action?: THREE.AnimationAction };
type Options = {
  chapters: Chapter[];
  initialChapter?: number;
  reducedMotion: boolean;
  onChange: (snapshot: BookSnapshot) => void;
  onRustle: () => void;
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
  private turnAction?: THREE.AnimationAction;
  private readingAction?: THREE.AnimationAction;
  private readingHinge?: THREE.Object3D;
  private turnPage?: THREE.Object3D;
  private currentRig?: Rig;
  private nextRig?: Rig;
  private text?: ReturnType<typeof makePaperText>;
  private cache = new Map<number, Promise<Rig>>();
  private textures: THREE.Texture[] = [];
  private paper?: THREE.Texture;
  private walnut?: THREE.Texture;
  private backdrop?: THREE.Texture;
  private environmentTarget?: THREE.WebGLRenderTarget;
  private released = new WeakSet<object>();
  private graphicsLost = false;
  private textIndex = -1;
  private inspectionProgress: number | null = null;
  private observer: ResizeObserver;
  private frame = 0;
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
  private metrics = { frames: 0, seconds: 0, fps: 0, drawCalls: 0, triangles: 0, longestFrameMs: 0 };
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
    this.observer = new ResizeObserver(this.resize);
    this.observer.observe(element);
    this.resize();
    this.frame = requestAnimationFrame(this.tick);
  }

  async init() {
    try {
      await Promise.all([
        document.fonts.load('400 64px "Cormorant Garamond"'),
        document.fonts.load('500 91px "Cormorant Garamond"'),
        document.fonts.load('italic 500 63px "Cormorant Garamond"'),
        document.fonts.load('500 34px Inter'),
        this.loadTextures(),
      ]);
      if (this.disposed || this.graphicsLost) return;
      this.environment();
      this.publish({ progress: 0.25 });
      const book = await this.loader.loadAsync(asset('models/book.glb'));
      if (this.disposed || this.graphicsLost) { this.disposeObject(book.scene); return; }
      this.book = book;
      this.prepareMaterials(book.scene);
      this.group.add(book.scene);
      this.bookMixer = new THREE.AnimationMixer(book.scene);
      this.openAction = this.action(this.bookMixer, book.animations, 'open');
      this.turnAction = this.action(this.bookMixer, book.animations, 'turn');
      this.readingAction = this.action(this.bookMixer, book.animations, 'reading');
      this.readingHinge = book.scene.getObjectByName('ReadingHinge');
      if (!this.openAction || !this.turnAction || !this.readingAction || !this.readingHinge) throw new Error('The book animations could not be loaded.');
      this.turnPage = book.scene.getObjectByName('TurnPage');
      if (this.turnPage) this.turnPage.visible = false;
      this.sample(this.openAction, 0);
      this.sample(this.readingAction, 0);
      this.bookMixer.update(0);
      this.publish({ progress: 0.65 });
      const initialChapter = this.options.initialChapter ?? 0;
      this.currentRig = await this.loadChapter(initialChapter);
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
    const loader = new THREE.TextureLoader();
    const [paper, walnut, backdrop] = await Promise.all([
      loader.loadAsync(asset('textures/paper.webp')),
      loader.loadAsync(asset('textures/walnut.webp')),
      loader.loadAsync(asset('textures/bookshop.webp')),
    ]);
    if (this.disposed) { paper.dispose(); walnut.dispose(); backdrop.dispose(); return; }
    for (const texture of [paper, walnut]) {
      texture.colorSpace = THREE.SRGBColorSpace;
      texture.wrapS = texture.wrapT = THREE.MirroredRepeatWrapping;
      texture.anisotropy = Math.min(8, this.renderer.capabilities.getMaxAnisotropy());
    }
    walnut.repeat.set(3, 3);
    this.paper = paper;
    this.walnut = walnut;
    backdrop.colorSpace = THREE.SRGBColorSpace;
    this.backdrop = backdrop;
    this.scene.background = backdrop;
    this.textures.push(paper, walnut, backdrop);
    this.resize();
  }

  private environment() {
    // The photographed environment supplies fine walnut detail and optical depth.
    // This real plane receives shadows from every animated mesh above the desk.
    const desk = new THREE.Mesh(
      new THREE.PlaneGeometry(60, 60),
      new THREE.ShadowMaterial({ color: '#21170e', opacity: 0.30 }),
    );
    desk.rotation.x = -Math.PI / 2;
    desk.position.y = -0.045;
    desk.receiveShadow = true;
    this.scene.add(desk);

    const pmrem = new THREE.PMREMGenerator(this.renderer);
    const room = new RoomEnvironment();
    this.environmentTarget = pmrem.fromScene(room, 0.08);
    this.scene.environment = this.environmentTarget.texture;
    this.scene.environmentIntensity = 0.45;
    room.dispose();
    pmrem.dispose();

    this.scene.add(new THREE.HemisphereLight('#fff4df', '#705039', 0.8));
    const sun = new THREE.DirectionalLight('#ffebcf', 2.6);
    sun.position.set(-3.5, 7, -1.5);
    sun.castShadow = true;
    sun.shadow.mapSize.set(2048, 2048);
    Object.assign(sun.shadow.camera, { left: -4.5, right: 4.5, top: 5, bottom: -4, near: 0.1, far: 20 });
    sun.shadow.normalBias = 0.003;
    sun.shadow.bias = -0.0001;
    sun.shadow.radius = 3;
    this.scene.add(sun);
    const bounce = new THREE.DirectionalLight('#f1ddbc', 0.7);
    bounce.position.set(4, 3, 5);
    this.scene.add(bounce);
  }

  private prepareMaterials(object: THREE.Object3D) {
    object.traverse(node => {
      if (!(node instanceof THREE.Mesh)) return;
      node.castShadow = true;
      node.receiveShadow = true;
      const materials = Array.isArray(node.material) ? node.material : [node.material];
      for (const material of materials) {
        if (!(material instanceof THREE.MeshStandardMaterial)) continue;
        const name = material.name.toLowerCase();
        if (name.includes('paper') && !material.map && this.paper) {
          material.map = this.paper;
          material.bumpMap = this.paper;
          material.bumpScale = 0.008;
          material.roughness = 0.92;
        }
        if (name.includes('wood') && !material.map) material.map = this.walnut ?? null;
        if (name === 'leather') {
          if (material.map) material.bumpMap = material.map;
          material.bumpScale = 0.006;
          material.map = null;
          material.color.set('#553522');
          material.roughness = 0.72;
          material.envMapIntensity = 0.2;
        }
        if (name === 'leather_dark') { material.color.set('#382216'); material.envMapIntensity = 0.35; }
        material.needsUpdate = true;
      }
    });
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

  private loadChapter(index: number): Promise<Rig> {
    const existing = this.cache.get(index);
    if (existing) return existing;
    const promise = this.loader.loadAsync(asset(this.options.chapters[index].scene)).then(gltf => {
      if (this.disposed || this.graphicsLost) { this.disposeObject(gltf.scene); throw new Error('Book unavailable'); }
      this.prepareMaterials(gltf.scene);
      const mixer = new THREE.AnimationMixer(gltf.scene);
      const action = this.action(mixer, gltf.animations, 'unfold');
      if (!action) { this.disposeObject(gltf.scene); throw new Error(`Missing unfold animation: chapter ${index + 1}`); }
      const rig = { gltf, mixer, action };
      this.setPopup(rig, 0);
      return rig;
    }).catch(error => {
      if (this.cache.get(index) === promise) this.cache.delete(index);
      throw error;
    });
    this.cache.set(index, promise);
    return promise;
  }

  private setPopup(rig: Rig | undefined, progress: number) {
    if (!rig) return;
    this.sample(rig.action, progress);
    rig.mixer.update(0);
  }

  private setText(index: number) {
    this.textIndex = index;
    if (this.text) {
      this.text.removeFromParent();
      this.text.material.map?.dispose();
      this.text.material.dispose();
      this.text.geometry.dispose();
    }
    this.text = makePaperText(this.options.chapters[index], this.renderer);
    if (this.readingHinge) this.readingHinge.add(this.text);
    else {
      this.text.position.set(-1.225, 0.26, 0.24);
      this.group.add(this.text);
    }
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
    try {
      this.nextRig = await this.loadChapter(index);
      if (this.disposed || this.graphicsLost) return;
      this.group.add(this.nextRig.gltf.scene);
      this.nextRig.gltf.scene.visible = false;
      this.setPopup(this.nextRig, 0);
      this.motionStart = performance.now();
      this.options.onRustle();
      if (this.options.reducedMotion) this.finishTurn();
    } catch (error) {
      console.warn('[book] Chapter load failed', index + 1, error);
      if (!this.disposed && !this.graphicsLost) this.publish({ phase: 'reading', error: 'That chapter could not load. Please try the page again.', progress: 1 });
    }
  }

  private finishTurn() {
    if (!this.nextRig) return;
    if (this.currentRig) { this.currentRig.gltf.scene.visible = false; this.group.remove(this.currentRig.gltf.scene); }
    this.currentRig = this.nextRig;
    this.nextRig = undefined;
    this.currentRig.gltf.scene.visible = true;
    this.setPopup(this.currentRig, 1);
    if (this.turnPage) this.turnPage.visible = false;
    this.sample(this.openAction, 1);
    this.sample(this.readingAction, 1);
    this.bookMixer?.update(0);
    if (this.textIndex !== this.nextIndex) this.setText(this.nextIndex);
    if (this.text) { this.text.visible = true; this.text.material.opacity = 1; }
    this.publish({ phase: 'reading', chapter: this.nextIndex, progress: 1 });
    this.prefetch(this.nextIndex);
  }

  setPointer = (x: number, y: number) => { this.pointer.set(x, y); };
  setReducedMotion = (reduced: boolean) => {
    this.options.reducedMotion = reduced;
    if (!reduced) return;
    if (this.state.phase === 'closed' || this.state.phase === 'entering') this.enter(true);
    else if (this.state.phase === 'turning' && this.motionStart && this.nextRig) this.finishTurn();
  };
  setInspectionProgress = (value: number | null) => {
    if (import.meta.env.DEV) this.inspectionProgress = value === null ? null : clamp01(value);
  };
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

  private poseEntrance(t: number) {
    this.entry = t;
    const pull = interval(t, 0, 0.22);
    const rotate = interval(t, 0.13, 0.34);
    const lower = interval(t, 0.39, 0.54);
    this.group.position.set(THREE.MathUtils.lerp(0.26, -1.25, rotate), 1.78, 0.4 + pull * 0.35);
    this.group.position.lerp(new THREE.Vector3(0, 0, 0), lower);
    this.group.quaternion.copy(initialRotation).slerp(coverRotation, rotate).slerp(flatRotation, lower);
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

  private updateCamera() {
    const aspect = this.camera.aspect;
    const height = this.element.clientHeight || 1000;
    const verticalFit = Math.sqrt(Math.max(1, 850 / height));
    const readingDistance = Math.max(8.2 * verticalFit, 5.85 / (2 * Math.tan(THREE.MathUtils.degToRad(16)) * aspect));
    const closedPosition = new THREE.Vector3(0.25, 2.2, 11.2);
    const readingPosition = new THREE.Vector3(0.12, 0.53 * readingDistance + 0.65, 0.86 * readingDistance);
    const transition = interval(this.entry, 0.44, 0.78);
    this.camera.position.copy(closedPosition).lerp(readingPosition, transition);
    const moving = !this.options.reducedMotion && this.state.phase === 'reading';
    // Keep the current framing fixed throughout a page turn.
    if (this.state.phase !== 'turning') this.cameraOffset.lerp(moving ? this.pointer : new THREE.Vector2(), 0.035);
    this.camera.position.x += this.cameraOffset.x * 0.1;
    this.camera.position.y += this.cameraOffset.y * 0.045;
    this.look.set(0, THREE.MathUtils.lerp(1.65, 0.75, transition), 0);
    this.camera.lookAt(this.look);
  }

  private tick = (now: number) => {
    if (this.disposed || this.graphicsLost) return;
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
      const t = this.inspectionProgress ?? clamp01((now - this.motionStart) / (TURN_DURATION * 1000));
      this.turningProgress = t;
      const pose = turnPose(t);
      this.setPopup(this.currentRig, pose.outgoing);
      this.setPopup(this.nextRig, pose.incoming);
      this.currentRig!.gltf.scene.visible = pose.showOutgoing;
      this.nextRig.gltf.scene.visible = pose.showIncoming;
      if (this.turnPage) this.turnPage.visible = pose.showPage;
      this.sample(this.turnAction, this.direction > 0 ? pose.page : 1 - pose.page);
      this.sample(this.readingAction, pose.showOutgoing ? pose.outgoing : pose.incoming);
      this.bookMixer?.update(0);
      if (pose.showIncoming && this.textIndex !== this.nextIndex) this.setText(this.nextIndex);
      if (this.text) {
        this.text.visible = pose.showText;
        this.text.material.opacity = pose.textOpacity;
      }
      if (t >= 1) this.finishTurn();
    }
    this.updateCamera();
    this.renderer.render(this.scene, this.camera);
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
    this.frame = requestAnimationFrame(this.tick);
  };

  private resize = () => {
    const { width, height } = this.element.getBoundingClientRect();
    if (!width || !height) return;
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, width < 768 ? 1.5 : 1.75));
    this.renderer.setSize(width, height);
    if (this.backdrop?.image) {
      const source = this.backdrop.image as HTMLImageElement;
      const imageAspect = source.width / source.height;
      const viewAspect = width / height;
      this.backdrop.repeat.set(Math.min(1, viewAspect / imageAspect), Math.min(1, imageAspect / viewAspect));
      this.backdrop.offset.set((1 - this.backdrop.repeat.x) / 2, (1 - this.backdrop.repeat.y) / 2);
    }
    this.updateCamera();
  };

  private publish(change: Partial<BookSnapshot>) {
    this.state = { ...this.state, ...change };
    this.options.onChange({ ...this.state });
  }

  private contextLost = (event: Event) => {
    event.preventDefault();
    this.graphicsLost = true;
    cancelAnimationFrame(this.frame);
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
    cancelAnimationFrame(this.frame);
    this.observer.disconnect();
    this.renderer.domElement.removeEventListener('webglcontextlost', this.contextLost);
    this.bookMixer?.stopAllAction();
    for (const promise of this.cache.values()) void promise.then(rig => { rig.mixer.stopAllAction(); this.disposeObject(rig.gltf.scene); }).catch(() => {});
    this.cache.clear();
    if (this.text) this.text.material.map?.dispose();
    this.disposeObject(this.scene);
    this.textures.forEach(texture => texture.dispose());
    this.environmentTarget?.dispose();
    this.renderer.dispose();
    this.renderer.domElement.remove();
  }
}
