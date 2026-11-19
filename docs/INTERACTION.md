# Page turn, drag and loupe (Interaction rebuild, 18 November 2026)

This covers section C of `docs/QUALITY-SPEC.md`. Code: `src/book/leaf.ts`, `src/book/motion.ts`, `src/book/loupe.ts`, the turn, drag and loupe parts of `src/book/BookScene.ts`, the drag and loupe handlers in `src/App.tsx`, and `tests/book-motion.test.ts`. Evidence: `docs/qa/rebuild/interaction/`.

## What changed and why

The old turn ran in three steps: fold every piece flat, move a baked 4-pose leaf carrying a top-down photograph ("print") of the folded scene, then unfold the next scene. That caused every blocky frame the user saw:
- cards seen edge-on, as grey strips, while the whole scene folded at once;
- a folded scene printed onto the leaf as coloured slabs;
- new pieces rising from white rectangles;
- a print that never matched the lit page exactly.

The new turn has no prints at all. Everything on the leaf is real geometry, lit by the scene.

### The leaf (`leaf.ts`, class `Leaf`)

- **Shape.** The leaf is a 72 × 18 grid over the right page. Its rest shape is raycast from the `RightPage` mesh at load, 0.006 above it. Its footprint comes from the old `TurnPage` bounds when that node exists, otherwise from the page, so it follows whatever binding the book model has.
- **Bending.** Each row is a cross-section bent by a tangent-angle field: angle = rest + (π − 2·rest) · w(u, v, L).
  - The sheet keeps its length: it bends but never stretches.
  - When w = 1 it is the exact mirror over the left page, so both ends lie exactly on a page.
  - Backward turns use the mirror image of a forward turn (1 − w).
- **S-curve** (`curlWeight`).
  - The fore-edge leads while the page lifts, then trails as it falls, and catches up on landing.
  - The root leaves the binding slightly behind the body.
  - The row the hand holds leads the others, and a click holds the front corner.
  - Tests check that w stays within 0..1, only increases with L, and is exactly 0 and 1 at the ends.
- **Faces.**
  - Front: a clone of the right page's own paper material.
  - Back: a clone of the left page's paper material.
  - Edges: a thin fore-edge, head and tail strip between the two faces, which are 0.0028 apart.
  - UVs are least-squares fits of each page's own UV mapping, so the grain does not shift when the leaf takes over from a page or hands back to one.
  - The gutter shade is taken from where each point rests, and fades while the sheet is away from the gutter.
- **Shadow.**
  - The leaf casts a real shadow-map shadow.
  - It also writes a soft occlusion table (192 × 19, blurred) that darkens the pages and the reading panel beneath it. This is zero where the leaf touches the page, deepest a little above it, and fades with height.
- **Cost.** The geometry is rewritten on the CPU only while a turn is moving.

### Pieces ride on the leaf (`deformMaterial`)

Every chapter material, and its shadow-depth material, gets a vertex hook (chained after any existing `onBeforeCompile`). The hook reads a float frame texture: leaf position, normal and tangent; rest frame; and squash factors. It has four modes per rig:

| Mode | Used for | What happens |
|---|---|---|
| 0 | At rest | Identity. |
| 1 | Hinged to the leaf's front (forward: outgoing; backward: incoming) | Each vertex keeps its height, along and across offsets, re-expressed in the bent leaf's frame. Pieces are seated on the front face and pressed flat as the front closes on the other page. |
| 2 | Left on the right page under the leaf | Heights are scaled down to the leaf's clearance, so nothing passes through the sheet. |
| 3 | Lying on the leaf's back | The reading panel and its writing, described from the left page and mirrored. |

The reading panel on the leaf is a copy of the book's `ReadingPanel`, under a sibling of `ReadingHinge`. Forward, it carries the new writing. Backward, the old writing leaves on it while the earlier chapter's writing is already on the real panel beneath.

## Sequencing contract (`motion.ts`, tested)

Click turn: `TURN_DURATION` is 1.0 s. Progress t runs 0..1.

| t | What happens |
|---|---|
| 0 → 0.08 | The reading panel lies flat (`TURN_PANEL_DOWN`). No page moves while it is raised. |
| 0.08 → 0.80 | The leaf travels for 0.72 s (`leafTravel`): two joined parabolas, so it leaves briskly and lands softly. |
| 0.82 → 1.0 | The new panel rises (`TURN_PANEL_RISE`). |

