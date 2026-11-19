# Stripe Press review and improvement plan

Revised 18 November 2026 after user feedback. Planning only: nothing here is approved yet. Approved decisions in `AGENTS.md` (header, walnut library, fixed turn camera, soundtrack) stay in force.

## User direction

- Lighting is **not** the priority. Stripe's lamp just follows the pointer, which isn't what makes the site good.
- What matters: **page texture**, **how the pages move when you interact**, and **how our book looks and works**.
- Take the good ideas and adapt them to a pop-up book. No straight copy of Stripe Press.

## What Stripe Press gets right about pages

Observed at stripe.press on the Hamming book's reading view, in headless Chrome at 1440 × 900 and 2× pixel density.

1. **Paper reads as paper.** The stock is smooth and warm with very low-contrast tonal variation. The realism comes from the page's shape and shading, not from a grain pattern.
2. **Pages have form.** Each page rises out of the gutter in a soft curve and the lines of text bend with it. The gutter darkens gradually with no hard line.
3. **The book shows where you are.** The page block is thin on the left and thick on the right at page 40, and the stack edges have fine, slightly uneven lines. The cover boards stick out a little beyond the pages.
4. **The turning page is never blank.** The leaf stands up with a gentle S-bend and shows its printed text. The next page is already visible underneath, and the leaf casts a soft moving shadow on it.
5. **Turns are quick and continuous.** About half a second, with no pause between stages.
6. **The book responds to your hand.** Hover and drag tilt the whole book slightly, as if you were holding it. Clicks, arrows and keys turn the page.

## How ours compares

Frames in `docs/qa/stripe-review/`: `paper-closeup`, `gutter-closeup`, `page-edge-closeup`, `turn-sequence` (our turn frozen at 5, 15, 25, 35, 45, 55, 65, 75 and 90 percent), plus `spread-01`, `spread-06`, `spread-12`.

### Page texture and form

| | Ours today | Effect |
|---|---|---|
| Grain | Strong sandy speckle across the whole page (`textures/paper.webp`) | Reads as plaster or sandpaper when close, and fights with the fine paper-cut pieces |
| Shape | Both pages are flat planes right up to the spine | Looks like a board, not a bound book |
| Gutter | A hard dark brown strip runs up the middle | Reads as a stick between the pages; there's no gutter shadow |
| Page block | Even, regular lines, the same thickness on both sides for all 12 chapters | Doesn't show progress through the book |
| Cover | A flat brown slab under the pages with no visible board edge or turn-in | Loses the leather quality seen on the closed book |

### Page motion

From `src/book/motion.ts` (`turnPose`) and the frozen frames, a turn takes 2.7 s:

| Progress | What happens |
|---|---|
| 0 to 24 % | Scene folds flat. Reading text fades out by 14 %. |
| 27 % | Folded scene is **hidden** all at once. |
| 28 to 73 % | The leaf turns with a nice curl, but it is **blank**, both pages are **blank**, and it casts no shadow. |
| 75 % | New scene **appears** all at once, then unfolds. Text fades in from 88 %. |

So for about 1.3 s the reader sees an empty book. The folded pieces don't travel with the leaf; they vanish and the new ones appear. That breaks the spirit of the 9 September rule ("every paper piece remains attached… no instantaneous appearance"), even though each piece is flat when it disappears.

What already works: the leaf's curl is good, the camera stays fixed, and folding before turning is right for a pop-up book.

## Improvement plan

Every step is checked on real browser frames: forward and back turns, entrance, reduced motion and phone.

### A. Turning motion (biggest win, mostly application code)

1. **Printed pages under the leaf.** When a scene folds flat, it stays visible as a flat print on its page instead of disappearing. Render each chapter's folded scene once into a page texture and show it under and on the leaf. The new chapter's flat print sits on the page underneath before it rises.
2. **Text on the leaf.** The front of the leaf carries the outgoing right page. The back carries the incoming left page's printed text, drawn with the same canvas text code as `paper.ts`. The reading panel folds down, its text turns with the page, and it rises again on the other side.
3. **Leaf shadow.** A soft shadow follows the leaf across the page underneath.
4. **No dead time.** Overlap the stages: fold about 0.5 s, leaf about 0.7 s starting just before the fold ends, then unfold about 0.7 s. Total about 1.8 s instead of 2.7 s, with something on the page at every frame. The fold still finishes before the leaf lifts off, so nothing clips.
5. **Drag to turn.** Grab the right or left page edge and the turn follows your finger or mouse: pieces fold as you start pulling, then the leaf follows. Release past halfway and it completes; release before that and it eases back. Uses the existing scrubbable turn progress. Click, arrows and swipe keep working.
6. **Corner hint.** On hover, the page corner lifts a few millimetres to show that it can be turned. Disabled on touch and under reduced motion.

### B. Paper and book form (texture work plus a Blender change to the book mesh)

