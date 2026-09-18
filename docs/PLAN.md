# Implementation milestones

1. **Foundation and visual revision — complete:** scaffold, typed content, research, book and two chapter assets exist. The initial visual result was rejected; see `REVISION.md` and the durable feedback in `AGENTS.md`.
2. **Working book gate — verified 10 September:** browser-check spine-first entrance, cover opening, popup, forward and reverse turn, text and touch input. Freeze export conventions.
3. **Twelve spreads — complete, 11 September:** produce and integrate chapters 3–12; each has distinct scenery, source-backed text, and quotation. Add contents, sound, accessibility and recovery.
4. **Verification — passed locally, 11 September:** typecheck, build, transition tests, asset validation, browser flow and visual checks, mobile viewports, performance observations.
5. **Publication — complete, 11 September:** public `BhavyaAk25/simone-weil`, thirteen LFS Blender sources uploaded, `dist/client` deployed through GitHub Actions, public entrance, chapter jump/reverse, source view and illustrated edition checked.

## Ownership

Main: web application and integration; content agent: narrative and quotations; Blender agent: model sources and exports; verification agent: independent checks once runnable. See AGENTS.md for file boundaries.

## Acceptance

The complete book runs in a browser, all twelve spreads can be read in both directions, the page scenery actually folds and turns, and unsupported graphics retains a readable illustrated experience. Appearance is compared against the selected dark-walnut mood study. Any unverified physical-phone target must be reported explicitly.

## Published result

- Current website: https://simone-weil.bhavyaak.chatgpt.site
- Original GitHub Pages release below is historical; Pages is disabled.
- Repository: https://github.com/BhavyaAk25/simone-weil
- First successful release: commit `c130d5c`, [Actions run 34654374350](https://github.com/BhavyaAk25/simone-weil/actions/runs/34654374350).
- Physical-phone performance remains unmeasured; desktop and mobile viewport checks are documented in QA.

## Scoped follow-up

Implemented the requested fixed-camera page turns, cover photograph/artistic spine, guitar-style music, label cleanup, revised invitation, visible same-chapter 3D return and tree/gear surface separation. See REVISION and QA for details; publication follows the existing checks.

## Approved header and follow-up refinements — 13 September

Implemented independent responsive header component with live HTML lettering and controls, approved amber/olive mosaic and branching ends, locally bundled Cinzel title, restored book prominence and darker library backdrop. Main integrates and publishes; header-art supplied isolated assets; header-review completed desktop/tablet/phone comparison. Verification evidence and remaining device limits are recorded in HEADER-QA.md and QA.md.

## Shareable release, 18 September 2026

Completed the approved security and performance pass: patched development tooling, loopback binding, CI audit, removed unused Playwright dependency, lazy 3D bundle, parallel loading, idle/hidden rendering pause, lossless shared textures and removal of authoring-only public duplicates. Existing visuals, story and selected music remain unchanged. Main resumed the asset agent's final documentation after its usage limit; independent candidate review found no actionable blocker. Full checks and release evidence are in QA. Older screenshots and editable Blender sources remain as provenance, rather than being confused with visitor downloads.
