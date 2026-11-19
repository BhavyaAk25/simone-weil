"""Brass banker's desk lamp (Emeralite archetype) for the room. Room agent, docs/ROOM-LAMP.md.

  /Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup \
      --python scripts/blender/build_lamp.py

Writes public/models/lamp.glb and assets/source/lamp.blend. Self-contained (does
not import build_book.py). Modelled in centimetres, Z up, then scaled so the lamp
stands LAMP_HEIGHT scene units tall; exported Y up. Every mesh is generated from
explicit profiles so the result is deterministic and has clean UVs (U runs around
turned parts, which the browser uses as the brushing direction).

Runtime contract (src/book/room.ts, scripts/validate-assets.mjs):
  nodes      LampRoot, LampBase, LampStem, LampHarp, LampShade (lamp_glass, outer cased
             layer), LampShadeInner (lamp_opal, inner layer), LampBulb (lamp_bulb),
             PullChain (the hanging chain; the browser animates it), PullHandle
             (invisible pick target, lamp_hit), LightAnchor (bulb centre),
             ChainAnchor (where the chain leaves the socket)
  materials  lamp_brass, lamp_brass_dark, lamp_glass, lamp_opal, lamp_bulb, lamp_felt,
             lamp_chain, lamp_hit
  origin     the centre of the felt pad's underside, so y = 0 is the desk surface.
No animation clips: the pull is simulated in the browser (a damped spring).
"""
import bpy, bmesh, math
from pathlib import Path
from mathutils import Vector, Matrix

ROOT = Path(__file__).resolve().parents[2]
MODELS, SOURCE = ROOT / 'public' / 'models', ROOT / 'assets' / 'source'
LAMP_HEIGHT = 1.82           # scene units, felt to the top of the shade
CM = 1.0                     # authored in cm; the root is scaled at the end

# ---------------------------------------------------------------- dimensions (cm)
FOOT_R, FOOT_L = 6.4, 2.6            # stadium foot: half-depth and straight half-length
STEM_TOP = 23.8
SHADE_LEN = 23.0
SHADE_RIM_Z = 27.4                   # bottom rim of the shade
SHADE_HALF_W = 6.2                   # half width at the rim
SHADE_H = 7.4                        # rim to crown
SHADE_TILT = math.radians(9)         # the opening leans towards the reader
PIVOT = Vector((0, 0, 30.2))         # harp ends meet the shade's end caps here
CHAIN_X, CHAIN_Y = 2.4, -1.2         # chain leaves the socket, front right
CHAIN_TOP = 28.2
BEAD_PITCH, BEAD_R = 0.52, 0.20
CHAIN_BEADS = 15


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.objects):
        for item in list(block):
            block.remove(item)


def material(name, rgb, roughness, metallic, alpha=1.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*[c ** 2.2 for c in rgb], 1)
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Metallic'].default_value = metallic
    if alpha < 1:
        bsdf.inputs['Alpha'].default_value = alpha
    return mat


def empty(name, location=(0, 0, 0), parent=None):
    obj = bpy.data.objects.new(name, None)
    obj.location = location
    bpy.context.collection.objects.link(obj)
    if parent:
        obj.parent = parent
    return obj


def build_mesh(name, verts, faces, uvs, mat, parent, sharp=None, location=(0, 0, 0)):
    """faces: vertex index tuples; uvs: per face, a tuple of (u, v) per corner."""
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    mesh.update()
    layer = mesh.uv_layers.new(name='UVMap')
    i = 0
    for poly, face_uv in zip(mesh.polygons, uvs):
        for corner, loop in enumerate(poly.loop_indices):
            layer.data[loop].uv = face_uv[corner]
    for poly in mesh.polygons:
        poly.use_smooth = True
    if sharp is not None and hasattr(mesh, 'set_sharp_from_angle'):
        mesh.set_sharp_from_angle(angle=math.radians(sharp))
    mesh.materials.append(bpy.data.materials[mat])
    obj = bpy.data.objects.new(name, mesh)
    obj.location = location
    bpy.context.collection.objects.link(obj)
    obj.parent = parent
    return obj


