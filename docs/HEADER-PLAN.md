# Sculpted header — implementation record

Status: implementation authorized, 12 September 2026. Selected final visual: `references/header-approved.png`. Scope includes the header and the 13 September corrections to book prominence, title typography and backdrop darkness; ownership is recorded in AGENTS.md.

## Visual source and scope

Primary reference: `/Users/bhavyakhimavat/Desktop/ccb3519c-5037-49c4-a538-390631bf4203.png` supplied by the user. Current header comparison: `/Users/bhavyakhimavat/Desktop/Screenshot 2026-09-12 at 5.23.19 PM.png` (the actual supplied filename uses a narrow no-break space before PM).

Replace the existing translucent rectangular top bar with the reference's sculpted ivory-and-glass header. Preserve the walnut bookshop, book, chapters, bottom controls, audio behavior, and entrance/page animations. This is a proposed implementation plan, not a claim of achieved visual fidelity.

## Reference analysis

- Continuous asymmetric wave silhouette; rounded ivory ribs overlap and form deep arched openings.
- Aged ceramic-like surfaces with fine crackle, warm edge highlights, darker recessed seams and soft contact shadows. Crackle remains restrained at normal display size.
- Irregular amber, olive, teal and blue glass pieces occupy recesses; colour is concentrated in the ornament, with calm ivory text areas.
- Left title plaque, central decorative arches, right date/menu plaque. Approximately one-third / two-fifths / remaining width, to be measured precisely during asset authoring.
- The large cream area above and below the object belongs to the presentation image, not to the website header.
- Lettering must be HTML, including the established “A LIFE IN 12 CHAPTERS”; do not bake the mock's “TWELVE” or menu text into artwork.

## Proposed pipeline and gates

1. Produce a full-page desktop composition over the actual closed and open book screenshots, plus a dedicated phone composition. Keep the reference's silhouette, depth, palette and visual hierarchy. Compare these in context before authoring production assets. ImageGen can edit the provided reference into a text-free design study; inspect for malformed edges and inconsistent material/light.
2. Author the approved frame as a separate Blender source: curves for the rounded ribs and perimeter, shallow plaque surfaces, glass inserts, intentional recesses, warm light matching the bookshop. Use controlled thickness, bevels and surface materials. Keep this independent of the shared book rig.
3. Render transparent artwork from Blender at desktop/tablet/phone compositions, with sufficient resolution for high-density displays. Use an orthographic camera for predictable layout. Export compressed transparent WebP; keep source PNG and editable blend/export script. Avoid stretching one wide asset into a phone header.
4. Implement a separate React header with decorative, non-interactive artwork and live HTML title, subtitle, dates and buttons in reserved safe areas. Use responsive picture sources. Retain the current About/Contents behavior unless separately requested. Header navigation must function before the artwork loads and when WebGL is unavailable.
5. Check in the real browser at wide desktop, short laptop, tablet and portrait phone sizes. Compare reference and implementation together at matching scales. Check entrance/turn peak clearance, open-book writing, 200% browser zoom, focus, contrast, tap targets, dialogs, loading and illustrated fallback. Do not move the book camera as an incidental header fix; flag an unavoidable framing conflict for discussion.
6. Update project QA/credits/pipeline notes, run existing checks, and publish only after the user has approved proceeding beyond this planning stage and the visual/functional gates pass.

## Initial layout targets, subject to composition proof

- Desktop: approximately 130–155 px high at 1440 px width; smaller on short screens if needed to preserve book clearance.
- Phone: approximately 80–100 px, title and menu as the main anchors, fewer central arches. Recompose ornament rather than shrinking all text.
- Keep typography dark brown on calm ivory. Retain current font family initially and compare weight/spacing against the supplied reference before considering a replacement.
- Reserve dimensions to prevent layout shifts; aim for a desktop header image below 500 KB and phone below 200 KB, subject to acceptable image quality. These are targets, not measured results.
- Default: static sculpture, subtle button hover/focus only. No automatic shimmer, orbit, floating pieces or additional real-time 3D renderer.

## Approved palette and edge treatment

The user selected the warm amber/olive palette with restrained teal, refined through three edge revisions: cover the top gaps, fill that extension with glass mosaic rather than plain ivory, and integrate branching leaf-glass designs at both outer ends. Preserve the approved calm text plaques. The website below the header remains the existing implementation.

## Technical references

- Blender transparent film: https://docs.blender.org/manual/en/3.0/render/cycles/render_settings/film.html
- Responsive art direction with picture: https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/picture

## Implemented, 13 September 2026

The delivered asset pipeline uses a Blender UV-textured silhouette with baked relief from the approved artwork, rather than individually modeled ceramic ribs and glass. This preserves the selected image more closely and adds no second real-time renderer. See HEADER-ASSETS.md for the exact reproducible method and its limits.

The live title uses locally bundled Cinzel 400, with Inter subtitle/menu and the existing serif dates. Dedicated mobile artwork applies through 760 px; the desktop canvas reserves 60% of the header height to recover book scale while preserving chimney and turning-sheet clearance. Background intensity is 0.80; page materials, lighting, meshes and camera formulas are unchanged. HEADER-QA.md and QA.md record actual verification.
