# Room and lamp (Room agent, 18 November 2026)

Scope: `docs/QUALITY-SPEC.md` section B. The user rejected the earlier lamp because it "floats in the air", is "gimmicky" and "not well designed". This pass replaces the flat-photo room with a real desk and rebuilds the lamp. The approved look stays: a dark walnut library, warm window light, the book framing and camera (BookScene) unchanged.

## What was wrong

- The room was one photograph drawn as `scene.background`, and the "desk" was an invisible shadow-catcher plane. Anything away from the book had no surface to stand on: the lamp sat over the photographed window and back edge, at the wrong perspective, with no contact.
- The lamp had primitive proportions, a solid green cylinder painted with emissive colour, painted beads, no contact shadow and a hard spotlight ring.

## Design decisions

### Desk

- **A real 3D desktop.** A slab built in `room.ts` (`deskGeometry`): a flat top at y = −0.046 (the book rests at −0.045) from far in front of the camera back to a rounded back edge at z = −2.95 (radius 0.075), then a vertical back face. It is wide enough (±18) that its ends are never seen. A glTF was not needed for a slab, so there is no `desk.glb` or `build_desk.py`; the geometry is code and the textures are generated.
- **Physical consequence for the framing.** The camera looks down about 31°, so a desk that physically holds the open book (whose back edge is at z = −1.7) must end higher on screen than the photographed desk did. In the reading view the library band now runs from the header to about 40 % of the canvas height, where it previously reached about 60 %. The old composition placed the book over the photographed bookcases, which is why nothing beside it could sit on anything.
- **Walnut material.** `MeshPhysicalMaterial`: a procedural albedo, a tiling pore/fibre normal and roughness, and a clear coat (roughness about 0.2 × wear map) for a polished finish with faint wipe marks. Desk, brass and glass reflect a **library light probe** built from the backdrop photograph (`libraryProbe`): the bookcases and window beyond the desk, a dimmer echo behind the viewer, a dark ceiling and walnut below. The book keeps the neutral `RoomEnvironment` as `scene.environment`, so the Book agent's materials are unchanged.
- **Textures** (`scripts/make-desk-textures.py`, deterministic, numpy and Pillow, all FFT-periodic so they tile):
  - `desk-color.webp`, 4096 × 2048, one tile = 10 × 5 units. Three glued flat-sawn boards. Rings come from a log model (the board plane passing a wandering, tilted log), giving cathedral figure. Fibre streaks, mineral streaks and grain-aligned pores are added and mapped through a walnut palette in linear light.
  - `desk-normal.webp` and `desk-rough.webp`, 1024², tile = 2.5 units: open pores and fibre ridges under the finish, about 410 texels per unit.
  - `desk-coat.webp`, 512²: clear-coat wear and wipe marks.
  - Maximum anisotropic filtering is applied at runtime.
- **Soft reflections of the book and lamp.** The desk renders a mirrored camera (the Reflector method, with an oblique near plane at the desk) at a quarter of the canvas resolution. It does this from the desk's `onBeforeRender`, for the main camera only, and blurs the result. The desk shader adds it weighted by Fresnel and the polish map, nudged by the pore normals. Lit, the shade appears as a soft green-gold smear in the walnut.
- **No hot spot.** The bulb is hidden inside the shade, so the desk takes no direct specular from the lamp's spot or point light (a shader patch scales those terms to 0). The window's specular is kept. The shade's glow reaches the desk through the planar reflection instead. Without this patch, the clear coat showed a meaningless bright dot in front of the book.
- **Contact shadows and ambient occlusion.** Each rendered frame draws the scene from just under the desk with a depth override, in an orthographic window (9.2 × 5.4 units, 0.42 units tall) covering the book and the lamp. Darkness is c² of the height above the desk, blurred twice. The result is laid on the desk as a multiply-like transparent plane. It follows the book through tilt, entrance and turns. The sun shadow map remains for cast shadows.
- **Backdrop.** The photograph is now a world-space plane far behind the desk. On every main-camera render, `fitBackdrop` re-aims it at the camera, then scales and offsets the image so the photograph's own desk line (row 0.585) sits just under the real desk's back edge. The photo is never smaller than the previously approved full-height fit. A 12-tap blur keeps it softly out of focus. Because it is real geometry, the loupe's view-offset camera magnifies the correct part of the room (the old screen-space background showed the whole photo shrunk).