def grid(rings, closed=True, cap_bottom=None, cap_top=None):
    """Connect rings of equal length into quads. rings: list of lists of Vector.
    Returns verts, faces, uvs. U runs around the ring (0..1), V along the rings by arc length."""
    n, m = len(rings), len(rings[0])
    verts = [v for ring in rings for v in ring]
    lengths = [0.0]
    for a, b in zip(rings, rings[1:]):
        lengths.append(lengths[-1] + (a[0] - b[0]).length)
    total = lengths[-1] or 1
    faces, uvs = [], []
    cols = m if closed else m - 1
    for i in range(n - 1):
        for j in range(cols):
            k = (j + 1) % m
            faces.append((i * m + j, i * m + k, (i + 1) * m + k, (i + 1) * m + j))
            u0, u1 = j / m, (j + 1) / m
            v0, v1 = lengths[i] / total, lengths[i + 1] / total
            uvs.append(((u0, v0), (u1, v0), (u1, v1), (u0, v1)))
    for ring_index, cap, flip in ((0, cap_bottom, True), (n - 1, cap_top, False)):
        if cap is None:
            continue
        centre = len(verts)
        verts.append(cap)
        base = ring_index * m
        for j in range(m):
            k = (j + 1) % m
            face = (centre, base + j, base + k) if not flip else (centre, base + k, base + j)
            faces.append(face)
            uvs.append(((0.5, 0.5), (0.5 + 0.5 * math.cos(2 * math.pi * j / m), 0.5 + 0.5 * math.sin(2 * math.pi * j / m)),
                        (0.5 + 0.5 * math.cos(2 * math.pi * k / m), 0.5 + 0.5 * math.sin(2 * math.pi * k / m))))
    return verts, faces, uvs


def stadium(r, l, z, count=96):
    """Points round a stadium (racetrack) outline, evenly by arc length; l = 0 gives a circle."""
    perimeter = 4 * l + 2 * math.pi * r
    out = []
    for i in range(count):
        s = perimeter * i / count
        # Start mid front straight, go anticlockwise seen from above.
        s = (s + l) % perimeter
        if s < 2 * l:                                   # front straight, -y, x from -l to l
            out.append(Vector((-l + s, -r, z)))
        elif s < 2 * l + math.pi * r:                   # right semicircle
            a = -math.pi / 2 + (s - 2 * l) / r
            out.append(Vector((l + r * math.cos(a), r * math.sin(a), z)))
        elif s < 4 * l + math.pi * r:                   # back straight
            out.append(Vector((l - (s - 2 * l - math.pi * r), r, z)))
        else:                                           # left semicircle
            a = math.pi / 2 + (s - 4 * l - math.pi * r) / r
            out.append(Vector((-l + r * math.cos(a), r * math.sin(a), z)))
    return out


def loft(name, profile, mat, parent, count=96, cap_bottom=True, cap_top=True, sharp=None, centre=(0, 0)):
    """profile: (r, l, z) from bottom to top; r half-depth, l straight half-length."""
    rings = [[p + Vector((*centre, 0)) for p in stadium(r, l, z, count)] for r, l, z in profile]
    cb = Vector((*centre, profile[0][2])) if cap_bottom else None
    ct = Vector((*centre, profile[-1][2])) if cap_top else None
    return build_mesh(name, *grid(rings, True, cb, ct), mat, parent, sharp)


def lathe(name, profile, mat, parent, count=64, cap_bottom=True, cap_top=True, sharp=None, centre=(0, 0)):
    return loft(name, [(r, 0.0, z) for r, z in profile], mat, parent, count, cap_bottom, cap_top, sharp, centre)


def smooth_path(points, steps=10):
    """Catmull-Rom through the points."""
    pts = [Vector(p) for p in points]
    out = []
    for i in range(len(pts) - 1):
        p0, p1, p2, p3 = pts[max(i - 1, 0)], pts[i], pts[i + 1], pts[min(i + 2, len(pts) - 1)]
        for s in range(steps):
            t = s / steps
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(pts[-1])
    return out


