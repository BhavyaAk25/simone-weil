# Stripe-quality rebuild spec, 18 November 2026

The user rejected the overnight pass in these words: the lamp "floats in the air" and is "gimmicky", the cover "should be a lot better", "the 3D book is not great", pages still show "blocky" things while turning, the page quality is weak, and the loupe is "broken" with a poor handle. The bar is stripe.press in every small detail. This spec comes from a measured study of how Stripe builds its book, followed by a diagnosis of ours. Builders work to it, and acceptance is judged on real browser frames, not renders.

## 1. What Stripe Press actually builds (observed 18 November)

The study used network inventory, the structure of their `book.glb` (inspected, not reused), frames at 2× density and a real-time screencast.

**One shared book model.** `/3d/book.glb`, about 230 KB, Draco-compressed, WebP textures, three.js r185.
- **Cover:** boards and spine are one continuous skinned mesh (~7.6k vertices, one material and UV atlas). Two 5-bone chains (`frontcover1..5`, `backcover1..5`) bend each board through the joint, so the hinge creases and the spine rounds as it opens; there is no rigid hinge.
- **Inside the spine:** a separate `crash` mesh (the gauze lining) and an `innerspine` plane give depth at the gutter.
- **Pages:** two page blocks (`pages1`, `pages2`). Each has three materials (top sheet `endpaper`, `sides` and fore-edge `front`) and one morph target, so block thickness shifts between left and right as you read.
- The turning leaf is not in the model; it is generated at runtime.

**Per-title cover maps** (KTX2): `diffuse`, `bump` and `foil` (a foil mask), plus `gloss` on some titles. Shared maps: `bump_buckram` (cloth weave), `bump_paper`, `diffuse_overlay` and `glitter`, a sparkle map that makes foil glint as it moves.

**Cover design.** Lots of negative space. One bespoke image is printed or foiled into the cloth, so it is part of the material rather than a pasted rectangle: The Dream Machine and Poor Charlie's Almanack print a portrait photograph straight onto the cloth as a halftone or line screen. Small, quiet type sits in the corners, there is one foil colour, and a small square badge is the only ornament. The boards stand proud of the page block on three sides, and the pale page block shows at the edges.

**Pages.**
- Each page is a typeset image (`page-215.png`) with real running heads, folios and text. The page block curves into a deep, soft gutter, and the fore-edges show many fine, uneven sheet lines.
- Paper has a gentle bump; there is no speckle.
- A soft specular sheen on the paper follows the pointer.

**Interaction.**
- The closed book turns a little to follow the pointer, and light glides across the cloth weave and foil as it does.
- The page turn is about half a second. The leaf bends in an S-curve, shows its printed text, and casts a soft moving shadow; the next page is already in place beneath it. A drag follows the hand.
- The magnifier is a real lens over the page.
- Nothing pops, flashes or changes material abruptly.

## 2. Diagnosis of ours

| Fault | Cause | Evidence |
|---|---|---|
| Lamp floats | The room is a flat photo (`scene.background`) and the "desk" is an invisible shadow-catcher plane. Any object away from the book cannot sit on the photographed desk, because perspective, contact and occlusion do not match. The lamp base lands on the photo's window/back-edge region. | `docs/qa/stripe-review/full-lamp-*` |
| Lamp looks gimmicky | Primitive proportions, a solid cylinder shade, painted chain beads, no contact shadow or ambient occlusion, emissive "glow" materials, a hard spotlight pool | same |
| Loupe broken | Its render pass draws `scene.background` (screen-space) into the square target, so the lens shows the whole room photo shrunk instead of the magnified region. The bezel and handle are a CSS gradient that does not read as metal or wood, and the handle angle and size are arbitrary. | `full-loupe-*` |
| Blocky turn | Sequential fold, then leaf, then unfold. Mid-fold, the cards are seen edge-on as grey strips. Folded flat, whole scenes become solid coloured slabs, printed onto the leaf as blocks. New pieces rise from flat white rectangles. | real-time screencast, 18 November |
| Book model | Rigid box boards, a hinged cover with no joint, a box-like spine, page block layers that read as stripes, a brown slab under the pages, no headbands, endpapers, turn-ins or squares. One flat leather colour with weak grain. | entrance frames |
| Cover design | A pasted photo rectangle with a busy arch frame, too many elements competing, a heavy title, decorative corners. It reads as a template, not a designed book. | `full-entrance-cover` |
| Page quality | The writing panel is a flat card floating at 18°. Typography is functional but has no book craft: no running head, poor measure and hierarchy, a dull folio. Paper has no sheen, no show-through and no believable edge. | spreads |

## 3. Targets (acceptance gates)

Every gate is judged on headless-Chrome frames at 1440 × 900, 2× density for close-ups, plus a 390 × 844 phone emulation. Real-time screencasts are required for anything that moves. Earlier user decisions stay in force unless listed here:
- tobacco leather, the walnut-library setting and the approved header;
- the photograph on the front and the engraved likeness on the spine;
- fixed page-turn framing;
- the Evening soundtrack;
- a raised writing panel, still attached and folding before a turn;
- reduced-motion support.

### A. Book object (model, cover, pages)

