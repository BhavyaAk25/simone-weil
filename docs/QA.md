# Verification record

## Release status

**Local release gate passed, 11 September 2026.** All twelve revised scenes and both navigation directions were checked in the browser. Public deployment verification passed and is recorded below. Earlier failures are retained as history; they do not describe the final exports.

The selected appearance reference is `docs/references/dark-walnut.png`. The required correction is recorded in `AGENTS.md` and `docs/REVISION.md`.

## Executed checks — 9 September 2026

| Check | Actual result | Meaning and limit |
|---|---|---|
| `npm test -- --run tests/book-motion.test.ts tests/book-assets.test.ts` | **15 tests passed**, 2 files | Sequential folding, page turn, unfolding, safe scene visibility, entrance cover ordering, monotonic easing, navigation guards, and binary/morph validator fixtures. This proves the pure schedule and guard behavior, not the rendered result. |
| `npm test` | **Failed**: Vitest collected `tests/sites-worker.test.mjs`, a Node test-runner file, and reported “No test suite found.” The 15 Vitest tests passed; the four Node subtests also emitted passing TAP results. | Main agent must separate the two test runners in configuration. Preserve the Sites tests. |
| `node scripts/validate-assets.mjs --milestone --json` against the **old** exports | **Book passed; chapters 1 and 2 failed.** | The validator reads binary vertices and evaluates animation transforms/morphs. It detected the exact collapsed-geometry problem instead of accepting the open-pose preview. New exports have not been checked in this record yet. |
| Revised entrance/forward/back browser frames | **Pending** | Must inspect intermediate poses, not only endpoint screenshots. |
| All 12 spreads and asset-failure recovery | **Pending** | Required before publishing. |
| Physical-phone performance | **Not measured** | Desktop viewport emulation is not a phone benchmark. |

The old chapter 1 collapsed bounds were X `[-2.1456, 2.5233]`, Y `[0.0418, 0.6837]`, Z `[-1.4007, 1.2759]`. Chapter 2 collapsed bounds were X `[-1.6600, 2.3550]`, Y `[-0.0116, 0.6660]`, Z `[-1.2400, 1.2000]`. Both had geometry far above or below the paper when supposedly flat. These results concern the rejected assets, not a future revised export.

## Revision checks — 10 September 2026

- `npm test` now scopes Vitest to the book tests. **19 tests passed across 3 files** after adding all-twelve manifest checks for complete ordered IDs, unique chapter/asset addresses, 45–65-word prose, short quotation provenance, and paths compatible with GitHub Pages. This resolves the earlier mixed-test-runner failure.
- The first revised book and chapters 1–2, before the raised reading panel revision, passed all structural and 21-pose checks. Their combined transfer size was 9.45 MiB. Chapter 1 folded Y was `[0.221, 0.295]`; chapter 2 was `[0.221, 0.2905]`.
- The subsequent book export with `ReadingHinge`, `ReadingPanel`, and a one-second `reading` clip passed. It is 2,134,688 bytes, 68 material primitives, and 32,304 triangles. The panel is flat when `reading=0` and reaches the agreed 18° reading pose at `reading=1`. Combined `open=0, reading=0` sampling confirms the panel remains inside the compact closed book.
- Revised chapter exports are still being finalized for the more curved paper surface. The validator's previous global Y floor needs to distinguish the lower gutter from the higher page crown; this is being coordinated with the Blender owner. No browser acceptance or visual gate is inferred from these interim asset checks.

## Asset validation contract

Run `npm run validate:assets -- --milestone` during the first-spread gate. The default `npm run validate:assets` requires the book plus all twelve chapters, editable `.blend` files, and fallback posters.

The validator checks GLB headers and binary bounds; embedded buffers/textures; material and stable book-node names; nonempty triangulated geometry and valid indices; required animation clips; target nodes, key times and sample counts; actual world-space vertices in sampled poses; and morph-based page endpoints on both sides of the spine. It requires each chapter mesh to descend from an animated hinge. The book also requires `ReadingHinge`, `ReadingPanel`, and the `reading` clip; checks sample the reading and cover clips together to verify the flat, raised and closed poses.

