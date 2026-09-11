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

Stable nodes are `BookRoot`, `CoverHinge`, `Spine`, `LeftPage`, `RightPage`, `TurnPage`, `FrontCover`, `BackCover`, `Front title`, `Spine title`, `ReadingHinge`, and `ReadingPanel`. Transform the entire exported scene: `Spine` is a sibling of `BookRoot`.

- `open`: 2.0 seconds, 0=closed, 1=fully open when normalized. It rotates `CoverHinge` and compresses `Spine`. Closed book bounds are approximately X [0,2.52], Y [0,.52], Z ±1.65. Center its presentation using X=-1.25 before whole-book orientation.
- `turn`: 1.4 seconds, right-to-left. `TurnPage` has four baked curl morph poses. Both flat endpoints match the curved page +.006. Reverse for backward turns. Hide this sheet at rest.
- `reading`: 1.0 second, 0=flat and 1=18° raised toward the visitor. It rotates `ReadingHinge` around X. This hinge is under `CoverHinge`, so a flat reading panel closes inside the book correctly.
- Chapter `unfold`: 1.0 second, 0=flat toward the visitor, 1=upright. Meshes export upright by default. Runtime must sample zero before showing them.

The book exports open; the reading panel exports flat. Explicitly sample `open=0`, `reading=0`, and hide `TurnPage` before presenting the closed book. Do not rely on default transforms. Closed-book validation samples both relevant clips together.

## Raised writing panel

The panel responds to the user's request for writing to be slightly raised in 3D so it is easier to read.

`ReadingHinge` is at open-world X=-1.225, Z=1.43, Y=`pageHeight(-1.225,1.43)+.008`. Its local panel spans X [-1.025,1.025], Z [-2.33,0]. The panel top is local Y=0, with .006 thick ivory stock beneath it. UV [0,0] is the front-left corner and UV [1,1] the rear-right. Parent the transparent writing mesh to this hinge, centered at local `(0,.010,-1.165)`, sized 2.05 × 2.33, facing upward. It folds flat before a page turn and rises only after the new page settles. Mobile HTML remains available below the scene.

## Sequencing and collisions

The main application owns extraction, cover reveal, descent, camera movement, and sequence timing. Keep chapter scenery hidden until the cover is fully open and settled. Fold both scenery and reading panel completely before the turning sheet starts. Hide collapsed outgoing geometry during page crossing. Sample the incoming chapter at zero before revealing it, then unfold after the sheet settles. Prevent overlapping transitions and restore writing with the panel.

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
