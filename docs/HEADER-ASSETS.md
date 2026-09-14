# Approved ivory and stained-glass header assets

The selected reference is `docs/references/header-approved.png`. It contains the final leaf-shaped side treatments and a mosaic filling the top edge. The header is decorative artwork; title, subtitle, date and Contents control remain semantic HTML.

## Runtime assets and placement

| Asset | Pixels | Encoded size | Placement |
| --- | --- | --- | --- |
| `public/textures/header-desktop.webp` | 3344 × 343 | 229,252 bytes | Full-bleed top, approximately 9.75:1 |
| `public/textures/header-mobile.webp` | 1560 × 364 | 163,082 bytes | Separately composed phone header, approximately 4.29:1 |

Both files contain genuine alpha (verified range 0–255) below the wavy lower edge. Top mosaic and branching ends meet the top/side bounds. Desktop text safe areas are approximately x7.5–29% and x72–95%; phone title x8–59% and menu x77–91%. Text should be vertically centered within its ivory plaque, around 50–55% of the full header height. The reference's generated lettering has been removed from the decoration.

## Actual authoring method

Built-in ImageGen was used to extract text-free ornament from the approved reference and to recompose a phone variant. The tool produced RGB artwork with a painted checkerboard despite two requests for genuine transparency. Neither that background nor a fake transparency image is shipped.

The separate Blender source maps the generated high-fidelity artwork onto an editable silhouette mesh. The mesh follows the ivory lower edge and excludes the neutral background. An orthographic emission-material render preserves the approved baked highlights, depth and glass coloration. **This is a textured silhouette with baked relief shading, not a hand-sculpted reconstruction of every rib or glass piece.** It is also not part of the live book mesh or a new browser 3D scene.

Source artwork is 2172 pixels wide on desktop and 1983 pixels wide on phone. The desktop render is supersampled to 3344 pixels to produce smooth geometry edges; that does not invent native texture detail. Each `.blend` packs its source texture and has a separate camera and editable boundary. Existing book/chapter Blender files are untouched.

## Source files and reproduction

- `assets/source/header/desktop-artwork.png`: generated text-free desktop artwork.
- `assets/source/header/phone-artwork.png`: generated compact phone composition.
- `assets/source/header/header-desktop.blend`, `header-phone.blend`: independently editable packed scenes, tracked with the repository's Blender LFS convention.
- `assets/source/header/header-desktop.png`, `header-phone.png`: lossless RGBA render masters.
- `scripts/blender/build_header.py`: deterministic silhouette mesh, UV, camera and RGBA export.
- `scripts/blender/compress_header.py`: WebP encoding only, quality 94, method 6; requires Pillow.

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/blender/build_header.py
python3 scripts/blender/compress_header.py
```

The silhouette traces only the lower-edge scan band, using warm ivory chroma to exclude gray backdrop pixels. A median/mean smoothing pass and small inset prevent checkerboard fringe. If the source composition changes, inspect and update the scan band before rerendering.

## Image generation provenance

Built-in ImageGen only; no paid CLI/API fallback. Desktop selected output: `exec-e7d1c0df-579d-4631-a7e1-adefc354255a.png`. Phone selected output: `exec-d9d1f08d-9dbd-4e0b-971e-3c55e7b06bb0.png`. The original generated source files are preserved in this project, so runtime and reproduction do not depend on the Codex image cache.

Desktop prompt:

> Extract ONLY the decorative ivory and stained-glass website header at the very top of this image as a production-ready high-resolution PNG asset. Preserve the exact approved sculpture, proportions, lighting, materials and arrangement; this is a precise extraction and removal of lettering, not a redesign. Remove ALL lettering, numbers, hamburger menu and other symbols from the two ivory text plaques, restoring uninterrupted fine ivory crackle texture in those areas. Remove the entire bookshop, book, table and all UI below the header. Output the isolated header in an extremely wide approximately 10:1 canvas, ideally 3840 by 384 pixels, tightly fitted: its mosaic reaches fully to the top edge; branching ivory and leaf glass ends meet the left and right canvas edges; below the gently wavy lower ivory edge is REAL ALPHA TRANSPARENCY, not a checkerboard drawing. Preserve the warm amber/olive glass, restrained muted teal, sophisticated rounded ivory ribs, deep central arches, soft highlights, and detailed leaf-shaped end caps. Left quiet ivory plaque spans approximately x7.5-29%; center sculpted arches x30-69%; right quiet ivory plaque spans x72-95%. Absolutely no text, no icons, no white rectangular background, no extra border or scene. All internal stained glass retains its colored amber glow and optical material; only outside the silhouette below is transparent.

Final phone refinement prompt (using the initial phone composition generated in the same style):

> Edit this ornament layout. It MUST be a compact mobile header: expand the large left ivory plaque to occupy from 8 percent all the way to 62 percent of the image width. The plaque must reach past the center of the image. Shrink the central stained glass arch into a very narrow sliver at 64-73 percent width. Keep small right blank ivory plaque at 77-93 percent width. Both ends remain detailed branching ivory leaf glass. Increase the whole ornament height to one quarter of its width, meaning 4 to 1 proportions for the ornament itself, taller than existing. Fill top and left right boundaries, no margins. Fine warm amber olive muted teal glass, crackled ivory and dimensional sculpted ribs same style as input. NO TEXT, no letters, no numbers or icons. Below the lower wavy edge transparent background. Preserve the beautiful organic workmanship. This is specifically a narrow mobile phone composition with one large left panel and one small right panel, not two equally sized plaques.

## Asset checks

Inspected text-free desktop and phone artwork and both Blender outputs. Tightened the desktop mesh after the first export exposed small gray/white backdrop fragments under the rim. Final exports have real alpha, detailed leaf ends, full top mosaic, and no baked interface text. Browser composition and interaction verification belong to the application integration pass; these source renders alone do not establish website acceptance.