def sweep(name, path, width, depth, mat, parent, count=20, up=Vector((0, 1, 0)), caps=True):
    """A rounded bar (superellipse section width x depth) along a path; `up` fixes the section's roll."""
    rings = []
    for i, p in enumerate(path):
        tangent = (path[min(i + 1, len(path) - 1)] - path[max(i - 1, 0)]).normalized()
        side = up.cross(tangent).normalized() if abs(up.dot(tangent)) < 0.99 else Vector((1, 0, 0))
        normal = tangent.cross(side).normalized()
        ring = []
        for j in range(count):
            a = 2 * math.pi * j / count
            c, s = math.cos(a), math.sin(a)
            # superellipse: flat faces, softly rounded corners
            x = math.copysign(abs(c) ** 0.6, c) * width / 2
            y = math.copysign(abs(s) ** 0.6, s) * depth / 2
            ring.append(p + side * x + normal * y)
        rings.append(ring)
    return build_mesh(name, *grid(rings, True, path[0] if caps else None, path[-1] if caps else None), mat, parent, 50)


def shade_section(inset=0.0, steps=56):
    """Cross-section of the shade in (y, z) from the front rim over the crown to the back rim.
    Near-vertical skirts with a slight outward flare, rounding into a flattened crown."""
    pts = []
    for i in range(steps + 1):
        t = i / steps                        # 0 front rim .. 1 back rim
        a = math.pi * t                      # 0..pi
        # superellipse arch: exponent < 2 makes it squarer (rectangular-to-cylindrical)
        c, s = math.cos(a), math.sin(a)
        y = -math.copysign(abs(c) ** 0.92, c) * (SHADE_HALF_W - 0.6)
        z = abs(s) ** 0.92 * SHADE_H
        # flare the lowest 15 % of the skirt outwards
        flare = max(0.0, 1 - z / (0.26 * SHADE_H)) ** 2 * 0.75
        y += math.copysign(flare, y) if abs(y) > 1e-6 else 0
        pts.append(Vector((0, y, z)))
    # offset inward along the 2D normal
    out = []
    for i, p in enumerate(pts):
        a, b = pts[max(i - 1, 0)], pts[min(i + 1, len(pts) - 1)]
        tangent = (b - a).normalized()
        normal = Vector((0, -tangent.z, tangent.y))   # outward: front skirt -y, crown +z
        q = p - normal * inset
        out.append(q)
    return out