### Lamp

`scripts/blender/build_lamp.py`, self-contained (it no longer imports `build_book.py`), produces `public/models/lamp.glb` and `assets/source/lamp.blend`.

- **Emeralite proportions, modelled in centimetres** (35.2 cm overall), then scaled to 1.82 scene units so the whole lamp fits beside the book under the header.
  - A weighted **stadium foot** (17.6 × 12.8 cm) on green felt: a plinth with softly broken arrises, a flat step, a small torus bead, a fillet, and an ogee dome rising into the collar.
  - A **turned stem** with a cushion, a mid knop, an upper ring and a pivot collar.
  - A **U-shaped flat-strap harp** sweeping from under the socket up to knurled thumb screws through the shade's end caps.
  - A **cased shade**, 23 cm long: a superellipse arch (rectangular-to-cylindrical) with a flared skirt, rolled ends and molded end caps, tilted 9° towards the reader.
  - Inside the shade, a socket and a tubular bulb.
- **Two real glass layers**: an outer emerald layer (`lamp_glass`) and an inner opal layer (`lamp_opal`), both closed shells, so the rim shows the white opal edge under the green.
- **Glass material.** A glossy `MeshPhysicalMaterial` (clear coat, IOR 1.52, reflecting the library probe). When lit, a shader term adds light scattered by the opal from the bulb's world position: brightest over the bulb, falling off towards the ends, and deeper at grazing angles where the light passes through more green. Physical transmission was rejected because it re-renders every opaque object once more per frame whenever the shade is on screen.
- **Brushed brass.** Metalness 1, roughness 0.28–0.42, anisotropy 0.55 along the turning direction (the lathe UVs run round each part), and a light lacquer clear coat on the polished parts.
- **Ball chain.** 18 beads, 4 mm across at a 5.2 mm pitch, joined by links (one mesh), ending in a turned teardrop pull. Three beads wait inside the socket, so a tug draws out more chain instead of opening a gap.

### Light and switching

- **Lamp on.**
  - A warm spot light sits at a virtual source in the shade's mouth, 0.1 below and 0.2 in front of the bulb, so the stem and foot are lit from the side, not blown out from directly above: angle 1.16 rad, penumbra 0.55, inverse-square decay, about 30° off vertical towards the left page. The pool is brightest by the foot and has a soft rim, with no hot centre and no hard ring.
  - A faint point light spills under the shade onto the foot.
  - The spot's shadows are soft (PCF, radius 6). The shade, bulb, socket, stem, harp, chain guide and chain do not cast into the lamp's own shadow map. Seen end-on from the bulb, they would throw a hard disc round the foot that a real long bulb never makes. They still cast the window's shadow.
- **The room dims to lamplight.**
  - The hemisphere light drops to 0.1, the sun to 0.12 and the bounce light to 0.03.
  - The backdrop drops to 0.13 and is warmed.
  - Environment reflections drop to about 15 %.
- **Smooth return.** The light warms over 650 ms (filament ease-out) and falls away over 480 ms.
- **No compile or shadow hitch.** The light count never changes: the lights stay in the scene at intensity 0, so switching never recompiles shaders. While off, the spot's shadow map is not re-rendered (`shadow.autoUpdate = false`), but it is created once. A missing map breaks every receiving material.
- **The pull** (`Room.chainPose`):
  - 150 ms draw-down of 0.11 units (smoothstep), with a slight lean.
  - The **click** at 150 ms switches the lamp.
  - A 70 ms hold.
  - Release: the spring takes the slack back with one small overshoot (14 s⁻¹ damping, 3.2 Hz), and the pull swings like a short pendulum (1.65 Hz, 0.55 s decay, with a small crosswise component).
  - Frames run for about 1.8 s, then the loop stops.
  - Reduced motion switches instantly with no movement.
- **API kept:** `lampHit`, `pullLamp` (L key and the footer button), `setLamp`, the `onLamp` callback, the `lampOn` initial state and `inspectLamp`. The pick box lives on layer 5: the raycaster sees it, and cameras, shadows and contact passes never draw it.

### Placement