**Pieces on the moving leaf** collapse in step with it, the way a pop-up closes with its page:
- Angle from flat = 1 − L / 0.56. They are flat when the leaf is 100° over, facing away, and still far above the other page.
- Backward, they rise in reverse and are upright exactly at landing.
- In the leaf's frame the camera edge-on angle is atan(0.61·cos φ). The fold always stays above it, so these pieces are never seen edge-on.

**Pieces on a still page** (forward: incoming; backward: outgoing) use `quickFold`. It crosses the 20–45° band, where cards read as edge-on strips, in under 0.05 s (tested). It also keeps them flat whenever the leaf could reach them:
- Forward, incoming pieces rise only once the leaf is past travel 0.65.
- Backward, outgoing pieces are flat before travel 0.3.

The clips' own easing is inverted (`clipForAngle`), so these curves are true hinge angles.

**Visibility:**
- The outgoing scene exists until the leaf lands.
- The incoming scene exists from the moment the leaf leaves.
- Both exist only while the leaf is there to carry or cover one of them.
- The real panel hides only while the leaf lies within 0.03 of it; it stands 0.002 proud of the landed leaf.

These earlier rules still hold:
- The panel is flat before its page moves.
- Nothing appears in a default exported pose.
- Nothing floats free of a hinge.
- Nothing crosses the other page.

The one relaxation is that pieces now fold *with* the leaf, as a real mechanism would, as QUALITY-SPEC C1 allows.

**Drag** (`beginDrag(direction, x, y)`, `dragTo(progress, x, y)`, `endDrag(commit?, flick)`):
- The hand's point on the page plane fixes which row leads (the grab).
- The held fore-edge follows the hand's angle about the spine, measured from where it took hold, so nothing jumps at pick-up. `travelForTip` inverts the curl for the held row.
- The page follows on a light spring (rate 22/s). The panel's 0.08 s lie-down runs on the clock even when the hand is faster.
- **Release:**
  - The page turns if it is past 45% of its travel, or flicked onward faster than 0.4 stage widths per second.
  - A flick back returns it.
  - Otherwise it falls back from where it is.
  - Both continue on the same timeline, so pieces re-rise or keep folding correctly.

Reduced motion swaps spreads instantly (no leaf).

## Loupe v2 (`loupe.ts`)

- **What it is.** A 3D reading glass drawn over the scene with an orthographic overlay camera in stage pixels:
  - a turned brass bezel (lathe profile with bevelled face, rolled edge and a dark glass seat);
  - a brass neck, collar and grooved ferrule;
  - a turned walnut grip (generated grain, clearcoat) with a brass end cap.
  - It is lit by a window key light, a warm fill and the room's own environment map.
  - A soft shadow of the rim and grip falls on the page, offset away from the window.
  - Held by a mouse, the handle points down-right. On touch it points down to the finger, and the lens floats above it.
- **Lens.** The live scene re-rendered through a view-offset copy of the main camera at **2.5×**:
  - into a half-float target with 4× MSAA, at the canvas's own pixel density (so crisp on 2× screens);
  - with a 10% margin for refraction.
  - The shader adds rim refraction (barrel at the edge), a slight lateral colour fringe, a vignette, the dark ground edge, and window reflections (a soft sheen and a bright arc).
  - Tone mapping and output colour are applied once, as in the main frame.
- **Background.** The room behind is correct.
  - The Room agent's backdrop is now a world-space plane, so the view-offset camera sees the magnified region.
  - For any screen-space `scene.background` texture, the loupe crops the texture to the same window (the old bug) and restores it afterwards.
- **Behaviour.**
  - Unchanged: footer button and M key, Esc, mouse follow, and the book holds still while it is out.
  - The camera drift, held tilt and paper sheen pause while the loupe is out.
  - The CSS bezel (`.loupe-bezel`) is removed.

## Held book and sheen

- The pointer tilt is unchanged and subtle (≤ 0.03 rad).
- It returns to rest during turns, drags and while the loupe is out, so it never fights them.
- A faint point light (0.9) hovers over the page under the smoothed pointer while reading, so the Book agent's paper sheen moves with the hand. It is always in the scene, at zero when unused, so toggling it never recompiles materials.
- It is off for reduced motion and while the loupe is out.