def shade_layer(name, inset, thickness, mat, parent, cap_inset):
    """One cased layer: an extruded arch with rounded ends and molded end caps, as a closed shell."""
    outer = shade_section(inset)
    inner = shade_section(inset + thickness)
    half = SHADE_LEN / 2 - cap_inset
    # x stations with a soft roll at both ends
    stations = [(-half, 0.93), (-half + 0.12, 0.975), (-half + 0.4, 0.995), (-half + 0.9, 1.0)]
    # The span between the rolled ends is straight: no interior stations are needed.
    stations += [(half - 0.9, 1.0), (half - 0.4, 0.995), (half - 0.12, 0.975), (half, 0.93)]
    centre = Vector((0, 0, SHADE_H * 0.35))

    def ring(section, x, scale):
        return [Vector((x, *(centre.yz + (p.yz - centre.yz) * scale))) for p in section]

    verts, faces, uvs = [], [], []

    def add_strip(rows, flip=False):
        base = len(verts)
        m = len(rows[0])
        for row in rows:
            verts.extend(row)
        for i in range(len(rows) - 1):
            for j in range(m - 1):
                a, b, c, d = base + i * m + j, base + i * m + j + 1, base + (i + 1) * m + j + 1, base + (i + 1) * m + j
                faces.append((a, d, c, b) if flip else (a, b, c, d))
                uv = ((i / (len(rows) - 1), j / (m - 1)), (i / (len(rows) - 1), (j + 1) / (m - 1)),
                      ((i + 1) / (len(rows) - 1), (j + 1) / (m - 1)), ((i + 1) / (len(rows) - 1), j / (m - 1)))
                uvs.append(tuple(reversed((uv[0], uv[1], uv[2], uv[3]))) if flip else uv)

    outer_rows = [ring(outer, x, s) for x, s in stations]
    inner_rows = [ring(inner, x * (half - thickness) / half, s) for x, s in stations]
    add_strip(outer_rows, flip=True)
    add_strip(inner_rows, flip=False)
    # rim strips along the bottom edges (front and back) and the end caps
    for idx in (0, -1):
        rows = [[outer_rows[k][idx] for k in range(len(stations))], [inner_rows[k][idx] for k in range(len(stations))]]
        add_strip(rows, flip=(idx == 0))
    for k, flip in ((0, False), (len(stations) - 1, True)):
        # molded end cap: a fan from the cap centre to the end ring, outer and inner faces
        for rows, f in ((outer_rows, flip), (inner_rows, not flip)):
            ring_pts = rows[k]
            base = len(verts)
            verts.append(Vector((ring_pts[0].x, 0, SHADE_H * 0.32)))
            verts.extend(ring_pts)
            for j in range(len(ring_pts) - 1):
                face = (base, base + 1 + j, base + 2 + j)
                faces.append(tuple(reversed(face)) if f else face)
                uvs.append(((0.5, 0.0), (j / len(ring_pts), 1.0), ((j + 1) / len(ring_pts), 1.0)))
            # close the cap's bottom edge between the two rim points
            faces.append((base, base + len(ring_pts), base + 1) if not f else (base, base + 1, base + len(ring_pts)))
            uvs.append(((0.5, 0.0), (1.0, 1.0), (0.0, 1.0)))
        # cap rim between outer and inner end rings
        add_strip([outer_rows[k], inner_rows[k]], flip=not flip)
    obj = build_mesh(name, verts, faces, uvs, mat, parent, 38)
    bm = bmesh.new(); bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data); bm.free()
    for poly in obj.data.polygons:
        poly.use_smooth = True
    if hasattr(obj.data, 'set_sharp_from_angle'):
        obj.data.set_sharp_from_angle(angle=math.radians(38))
    return obj


def bead(name, location, r, mat, parent, seg=12):
    profile = [(max(1e-4, r * math.sin(math.pi * i / seg)), -r * math.cos(math.pi * i / seg)) for i in range(seg + 1)]
    obj = lathe(name, profile[1:-1], mat, parent, count=seg, cap_bottom=True, cap_top=True)
    obj.location = location
    return obj


