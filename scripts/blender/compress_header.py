"""Encode Blender's RGBA header renders as deployable WebP without changing art."""
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
for source, target in [('desktop', 'desktop'), ('phone', 'mobile')]:
    image = Image.open(ROOT / f'assets/source/header/header-{source}.png')
    output = ROOT / f'public/textures/header-{target}.webp'
    image.save(output, format='WEBP', quality=94, method=6)
    print(output.name, image.size, output.stat().st_size, 'bytes')