Agreed authoring limits: book at most 5 MiB, chapter at most 4 MiB, first three GLBs targeted below 10 MiB. Structural render ceilings are 256 material primitives and 250,000 triangles per GLB. These are ceilings, not frame-rate guarantees.

Folded scenery fits X ±2.50 and Z ±1.64, with nominal Y `[0.213, 0.320]`; the validator permits 0.003 units of numerical tolerance on Y. Maximum open height is 2.40 with the same tolerance. It samples 21 unfolding poses and checks paper penetration and the book footprint. This detects large hinge/extent defects; it does not prove absence of every triangle-to-triangle collision, shadow artifact, visibility jump, or text overlap.

## Browser acceptance checklist — final local status

- [x] Closed state shows one centered, spine-facing book with the complete title.
- [x] Click, tap and Enter perform extraction, cover reveal, descent, opening, and unfolding in that order.
- [x] No chapter is exposed through the closed or moving cover. Inspect frames before opening, during opening, just before reveal, and during unfolding.
- [x] Skip opening lands in the complete first spread. Reduced motion starts there without the entrance.
- [x] A forward turn folds all outgoing scenery, moves the page, then unfolds the incoming scene. Inspect boundaries and the middle of the crossing.
- [x] The reverse turn has the same safe ordering and the sheet moves back correctly.
- [x] Rapid repeated input, boundary navigation, and contents jumps never overlap transitions or select the wrong text.
- [x] Every chapter has its own finished scene, readable paragraph, quotation, and source.
- [x] Missing chapter assets show a recoverable error while preserving the current spread.
- [ ] Initial asset failure, unavailable WebGL, and context loss expose a readable illustrated edition.
- [x] Sound remains off until enabled and can be muted; failures do not block reading.
- [x] Keyboard focus is visible, dialogs contain focus and close with Escape, controls have names, and chapter changes are announced.
- [x] Desktop writing stays on the paper without scene overlap; phone portrait and landscape show the same text below the canvas.
- [x] Walnut, leather, paper edges, scene detail, lighting and composition pass direct screenshot comparison with the reference. Record intentional differences separately.
- [x] Type check, production build, focused tests, Sites tests and release asset validation pass on the final code/assets.
- [x] Deployed GitHub Pages paths, asset loading, navigation and fallback are verified on the public URL.

## Performance measurement protocol

Record the actual device model, OS, browser/version, viewport, display scale, renderer pixel ratio, and whether the browser uses hardware acceleration. Record loading conditions and at least a complete entrance plus repeated forward/back turns after warmup. Report measured frame times or frames per second, draw calls, triangles and cache/texture counts; distinguish animation from idle readings.

Target near 60 fps on the desktop and at least 30 fps on a representative physical phone. No phone performance claim is valid until a physical device is measured. Repeated chapter jumps and a return to a previous chapter should also show bounded geometry/texture memory rather than monotonic growth.

## Live revision checks — 10 September, main agent

- First-two gate completed in the in-app Chromium browser at 1440 × 1000: spine-first entry, cover reveal, settled reading, forward crossing, education, flat outgoing pose at 0.24, reverse crossing at 0.5, return to childhood. A 390 × 844 horizontal pointer swipe initiated the next turn; HTML prose remained below the stage.
- Normal opening completed at 1280 × 720 and 1440 × 1000. Captures are under `docs/qa/`.
- Contents showed all twelve chapter names; jump 1 → 3 loaded the correct scene and text.
- While chapter 12 had not yet been exported, a 3 → 12 jump returned a recoverable message and preserved chapter 3. The following successful navigation cleared the error.
- Sound was initially off; enabling changed the control to Mute sound, and muting restored Enable sound. This checks activation and UI state, not a calibrated audio listening test.
- Reading dialog displayed the French work link, edition/page locator, project translation and retrospective context. Escape closed it and returned control to the book.
- User-selectable reduced motion in About preserves the current chapter. Enabling it on chapter 3 then advancing produced chapter 4 immediately. Keyboard Right then produced chapter 5.
- Type check, 19 focused tests, four Sites tests and milestone asset validation passed. Release validation remains pending assets 3–12 and their final reexports.


