# Header acceptance — 12 September 2026

Scope: approved header only. Reviewer owns this file; application, asset generation, browser operation and final `design-qa.md` remain with the main agent until reassigned.

Source viewed: `/Users/bhavyakhimavat/.codex/generated_images/01a082d0-8508-7362-a931-f263e9bfb48c/exec-89418ccb-aa60-49e1-af13-61de95f2f8a1.png` (1672 × 941). Its header occupies approximately the upper 168 px. This is the approved full-width mosaic and branching endcap version, superseding the earlier plain top extension.

Status: acceptance criteria prepared from source image and existing code. No implementation screenshot comparison or browser verification has been performed by this reviewer yet. This is not a visual pass.

## Visual acceptance

- Preserve the continuous top mosaic with amber, olive and restrained teal glass. No blank ivory extension above the wavy ribs.
- Preserve the complete branching ivory/leaf-glass ends on both sides, reaching the viewport edges without clipping their meaningful shapes or leaving background slivers.
- Keep the broad quiet ivory plaques behind the name and date/menu. Text must remain separate HTML; remove all baked title, date and menu text from decorative artwork.
- Retain the central arch, overlapping rounded ribs, highlights, recessed seams and fine crackle. No flat CSS/SVG substitute, uniform gradient, repeated tile or obvious horizontal stretching.
- Match the source's dark brown serif title and dates, restrained sans-serif subtitle and menu, and letter spacing. Exact approved copy: `SIMONE WEIL`, `A LIFE IN 12 CHAPTERS`, `1909 — 1943`, and `Contents` in the reading state.
- Judge the whole header and close crops of both ends, title plaque, central arch and menu plaque. Check dark-background cutout halos, sharpness, visible compression and any baked room fragments around the perimeter.
- Phone composition must retain material and side craftsmanship with legible controls. It may reduce the central arches, but cannot simply shrink the desktop title to unreadable text or stretch the ornament vertically.

## Functional acceptance

1. Closed/loading/error: About remains reachable through the title and the existing right-side edition action. Header buttons do not open the book or enable sound accidentally.
2. Open/turning: Contents opens the existing chapter dialog, is guarded during transition, and chapter selection still works. Dialog Escape/close returns focus to its trigger.
3. Header decoration intercepts pointer events within its occupied area; clicking an ivory/glass area does not click through to the book stage.
4. Header art failure leaves a readable title and usable action on a quiet fallback surface, with the same reserved height. Artwork is decorative (`alt=""` or CSS), with no duplicate screen-reader title.
5. Desktop open scene, opening peak, page-turn peak, and short laptop remain clear of the header without changing the book camera/animation as an incidental fix.
6. Illustrated edition padding respects the new header height. Portrait reading canvas and text remain clear at 320, 390, 768, 1099 and 1100 px breakpoint boundaries; no horizontal overflow.
7. Header keyboard focus is visible against ivory/glass, action targets are comfortably tappable, and 200% zoom does not clip or overlap the title/actions.
8. First-spread 3D return, normal back/next controls and sound preference retain existing behavior.

## Likely integration risks from existing code

- `.topbar` currently sets `pointer-events: none`; only buttons catch input. Carrying that rule into opaque artwork would make parts of the header unexpectedly open the closed book beneath it.
- Existing illustrated top padding is fixed at 135 px desktop and 100 px below 1100 px. Link padding to actual header height rather than leaving it independent.
- Below 1100 px the open canvas starts at y=0. A larger header can obscure paper scenery; reserve layout clearance and inspect real frames before accepting.
- Global `.text-button:hover` makes text pale, which would reduce contrast on the new ivory plaque. Header hover/focus colors need their own dark treatment.
- Narrow title and action plaques impose real safe-area limits. A single width breakpoint or unconstrained flex row can put long `About this edition` text over the glass when the reading `Contents` label fits.

## Evidence required before publication

- Matching-scale full-view source/implementation comparison in one input, plus focused header crops. Record source pixels, screenshot pixels, CSS viewport, state and any density normalization.
- Browser captures: closed and open desktop; short desktop entrance/turn peak; portrait phone; landscape phone or tablet; illustrated edition; dialog and keyboard focus.
- Actual results for header loading/failure and WebGL-unavailable path, or clearly identified remaining gaps.
- Main agent runs required typecheck, tests, asset validation, production build and Sites checks, and records final comparison history in `design-qa.md`.

Final visual result: see the 13 September final comparison below.

## Component review, before artwork/browser captures

Reviewed `src/BookHeader.tsx`, `src/BookHeader.css` and the header-only changes in `src/App.tsx` / `src/styles.css` on 12 September.

Addressed in code: the header now intercepts pointer input, uses dark scoped hover/focus colors, keeps text as semantic buttons with decorative empty-alt artwork, preserves About/Contents callbacks and turn locking, reserves height before image loading, and ties illustrated/error top spacing to `--header-height`. Existing book camera formulas remain unchanged.

Pending visual checks, not yet classified as rendered defects:

- Artwork uses `object-fit: fill` while the desktop header height is clamped. Native declared desktop ratio is 3344:334 (about 10:1). At 601 px the layout is 601:88 (6.8:1); at 2560 px it is 2560:190 (13.5:1). Check ribs and leaf shapes at those widths; use a matching intermediate composition or adjusted sizing if distortion is visible.
- The 600→601 px breakpoint changes header height from 112 px to 88 px and swaps artwork. Inspect either side of that boundary for abrupt proportion changes or text leaving plaque safe areas.
- The open mobile canvas still begins at y=0. Browser evidence must establish scenery clearance. If required, reserve header space at layout level; `BookScene` already observes element size. Keep the same inset through entering/reading to avoid a phase-change jump, and check the existing below-1100px absolute-to-relative stage switch.
- When a responsive artwork source fails after a previous source succeeded, confirm the flat fallback reappears without broken-image decoration. The existing `onError`/`onLoad` state should cover this, but it needs an actual failure check.

