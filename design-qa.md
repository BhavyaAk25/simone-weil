# Visual verification — 11 September 2026

Final result: local visual and interaction review passed after corrections; physical-phone performance remains unmeasured. This is agent verification, not a claim that the user has approved the revised art.

## Comparison inputs

Source: `docs/references/dark-walnut.png` (1487 × 1058, including a palette strip below the scene). Actual implementation: `docs/qa/desktop-childhood-final.png` and revised `desktop-childhood-lighting.png` (1440 × 1000 browser viewport, no browser chrome). The source and initial implementation were opened together in one comparison input. The source is a material/composition study containing a combined Paris/spiritual scene, not the final childhood content or navigation layout. The agreed twelve scenes and later raised-writing request intentionally change this composition. Do not describe this as a pixel-identical reproduction or a photorealistic match.

## Findings and corrections

- P1, animation: the earlier prototype exposed upright geometry before the cover opened. Chapter visibility now begins only after the cover has completed its opening. Actual entrance and fold/turn boundary frames were inspected.
- P1, writing: the original print was too flat and small. A real 18-degree paper panel now carries dark, larger Cormorant text. The complete prose and quotation were inspected across all twelve chapters; the chapter 11 attribution overlap was fixed by reserving its measured space. Phone text appears in semantic HTML below the stage.
- P2, halfway turn: the paper appeared notched when viewed almost exactly edge-on and approached the header. A restrained camera arc and pullback keep the full sheet framed and make its curl visible. Both directions were checked at the midpoint.
- P2, material depth: the initial comparison showed weak grounding shadows. Moved the warm key light behind/left of the book, reduced ambient fill and retained a front fill. The revised capture shows shadows from the paper panel, figures, foliage and architecture falling onto the pages.
- P2, small text contrast: source notes, chapter dates and contents numbers on ivory were too pale. Their colours were darkened. The dark-background reading/fallback palette remains separately styled.
- P2, mobile focus: focusing the semantic article could inherit the desktop overlay translation. The mobile rule now clears that transformation.

## Required surfaces

- Typography: Cormorant Garamond display/body/quotes and restrained Inter navigation; fonts are bundled locally with OFL notices. Large 3D print and semantic reading dialog retain the complete prose and attribution. No source artwork lettering is substituted for actual text.
- Spacing: the book stays centered with a reserved left writing region and right/rear scenery. Header/footer controls have their own space. Short desktop and portrait/landscape phone viewports were reviewed after integration.
- Colour: dark walnut, ivory, tobacco and restrained brass follow the palette. The leather was darkened after the first corrected pass to avoid the earlier washed-out cover. Live light and shadows supply depth.
- Image quality: the library is original generated environmental artwork, with actual 3D shadows and book geometry in front. Facade engraving is an albedo print on real hinged cards; roofs, thickness, figures and vegetation are mesh geometry. The rendering is stylized cut paper and is simpler than the photorealistic concept.
- Content: twelve distinct chronological topics and verified short project translations, with retrospective and posthumous context in the source view. The concept's mixed scenery is divided across the relevant chapters.

## Final comparison and review

The selected reference and `docs/qa/production-childhood.png` were opened together in the same comparison input on 11 September, after the lighting, leather, header clearance and text corrections. The actual 1440 × 1000 browser capture shows a centered, substantial layered book, dark walnut setting, warm side light, ivory paper, grounded card shadows and clearly raised dark lettering. No observed blocking overlap or floating card remained in the inspected entrance/turn frames and settled spreads.

Intentional differences: the source's combined city/chapel is divided into chronological chapters; the childhood spread contains the apartment, two desks and figures. The raised writing panel takes the left foreground, as requested. Architecture, foliage and figures are stylized paper scenery and remain simpler than the photorealistic source. The environmental backdrop is an image, while the book, paper cards and shadows are rendered geometry. This is not a pixel-identical or photorealistic reproduction.

All twelve scene endpoints, forward/back sequence, portrait/landscape layouts, closed entry, recovery, contents, reading and reduced motion were checked. Measured desktop results and limits are in `docs/QA.md`. Final captured typography has a complete paragraph, quotation and separated attribution; the reserved writing area is free of scenery.