## Final local release checks — 11 September 2026

- Type checking passed; 19 focused tests and four Sites tests passed. Production build passed and retains all three required Sites artifacts. Vite reports a non-blocking large-chunk warning: main JavaScript 896.26 kB, 242.85 kB gzip.
- Release asset validation: **13 passed, zero failed**. Every GLB has its editable Blender source and illustrated poster. Final fixes corrected folded foliage extent, carriage wheel/page penetration and required paper materials.
- Normal browser navigation covered chapters 1–12 forwards and 12–1 backwards. Six rapid Right presses advanced exactly once. Both boundaries, contents jump 1–12 and return navigation worked.
- Entrance click and Enter, skip, live reduced motion, and saved reduced-motion reload were checked. Saved reduced motion reloads directly into the first open spread. Forward/reverse boundary and midpoint frames were inspected during the first-spread gate.
- All chapter scenery and print were visually inspected. Chapter 11 exposed a quotation/attribution overlap, corrected by measuring the entire text block before sizing the paragraph. The corrected reverse capture confirms separation.
- Missing chapter assets preserved the current chapter and recovered on subsequent navigation. Simulated graphics context loss displayed the recovery screen; the illustrated edition preserved the chapter and allowed onward reading. Direct illustrated mode is available with `?read`. Initial network failure and a machine entirely lacking WebGL were not separately induced in this final pass.
- Reading/source dialog, Escape, named controls, visible keyboard focus, semantic chapter announcements, and opt-in sound/mute state were exercised. This was not a screen-reader audit or calibrated audio test.
- Portrait 390 × 844 and landscape 844 × 390 layouts were exercised, including swipe, scrolling to the complete text and source dialog. These are desktop viewport checks, not physical-phone measurements.
- Production preview at 1440 × 1000 loaded the closed spine and complete childhood spread; console errors/warnings were empty. Final reference and production screenshot were opened together after corrections; see `design-qa.md` for intentional artistic differences.

### Actual desktop animation measurements

MacBook Air Mac16,12, Apple M4 (10 cores), 16 GB, macOS 15.3; in-app Chromium 152.0.0.0; 1280 × 720 viewport; renderer DPR capped at 1.75. Local server, warm chapter traversal, normal animations (inspection hold disabled).

Entrance plus eleven forward turns: 2,058 animation frame samples, approximately **60 fps**, 95th percentile **18 ms**. After resetting measurements, eleven backward turns: 1,793 samples, **60 fps**, P95 **18 ms**, longest recorded frame **18 ms**. The latter snapshot is saved in `qa/desktop-metrics.json`.

The final snapshot reported 213 draw calls and 111,550 triangles. Chapter cache stayed at two or three; observed geometry counts 87–138 and texture counts 11–14 did not grow monotonically. These are runtime frame-interval observations on this laptop, not laboratory benchmarks. GPU acceleration was not independently profiled. **Physical-phone 30 fps target remains unmeasured.**

### Evidence

`qa/production-closed.png`, `qa/production-childhood.png`, chapter browser captures 01–12, `qa/chapter-11-reverse.png`, `qa/phone-portrait.png`, `qa/phone-reading.png`, and `qa/phone-landscape.png` record the inspected states. Development captures may include the inspection panel; production captures do not.

## Public deployment verification — 11 September 2026