## Measured results (headless Chrome 158, 1440 × 900, this Mac)

**Click turns**, real-time CDP screencast, `screencast-fwd.jpg` and `screencast-back.jpg`:

| Turn | Frames | Duration | Largest gap | Reading again after keypress |
|---|---|---|---|---|
| Forward | 64 | 1033 ms | 17 ms | 1096 ms |
| Backward | 64 | 1033 ms | 17 ms | 1086 ms |

**Drags:**

| Case | Reading again | Largest frame gap |
|---|---|---|
| Drag and commit (≈0.9 s hand) | 2.0 s after pointer-down | 33 ms |
| Drag released early (falls back) | 1.15 s | 33 ms |
| Backward drag | 1.9 s | 33 ms |

**Other cases:**
- Contents jump 1 → 7: 1.6 s, including the chapter load (the old spread holds still until the new one is ready).
- Sweep of all 12 chapters forward and back (22 turns):
  - 1023–1090 ms per turn;
  - 60 fps during motion, p95 frame 17 ms, worst frame 67 ms;
  - geometries steady at 136 and textures at 38;
  - 2 chapters cached; no page errors.
- Idle: **0 frames rendered in 2 s** after settling (rendering stays on demand).
- Reduced motion (`reducedMotion: 'reduce'` context): 22 instant swaps in 41–103 ms, no errors.
- Phone 390 × 844 emulation (touch): a finger swipe-drag turns the page; the touch loupe floats above the finger with the handle down; the button turn works. See `phone-390x844.jpg`.
- Loupe at 2× density: over text, figures, the room behind and the lamp light; a turn with the loupe out; Esc puts it away. See `loupe-closeups-2x.jpg` and `loupe-states.jpg`.

**Typecheck, tests and assets:** `npm run typecheck`, `npx vitest run tests/book` (41 tests) and `npm run validate:assets` (15 checks) all pass.

## Limitations (honest)

- **Edge-on cards on a still page.** Cards on a page that does not move still pass the angle where the camera sees them edge-on. It lasts one or two frames at 60 fps (for example 150 ms in the backward screencast, 850 ms in the forward one) and shows as a thin band of the card's own art. That is physically correct paper, but it is not invisible.
- **The chapter models themselves:**
  - Card backs are the models' own colours. The Luxembourg garden backdrop folds flat as an ochre band at the head of the page.
  - Folded kerbs and foreground strips overhang the page's front edge by up to 0.1, so they show as scallops along the leaf's lower edge while it lifts.
  - These belong to the chapter models (`story_scenes.py`), which no agent owns in this rebuild.
- **No true developable surface.** Leaf rows bend independently. The corner twist introduces a slight shear across the sheet, which is not visible at this camera distance.
- **Assumed book shape.**
  - The left page is assumed to mirror the right.
  - The page thickness morph on `LeftPage`/`RightPage` is not driven. If someone drives it, the leaf's rest surface must be resampled (call `prepareLeaf` again, or add a hook).
- **Loupe under the HTML chrome.** The loupe is drawn in the canvas, so the HTML header and footer sit above it at the stage edges.
- **No real devices.** Physical phones and tablets were not tested; all figures above come from emulation in headless Chrome.

## Notes for other agents and the integrator

- **Book model.**
  - `TurnPage` and the `turn` clip are no longer animated. The node is hidden, and its base footprint is read only as an optional size hint.
  - `ReadingPanel` is cloned for the leaf.
  - Page and chapter materials are cloned or hooked. Their hooks are chained, so any new `onBeforeCompile` must also chain rather than replace.
  - Gutter shading is applied only to materials named `paper`.
- **Chapter rigs.** They no longer use clipping planes, and `renderer.localClippingEnabled` is no longer set.
- **`docs/PIPELINE.md`.** Its section "Printed turning leaf…" is superseded by this document. That file belongs to the main agent.
- **API.** All changes are backward compatible:
  - `beginDrag(direction, x?, y?)`
  - `dragTo(progress, x?, y?)`
  - `endDrag(commit?, flick?)`
  - `setLoupe(active, x?, y?, radius?, touch?)`
  - In development only: `__bookDebug.inspect()` exposes the scene for frame scripts.