7. **New paper texture.** Smooth, warm, slightly ivory stock with large, soft tonal variation, very fine fibres only visible up close, and a faint ageing tone towards the edges. Make a normal map so the light catches the fibres instead of printing speckles into the colour.
8. **Gutter curve.** Curve the last few centimetres of each page into the spine and replace the brown strip with a soft gutter shadow. The area where the pop-up pieces are hinged stays flat, so no hinge moves.
9. **Page block that shows progress.** Chapter 1 has a thin left block and a thick right one; chapter 12 the reverse. The edges get finer, slightly uneven sheets.
10. **Cover board.** Visible leather board edge, overhang beyond the pages, and the leather turn-in at the corners, matching the closed book.

### C. How the scenes look (Blender, one spread first)

11. **Distinct figures.** Replace the single peg silhouette with cut-paper figures that read as people: Simone with round glasses and cape, pupils, factory workers, militia, farm workers. Visible cut details.
12. **Plants that fit the place.** Chestnut and plane trees for Paris, olives and vines for the south, scrub for Aragon. Each one layered, not one repeated sprig.
13. **No placeholder props.** Chapter 12's books get spines, bands and titles. Letters and signs get readable printed texture.
14. **Fill the page.** Add a foreground layer (cobbles, railings, grass) so the lower half of the right page isn't empty. Stop back-row pieces from poking above the reading panel.

Start with chapter 1 to chapter 2 (the original milestone pair): finish A and B there, check it in the browser, then extend to all 12 chapters.

## Deliberately not taken from Stripe

- **Pointer lamp light.** Not a priority for this book.
- **Top-down reading camera.** Our turn framing is fixed by request, and the oblique view is what shows the pop-up.
- **Typeset prose pages.** Our page is a scene plus a short raised panel. Only the panel's text goes on the leaf, not a full book page.
- **Monospace bracket interface, shop and theme switcher.** Not our tone.

## Open questions

- Start with A (motion) alone, or A and B together on chapters 1 and 2?
- Should drag-to-turn be in this pass, or follow once the faster turn is approved?

## Implemented for chapters 1 and 2, 18 November 2026

The user approved doing every item for chapters 1 and 2 first ("do all for 1 2 then I'll see").

| Plan item | Status |
|---|---|
| A1 Printed pages under the leaf | Done. Folded scenes stay visible and travel on the leaf |
| A2 Text on the leaf | Done. The writing turns with the page, never fades |
| A3 Leaf shadow | Partly. The real leaf casts a shadow-map shadow and darkens as it stands up; there is no extra soft decal |
| A4 No dead time | Done. 2.1 s turn, about 1.3 s of blank pages removed |
| A5 Drag to turn | Done. Follows the hand; completes or falls back on release |
| A6 Corner hint | Not done. It would cut through the upright pop-ups; a grab cursor is shown instead |
| B7 New paper texture | Done, book-wide (pages and all paper pieces) |
| B8 Gutter | Done. Soft gutter shadow and a shaded fold replace the brown rod |
| B9 Page block shows progress | Not done. Needs a page-height change that every chapter's hinges depend on |
| B10 Cover board | Not changed in this pass |
| C11-14 Scene art | Done for chapters 1 and 2: distinct figures, layered trees and laurel, a foreground layer, a clear left page |

Before and after frames are in `docs/qa/stripe-review/`. Details are in `docs/PIPELINE.md` and `docs/QA.md`. Chapters 3-12 pick up the new paper and printed leaf automatically, but keep their earlier scene art until the user reviews chapters 1 and 2.

## Full pass, 18 November 2026 (overnight, unattended)

The user approved chapters 1 and 2 and asked for the whole book to the same standard, plus a better cover, a magnifier, a pull-chain lamp and a book that feels held.

| Request | Result |
|---|---|
| Better cover, after studying Stripe Press covers | Done. Her photograph in a debossed arch with brass frame, foil title and details, monogram badge, 12-dot line, blind-tooled leaf corners, pebbled leather everywhere. Six Stripe Press covers were studied for the conventions only; none of their artwork is used |
| Magnifier | Done. Loupe with brass bezel, about 2.6× live 3D magnification; M or Esc; floats above the finger on touch |
| Lamp with an old-fashioned pull chain | Done. Brass banker's lamp with green glass; click, the Lamp control or L pulls the beaded chain; the room darkens to lamplight, with a synthesized chain click when sound is on |
| Less static, feels like a real book | Done. Spring tilt after the hand, paper pieces flex with the motion, every scene card has paper fibres; plus the earlier printed leaf and drag to turn |
| Chapters 3-12 to the chapter 1-2 standard | Done. All 10 rebuilt with landmarks, distinct figures, foregrounds and a clear left page; 13 posters re-rendered |
| Quality checked in the browser | Turn sweep both ways through all 12 chapters; entrance, lamp, loupe, phone emulation and production build. See `docs/QA.md` |

Still open: physical-device testing, Safari and Firefox. The picomatch audit advisory cleared before the release commit (`docs/QA.md`).
