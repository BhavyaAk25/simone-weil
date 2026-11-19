# Book object: Stripe-quality rebuild, 18 November 2026

Owner: Book agent (`docs/QUALITY-SPEC.md`, section A). This records what was built, why, how to rebuild it, what was measured in a real browser, and what is still weak. A passing build or a Blender render is not acceptance; the evidence frames below come from headless Chrome against the dev server.

## What changed

### Binding (one continuous skinned mesh)
- `Binding` is one leather mesh: back board, rounded spine and front board, with their edges, head and tail rounds, joint grooves and turn-ins, all in one surface. There are no separate board boxes any more.
- An armature named `Spine` (the stable node name, still a sibling of `BookRoot`) carries 11 bones, `binding.00` to `binding.10`, placed along the spine curve at even arc length. `binding.00` is the back board and never moves. `binding.10` is the front board: it turns about the same pivot as `CoverHinge` (X = 0, Z = 0.26 in Blender), so the cover, the left page block and the reading hinge stay in step with it.
- The spine is an analytic Hermite curve between the two board edges. Closed, its handle length is 0.52, which gives a convex rounded spine about 0.13 proud of the joints (outer arc 0.635). Open, the handle relaxes to 0.12 and the spine lies flat under the gutter. Every frame of the `open` clip is baked from that curve, so the leather bends through rounded joints with no rigid hinge.
- Cross-section: board 0.042 thick, spine shell 0.020. The joint has a 7.5 mm hinge groove, and the thickness ramps between board and spine.
- Edges: the fore-edges and the head and tail use superellipse rounds (exponent 0.5): soft but square-shouldered, like leather turned over board. The plan-view corners are rounded at r = 0.05.
- Squares: the boards overhang the page block by 0.072 at the fore-edge (3% of 2.4) and 0.095 at head and tail (3% of 3.1).
- The inner face of the spine uses a dark `crash` lining material. The inner faces of the boards show the leather turn-ins around printed `endpaper` pastedowns.

### Page blocks
- `RightPage` (under `BookRoot`) and `LeftPage` (under `CoverHinge`) are now complete backed blocks, not single sheets over 32 striped layers. Each has four materials:
  - `paper`: the top surface, exactly `paper_height()`, with a soft roll down into the gutter;
  - `page_edge`: head, tail, fore-edge and back faces;
  - `endpaper`: the underside;
  - `headband`: striped silk beads at head and tail.
- Each block sits flat on its board (Y = 0.045), so nothing brown shows under the pages.
- A `Closed` morph target is driven by the `open` clip. When the book is shut, each sheet keeps its height fraction, the tops flatten to meet with a 3 mm gap, and the middle sheets shift up to 0.035 toward the spine. That one displacement produces both the rounded back and the concave fore-edge of a rounded-and-backed book. The morph weight is `(angle/π)^1.3`, so the pages relax as the cover opens. It is exactly 0 when open, so every chapter hinge stays on the agreed surface.
- Sheet lines: `paper-stock-edge.webp` has about 230 uneven sheets, each with its own tone and a slight drift along the edge. The edge colour is a warm ivory, toned to match the page tops. The two olive endpaper sheets show as a thin band at the board side.
- A silk `Ribbon` leaves the gutter at the tail, crosses the edge and the square, and ends in a swallowtail just past the board.

### Front cover v2 and spine (`cover-*.webp`, one atlas)
The atlas is 3072 × 2160. Its layout is documented in `scripts/make-cover-textures.py` and mirrored in `build_book.py`.

Front cover:
- Her 1942 photograph is printed straight onto the leather as an engraver's line screen: 118 lines, very slightly bowed, with width modulated by tone, in warm ivory ink. A second espresso ink is used only for the deepest shadows.
- The photo's pale ground is removed with a flood-fill segmentation plus a torso polygon, so no rectangle or frame prints. The image dissolves into the leather toward the tail.
- Ink skips some of the grain's pores and has its own satin roughness.
- Lettering is small brass foil:
  - "The Life of / Simone Weil" at the top left;
  - a square "SW" badge at the top right;
  - "1909 – 1943" and "A life in 12 chapters" at the foot.
- Foil is pressed in: a debossed bevel in the normal map, a darkened pressed halo, metalness from the foil mask, and roughness 0.20.

Spine:
- It keeps the engraved likeness (`simone-weil-spine.jpg`), printed upright in sepia ink between two foil rules, plus a foil title and a small badge.
- It was composed as the visitor sees it in the entrance pose, where the book's tail is uppermost. In that pose the likeness reads upright and the title reads top to bottom (checked in the browser).