The first clean GitHub runner exposed an ordering error: Sites packaging checks preceded the build. Commit `c130d5c` moved that check after build generation, preserving the starter tests and worker. [Run 34654374350](https://github.com/BhavyaAk25/simone-weil/actions/runs/34654374350) then passed type checking, 19 tests, all 13 asset validations, production build, four packaging tests and Pages deployment.

Verified https://bhavyaak25.github.io/simone-weil/ in the in-app browser: complete spine-facing book, Enter entrance, childhood, contents jump to chapter 12, reverse turn to chapter 11, raised print and full source dialog, Escape, and illustrated edition onward navigation. Both the default narrow viewport and 1440 × 1000 desktop layout were inspected. No console warnings or errors were recorded during this live pass. Runtime assets and posters loaded under the repository subpath.

This final documentation update changes no runtime code or assets.

## Scoped revision checks — 11 September, evening

- Inspected the generated spine engraving upright in the actual browser, and the photographic front cover at entrance progress 0.43. Captures: `qa/revision-spine-engraving.png`, `qa/revision-cover-portrait.png`.
- Forward and reverse midpoint frames use identical fixed camera framing. Increased sheet curl fits below the header without a camera swoop; `qa/revision-fixed-turn.png`.
- Opening click enabled music automatically; mute worked and stayed muted across illustrated/3D switching. The original synthesized nylon-string-style loop has a 34.9-second period, restrained gain and soft room reflections. Agent buffer checks found no clipping; actual speaker listening was not independently assessed. Audio graph cleanup supports React StrictMode reinitialization.
- Checked “12” in the header/contents/cover and absence of the lower-left motto. The closed-book invitation displays courage, belonging, and independence.
- Illustrated chapter 2 returned directly to 3D chapter 2 using the visible 3D control. The control also fits the 390 × 844 phone footer; chapter 5 was used for the phone return check.
- Tree leaves were separated into distinct depths and gear layers given physical clearance. Childhood tree and factory gear browser frames show clean printed surfaces; `qa/revision-factory-surfaces.png`. Affected tree/gear exports and editable source files are rebuilt using the existing pipeline.

Final scoped checks: typecheck, 19 focused tests, all 13 asset validations, production build and four Sites packaging tests passed after the affected exports finished. Runtime browser error/warning log was empty. The latest user request overrides earlier default-off audio records; music now starts on the visitor's opening action. Physical-device and independent listening limitations remain as recorded above.

## First-spread 3D return — 12 September 2026

The first open spread now replaces the disabled left arrow with a circular “3D” control. It returns immediately to the centered, closed spine; later spreads retain the previous-page arrow. The existing illustrated edition control still restores the same chapter in 3D.

Production-preview browser acceptance at 1280 × 720 and 390 × 844: opening enabled sound; Enter on the new circle returned to the closed spine; reopening, forward to chapter 2, and backward to chapter 1 succeeded. The control was disabled during the turn. Phone-layout click return and reduced-motion return/reopen succeeded; mute remained off across reopening. Browser warnings/errors were empty. Phone checks are viewport emulation, not physical-device tests. Capture: `qa/first-spread-3d-return.png`.

Typecheck, all 19 focused tests, all 13 asset validations, production build, and four Sites packaging tests passed. The build retains its existing bundle-size advisory. The prior scoped portrait, audio, tree/gear, and invitation changes were already published successfully by [run 34671007032](https://github.com/BhavyaAk25/simone-weil/actions/runs/34671007032).

## Header release verification — 13 September 2026

Scope: approved ivory/glass header, Cinzel title, recovered book prominence and 0.80 backdrop intensity. Existing book meshes, camera formulas, story, audio and turn choreography are unchanged.

- Actual in-app Chromium browser: 1672×941 desktop, 1280×720 short desktop, 390×844 and 320×740 portrait, 601×900 tablet-width layout, 844×390 landscape. These are viewport checks on this Mac, not physical-phone benchmarks.
- Source `references/header-approved.png` and actual `qa/header-open-final.png` were viewed together at1672×941. The independent header reviewer found no P0/P1/P2 mismatch. The book is approximately1009px wide versus1040px in the mock, with33px clearance above childhood chimneys. Native screenshot capture softens both HTML and image content; supersampling does not create source detail.
- Entrance held at0.43, forward/back turns held at0.54 on1280×720: header does not obscure the cover or turning sheet. Files: `qa/header-entrance.png`, `header-turn.png`, `header-turn-back.png`.
- Contents opens by keyboard; Escape restores trigger focus. Chapter5 jump succeeds. All12 chapter counters traversed forward/back in reduced-motion mode. Header Contents and page buttons disable during held turns. Decoration click does not open the closed book.
- Real header asset failure tested by temporarily moving the local desktop WebP and reloading: quiet ivory fallback, legible live text and working About dialog. Asset restored before build.
- Simulated graphics loss exposes recovery and illustrated edition; reading text and header remain accessible. `qa/header-illustrated.png` records layout. Reduced-motion control immediately enters reading.
- Portrait and tablet lettering stays inside plaques. Landscape has no horizontal overflow; short landscape uses the existing scrollable reading layout and fixed footer, so the full book/text is not simultaneously visible.
- Typecheck PASS;19 transition/content/audio tests PASS;13 GLB validations PASS; production build PASS;4 Sites tests PASS. Existing large-JS-chunk advisory remains. No new physical-device performance or200%browser-zoom measurement is claimed.

Additional captures: `qa/header-detail.png`, `header-phone.png`, `header-tablet.png`, `header-landscape.png`, `header-factory.png`. Earlier `header-open.png` and `header-open-revised.png` are intermediate iterations, not final acceptance.

## Reader corrections and Sites release, 16 September 2026

- Re-rendered all 12 illustrated posters from existing Blender chapter sources at 1600 × 1112, replacing the brown plank ground with neutral warm limestone. Actual browser chapter 4 checked against the supplied rejected example: dark legible type on ivory, neutral poster, larger image. See `qa/september16-illustrated.png`.
- Enlarged the live reading book about 4.5 percent. At 1440 × 900 the childhood chimneys clear the header; sheet-turn frame 0.54 stays below it with fixed framing (`qa/september16-turn.png`). Opening via click succeeded and enabled sound. Traversed counters 1–12 and 12–1 through the actual UI with reduced motion; no console warnings/errors. This pass does not claim a new full animation or physical-device performance benchmark.
- About title and explanatory biography inspected in the actual dialog; the requested closing motto is absent. All 12 original paragraphs were revised together, with explicit narrative links, digits for quantities, age 34, and no em dashes. Exact quotation wording and sources remain unchanged. Live childhood text fits its paper panel.
- Illustrated phone layout checked at 390 × 844: no horizontal overflow (document width and scroll width both 390), dark text, ivory footer, visible previous/3D/next and reading/sound controls. `qa/september16-phone.png`. Viewport emulation on this Mac, not a physical phone.
- Typecheck, 19 focused tests, 13 asset validations, production build and 4 Sites packaging tests passed. Existing bundle-size advisory remains. The Sites build uses root-relative base and retains the worker and hosting metadata. GitHub workflow now verifies only.
- 3 sampled-piano auditions prepared separately. No current soundtrack replacement. Signal checks show no clipping; no independent speaker-listening or user preference approval is claimed. See `MUSIC-OPTIONS.md`.

## Additional book scale and guitar auditions, 17 September 2026

The reading-distance formula changes from 7.85/5.6 to 7.45/5.3, approximately 5 percent larger. Browser opening and forward/backward page turns succeeded at 1280 × 720; both directions held at frame 0.54 clear the header and preserve fixed camera framing. Childhood buildings also clear the header. Capture: `qa/september17-larger-turn.png`. The 1440 × 900 framing was inspected before interruption; the current short-desktop verification confirms the settled change. No geometry, story, header or active soundtrack change. All 19 focused tests, typecheck and 13 asset checks passed after the camera adjustment.

Three new guitar auditions use a recorded nylon-string instrument with fewer notes, softened transients, stable harmony and lower levels than the rejected piano choices. No clipping in the rendered samples. User listening and selection remain pending; no independent speaker-listening approval claimed.

Portrait 390 × 844 checked in the browser: header, book, reading text and controls visible; no console errors. Retained the prior 5.6 horizontal fit in portrait aspect ratios to preserve page-edge clearance while enlarging desktop framing. This is viewport emulation, not a physical-phone performance test. Production build and all 4 Sites worker tests passed.

## Selected Evening soundtrack, 17 September 2026

Replaced generated music with the user-selected official recording of Evening by Kevin MacLeod. Original MP3 metadata checked locally: stereo, 44.1 kHz, 160 kbps, 186.253 seconds. Recording unchanged; runtime gain 0.12, soft start, native repeat, pause/resume on mute. Attribution appears in About, CREDITS.md and public/licenses/evening-music.txt.

Typecheck, 23 tests (including 4 focused recorded-audio lifecycle cases), 13 asset validations, build, and 4 Sites tests passed. Existing bundle-size advisory remains. Browser check was rejected by automatic approval review due to a usage-limit prerequisite; subsequent retry was also rejected. No alternate browser path was attempted. Actual in-browser listening remains unverified for this release. This pass changes no book geometry, layout or chapter text.

### Soundtrack completion and cleanup

After the interruption was resolved, the local in-app browser opened the book and showed sound on after the playback request succeeded. Mute changed to sound off; enabling again restored sound on. About showed Evening by Kevin MacLeod with the official track and CC BY 4.0 links. Browser warning/error logs were empty. This verifies playback controls, not independent speaker listening.

Removed the rejected piano/guitar audition recordings, instrument sample banks, audition generators and their obsolete option documents. Their provenance remains in Git history. The selected MP3 and its license remain. Rebuilt the deployment output so deleted auditions are not shipped. Typecheck, 23 tests, 13 asset checks, production build and 4 Sites tests passed; the pre-existing bundle-size advisory remains.

## Shareable release verification, 18 September 2026

- Type checking, 31 Vitest tests, 13/13 model structural/pose validations, production build and 4 Sites tests pass. Full `npm audit --audit-level=moderate`: 0 known vulnerabilities. Vite resolves once at 6.4.3. `lsof` confirms the development listener is `127.0.0.1:4181`, not all interfaces.
- Prepatch and fresh candidate security reviewers completed scoped read-only reviews. Candidate reviewer independently reran typecheck, tests, audit and compared every model against the previous committed export: geometry/animation semantics and image bytes unchanged. No actionable blocker. The Windows-specific advisory was addressed by the patched dependency; its exploit was not reproduced on macOS. This is not a claim of exhaustive security proof.
- Initial browser check caught an illegal receiver when wrapping requestAnimationFrame. Corrected it by calling browser scheduling functions through arrow wrappers, then reran tests/build and all browser acceptance below. No remaining errors from the final production origin were observed.
- Local Chromium 153: normal entrance, skip, all 12 chapters forward and backward, contents jump 2 to 5, instant reduced-motion turn 5 to 6, and first-spread return to spine passed. Six rapid Right presses in production advanced only one chapter.
- Simulated graphics loss showed the recovery message; illustrated reading and same-chapter 3D restoration retained chapter 6. About contains the biography and official music/license links. User-gesture music activation and mute controls passed. No new soundtrack was introduced.
- Final production preview checked at desktop, 390×844 portrait and 844×390 landscape sizes. Portrait retains visible HTML chapter text below 3D and its pale illustrated alternative. A horizontal pointer drag advanced chapter 1 to 2. Responsive controls remained available. These are desktop viewport checks, not physical-phone testing.
- Development measurements at a 1280×643 stage, DPR cap 1.75, macOS host/Chromium 153: normal entrance 265 samples at about 60fps/P95 18ms; traversal's last 2400 samples about 60fps/P95 17ms, longest 18ms. Closed-book total rendered frames remained at 3884 across separate observations while idle. This measures frame intervals on this host, not general device guarantees. Physical-phone performance remains unmeasured.
- Published client file total: 25,368,720 →22,070,908 bytes, saving 3,297,812 bytes (13.0%). Initial app JS: 899,045 →243,313 bytes (about 73% smaller); Three.js loads in a separate 655,229-byte chunk only for 3D. Full 3D still needs that chunk. Shared-texture saving: 1,794,611 bytes across all chapters. These are file-size comparisons, not measured network speedups.
- Kept source Blender files, historical QA images, licenses and hosting worker/tests. No lossy mesh compression, visual redesign or content rewrite in this pass.
