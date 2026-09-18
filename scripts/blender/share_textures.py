"""Share byte-identical GLB images without changing mesh or animation data.

Run after Blender export and before updating the manifest. Safe to repeat, including
when only a subset of the models has been freshly exported.
"""
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import struct

ROOT = Path(__file__).resolve().parents[2]
MIME_EXT = {'image/png': 'png', 'image/jpeg': 'jpg', 'image/webp': 'webp'}
URI = re.compile(r'^\.\./textures/shared/([a-f0-9]{64})\.(png|jpg|webp)$')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_glb(path):
    data = path.read_bytes()
    assert len(data) >= 28 and struct.unpack_from('<III', data) == (0x46546C67, 2, len(data)), 'Invalid GLB header'
    offset, chunks = 12, {}
    while offset < len(data):
        length, kind = struct.unpack_from('<II', data, offset)
        assert length % 4 == 0 and offset + 8 + length <= len(data) and kind not in chunks
        chunks[kind] = data[offset + 8:offset + 8 + length]
        offset += 8 + length
    assert set(chunks) == {0x4E4F534A, 0x004E4942}, 'Unsupported GLB chunks'
    scene = json.loads(chunks[0x4E4F534A])
    binary = chunks[0x004E4942]
    assert len(scene['buffers']) == 1 and 'uri' not in scene['buffers'][0]
    assert scene['buffers'][0]['byteLength'] <= len(binary)
    for view in scene.get('bufferViews', []):
        assert view['buffer'] == 0 and view.get('byteOffset', 0) >= 0
        assert view.get('byteOffset', 0) + view['byteLength'] <= scene['buffers'][0]['byteLength']
    return scene, binary, len(data)


def view_bytes(scene, binary, index):
    view = scene['bufferViews'][index]
    start = view.get('byteOffset', 0)
    return binary[start:start + view['byteLength']]


def image_bytes(image, scene, binary, path):
    assert image.get('mimeType') in MIME_EXT
    if 'bufferView' in image:
        assert 'uri' not in image
        return view_bytes(scene, binary, image['bufferView'])
    match = URI.fullmatch(image.get('uri', ''))
    assert match and match[2] == MIME_EXT[image['mimeType']], 'Unexpected external image URI'
    target = (path.parent / image['uri']).resolve()
    assert target.parent == (path.parent.parent / 'textures/shared').resolve()
    raw = target.read_bytes()
    assert digest(raw) == match[1], 'Shared image hash mismatch'
    return raw


def references(value):
    if isinstance(value, dict):
        for key, child in value.items():
            if key == 'bufferView':
                yield child
            else:
                yield from references(child)
    elif isinstance(value, list):
        for child in value:
            yield from references(child)


def payload_fingerprint(scene, binary):
    """Hash all non-image JSON semantics and each referenced byte range.

    Resolve bufferView indices before hashing so repacking offsets cannot hide a
    changed attribute, animation sample, sparse accessor, or extension payload.
    """
    def normalize(value):
        if isinstance(value, list):
            return [normalize(child) for child in value]
        if isinstance(value, dict):
            return {key: ({'view': {k: v for k, v in scene['bufferViews'][child].items() if k not in ('buffer', 'byteOffset')},
                           'sha256': digest(view_bytes(scene, binary, child))} if key == 'bufferView' else normalize(child))
                    for key, child in value.items()}
        return value
    semantic = {key: value for key, value in scene.items() if key not in ('buffers', 'bufferViews', 'images')}
    return digest(json.dumps(normalize(semantic), sort_keys=True, separators=(',', ':')).encode())


def pack_glb(scene, binary):
    encoded = json.dumps(scene, separators=(',', ':'), ensure_ascii=False).encode()
    encoded += b' ' * (-len(encoded) % 4)
    binary += b'\0' * (-len(binary) % 4)
    return (struct.pack('<III', 0x46546C67, 2, 28 + len(encoded) + len(binary))
            + struct.pack('<II', len(encoded), 0x4E4F534A) + encoded
            + struct.pack('<II', len(binary), 0x004E4942) + binary)


def optimize(root=ROOT):
    records = []
    counts = Counter()
    for path in sorted((root / 'public/models').glob('*.glb')):
        scene, binary, size = read_glb(path)
        images = [image_bytes(image, scene, binary, path) for image in scene.get('images', [])]
        counts.update(set(digest(raw) for raw in images))
        records.append((path, scene, binary, size, images))
    shared = root / 'public/textures/shared'
    reports = []
    for path, scene, binary, size, images in records:
        before = payload_fingerprint(scene, binary)
        edited = deepcopy(scene)
        removed = set()
        for image, raw in zip(edited.get('images', []), images):
            sha = digest(raw)
            if counts[sha] < 2 or 'bufferView' not in image:
                continue
            shared.mkdir(parents=True, exist_ok=True)
            filename = sha + '.' + MIME_EXT[image['mimeType']]
            target = shared / filename
            if target.exists():
                assert target.read_bytes() == raw, 'Shared image collision'
            else:
                target.write_bytes(raw)
            removed.add(image.pop('bufferView'))
            image['uri'] = '../textures/shared/' + filename
        if removed:
            # A view could also be referenced by an accessor or extension. Keep it
            # in that case, even though its image now uses the shared resource.
            removed -= set(references(edited))
            remap, views, packed = {}, [], bytearray()
            for index, view in enumerate(scene.get('bufferViews', [])):
                if index in removed:
                    continue
                packed.extend(b'\0' * (-len(packed) % 4))
                remap[index] = len(views)
                views.append({**view, 'byteOffset': len(packed)})
                packed.extend(view_bytes(scene, binary, index))
            def rewrite(value):
                if isinstance(value, dict):
                    for key, child in value.items():
                        if key == 'bufferView':
                            value[key] = remap[child]
                        else:
                            rewrite(child)
                elif isinstance(value, list):
                    for child in value:
                        rewrite(child)
            rewrite(edited)
            edited['bufferViews'] = views
            edited['buffers'][0]['byteLength'] = len(packed)
            assert payload_fingerprint(edited, bytes(packed)) == before, 'Non-image payload changed'
            assert [image_bytes(image, edited, bytes(packed), path) for image in edited.get('images', [])] == images
            path.write_bytes(pack_glb(edited, bytes(packed)))
        after_scene, after_binary, after_size = read_glb(path)
        after = payload_fingerprint(after_scene, after_binary)
        assert before == after
        reports.append({'file': path.name, 'beforeBytes': size, 'afterBytes': after_size,
                        'payloadBeforeSha256': before, 'payloadAfterSha256': after})
    return {'files': reports, 'glbBytesSaved': sum(r['beforeBytes'] - r['afterBytes'] for r in reports),
            'sharedBytes': sum(p.stat().st_size for p in shared.glob('*')) if shared.exists() else 0}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    print(json.dumps(optimize(args.root), indent=2))