## Revised code and phone evidence — 13 September 2026

The main agent replaced the title with local Cinzel 400, changed desktop stage clearance to `0.60 × --header-height`, and extended the dedicated phone composition to 760 px in both the picture source and CSS. Library backdrop intensity is now 0.80; book material exposure, lights and camera formulas are unchanged. These follow the user's subsequent title, book-size and library-tint corrections.

Viewed `docs/references/header-approved.png` (1672 × 941) and `docs/qa/header-phone.png` (390 × 844) in the same comparison input. Phone viewport is a distinct responsive composition, not a pixel-equivalent desktop target. The complete header is readable at its native captured size, so a further phone-only crop was unnecessary for this check.

- Typography: the title is clear and remains in its ivory plaque; subtitle is visibly secondary. The font is a deliberate locally served approximation of the approved lettering, not text baked into the image.
- Layout: complete curved side ends, continuous mosaic top, narrower central arch and separate menu plaque remain visible. No title/menu clipping is visible. Scenery clears the header.
- Color: warm ivory, amber/olive and quiet teal accents retain the approved relationship to the walnut room.
- Image quality: no visible perimeter background sliver, missing endcap, obvious seam or placeholder geometry. The browser capture is softer than the original generated mock across both artwork and live text; do not infer an asset-only resolution defect from this capture.
- Copy: `SIMONE WEIL`, `A LIFE IN 12 CHAPTERS` and `Contents` are present. Dates are intentionally omitted at narrow widths.
- P3 refinement: the phone menu icon sits near the curved left rim of its small plaque. Text is legible and unclipped; omitting the icon at narrow widths would make this area calmer if desired.

No actionable P1/P2 phone-header mismatch is visible in this evidence. Desktop final screenshot and browser functional results remain pending; this is not yet a complete publication verdict.

## Final desktop and tablet visual comparison — 13 September 2026

Compared `docs/references/header-approved.png`, `docs/qa/header-open-final.png` and `docs/qa/header-tablet.png` together in one image input. Source and final desktop are both 1672 × 941 pixels; the main agent reports a 1672 × 941 CSS viewport. No scaling or density normalization was applied. Tablet capture is 601 × 900 and intentionally uses the separate narrow composition. The final desktop has Contents keyboard focus; the approved mock does not. Its focus outline is expected accessible state styling, not a fidelity defect.

**Finding: no actionable P0/P1/P2 header mismatch in the supplied final views.**

- Fonts/typography: Cinzel 400 restores the approved title's engraved Roman-capital character and approximate width. Date and Contents type are readable, correctly contrasted and inside their quiet plaque. All title/navigation words remain live HTML. P3: the subtitle is slightly smaller and begins flush with the title rather than the source's modest indentation.
- Spacing/layout: the frame keeps the intended shallow height and full-width presence, complete end branches, and clear central arch. Both writing plaques have breathing room. The final scene is visually close to the source's scale, with visible clearance between its highest chimney and the header. The main agent reports approximately 1009 px book width versus 1040 px in the source, and 33 px chimney clearance; these are approximate visual measurements, not DOM geometry.
- Colors/tokens: the warm ivory/brass/amber/olive palette and restrained teal remain recognizable. The darker room now better supports the frame without recoloring the book or the UI lettering. Static local art and HTML reproduce this appearance without additional animated decoration.
- Image quality: complete edges, top mosaic and leaf endcaps are visible. No background sliver, cutout halo, crude replacement geometry or broken-art placeholder is visible. Fine source crackle is less crisp in browser captures, but softness also affects independent live HTML and bottom controls; no asset-specific defect can be concluded from that evidence alone.
- Copy/content: title, numeric 12, dates and Contents retain the approved wording. The narrow composition intentionally hides dates. About remains the closed-state action per existing behavior rather than inventing new navigation.
- Tablet: changing the 601 px view to the dedicated narrow artwork fixes the earlier risk of title placement over the desktop central glass. Current title and action occupy their own ivory plaques, with complete side ornament and no clipped text.

### Comparison history

1. Initial code review flagged artwork stretching, 600 px breakpoint changes and mobile canvas overlap as checks requiring browser evidence.
2. Initial desktop capture used the taller canvas inset; the subsequent user correction requested the title adjustment, restoration of book size and darker library. The main agent changed title font to Cinzel 400, desktop canvas inset to 0.60 header height and backdrop intensity to 0.80. The dedicated narrow-art breakpoint became 760 px after a title/glass issue at 601 px was observed by the main agent.
3. Final paired captures show restored title character and book scale, unoccluded scene peak, and corrected tablet lettering position. No P0/P1/P2 visual issue remains in these supplied states. P3 subtitle alignment and narrow menu-icon placement can remain as refinements.

### Scope and remaining evidence

This reviewer did not operate the browser. The main agent reports Contents dialog Escape restores focus to Contents. Short-desktop entrance/turn peak, header asset failure, fallback navigation, loading/error, keyboard and zoom checks remain the main agent's acceptance responsibility. This visual verdict does not claim those unobserved behaviors passed. Full-view source/implementation comparisons were inspected at native dimensions; focused header capture evidence should accompany the main agent's final `design-qa.md` if available.

Final result: passed

This is a scoped visual/code review of the supplied header states; publication remains conditional on the main agent completing required functional acceptance and project checks.
