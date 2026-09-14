"""Render the approved header artwork on an editable, UV-mapped silhouette.

This is a textured 2D relief presentation, not a hand-sculpted reconstruction.
The generated RGB artwork contains an unwanted checkerboard outside the frame;
the mesh follows the warm ivory bottom edge, excluding it from the render.
Run: Blender --background --python scripts/blender/build_header.py
"""
import bpy
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'assets/source/header'
OUTPUT = ROOT / 'public/textures'


def build(name, scan_start, scan_end, width):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    image = bpy.data.images.load(str(SOURCE / f'{name}-artwork.png'))
    iw, ih = image.size
    pixels = list(image.pixels)
    # The outer ivory rim has warm chroma. The spurious checkerboard is neutral.
    # Scan only the outer boundary band, never the glass or plaque interiors.
    boundary = []
    for x in range(iw):
        last = scan_start
        for y in range(scan_start, scan_end):
            p = ((ih - 1 - y) * iw + x) * 4
            r, g, b = pixels[p:p + 3]
            if r - b > .065 and r > .25:
                last = y
        boundary.append(last - (4.5 if name == 'desktop' else 2.0))
    # Median smoothing suppresses isolated warm compression pixels at the edge.
    boundary = [sorted(boundary[max(0,x-6):min(iw,x+7)])[len(boundary[max(0,x-6):min(iw,x+7)])//2] for x in range(iw)]
    boundary = [sum(boundary[max(0,x-4):min(iw,x+5)])/len(boundary[max(0,x-4):min(iw,x+5)]) for x in range(iw)]
    height = math.ceil(max(boundary) + 2)
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 8
    scene.render.resolution_x = width
    scene.render.resolution_y = round(width * height / iw)
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.render.image_settings.color_depth = '8'
    scene.render.film_transparent = True
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'None'
    scene.view_settings.exposure = 0
    scene.view_settings.gamma = 1

    verts, faces, coords = [], [], []
    for x in range(iw):
        px = x / (iw - 1)
        y = boundary[x]
        verts.extend([(px * 10 - 5, height / iw * 5, 0),
                      (px * 10 - 5, height / iw * 5 - y / iw * 10, 0)])
        coords.extend([(px, 1), (px, 1-y/ih)])
        if x:
            a=2*x
            faces.append((a-2, a-1, a+1, a))
    mesh = bpy.data.meshes.new(f'{name}_silhouette_mesh')
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    uv = mesh.uv_layers.new(name='ApprovedArtworkUV')
    for face in mesh.polygons:
        for loop in face.loop_indices:
            uv.data[loop].uv = coords[mesh.loops[loop].vertex_index]
    obj = bpy.data.objects.new('Approved artwork silhouette — editable boundary', mesh)
    scene.collection.objects.link(obj)
    obj['authoring_method'] = 'Generated artwork mapped onto a traced silhouette; relief shading is baked in the artwork.'
    mat = bpy.data.materials.new('Approved ivory and glass artwork')
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    tex = nodes.new('ShaderNodeTexImage')
    tex.image = image
    tex.interpolation = 'Linear'
    emission = nodes.new('ShaderNodeEmission')
    output = nodes.new('ShaderNodeOutputMaterial')
    mat.node_tree.links.new(tex.outputs['Color'], emission.inputs['Color'])
    mat.node_tree.links.new(emission.outputs['Emission'], output.inputs['Surface'])
    obj.data.materials.append(mat)
    camera_data = bpy.data.cameras.new('Header orthographic export')
    camera = bpy.data.objects.new('Header orthographic export', camera_data)
    scene.collection.objects.link(camera)
    camera.location = (0, 0, 10)
    camera_data.type = 'ORTHO'
    camera_data.ortho_scale = 10
    scene.camera = camera
    image.pack()
    scene.render.filepath = str(SOURCE / f'header-{name}.png')
    bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE / f'header-{name}.blend'))
    bpy.ops.render.render(write_still=True)
    print(f'HEADER_EXPORT {name}: {width}x{scene.render.resolution_y}, source {iw}x{ih}, silhouette height {height}, boundary {min(boundary):.1f}–{max(boundary):.1f}')


build('desktop', 180, 242, 3344)
build('phone', 360, 495, 1560)
