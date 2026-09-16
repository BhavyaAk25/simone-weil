"""Render the illustrated edition from existing editable chapter sources.

Blender --background --python scripts/blender/render_posters.py -- --chapters 4
Omit --chapters to render all 12. Never saves source .blend files or exports GLBs.
"""
import argparse
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]


def linear_hex(value):
    channels = [int(value[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4 for c in channels)


def render(number):
    bpy.ops.wm.open_mainfile(filepath=str(ROOT / f'assets/source/chapter-{number:02}.blend'))
    scene = bpy.context.scene
    # Retain the precise saved book/hinge pose. Only the studio changes.
    for obj in list(scene.objects):
        if obj.name.startswith('Desk join'):
            bpy.data.objects.remove(obj, do_unlink=True)
    surface = bpy.data.objects.get('Render walnut desk')
    mat = bpy.data.materials.new('Illustrated edition - honed warm limestone')
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    shader = nodes.get('Principled BSDF')
    shader.inputs['Roughness'].default_value = .92
    texture = nodes.new('ShaderNodeTexNoise')
    texture.inputs['Scale'].default_value = 78
    texture.inputs['Detail'].default_value = 2
    coordinates = nodes.new('ShaderNodeTexCoord')
    links.new(coordinates.outputs['Object'], texture.inputs['Vector'])
    tones = nodes.new('ShaderNodeValToRGB')
    tones.color_ramp.elements[0].color = (*linear_hex('C5BBA9'), 1)
    tones.color_ramp.elements[1].color = (*linear_hex('D3CABA'), 1)
    links.new(texture.outputs['Fac'], tones.inputs[0])
    links.new(tones.outputs['Color'], shader.inputs['Base Color'])
    bump = nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = .13
    bump.inputs['Distance'].default_value = .004
    links.new(texture.outputs['Fac'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], shader.inputs['Normal'])
    surface.data.materials.clear()
    surface.data.materials.append(mat)
    world = scene.world.node_tree.nodes.get('Background')
    world.inputs[0].default_value = (.72, .70, .66, 1)
    world.inputs[1].default_value = .38
    for obj in scene.objects:
        if obj.type == 'LIGHT':
            obj.data.color = {'Window key': (1, .94, .84), 'Paper fill': (.89, .94, 1), 'Back rim': (1, .92, .77)}.get(obj.name, (1, 1, 1))
            obj.data.energy *= .82
    camera = scene.camera
    camera.data.ortho_scale = 6.1
    # Match a restrained editorial still: generous paper, true shadows, quiet ground.
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 48
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 1112
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'WEBP'
    scene.render.image_settings.quality = 92
    scene.render.filepath = str(ROOT / f'public/posters/chapter-{number:02}.webp')
    bpy.ops.render.render(write_still=True)
    print(f'ILLUSTRATED_POSTER chapter-{number:02}: 1600x1112, camera 6.10, unchanged source geometry', flush=True)


if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument('--chapters', nargs='+', type=int, choices=range(1, 13), default=list(range(1, 13)))
    for number in parser.parse_args(args).chapters:
        render(number)
