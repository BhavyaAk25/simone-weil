import * as THREE from 'three';

/**
 * Book and scenery materials: texture loading and material preparation.
 * Owned by the Book agent (docs/QUALITY-SPEC.md, docs/BOOK-QUALITY.md). BookScene calls
 * loadBookTextures once and prepareMaterials for the book (cardStock false) and each
 * chapter (cardStock true).
 *
 * The book binding is one skinned mesh with material `leather`; its atlas
 * (scripts/make-cover-textures.py) carries the tobacco leather, edge wear, the
 * line-screen photograph, foil and lettering. A tiled full-grain map is added in
 * physical units through TEXCOORD_1, and foil glints through a flake normal map.
 */
export type BindingTextures = {
  color: THREE.Texture; orm: THREE.Texture; normal: THREE.Texture;
  leatherNormal: THREE.Texture; leatherRough: THREE.Texture; glitter: THREE.Texture;
  edge: THREE.Texture; endpaper: THREE.Texture; headband: THREE.Texture;
};
export type BookTextures = {
  paper?: THREE.Texture;
  walnut?: THREE.Texture;
  backdrop?: THREE.Texture;
  binding?: BindingTextures;
  [extra: string]: unknown;
};

const asset = (path: string) => `${import.meta.env.BASE_URL}${path.replace(/^\//, '')}`;

/** Load every texture the book needs. `track` receives each texture so the scene can dispose it. */
export async function loadBookTextures(renderer: THREE.WebGLRenderer, track: (texture: THREE.Texture) => void): Promise<BookTextures> {
  const loader = new THREE.TextureLoader();
  const load = (path: string) => loader.loadAsync(asset(path)).then(texture => { track(texture); return texture; });
  const anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
  const names = ['cover-color', 'cover-orm', 'cover-normal', 'leather-normal', 'leather-rough', 'binding-glitter', 'paper-stock-edge', 'endpaper-color', 'binding-headband'];
  const bindingReady = Promise.all(names.map(name => load(`textures/${name}.webp`)));
  const [paper, walnut, backdrop] = await Promise.all([load('textures/paper-stock.webp'), load('textures/walnut.webp'), load('textures/bookshop.webp')]);
  for (const texture of [paper, walnut]) {
    texture.colorSpace = THREE.SRGBColorSpace;
    texture.wrapS = texture.wrapT = THREE.MirroredRepeatWrapping;
    texture.anisotropy = anisotropy;
  }
  // The paper stock is generated to tile exactly (scripts/make-paper-texture.py).
  paper.wrapS = paper.wrapT = THREE.RepeatWrapping;
  walnut.repeat.set(3, 3);
  const [color, orm, normal, leatherNormal, leatherRough, glitter, edge, endpaper, headband] = await bindingReady;
  // glTF UVs put v = 0 at the image top, so the atlas images must not be flipped.
  for (const texture of [color, orm, normal, edge, headband]) { texture.flipY = false; texture.anisotropy = anisotropy; }
  for (const texture of [color, edge, endpaper, headband]) texture.colorSpace = THREE.SRGBColorSpace;
  for (const texture of [leatherNormal, leatherRough, glitter, endpaper]) {
    texture.wrapS = texture.wrapT = THREE.RepeatWrapping;
    texture.anisotropy = anisotropy;
  }
  edge.wrapS = THREE.MirroredRepeatWrapping;
  // Chapter scenery that still uses leather-coloured card keeps a 3 x 3 repeat of the grain.
  const chapterLeather = leatherNormal.clone();
  chapterLeather.repeat.set(3, 3);
  chapterLeather.needsUpdate = true;
  track(chapterLeather);
  return {
    paper, walnut, backdrop, chapterLeather, chapterLeatherRough: leatherRough,
    binding: { color, orm, normal, leatherNormal, leatherRough, glitter, edge, endpaper, headband },
  };
}