Back board: a small blind-stamped badge (depth only).

Edge wear: edges and joints are darker and smoother (atlas R = wear, G = roughness).

### Runtime materials (`src/book/materials.ts`)
- **`leather` (book only):** becomes a `MeshPhysicalMaterial`.
  - Base maps: atlas colour, ORM roughness and foil metalness, and the atlas normal.
  - A light clearcoat.
  - `onBeforeCompile` adds a tiled full-grain detail normal and roughness (`leather-normal`/`leather-rough`), sampled in physical units through the binding's `TEXCOORD_1` so grain size is uniform on every face. Foil keeps its own finish.
  - Foil also gets a flake normal map (`binding-glitter`), so it glints as the book tilts.
  - Skinned meshes have `frustumCulled = false`, because their bind pose is the closed book.
- **Book `paper`:** becomes physical with a gentle sheen (0.35) and specular 0.35, plus a subtler bump.
- **`page_edge`, `endpaper`, `headband`, `ribbon`, `crash`:** each has its own treatment. The silks use sheen.
- **Chapter materials (`cardStock`):** behave as before. Chapter `leather` card keeps a fine 3 × 3 grain.

### Typeset writing page (`src/book/paper.ts`)
- The page is set as a verso: outer margin 138, gutter margin 104, on a 1536 × 1746 layout drawn at 4/3 resolution (2048 × 2328) for the loupe and 2× screens.
- Running head: "CHAPTER n" on the outer side and the place toward the gutter, both in letterspaced small capitals.
- Title in Cormorant Garamond 500, 96–106 px, then italic dates and a short rule.
- Body text is justified. Loose lines are capped at 2.3 × the word space; the last line is ragged. The first three words are in small capitals.
- The quotation is indented on both sides, in italic, with a hanging opening mark. Its attribution is small capitals "SIMONE WEIL · WORK", and long titles take a second line.
- The folio sits centred in the foot.
- The writing material is now lit (`MeshStandardMaterial`), so the ink dims with the room and the lamp instead of glowing.
- `userData.textLayout` reports `bodySize`, `quoteSize`, line counts, `attributionBaseline` and `fits`.

## Contracts

Unchanged:
- Node names: `BookRoot`, `CoverHinge`, `Spine`, `LeftPage`, `RightPage`, `TurnPage`, `FrontCover`, `BackCover`, `Front cover art`, `Spine title`, `ReadingHinge`, `ReadingPanel`.
- Clips `open` (0 closed to 1 open, 2.0 s), `turn` and `reading`.
- `paper_height()` and the page footprint.
- The reading panel transforms.

What the stable names now are:
- `FrontCover`, `BackCover` and `Front cover art` are empty transform markers at the board centres. The endpapers are children of the two cover markers.
- `Spine` is the armature.
- `Spine title` is an empty parented to bone `binding.05`.

Legitimate validator changes (book section of `scripts/validate-assets.mjs`):
1. **Skinning.** `sampleBounds` now evaluates glTF skins (joint world × inverse bind, weights normalised), as glTF 2.0 §3.7.3 requires. The bounds therefore measure the real bent binding rather than its bind pose. It also checks that skin weights sum to 1.
2. **Required materials.** For the book these are now `leather`, `paper` and `page_edge`. `brass` is no longer required, because the foil lives in the leather atlas.

## Rebuild

```sh
python3 scripts/make-cover-textures.py      # binding atlas, leather grain, glitter
python3 scripts/make-paper-texture.py       # paper stock, page edges, endpaper, headband
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup \
  --python scripts/blender/build_book.py -- --book
npm run validate:assets
```

`--book` writes `public/models/book.glb`, `assets/source/book.blend` and `public/posters/book.webp` (the poster applies the same atlas through `texture_cover_for_render`). Never rebuild chapters for book-only work.

## Measured results (18 November 2026)

### Asset checks
`npm run validate:assets` passes all 15 assets. Book figures:
- Size and budget: `book.glb` is 0.71 MiB (budget 5 MiB), 15 primitives (budget 256), 12,328 triangles. It has one skin with 11 joints and no embedded runtime textures beyond Blender's two 256 px grain images (one shared).
- Clip lengths: `open` 2.0 s, `turn` 1.4 s, `reading` 1.0 s.
- Closed bounds (skinned, with page morphs at weight 1): X −0.070…2.490, Y 0…0.520, Z ±1.645 (ribbon tip to 1.735). The rounded spine stands 0.13 proud of the joints.
- Open bounds: X ±2.490, Y 0…0.2567.
- Turn endpoints and the flat or raised reading panel are unchanged: the panel rises to Y 0.976 at 18°, and X stays at −2.25…−0.20.

