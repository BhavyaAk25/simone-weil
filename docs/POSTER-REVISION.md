# Illustrated palette correction, 16 September 2026

The user rejected the flat brown illustrated reading surface and asked for a modestly larger book. The illustrated UI now uses aged ivory with dark umber text and restrained brass controls. All 12 posters were re-rendered from their existing Blender chapter sources on a subtly textured warm limestone surface, with softer neutral light and no plank seams. The poster camera changes from 6.65 to 6.10 orthographic scale. Geometry and source blend files are unchanged.

Reproduce: `/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/blender/render_posters.py`. Output: 1600 by 1112 WebP, Cycles 48 samples and denoising. Live 3D reading distance changes from 8.2/5.85 to 7.85/5.6 in the existing fit formula (about 4.5 percent larger); fixed page-turn framing is preserved. The live library background and header are unchanged in this pass.
