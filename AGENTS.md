# Prototype Instructions

## The Life of Simone Weil

Implement the approved twelve-spread, English, interactive biography. The approved colour reference is `docs/references/dark-walnut.png`; it establishes materials and atmosphere, not a flattened substitute for the real 3D book. Entry is a centred, spine-facing closed book titled "The Life of Simone Weil", extraction, front-cover reveal, descent to the walnut desk, opening, then unfolding scenery. Desktop text belongs on the paper; mobile text may sit below the canvas. Guided buttons/swipe/keyboard, restrained camera motion, opt-in audio, and reduced-motion reading are required.

### Ownership and collaboration

- Main agent: application, integration, shared types, project docs, dependency changes, git and publishing.
- Content agent: `src/content/chapters.ts`, `docs/STORY.md`, `docs/SOURCES.md`, quotation entries in `CREDITS.md` only. Verify exact quotations and label translations, retrospective dates, and posthumous compilations.
- Blender agent: `scripts/blender/`, `assets/source/`, `public/models/`, `public/posters/`, and `docs/PIPELINE.md`. Only this agent may operate the shared Blender application. No application source, git, or publishing changes.
- Verification agent: `tests/book*`, `scripts/validate-assets.mjs`, `docs/QA.md`, `design-qa.md`; read-only browser/app review. Coordinate browser ownership before acting. No application fixes without an explicit reassignment.
- Do not overwrite another agent's files. Send interface changes to the main agent first.
- Ownership handoff, 10 September: the Blender and verification agents were interrupted by account usage limits after saving their work. The main agent assumes their file ownership while they are inactive, including the Blender export pipeline. Reassign explicitly before either agent resumes; never run concurrent Blender authors.

### Quality gates

### User correction — 9 September 2026

The first prototype was rejected as visually sloppy and unlike the selected reference. This is a durable requirement, not optional polish. Do not expand a crude technical demonstration into twelve crude scenes.

- Setting: beautiful natural walnut furniture, subtle fine grain, soft amber window light and a deep, softly focused bookshop. No oversized streaky wood texture or rows of untextured rectangular placeholder books.
- Book: substantial tobacco leather, restrained brass embossing, visibly layered curved ivory pages and a convincing spine. Match the craftsmanship and visual richness of `docs/references/dark-walnut.png`.
- Scenery: layered, detailed paper architecture and organic silhouettes with intentional composition. Avoid repetitive box buildings, stick trees and sparse generic props.
- Animation: every paper piece remains attached to a hinge on the page. Fold completely before turning; unfold only after the book/page is open and settled. No instantaneous default-pose appearance, floating pieces, clipping through covers or overlapping transitions.
- Verify actual browser frames during entrance and both turn directions, not only endpoint renders. One polished spread must pass before chapter expansion.
- Keep these decisions, measured QA results and remaining limitations in Markdown. Never claim visual acceptance based only on a passing build or a Blender render.
- Readability correction (10 September): the writing should be slightly raised/tilted in 3D toward the visitor, with larger, darker, clearer lettering. Use a real folded paper reading panel attached to the page; it must fold down before turning and must never float independently. Preserve the semantic reading view and visible mobile text.

First export only the book, one finished childhood spread, and the neighboring education spread. The main agent must verify the entrance and both turn directions in a browser before detailed production of chapters 3–12. Asset paths and transforms become fixed at that gate.

Use actual Blender mesh assets and deterministic baked folding/page animations, not screenshots masquerading as 3D. Do not change source quotations without updating their sources. Record real verification results, distinguish viewport emulation from physical-device testing, and never claim a Blender render proves the website works.

Keep credentials out of files. No purchases. The user authorized creation of `BhavyaAk25/simone-weil`, pushing scoped changes, and GitHub Pages publication after verification. Preserve the starter's Sites build files. Run typecheck, build, tests, asset checks and browser acceptance before publishing; deploy `dist/client` with the `/simone-weil/` base path.

Run the local server yourself and open the preview in the browser available to this environment. Do not give the user server-start instructions when you can run it.

Before making substantial visual changes, use the Product Design plugin's `get-context` skill when the visual source is unclear or no longer matches the current goal. When the user gives durable prototype-specific design feedback, preferences, or decisions, record them in `AGENTS.md`.

When implementing from a selected generated mock, treat that image as the source of truth for layout, component anatomy, density, spacing, color, typography, visible content, and hierarchy.

Build app UI in `src/`. Keep `.openai/hosting.json`, `worker/index.js`, `scripts/prepare-sites-build.mjs`, and `tests/sites-worker.test.mjs` intact so the same local prototype can be handed to Sites. Before a Sites handoff, run `npm run build` and `npm run test:sites`; the build must leave `dist/client/index.html`, `dist/server/index.js`, and `dist/.openai/hosting.json`.

### Scoped user corrections — 11 September 2026

- Page turns use fixed camera framing: no orbit, swoop or zoom. Keep the sheet turn and the necessary attached-paper folding.
- Include Simone Weil's photographic portrait on the front cover and spine, attached to the corresponding book meshes.
- Audio remains opt-in: quiet, soothing Spanish-guitar-inspired instrumental accompaniment. Do not claim it represents her documented musical taste.
- Remove the bottom-left “A little time. A closer look.” text. Use “12” in interface and book labels instead of spelling “twelve”.
- This pass is limited to these four requests; preserve the chapter content and established setting.
- Portrait follow-up: keep the front-cover photograph; the spine uses an upright artistic brass/sepia engraved likeness matched to the book. Inspect the real spine orientation before publishing.

### Follow-up controls and surface fixes — 11 September 2026

