# Blender → browser pipeline

Blender 5.1.1 creates actual thin card-stock meshes, leather boards, 32 individually curved leaf layers per side, brass lettering, a flexible page morph, a hinged reading panel, and independently folding chapter scenes. The interactive book is geometry. The reference image is an appearance target, not a screenshot used in place of the model.

## Rebuild

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --python scripts/blender/build_book.py -- --milestone
```

The first milestone writes `book.glb`, `chapter-01.glb`, and `chapter-02.glb` into `public/models/`; editable Blender scenes go into `assets/source/`, and 1440 × 1000 WebP fallback renders into `public/posters/`. Source scenes contain the book, chapter, studio lights, and poster camera. Chapter GLBs contain only their chapter geometry. `scripts/blender/update_manifest.py` records metadata from the actual binaries. `.blend` sources use Git LFS; GLBs remain directly deployable.

Export uses Y-up, selected objects, NLA tracks, forced sampling, morph targets and embedded materials. Every chapter mesh has an animated paper-hinge ancestor. Materials use sRGB-to-linear colours, deterministic packed paper/leather grain, and a restrained palette of ivory, tobacco, dark green-grey, and brass. Mesh batches preserve hinges while reducing object/draw overhead.

## Coordinates and paper

Blender `(x, y, z)` maps to glTF `(X, Y, Z) = (x, z, -y)`. The open book footprint is X ±2.52 and Z ±1.65; the visitor faces the book from positive Z. The spine follows Z.

The curved top page height in browser coordinates is:

```text
u = clamp((abs(X) - .018) / 2.4, 0, 1)
v = (1.55 - Z) / 3.1
Y = .202 + .115*sin(pi*u)*exp(-1.8*u) - .007*u*u*cos((v-.5)*pi)
```

The stronger curvature replaces the almost-flat first prototype. Its maximum is about Y=.257. Hinge positions use the actual page height +.004. Grounded card-foot vertices follow this surface; because the gutter is lower, valid open scene feet can reach Y≈.206. Folded scene bounds are checked separately: X ±2.50, Z ±1.64, Y [.213,.32]. Thin layered details are normalized above their hinge before export, correcting the old negative-depth geometry that rotated below the paper.

## Book and animation contract

Stable nodes are `BookRoot`, `CoverHinge`, `Spine`, `LeftPage`, `RightPage`, `TurnPage`, `FrontCover`, `BackCover`, `Front cover art` (until 18 November: `Front title`), `Spine title`, `ReadingHinge`, and `ReadingPanel`. Transform the entire exported scene: `Spine` is a sibling of `BookRoot`.

- `open`: 2.0 seconds, 0=closed, 1=fully open when normalized. It rotates `CoverHinge` and compresses `Spine`. Closed book bounds are approximately X [0,2.52], Y [0,.52], Z ±1.65. Center its presentation using X=-1.25 before whole-book orientation.
- `turn`: 1.4 seconds, right-to-left. `TurnPage` has four baked curl morph poses. Both flat endpoints match the curved page +.006. Reverse for backward turns. Hide this sheet at rest.
- `reading`: 1.0 second, 0=flat and 1=18° raised toward the visitor. It rotates `ReadingHinge` around X. This hinge is under `CoverHinge`, so a flat reading panel closes inside the book correctly.
- Chapter `unfold`: 1.0 second, 0=flat toward the visitor, 1=upright. Meshes export upright by default. Runtime must sample zero before showing them.

The book exports open; the reading panel exports flat. Explicitly sample `open=0`, `reading=0`, and hide `TurnPage` before presenting the closed book. Do not rely on default transforms. Closed-book validation samples both relevant clips together.

## Raised writing panel

The panel responds to the user's request for writing to be slightly raised in 3D so it is easier to read.

`ReadingHinge` is at open-world X=-1.225, Z=1.43, Y=`pageHeight(-1.225,1.43)+.008`. Its local panel spans X [-1.025,1.025], Z [-2.33,0]. The panel top is local Y=0, with .006 thick ivory stock beneath it. UV [0,0] is the front-left corner and UV [1,1] the rear-right. Parent the transparent writing mesh to this hinge, centered at local `(0,.010,-1.165)`, sized 2.05 × 2.33, facing upward. It folds flat before a page turn and rises only after the new page settles. Mobile HTML remains available below the scene.

## Sequencing and collisions

The main application owns extraction, cover reveal, descent, camera movement, and sequence timing. Keep chapter scenery hidden until the cover is fully open and settled. Fold both scenery and reading panel completely before the turning sheet starts. Sample the incoming chapter at zero before revealing it, then unfold after the sheet settles. Prevent overlapping transitions and restore writing with the panel. Since 18 November the collapsed geometry is no longer hidden during the crossing; see *Printed turning leaf* below.

The model uses controlled hinges, not live paper physics. Collapsed cards are nested layers inside the page footprint. Their overlap must be covered/hidden during the page crossing; no default upright pose may appear for a frame.

## Corrected first milestone inspection — 10 September 2026

The rejected geometry was rebuilt with detailed multi-storey facades, stone courses, mansard dormers, iron balconies, connected person silhouettes, leafy paper branches, thin desk cards, a true cut-through arch, and a supported medallion. Floating decorative disks and thick desk groups were removed. Page edges are curved real leaves, and the reading panel is genuine hinged paper.

Measured bounds from the exported GLBs (glTF X,Y,Z):

| Asset | Folded min | Folded max | Open maximum height |
|---|---|---|---|
| Chapter 1 | [-1.9500,.2201,-1.4250] | [2.4301,.3077,1.1535] | 2.2844 |
| Chapter 2 | [-1.7300,.2192,-1.2865] | [2.2200,.3042,1.1324] | 2.2044 |

Book geometry was reduced from 4.4 MiB to approximately 2.04 MiB by using a coarser mesh for the hidden interior leaf layers while retaining detailed top sheets. The first two revised fallback renders were inspected for their geometry, panel, and composition. Their plain studio backdrop is for asset inspection; the browser's walnut bookshop is authored separately by the main agent.

This is **asset inspection, not browser visual acceptance**. The main agent must check entrance frames, forward/backward turns, and the raised writing in the actual website before authoring chapters 3–12. File paths and transforms freeze at that gate. Passing a build, a bounds test, or a Blender render alone cannot establish that gate.

Blender can crash during Metal probing in the restricted process before script execution. The background command succeeded with approved execution outside the sandbox. No manual scene state is required for reproduction.

## Browser gate completed — 10 September 2026

The main agent inspected the actual 1440 × 1000 browser entrance, raised chapter-one writing, chapter-two reading, folded reverse pose (0.24), and both turn directions at 0.5. The revised camera gently pulls back and arcs during the crossing so the curved sheet stays below the header and is not viewed exactly edge-on. Writing is larger, dark and fully contained on the 18-degree panel. At 390 × 844, HTML text appears below the 3D stage; a leftward pointer swipe initiated the next chapter. These checks authorize chapter production; final twelve-spread visual and release checks remain separate.

The coordinate, node, material and animation names above are now frozen. `story_scenes.py` builds chapters 3–12 through the same helpers and hinge normalization. Rebuild them with `--chapters 3 4 5 6 7 8 9 10 11 12`; `--no-render` saves editable sources and GLBs while retaining existing posters for animation-only iteration. Generate fresh posters after changing visible scenery.

## Scoped revision — 11 September

The front cover now includes the photographic portrait and the spine an upright generated engraved adaptation, each with a separate embedded texture/material. The cover label uses 12. The page-turn camera arc is removed at the user's request. A stronger arc-length curl (2.6 radians at midpoint) keeps the leaf inside the fixed reading view; its flat endpoints and clip contract stay the same. The old description of camera pullback above records the earlier gate, not current behavior.

## Separate header artwork pipeline — 13 September

Header sources live in `assets/source/header/`, with `scripts/blender/build_header.py` and `compress_header.py`. This is a UV-textured silhouette render with baked relief, separate from the actual 3D book mesh/animation pipeline. Runtime desktop/phone WebP files have transparent lower edges and contain no interface lettering. See HEADER-ASSETS.md for provenance, sizes and reproduction.

## Lossless shared textures, 18 September 2026

`update_manifest.py` now runs `share_textures.py` after export. It extracts byte-identical images used by multiple GLBs into `public/textures/shared/<sha256>.<extension>`. GLB images reference `../textures/shared/…`; single-use images remain embedded. The optimizer repacks buffer views with four-byte alignment and remaps accessor, sparse and extension references. Before writing, it verifies identical non-image semantics/payload hashes and exact image bytes. Repeating it is byte-idempotent, including after a subset is freshly exported. Deploy models and shared textures together.

The release removes 2,166,016 GLB bytes and adds 371,405 shared bytes, saving 1,794,611 bytes across the collection. All 13 geometry/animation fingerprints match the prior exports. The evidence is `docs/qa/shared-texture-integrity.json`. Asset validation rejects noncanonical/remote paths, escaped symlinks, missing or altered files and wrong MIME signatures.

Authoring inputs `paris-facade.webp`, `simone-weil-portrait.png` and `simone-weil-spine.jpg` moved to `assets/source/textures`; Blender packs them into sources as before. This removes 1,366,508 unused bytes from deployment, without deleting editable source material. No mesh compression or reauthoring was applied.

## Printed turning leaf and chapter 1-2 art pass, 18 November 2026

Following the Stripe Press review (`docs/STRIPE-PRESS-REVIEW.md`), folded pieces now travel with the page they are hinged to instead of disappearing.

- **Runtime contract.** At the start of a turn the runtime folds both spreads flat for one frame and renders two orthographic top-down "prints" of the half-spreads into half-float render targets (1536 × 1971, mipmapped, anisotropic). The `TurnPage` front shows the right half, its back the left half, unlit, so the replay matches the lit page. UVs are generated at runtime from the flat leaf positions (u from the gutter, v from the front edge); `geometry.boundingBox` cannot be used because it includes the curl morphs.
- **Clipping at the gutter.** Each chapter rig has one world-space clipping plane (`X = 0`). While the leaf travels, the outgoing rig keeps only the side that is not turning; the incoming rig shows only the turning side, folded, once the leaf is clear of it (`TURN_LIFTED`), and becomes whole when the leaf lands (`TURN_LEAF_END`). Pieces must not cross the gutter.
- **Writing and panel.** The writing is never faded. It swaps only while the leaf print covers the left page, and the reading hinge is hidden while that print lies on it, because the flat panel sits 0.002 above the landed leaf.
- **Timing.** `TURN_DURATION` is 2.1 s: fold 0.53 s, leaf 0.84 s, settle 0.06 s, unfold 0.67 s. See `src/book/motion.ts`.
- **Paper.** `public/textures/paper-stock.webp` (generated by `scripts/make-paper-texture.py`, tileable, 2048 px) replaces Blender's 256 px packed grain on every paper material at runtime. The colour factors reproduce the previously approved warm ivory. The open pages get a soft gutter shadow and faint edge toning in the shader, and a shaded paper fold covers the 0.036 gap at the spine.
- **Left page stays clear.** Folded pieces lie over whatever is in front of their hinge. Tall rear cards on the left page therefore fold over the writing, and they were only ever visible as tops above the raised panel. Chapters 1 and 2 now keep the left page for the writing alone.
- **Chapter 1.** Luxembourg garden silhouette with the Panthéon dome, the family home, promenade and lamp, a layered plane tree, two desks with distinct figures (Simone with bob, round glasses and satchel; André with cap and book), a Luxembourg planter, and a foreground of flower bed, bench, grass and a stone kerb.
- **Chapter 2.** The Lycée Henri-IV front seen through the cut window, Simone with beret, cape, glasses and book, a laurel bush, library shelf, and a foreground of courtyard paving, book pile with satchel, potted laurel and grass.
- **Folded layering.** For chapters 1 and 2, `normalize_hinges(stack_folds=True)` lifts each folded card by 0.0011 per rank from front to back, so overlapping flat cards never share a depth in the print. Overlapping crown masses also get separate depths, because coincident faces render black in Cycles.

Rebuild with `--chapters 1 2`. Chapters 3-12 keep the earlier art and the old figure and tree helpers, but they use the new paper and printed leaf at runtime.

## Cover, lamp and full chapter art pass, 18 November 2026

- **Front cover.** The separate title, portrait and subtitle meshes are replaced by one plane, `Front cover art` (2.47 × 3.22, material `cover_art`), 0.003 above the front-board inset. The browser maps `public/textures/cover-color.webp`, `cover-orm.webp` (R: unused, G: roughness, B: metalness) and `cover-normal.webp`, all from `scripts/make-cover-textures.py`, with `flipY = false`. The design follows Stripe Press's conventions without copying it: her photograph tipped into a debossed arch with a brass frame, title and details in foil, a monogram badge, blind-tooled leaf corners, and a foil line with 12 dots, one per chapter. The posters apply the same maps in Blender (`texture_cover_for_render`). Every leather surface now uses the tileable `leather-normal`/`leather-rough` grain. Blender text uses the site's Cormorant Garamond.
- **Lamp.** `scripts/blender/build_lamp.py` writes `public/models/lamp.glb` and `assets/source/lamp.blend`. It is a brass banker's lamp with a green cased-glass shade, an opal liner, and a beaded chain whose `pull` clip (0.5 s) dips and springs back. `PullHandle` (material `lamp_hit`) is an invisible pick target, and `LightAnchor` marks the bulb. The runtime places it on the desk behind and to the left of the book. Below 1.15:1 aspect it hides the model, but the Lamp control still works. Switching it fades the room lights, background and environment down and a 2700 K spotlight up (0.7 s on, 0.45 s off). The lamp model casts no shadows of its own, since the light sits inside it. The header and footer dim in CSS. The lamp state is remembered per visitor.
- **Chapters 3-12** (`story_scenes.py`) were rebuilt on the chapter 1-2 pattern:
  - every hinge sits on the right page;
  - each spread has a rear landmark backdrop, a hero construction, figures and a low foreground;
  - places are recognisable: the Le Puy needles, the Brandenburg Gate and Reichstag, sawtooth sheds with smoke, the Aragon sierra and village, Assisi with cypresses, a Troy wall with a Greek frieze, the Gare de Lyon, Notre-Dame de la Garde, the Vieux-Port and a pointu, Manhattan and Westminster, Kentish oast houses, and a library with the three posthumous titles (1947, 1949, 1950).
  - `person()` adds headscarf, short hair, newspaper, suitcase, pick and harvest-basket variants. `broadleaf()` takes a palette for olives.
  - `normalize_hinges(stack_folds=True)` now applies to every chapter, at 0.0009 per rank. Gear spokes and axles sit shallower, keeping chapter 4's folded stack below 0.323.
- **Card stock.** At runtime every non-metallic, untextured chapter material gets the paper-stock map and bump, so coloured card shows the same fibres as the pages.

## Stripe-quality rebuild, 18 November 2026: current contract

This section supersedes "Printed turning leaf…" and the lamp, cover and stable-node notes above, where they differ. Details: `docs/BOOK-QUALITY.md`, `docs/ROOM-LAMP.md`, `docs/INTERACTION.md`, `docs/QUALITY-SPEC.md`.

- **Book.**
  - One continuous skinned leather `Binding` with an 11-bone rig named `Spine`, a rounded spine, hinge grooves, squares, turn-ins, headbands, endpapers and a ribbon.
  - `LeftPage` and `RightPage` are solid page blocks whose top surface is exactly `paper_height()`. The `open` clip now also carries bone tracks and a `Closed` morph.
  - `FrontCover`, `BackCover` and `Front cover art` are empty markers. The cover art lives in the binding textures: the photograph as a 118-line screen, foil lettering and glitter.
  - The validator evaluates skinning.
- **Turn.**
  - The `TurnPage` morph and clip are no longer used, and the prints and clipping planes are gone.
  - `src/book/leaf.ts` bends a runtime 72 × 18 leaf in an S-curve. Chapter pieces are deformed in their vertex shaders so they ride and fold with the leaf, or press flat under it.
  - A click turn takes about 1.0 s; a drag follows the hand's angle about the spine.
  - Any later `onBeforeCompile` must chain, not replace.
- **Room.** `src/book/room.ts` builds a real walnut desk slab (top at y = −0.046) with reflections and a contact-shadow pass. The library photo is a refitted, blurred plane beyond it.
- **Lamp.** `build_lamp.py` makes an Emeralite-proportioned lamp with a ball-chain pull animated in code (no clips). Placement is solved per viewport with a copy of the reading-camera formula in `room.ts`; update it if framing changes.
- **Loupe.** `src/book/loupe.ts` is a 3D reading glass rendered over the scene: brass bezel, walnut handle, lens at 2.5× with refraction and fringe.
- **Chapter foregrounds.** Every foreground hinge moved 0.10 towards the spine (y ≥ −1.30), so folded strips stay inside the leaf while it lifts.