def build():
    reset()
    material('lamp_brass', (0.80, 0.62, 0.34), 0.28, 1.0)
    material('lamp_brass_dark', (0.55, 0.40, 0.21), 0.42, 1.0)
    material('lamp_chain', (0.78, 0.62, 0.36), 0.32, 1.0)
    material('lamp_glass', (0.05, 0.30, 0.18), 0.06, 0.0)
    material('lamp_opal', (0.95, 0.92, 0.85), 0.35, 0.0)
    material('lamp_bulb', (1.0, 0.95, 0.84), 0.3, 0.0)
    material('lamp_felt', (0.12, 0.20, 0.14), 0.95, 0.0)
    material('lamp_hit', (0, 0, 0), 1.0, 0.0)

    root = empty('LampRoot')
    base = empty('LampBase', parent=root)
    # Felt pad, then a weighted stadium foot: plinth step, cove, and an ogee dome into the stem collar.
    loft('Lamp felt', [(FOOT_R - 0.15, FOOT_L, 0.0), (FOOT_R - 0.05, FOOT_L, 0.05), (FOOT_R - 0.05, FOOT_L, 0.28)], 'lamp_felt', base, sharp=60)
    R, L = FOOT_R, FOOT_L
    foot = [
        (R - 0.30, L, 0.28), (R - 0.06, L, 0.34), (R, L, 0.55), (R, L, 1.15),          # plinth edge, softly broken
        (R - 0.08, L, 1.32), (R - 0.32, L, 1.40), (R - 0.55, L, 1.42),                 # rounded top arris, flat step
        (R - 0.75, L * 0.96, 1.48), (R - 0.88, L * 0.94, 1.66), (R - 0.86, L * 0.92, 1.86),  # small torus (bead) on the step
        (R - 1.02, L * 0.9, 1.98), (R - 1.30, L * 0.86, 2.02),                          # fillet
        (R - 1.70, L * 0.78, 2.18), (R - 2.30, L * 0.64, 2.52), (R - 3.00, L * 0.46, 2.86),  # ogee dome
        (R - 3.70, L * 0.26, 3.12), (R - 4.30, L * 0.10, 3.28), (1.55, 0.0, 3.36), (1.40, 0.0, 3.40),
    ]
    loft('Lamp foot', foot, 'lamp_brass', base, cap_bottom=True, cap_top=True, sharp=70)
    # Turned stem: collar, cushion, knops, slender shaft and the pivot collar at the top.
    stem = empty('LampStem', parent=root)
    turned = [
        (1.40, 3.40), (1.50, 3.55), (1.50, 3.85), (1.30, 4.00), (1.05, 4.10),          # collar
        (1.15, 4.35), (1.18, 4.65), (0.95, 4.95), (0.70, 5.20),                        # cushion
        (0.62, 5.60), (0.58, 6.50), (0.56, 10.0),                                      # shaft
        (0.66, 10.2), (0.95, 10.55), (1.02, 10.95), (0.95, 11.35), (0.66, 11.70), (0.56, 11.9),  # mid knop
        (0.52, 14.0), (0.50, 19.6),
        (0.64, 19.8), (0.88, 20.1), (0.90, 20.6), (0.66, 20.9), (0.52, 21.1),          # upper ring
        (0.50, 22.7), (0.78, 22.9), (0.86, 23.3), (0.80, 23.7), (0.55, 23.85),         # pivot collar
    ]
    lathe('Lamp stem turned', turned, 'lamp_brass', stem, count=48, sharp=70)
    # Harp: a flat brass strap arching out from the pivot to both end caps of the shade.
    harp = empty('LampHarp', parent=root)
    half = SHADE_LEN / 2
    # A U-shaped harp: low under the socket, sweeping up to the end caps.
    path = smooth_path([(-half - 0.35, 0, PIVOT.z), (-half - 0.1, 0, PIVOT.z - 2.2), (-half + 1.6, 0, 25.6),
                        (-6.0, 0, 24.15), (0, 0, 23.75), (6.0, 0, 24.15), (half - 1.6, 0, 25.6),
                        (half + 0.1, 0, PIVOT.z - 2.2), (half + 0.35, 0, PIVOT.z)], 10)
    sweep('Lamp harp strap', path, 0.95, 0.34, 'lamp_brass', harp, count=14, up=Vector((0, 1, 0)))
    for x in (-half - 0.35, half + 0.35):
        # Knurled thumb screws through the end caps.
        lathe('Lamp harp screw', [(0.05, -0.3), (0.62, -0.28), (0.66, 0.0), (0.62, 0.28), (0.30, 0.32), (0.05, 0.34)],
              'lamp_brass_dark', harp, count=24, centre=(0, 0)).matrix_world = Matrix.Translation((x + math.copysign(0.25, x), 0, PIVOT.z)) @ Matrix.Rotation(math.copysign(math.pi / 2, x), 4, 'Y')
    # Socket and bulb under the crown.
    lathe('Lamp socket', [(0.42, 23.9), (0.42, 26.4), (0.62, 26.5), (0.95, 26.8), (0.98, 28.9), (0.80, 29.05), (0.55, 29.1)], 'lamp_brass_dark', harp, count=32, sharp=50)
    bulb = lathe('LampBulb', [(0.55, 29.1), (0.75, 29.4), (1.05, 30.2), (1.10, 31.0), (0.90, 31.7), (0.45, 32.1), (0.05, 32.2)],
                 'lamp_bulb', harp, count=32)

    # The shade pivots on the thumb screws, tilted towards the reader.
    shade_pivot = empty('ShadePivot', PIVOT, root)
    shade_pivot.rotation_euler = (SHADE_TILT, 0, 0)
    for name, inset, thickness, mat, cap in (('LampShade', 0.0, 0.16, 'lamp_glass', 0.0),
                                             ('LampShadeInner', 0.16, 0.12, 'lamp_opal', 0.16)):
        obj = shade_layer(name, inset, thickness, mat, shade_pivot, cap)
        obj.location = (0, 0, SHADE_RIM_Z - PIVOT.z)

    empty('LightAnchor', (0, 0, 30.6), root)
    # Ball chain from the socket, with a turned brass pull. Beads above the anchor wait
    # inside the socket, so a tug draws out more chain instead of opening a gap.
    anchor = empty('ChainAnchor', (CHAIN_X, CHAIN_Y, CHAIN_TOP), root)
    lathe('Lamp chain guide', [(0.05, 0.1), (0.42, 0.08), (0.42, -0.30), (0.30, -0.42), (0.05, -0.44)], 'lamp_brass_dark', root,
          count=20, centre=(CHAIN_X, CHAIN_Y)).location = (0, 0, CHAIN_TOP)
    chain = empty('PullChain', (0, 0, 0), anchor)
    for i in range(-3, CHAIN_BEADS):
        bead('Chain bead', (0, 0, -0.45 - i * BEAD_PITCH), BEAD_R, 'lamp_chain', chain, 8)
        if i < CHAIN_BEADS - 1:
            lathe('Chain link', [(0.06, -0.45 - i * BEAD_PITCH - BEAD_R * 0.6), (0.06, -0.45 - (i + 1) * BEAD_PITCH + BEAD_R * 0.6)],
                  'lamp_chain', chain, count=6, cap_bottom=False, cap_top=False)
    end = -0.45 - (CHAIN_BEADS - 1) * BEAD_PITCH - BEAD_R
    # Pull: a small connector, a waisted neck and a teardrop weight.
    pull = [(0.05, end - 0.05), (0.16, end - 0.10), (0.16, end - 0.35), (0.30, end - 0.50), (0.40, end - 0.62),
            (0.30, end - 0.78), (0.24, end - 0.95), (0.42, end - 1.25), (0.56, end - 1.60), (0.58, end - 1.90),
            (0.50, end - 2.20), (0.32, end - 2.42), (0.10, end - 2.52), (0.02, end - 2.55)]
    lathe('Chain pull', pull, 'lamp_brass', chain, count=32, sharp=70)
    # One mesh for the beads and links (one draw call).
    parts = [o for o in chain.children if o.name.startswith('Chain bead') or o.name.startswith('Chain link')]
    bpy.ops.object.select_all(action='DESELECT')
    for o in parts:
        o.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    parts[0].name = 'Chain beads'
    # Generous invisible pick target around chain and pull.
    span = -end + 2.6
    hverts = [Vector((x, y, z)) for z in (0.3, -span) for y in (-1.6, 1.6) for x in (-1.6, 1.6)]
    hfaces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    hit = build_mesh('PullHandle', hverts, hfaces, [((0, 0), (1, 0), (1, 1), (0, 1))] * 6, 'lamp_hit', anchor)
    hit['pick_target'] = True

    # Scale the whole lamp from centimetres to scene units.
    bpy.context.view_layer.update()
    top = SHADE_RIM_Z + SHADE_H + 0.4
    scale = LAMP_HEIGHT / top
    root.scale = (scale, scale, scale)
    root['height_cm'] = top
    root['scale'] = scale
    bpy.context.view_layer.update()

    MODELS.mkdir(parents=True, exist_ok=True)
    SOURCE.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE / 'lamp.blend'))
    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.context.scene.objects:
        obj.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(MODELS / 'lamp.glb'), export_format='GLB', use_selection=True,
                              export_animations=False, export_materials='EXPORT', export_extras=True, export_yup=True,
                              export_apply=True)
    tris = sum(len(o.data.polygons) for o in bpy.context.scene.objects if o.type == 'MESH')
    print(f'lamp: scale {scale:.5f} scene units per cm, {tris} faces')


build()