- The closed-book invitation reads “A story of courage, belonging, and independence.”
- The illustrated edition has a visible 3D return beside the page counter; restore the same chapter in 3D.
- Latest audio preference supersedes the earlier default-off rule: starting the book through a click, tap or Enter starts music; keep a working mute control and respect browser audio restrictions. Do not force playback before a visitor gesture.
- Fix flickering overlapping tree leaves and factory gears at the mesh surfaces, preserving their composition and the rest of the story.

### First-spread navigation clarification — 12 September 2026

- In the open 3D book, the first spread's left circular control reads “3D” and returns to the closed, spine-facing book. Later spreads keep the previous-page arrow. Return immediately without adding camera choreography; the book can then be opened again.
- Preserve the illustrated edition's same-chapter 3D return and the visitor's sound preference. This pass does not redesign the header.

### Header planning — 12 September 2026

- The user now requests planning a header redesign from `ccb3519c-5037-49c4-a538-390631bf4203.png`: sculpted ivory ribs, arched recesses, coloured glass and calm lettering areas. The current rectangular blurred bar is rejected as generic.
- This turn authorizes analysis and a plan only. See `docs/HEADER-PLAN.md` for the proposed pipeline, visual gates and unresolved palette choice. Do not treat proposed dimensions or material adaptations as approved.
- Judge the header over the actual walnut bookshop and both closed/open book states, including a separately composed phone version. Preserve existing book behavior and scope the implementation to the header when authorized.

### Approved header implementation — 12 September 2026

- User approved `docs/references/header-approved.png` and authorized execution with agents. It supersedes the earlier planning-only status: warm ivory sculpture, amber/olive glass with muted teal, mosaic filling the top edge, and branching leaf-shaped glass at both outer edges. No plain filler strips or detached rounded end caps.
- Focus exclusively on the top header and its responsive functional controls. Preserve the live book, chapter assets, room, audio, page-turn camera and bottom navigation. Generated variations below the header are not new requirements.
- Main owns application/integration/docs/publishing. Header-art agent owns only header-prefixed assets and Blender script/source plus `docs/HEADER-ASSETS.md`. Header-review agent owns `docs/HEADER-QA.md`; browser ownership requires explicit handoff. Existing book Blender sources remain untouched.

### Header integration correction — 13 September 2026

- The user rejected the first integration's smaller book and weak title typography. Restore the book's visual prominence while keeping header clearance; avoid reserving the full header height inside the desktop canvas.
- Match the approved reference's darker, richer walnut-library background. This specific backdrop colour correction is authorized in addition to the header. Keep paper/scene lighting and chapter assets unchanged.
- Header agents saved assets and review notes before hitting usage limits. Main assumes their remaining verification/doc ownership while they are inactive.

### Sites-only release and reader corrections — 16 September 2026

- Publish the website publicly on ChatGPT Sites. Disable GitHub Pages; retain GitHub only for source and Blender LFS storage. The root-domain Vite base is now the default. GitHub Actions should verify, not deploy.
- Illustrated reading uses warm aged ivory with dark espresso text and refined neutral poster grounds. Remove the crude brown plank renders. Increase book prominence modestly, checking header and turn clearance.
- About must explain who Simone Weil was in a clear paragraph. Remove “Made with curiosity, and a little attention.”
- Review all12 original chapter paragraphs for accessible language, connected chronology and a balanced account of her life. Use digits for numeric quantities (especially34) and no em dashes in editorial copy. Preserve verified quotations and source labels.
- Prepare3 gentle piano audition samples for user choice. Do not select or replace the active soundtrack before the user chooses.

- 16 September handoff: content revisions completed; illustrated-art and piano agents saved work before hitting usage limits. Main resumes their unfinished rendering, attribution, verification and integration while they are inactive.

### Softer guitar and book size follow-up, 16 September 2026

- The user rejected the piano auditions as harsh, with overly obvious note/tone changes. Prepare guitar alternatives with rounded attacks, sparse low-register notes, stable harmony and a quiet sustained background. Do not confuse lower volume alone with a calmer arrangement. Present choices before replacing the soundtrack.
- Enlarge the live open book a little further (about 5 percent), retaining header clearance and fixed page-turn framing. Limit this pass to these 2 requests.

### Selected soundtrack, 17 September 2026

- User chose option 3, “Evening” by Kevin MacLeod (guitar, cello, oboe). This supersedes the original synthesized soundtrack and the unselected piano/guitar auditions. Keep the official recording quiet, start only on a visitor gesture, and preserve mute and same-session playback position.
- Bundle the unchanged official MP3 locally and retain CC BY 4.0 attribution in About, CREDITS.md and public/licenses/evening-music.txt. Do not make unrelated visual changes.

- Cleanup approved: remove rejected music auditions, their source sample banks, generation scripts and obsolete option documents. Keep only the selected Evening recording and its attribution in the deployed audio assets. Preserve the book, chapter assets and other project work.

### Release maintenance, 18 September 2026

- Preserve the approved appearance, content and official Evening soundtrack during security/performance maintenance. The user authorized finishing the release and sharing its public Sites link; GitHub remains source-only.
- Vite development/preview defaults to loopback only. Keep tooling patched and run full `npm audit --audit-level=moderate` with the release checks.
- Keep the 3D scene dynamically imported, on-demand/visibility-aware rendering, and parallel initial asset requests. Test entry, both turn directions, fallback return and reduced motion when changing these lifecycles.
- Shared texture files under `public/textures/shared` are required runtime dependencies of GLBs. Do not delete them as apparently unreferenced assets. Original authoring images are in `assets/source/textures`.