`solvePlacement` places the lamp for any viewport:
- It reproduces BookScene's settled reading camera. **If BookScene's framing formula changes, update `readingCamera` in `room.ts`.**
- It searches (x, z, turn), coarse then fine, for the spot nearest the preferred back-left position (−3.65, −1.55, turn 0.9).
- Every sampled lamp vertex must be:
  - inside the canvas, at least 1 % from its left edge;
  - at least 2 % below the measured `.book-header` bottom;
  - left of the book's projected left edge;
  - with the foot on the desk, in front of its back edge and left of x = −2.8.
- It takes about 15 ms per resize.
- Where nothing fits (aspect ≤ 1.15, i.e. phones), the lamp model is hidden but stands just out of view at the preferred spot, so the footer Lamp button still dims the room to its warm light (`phone.jpg`, third panel).

## Reproduction

```sh
python3 scripts/make-desk-textures.py
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --python scripts/blender/build_lamp.py
node scripts/validate-assets.mjs          # inspectLamp + inspectDesk
```

## Measurements (headless Chrome, 18 November 2026)

| Check | Result |
|---|---|
| Lamp asset | 0.59 MiB, 14 primitives, 18,268 triangles, static (no clips); stands on y = 0, height 1.82 units |
| Desk textures | 1.65 MiB total (colour 0.66, normal 0.92 lossless, rough 0.14, coat 0.01) |
| Placement at 1440 × 900 (canvas 1440 × 814) | x −3.60, z −1.55, turn 0.9; shade top about 90 px below the header; left end inside the canvas |
| Idle | 0 room ticks in 2 s at rest, before and after a pull (on-demand loop stops) |
| Pull | about 109 frames (about 1.8 s) of animation, then idle; rAF gaps all ≤ 17 ms during three consecutive pulls (no stall at the click) |
| Reduced motion | the lamp is fully on within one frame; 3 ticks; no chain motion |
| Extra cost per rendered frame | contact plus reflection passes: 156 → 287 draw calls; median frame with `gl.finish` 0.5 → 2.1 ms (headless, this Mac) |
| Programs | no new shader programs compiled on switching |
| Phone 390 × 844 | lamp model hidden; desk edge, grain and backdrop present in both the closed and reading views; the Lamp button still lights the book from out of view |

These are headless-Chrome results on one Mac. They are not physical-device measurements.

## Evidence (`docs/qa/rebuild/room/`)

- `closed-off|on-<size>.jpg` and `reading-off|on-<size>.jpg` at 1280 × 720, 1440 × 900 and 1920 × 1080.
- `lamp-off|on-2x.jpg`, `foot-*-2x.jpg`, `shade-*-2x.jpg`: 2× close-ups of the base contact, the glass and the chain.
- `chain-poses-2x.jpg`: the chain at 0–900 ms of a pull.
- `pull-realtime.jpg`: real-time CDP screencast frames of a pull.
- `entrance-realtime.jpg`, `turn-forward-realtime.jpg`, `turn-backward-realtime.jpg`.
- `phone.jpg`, `loupe.jpg`.

## Limitations and open points

- The lamp is about 60 % of real scale relative to the book. A real-size lamp cannot stand beside the open book inside this fixed framing without crossing the header, so the proportions are real and the size is not.
- The glass glow is a shader term, not light transport. The opal interior is visible only from below the rim, so the lit glass reads correctly from the reading camera but has not been judged from extreme angles.
- The planar reflection is blurred uniformly, not by distance from the desk. Near contact it is softer than real polish would be.
- The contact and reflection passes add two scene passes to every rendered frame (only while the loop runs). On slow phones this may matter; profile on a device before release.
- The photograph still contains a brass lamp on the right-hand bookcase. It reads as another lamp in the room, but a stricter art direction might retouch it out.
- The book's own entrance pose holds it in the air before it descends. During that phase its sun shadow falls on the desk well away from it, which is BookScene's pose, not the room.
- Console: a `leafPosition` shader compile error comes from `src/book/leaf.ts` (`deformDepthMaterial`), not from the room. It appeared during these checks and belongs to the Interaction agent.
- Header CSS: `.lamp-on .book-header { filter: brightness(.52) saturate(.85) }` still suits the dark room and should stay. Adding `transition: filter .6s ease` would let it fade with the lamp's 650 ms warm-up instead of snapping.