/** Full-grain detail, foil flakes and edge wear on the binding. */
function bindingShader(material: THREE.MeshPhysicalMaterial, t: BindingTextures) {
  const uniforms = {
    uDetailNormal: { value: t.leatherNormal },
    uDetailRough: { value: t.leatherRough },
    uGlitter: { value: t.glitter },
  };
  material.onBeforeCompile = shader => {
    Object.assign(shader.uniforms, uniforms);
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', `#include <common>
#ifndef USE_UV1
attribute vec2 uv1;
#endif
varying vec2 vGrainUv;`)
      .replace('#include <uv_vertex>', `#include <uv_vertex>
\tvGrainUv = uv1;`);
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <common>', `#include <common>
uniform sampler2D uDetailNormal;
uniform sampler2D uDetailRough;
uniform sampler2D uGlitter;
varying vec2 vGrainUv;`)
      // Grain roughness: polished tops, matte creases. Foil keeps its own finish.
      .replace('#include <metalnessmap_fragment>', `#include <metalnessmap_fragment>
\tfloat foilMask = smoothstep(0.35, 0.85, metalnessFactor);
\t// Worn edges and joints are rubbed smooth: less grain there (atlas R = wear).
\tfloat wearMask = texture2D(metalnessMap, vMetalnessMapUv).r;
\tfloat grainRough = texture2D(uDetailRough, vGrainUv * 0.45).g;
\troughnessFactor = clamp(mix(roughnessFactor * (0.45 + 0.8 * grainRough), roughnessFactor, foilMask), 0.08, 1.0);`)
      .replace('#include <normal_fragment_maps>', `#include <normal_fragment_maps>
\t{
\t\tvec3 grain = texture2D(uDetailNormal, vGrainUv * 0.45).xyz * 2.0 - 1.0;
\t\tvec3 flake = texture2D(uGlitter, vGrainUv * 18.0).xyz * 2.0 - 1.0;
\t\t// Leather grain everywhere except where foil was pressed smooth.
\t\tnormal = normalize(normal + tbn * vec3(grain.xy * 0.55 * (1.0 - foilMask) * (1.0 - 0.75 * wearMask), 0.0));
\t\t// Foil: tiny flakes tilt in their own directions, so it glints as the book moves.
\t\tnormal = normalize(normal + tbn * vec3(flake.xy * 0.42 * foilMask, 0.0));
\t}`);
  };
  material.customProgramCacheKey = () => 'book-binding';
}

function physical(from: THREE.MeshStandardMaterial, extra: THREE.MeshPhysicalMaterialParameters) {
  const material = new THREE.MeshPhysicalMaterial({ name: from.name, color: from.color.clone(), roughness: from.roughness, metalness: from.metalness, side: from.side });
  material.setValues(extra);
  return material;
}

export function prepareMaterials(object: THREE.Object3D, textures: BookTextures, cardStock = false) {
  object.traverse(node => {
    if (!(node instanceof THREE.Mesh)) return;
    node.castShadow = true;
    node.receiveShadow = true;
    // A skinned binding moves far from its bind pose; never cull it on the stale bounds.
    if ((node as THREE.SkinnedMesh).isSkinnedMesh) node.frustumCulled = false;
    const list = Array.isArray(node.material) ? node.material : [node.material];
    const replaced = list.map(material => {
      if (!(material instanceof THREE.MeshStandardMaterial)) return material;
      const name = material.name.toLowerCase();
      const b = textures.binding;
      // Pop-up scenery is all card: coloured stock gets the same fibres as the pages.
      if (cardStock && textures.paper && !name.includes('paper') && !material.map && material.metalness < 0.2) {
        material.map = textures.paper;
        material.bumpMap = textures.paper;
        material.bumpScale = 0.4;
        material.roughness = Math.max(material.roughness, 0.82);
      }
      if (!cardStock && name === 'leather' && b) {
        // The binding atlas: leather, wear, ink, foil (ORM: R wear, G roughness, B foil).
        const leather = physical(material, {
          map: b.color, roughnessMap: b.orm, metalnessMap: b.orm, normalMap: b.normal,
          roughness: 1, metalness: 1, color: new THREE.Color('#ffffff'),
          // A thin, worn finish over the grain.
          clearcoat: 0.05, clearcoatRoughness: 0.45,
          envMapIntensity: 0.75,
        });
        leather.normalScale.set(1, -1);
        bindingShader(leather, b);
        material.dispose();
        return leather;
      }
      if (!cardStock && name === 'crash') { material.color.set('#2e1e14'); material.roughness = 0.95; }
      if (!cardStock && name === 'page_edge' && b) {
        // Fine, uneven sheet lines on the block edges, with a little relief.
        material.map = b.edge;
        material.bumpMap = b.edge;
        material.bumpScale = 1.2;
        // Toned to sit with the warm ivory page tops, not brighter than them.
        material.color.set('#e2d2b4');
        material.roughness = 0.82;
        material.envMapIntensity = 0.5;
      }
      if (!cardStock && name === 'endpaper' && b) {
        material.map = b.endpaper;
        material.color.set('#ffffff');
        material.roughness = 0.8;
      }
      if (!cardStock && name === 'headband' && b) {
        const silk = physical(material, { map: b.headband, color: new THREE.Color('#ffffff'), roughness: 0.42, sheen: 0.8, sheenRoughness: 0.35, sheenColor: new THREE.Color('#f0d9b8') });
        material.dispose();
        return silk;
      }
      if (!cardStock && name === 'ribbon') {
        const silk = physical(material, { color: new THREE.Color('#5c2019'), roughness: 0.36, sheen: 1, sheenRoughness: 0.3, sheenColor: new THREE.Color('#d98f7a') });
        material.dispose();
        return silk;
      }
      if (name.includes('paper') && textures.paper) {
        // Replace Blender's coarse packed grain with smooth, fibrous stock.
        // That grain carried the base colour, so restore it as a factor.
        // Matches the approved warm ivory: the old grain was linear data read as
        // sRGB, and the other paper colours were multiplied by a beige sheet.
        if (name === 'paper' && material.map) material.color.set('#d4bd99');
        else material.color.multiply(new THREE.Color(0.845, 0.734, 0.581));
        material.map = textures.paper;
        material.bumpMap = textures.paper;
        material.bumpScale = cardStock ? 0.5 : 0.35;
        material.roughness = cardStock ? 0.9 : 0.74;
        if (!cardStock) {
          // Book paper: a gentle sheen that follows the light, never a gloss.
          const sheet = physical(material, {
            map: material.map, bumpMap: material.bumpMap, bumpScale: material.bumpScale,
            sheen: 0.35, sheenRoughness: 0.55, sheenColor: new THREE.Color('#fff4de'),
            specularIntensity: 0.35, envMapIntensity: 0.55,
          });
          material.dispose();
          return sheet;
        }
      }
      if (name.includes('wood') && !material.map) material.map = textures.walnut ?? null;
      if (cardStock && (name === 'leather' || name === 'leather_dark')) {
        // Chapter props in leather-coloured card keep a fine grain.
        material.map = null;
        material.bumpMap = null;
        material.color.set(name === 'leather' ? '#5a3826' : '#382216');
        const grain = textures.chapterLeather as THREE.Texture | undefined;
        if (grain) { material.normalMap = grain; material.normalScale.set(0.6, 0.6); }
        material.roughness = 0.8;
      }
      material.needsUpdate = true;
      return material;
    });
    node.material = Array.isArray(node.material) ? replaced : replaced[0];
  });
}
