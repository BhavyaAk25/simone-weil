# Walnut bookshop environment plate

Generated 9 September 2026 with the built-in OpenAI image generation tool. The selected `docs/references/dark-walnut.png` was supplied as an atmosphere/material reference. This asset replaces the rejected rectangular placeholder shelves with photographic depth; it is an environment plate only. The book, page geometry, scenery, and their animations must remain real Blender-authored GLB assets.

## Deliverable

- Runtime image: `public/textures/bookshop.webp`
- Dimensions: 1672 × 941 (approximately 16:9; generator selected its output dimensions)
- Encoded size: 184,190 bytes (180 KiB)
- WebP quality: 88; RGB; method 6. Encoding only, no visual edits or image compositing.
- Original generated file: `local generated-image archive: 01a0888b-6669-7323-95f3-d802a071dc69/exec-c894834a-becd-47e5-8f29-f195e05b6972.png`
- Provenance: project-generated image. No external stock photograph, font, or purchased asset was incorporated separately. The generated reference is a project concept asset, not a photograph of an actual location.

## Inspection and integration guidance

The image was inspected at native resolution after generation and after WebP encoding. It contains an empty desk across the bottom 41%, richly detailed leather books, warm walnut cabinetry, a softly focused window on the left, and a restrained brass lamp on the right. The central background is dark and uncluttered enough to separate an ivory book silhouette. There is no central book, paper scenery, readable title, website interface, person, watermark, or palette strip. Small peripheral decor remains away from the empty desk.

Keep the natural desk grain at photographic scale; do not tile or stretch this plate. Use cover-style aspect cropping. A subtle gradient can support controls, but avoid crushing the walnut shadow detail. Match actual 3D book lighting to the window on the left. Use a real desk/shadow-receiving surface for book contact shadows where needed. The plate is fixed background depth, so camera motion should remain restrained; do not imply that the raster shelves have interactive parallax. Final acceptance still requires actual browser viewing with the book and both turn directions.

## Generation prompt

> Use case: photorealistic-natural. Asset type: environment background plate for a sophisticated interactive 3D biography website. Input Image 1 is a material, light, color and atmosphere reference only. Create ONE beautiful photorealistic EMPTY walnut bookshop environment, wide 16:9, target 2048x1152. The foreground pop-up book, paper sculptures, palette strip, writing, and people in the reference must NOT appear. A quiet antique Paris bookshop: warm beautiful deep walnut shelves behind, authentic irregular aged tobacco leather books with delicate spine ridges and subtle brass tooling but NO readable writing, softly focused in the distance. Tall sunlit window occupies far LEFT edge and casts warm soft amber afternoon light. Restrained antique brass reading lamp at far RIGHT, mostly softly focused. Lower 40% of frame is a large entirely EMPTY clean dark walnut reading desk, extends uninterrupted to bottom edge, beautiful fine natural grain, satin low-contrast sheen, authentic rich chocolate brown not red-orange, no huge streaks. Desk back edge about 55% image height; eye-level view angled slightly down at desk, enough empty surface to digitally place a wide open book centrally. Middle and top background have photographic depth and soft optical bokeh, not crude geometry. Composition center uncluttered and relatively dark to frame an ivory book we will render separately; desk foreground slightly sharper than distant shelves. Restrained luxurious tactile craftsmanship, warm walnut/tobacco/ivory palette from reference, rich shadow detail. Avoid: foreground objects or books on desk, any pop-up book, people, text, logos, watermark, swatches, website UI, cartoon or plastic CGI, rows of identical rectangular book blocks, oversized wood grain, harsh stripes, overexposed window, strong orange cast. Output full-frame photographic scene only.