### Code checks
- `npm run typecheck` passes.
- `npx vitest run tests/book` passes (6 files, 39 tests).

### Page fit
The 12 typeset pages were rendered in Chrome with the site's fonts. All report `fits: true`:
- body 72–76 px, quotation 65–68 px;
- 9 or 10 body lines;
- attribution baseline at or below 1587 (limit 1590).

### Browser evidence
Frames come from headless Chrome against `npm run dev -- --port 4181`, captured at 1440 × 900 and 2× density, with the entrance frozen through `?inspect`. Files are in `docs/qa/rebuild/book/`:

| File | Shows |
|---|---|
| `01-closed-spine.jpg` | entrance: standing spine, upright sepia likeness, foil title top to bottom, badge |
| `02-cover-rising.jpg`, `03-cover-facing.jpg` | the cover turning toward the visitor; line-screen photograph, small foil type |
| `04-closed-on-desk.jpg`, `09-closed-tail-headband-2x.jpg` | closed book: squares, rounded spine, headband, closed blocks meeting with no gap, ribbon |
| `05-cover-opening.jpg` | cover and left block mid-swing on the bending spine |
| `06-open-spread.jpg` | the open spread in the room |
| `07-spine-2x.jpg`, `08-cover-closeup-2x.jpg` | grain, foil bevel, ink screen at 2× |
| `10-writing-page-2x.jpg` | the typeset page on the raised panel |
| `11-gutter-headbands-ribbon-2x.jpg`, `12-fore-edge-square-2x.jpg` | gutter roll, headbands, ribbon, fine sheet lines, board square and turned leather edge |
| `13-phone-390-closed.jpg`, `14-phone-390-open.jpg` | 390 × 844 at 2× |
| `15-turn-forward-mid.jpg`, `16-turn-backward-mid.jpg` | turn at progress 0.5 in both directions (the leaf itself is the Interaction agent's work in progress) |

Measured leather in the cover-facing frame is about sRGB (130, 88, 68) under the room light. The reference tobacco is #785039, (120, 80, 57). The first pass measured (124, 97, 85): grey and pink from too much clearcoat and specular, which was corrected.

### Comparison with the Stripe study
Matched:
- one continuous bent binding;
- an image printed into the material rather than pasted on;
- one foil colour and small type with a corner badge;
- squares, with a pale block showing at the edges;
- fine sheet lines;
- typeset running head and folio;
- foil that glints with movement.

Still short of Stripe:
- the gutter is a soft roll, not their deep curved valley;
- the page has no pointer-following highlight (see below);
- the leaf print and the curl belong to the Interaction agent.

## Remaining limitations

- **Endpapers are rarely visible.** `LeftPage` is rigid with `CoverHinge` (a contract), so the cover and the left block open together and the pastedown is never exposed during opening. The printed endpaper is real geometry inside the turn-ins, but in practice it shows only as the olive endpaper sheets at the board side of every block edge. Showing a full endpaper at opening would need a separate front-board/flyleaf opening, which changes the `open` contract.
- **Block thickness cannot change by chapter.** The top surface must stay `paper_height()` and the blocks rest on the boards, so the visible block thickness is fixed. A per-chapter thickness change would mean changing the page surface contract that every chapter hinge depends on. This is not done.
- **No pointer-following paper highlight.** Book paper now has a physical sheen (0.35) and specular 0.35, so it responds to the room lights and the lamp, but the highlight does not follow the pointer. That needs a faint pointer-driven light in `BookScene` (requested from the integrator).
- **The writing panel still sits flat at 18°.** Its front edge is up to 0.03 above the curved page near the gutter, because the panel contract requires a flat card (validator: flat thickness < 0.03). Typography is now book-like, but the panel's attachment is unchanged.
- **The spine is not bone-perfect at the joints.** The bones follow an analytic curve, not a cloth simulation. Between 30° and 120° of opening the spine shell compresses rather than keeping a constant arc length (hidden under the gutter; the visible joint stays rounded).
- **Headband scale.** Headbands are a bead of 0.0095 radius with diagonal stripes. At 2× they read clearly as stitched silk; at 1× they are a small striped mark at the gutter, as on a real book.
- **Figures in the type.** Cormorant's old-style "1" resembles a small capital I in the running head and folio. Canvas 2D cannot switch to lining figures.
- **Phone framing.** At 390 × 844 the open book's left board edge touches the screen edge. Framing belongs to `BookScene`.
- **Not tested on physical devices.** All frames are headless Chrome on macOS (ANGLE/Metal).
