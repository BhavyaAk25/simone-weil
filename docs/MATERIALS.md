# Generated material textures

Created 2026-09-08 using the built-in OpenAI Image Generation tool, with one independent generation call per material. The reference `docs/references/dark-walnut.png` was inspected for palette and atmosphere; it was not flattened or used as a texture. Both delivered files are material-only albedo maps for actual 3D surfaces.

## Deliverables

| Asset | Dimensions | File size | Average sRGB | Intended surface |
| --- | --- | --- | --- | --- |
| `public/textures/walnut.webp` | 1024 × 1024 | 95,442 bytes | approximately #4A2E1E | Walnut desk and wood surfaces |
| `public/textures/paper.webp` | 1024 × 1024 | 136,176 bytes | approximately #E7D8BF | Book pages and paper scene pieces |

- Both original generations were 1254 × 1254 PNG images. They were resized to 1024 × 1024 and encoded as WebP with quality 86 and effort 6 using the existing bundled Sharp library. No project dependency was added.
- No Python image editing or procedural replacement was used. The generated image content was unchanged apart from resizing and format conversion.
- No external photographs, downloaded textures, text, logos, or brands are embedded in these generated assets. Record them as AI-generated project materials in general credits.
- Original PNG outputs remain at the generation paths below; runtime use must reference the project WebP files.
- Use `SRGBColorSpace` for these base-color textures. Apply roughness and lighting through the 3D material; these files contain no intentional directional illumination.
- The prompts requested seamless repeatability. Opposite edges are not mathematically identical. Measured mean absolute RGB differences across opposite borders are 5.56 / 4.30 out of 255 (walnut horizontal / vertical) and 5.92 / 6.15 (paper). These are restrained transitions, but final repeat visibility still requires the browser material review. Mirrored repeat wrapping is available if a visible join appears.
- Visual inspection confirmed no boards, gaps, text, borders, directional highlights, or page edges. Paper has fine fibers and small speckles; wood has fine vertical grain. Website lighting and projected text readability were not verified by this asset-only task.

## Walnut provenance

Original output:
`local generated-image archive: 01a0835f-32fc-7d12-a41b-31bb2a0495a0/exec-79f49a48-946c-4bfe-9f4b-a7622ca149f1.png`

Exact generation prompt:

```text
Use case: photorealistic-natural
Asset type: seamless tileable base-color (albedo) texture for the walnut desk in a real-time 3D luxury antique pop-up book scene.
Primary request: Generate one square 1024x1024 texture of rich dark walnut wood, viewed perfectly straight down, orthographic, surface fills every pixel.
Color palette: dark tobacco walnut centered around sRGB #422A20, subtle warm brown grain, restrained natural variation.
Materials/textures: fine long mostly vertical flowing walnut grain, small-scale pores, gentle organic grain movement. Physically plausible, refined antique furniture wood, smooth matte surface with realistic fine detail.
Lighting: flat uniform diffuse albedo only, no directional lighting, no specular highlight, no shadows, no vignette, no depth or perspective.
Constraints: seamless at all four borders so repeat tiling has no visible seams; grain should flow from top edge to bottom edge and match left/right. One continuous wood surface. No boards, no gaps, no seams, no planks, no prominent knots, no edge, no objects, no lettering, no watermark, no border. Do not render a desk or environment; only the material texture.
```

## Paper provenance

Original output:
`local generated-image archive: 01a0835f-32fc-7d12-a41b-31bb2a0495a0/exec-09f855d3-c4bf-4590-9dc0-a204a451b48e.png`

Exact generation prompt:

```text
Use case: photorealistic-natural
Asset type: seamless tileable base-color (albedo) texture for aged ivory pages and paper pop-up scenery in a real-time 3D luxury antique book.
Primary request: Generate one square 1024x1024 texture of warm ivory handmade archival book paper. Perfectly straight-down orthographic view; paper surface fills every pixel.
Color palette: aged ivory centered around sRGB #E8DDC7, very subtle cream and warm linen variations; light enough for crisp dark paragraph text.
Materials/textures: restrained natural paper fibers, tiny fine irregular speckles, faint pressed grain, soft organic variation at small scale. Refined, intact and well-kept handmade paper, not grungy or distressed.
Lighting: completely flat uniform diffuse albedo only. No directional light, no highlights, no cast shadows, no vignette, no depth or perspective.
Constraints: seamlessly repeatable at all four borders; uniform average color throughout. No page edges, no fold, no crease, no torn edge, no holes, no stains, no decorative border, no lettering, no writing, no watermark, no objects or scenery. Do not draw a sheet or a book; output only the pure paper material texture.
```