1. **Continuous skinned binding.** The front board, spine and back board form one leather mesh, bent by bone chains through rounded joints with a visible hinge groove. The spine is rounded (convex) when closed and relaxes as the book opens. Exported clips keep the existing names (`open`, `turn`, `reading`) and their 0..1 meaning.
2. **Squares and edges.** The boards overhang the page block by about 3% on head, tail and fore-edge, with softly rounded corners, a bevelled edge and slightly darker, rubbed edges.
3. **Page block.** Backed, rounded binding with a concave fore-edge. The edges show fine, uneven sheet lines in a tinted (or lightly gilt) edge colour, not stripes. Headbands (striped silk thread) at head and tail. The left/right thickness changes with chapter (a morph or scale), and nothing brown shows under the pages.
4. **Endpapers and turn-ins.** A designed printed endpaper (for example a subtle repeat of olive leaves in two inks) inside both boards, with the leather turned in around its edges.
5. **Leather material.** Full-grain normal and roughness at high resolution, slight specular breakup, darker and smoother wear at edges and joints. It must read as leather at close range in the entrance frames.
6. **Front cover v2.** The photograph is printed on the leather as a fine duotone halftone or line screen, so it reads as part of the material, the way Stripe prints portraits on cloth. It still is her 1942 photograph; no pasted rectangle or frame. Lettering: a small title in brass foil, a small author line and a small square badge, in Stripe-like restraint, with generous negative space. Foil has a mask, a sparkle/glitter response and a crisp bevel. The spine keeps the engraved likeness and title. The photograph must stay recognisable at the closed-book entrance size.
7. **Pages.**
   - The writing panel becomes a properly typeset page: running head (chapter, place), refined title, measured body copy, the quotation set apart, a folio and margins.
   - Paper gets a subtle bump and a pointer-following sheen.
   - The panel keeps its hinge and fold contract and must not look like a floating card.

### B. Room and lamp

1. **A real desk.** A 3D walnut desktop extends from the near edge to its back edge behind the book, with real wood material (fine grain, clearcoat sheen, soft reflections of the book and lamp). The room photo sits beyond it, softly out of focus. The book and lamp get contact shadows and ambient occlusion. The existing framing and overall colour stay recognisable.
2. **A well-designed lamp.** It sits fully on the desk with a contact shadow and must never look like it is floating.
   - A properly proportioned brass banker's lamp, modelled on the real archetype: weighted brass base, turned stem, curved harp holding the shade.
   - A cased emerald-glass shade with an opal-white interior, using a physical transmission or thickness material, not emissive paint.
   - A real beaded chain with brass pull.
   - Brushed brass with an anisotropic or roughness sheen.
3. **Lamp light.**
   - Switched on: a warm, soft-edged pool on the desk and book; the shade glows through its glass; the room falls to dim lamplight.
   - Switched off: the room returns smoothly.
   - The pull feels mechanical: the chain stretches, clicks, and springs back with a small swing. Visible on desktop and tablet; the phone layout must still look designed.
4. Remove the CSS header dimming if the new light makes it unnecessary; keep it only if it looks right.

### C. Page turn and interaction

1. **No blocky frames.** No frame of a turn (real-time screencast, forward, backward and drag) may show edge-on grey strips, solid slabs, white rectangles or pops.
   - Allowed approach: pieces fold progressively and stay geometrically attached to the leaf as it lifts, so they are flat against it before it passes the vertical. Printed prints are fine if they look like real flattened paper art.
   - The 9 September rule (fold before turn, unfold after landing, no floating or clipping) still holds in spirit. Pieces may fold with the leaf as a real mechanism would, but never clip or float.
2. **Leaf.** A runtime S-curve curl driven by progress and, for a drag, the grab point. Paper thickness and soft shading, a soft moving shadow on the page beneath, about 0.6–0.9 s for a click turn, and drag follows the hand with a natural release.
3. **Held book.** Keep the tilt, but subtle. On the closed book, the leather and foil catch light as it turns.
4. **Loupe v2.**
   - A real 3D magnifier rendered in front of the scene: a polished brass bezel with bevel, a glass lens with edge refraction, a slight chromatic fringe, a soft reflection and vignette, and a turned wooden handle with a brass ferrule at a natural angle. It casts a soft shadow on the page.
   - The magnified image must be correct, including the room behind, at 2–3×, and crisp on 2× screens.
   - Mouse and touch both work. It must not break turning, keyboard or reduced motion.

## 4. Ownership for this rebuild

| Agent | Owns (edit only these) |
|---|---|
| Book | `book()` and binding helpers in `scripts/blender/build_book.py` (not chapter scene code), `scripts/make-cover-textures.py`, `scripts/make-paper-texture.py`, new `scripts/make-*` texture scripts for the book, `public/textures/{cover-*,leather-*,paper-stock*,endpaper-*,binding-*}`, `public/models/book.glb`, `assets/source/book.blend`, `public/posters/book.webp`, `src/book/materials.ts`, `src/book/paper.ts`, the book section of `scripts/validate-assets.mjs`, `docs/BOOK-QUALITY.md` |
| Room | `scripts/blender/build_lamp.py`, new `scripts/blender/build_desk.py`, `public/models/{lamp,desk}.glb`, `assets/source/{lamp,desk}.blend`, `public/textures/desk-*`, `src/book/room.ts`, `inspectLamp` in `scripts/validate-assets.mjs`, `docs/ROOM-LAMP.md` |
| Interaction | `src/book/BookScene.ts`, `src/book/motion.ts`, `src/book/loupe.ts`, `src/book/leaf.ts` (new), loupe/drag code in `src/App.tsx`, loupe styles in `src/styles.css`, `tests/book-motion.test.ts`, `docs/INTERACTION.md` |
| Main | Integration, `AGENTS.md`, `docs/QA.md`, `docs/PIPELINE.md`, publishing |

Rules:
- Edit shared files only in your own regions, and never overwrite another agent's files.
- Only the Book agent runs `build_book.py`, and only with `--book`.
- The Room agent runs only its own Blender scripts.
- Never claim acceptance from a render or a passing build.
