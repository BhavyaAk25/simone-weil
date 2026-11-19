"""Procedural walnut desktop textures for the room (Room agent, docs/ROOM-LAMP.md).

  python3 scripts/make-desk-textures.py

Deterministic (fixed seeds); needs only numpy and Pillow. Every field is built
from FFT-filtered noise, so all maps tile seamlessly. Writes:

  public/textures/desk-color.webp   4096 x 2048 sRGB albedo, one tile = 10 x 5 scene units
                                    (three glued flat-sawn boards, grain along X)
  public/textures/desk-normal.webp  1024 x 1024 tangent-space detail normal, tile = 2.5 x 2.5 units
                                    (open pores and fibre ridges under the finish)
  public/textures/desk-rough.webp   1024 x 1024 detail roughness in G (pores rougher), same tile
  public/textures/desk-coat.webp    512 x 512 clearcoat roughness in G: faint wipe marks
                                    and wear in the polish, tile = 10 x 10 units
"""
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'public' / 'textures'


def noise(h, w, fx, fy, seed, power=2.0):
    """Periodic Gaussian-filtered noise; fx, fy are the cut-off in cycles per tile."""
    rng = np.random.default_rng(seed)
    white = rng.standard_normal((h, w))
    ky = np.fft.fftfreq(h)[:, None] * h
    kx = np.fft.fftfreq(w)[None, :] * w
    filt = np.exp(-((np.abs(kx) / fx) ** power + (np.abs(ky) / fy) ** power))
    field = np.real(np.fft.ifft2(np.fft.fft2(white) * filt))
    return (field - field.mean()) / (field.std() + 1e-9)


def stamp(h, w, count, weight, sx, sy, seed):
    """Short grain-aligned dashes (pores): weighted random impulses blurred by an elongated kernel."""
    rng = np.random.default_rng(seed)
    p = weight.ravel() / weight.sum()
    idx = rng.choice(h * w, size=count, p=p)
    field = np.zeros(h * w)
    np.add.at(field, idx, rng.uniform(0.5, 1.0, count))
    field = field.reshape(h, w)
    ky = np.fft.fftfreq(h)[:, None]
    kx = np.fft.fftfreq(w)[None, :]
    kernel = np.exp(-2 * np.pi ** 2 * ((kx * sx) ** 2 + (ky * sy) ** 2))
    out = np.real(np.fft.ifft2(np.fft.fft2(field) * kernel))
    return np.clip(out / (np.percentile(out, 99.7) + 1e-9), 0, 1)


def srgb_to_linear(c):
    c = c / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055) * 255


def albedo():
    W, H = 4096, 2048
    TX, TZ = 10.0, 5.0                     # scene units per tile
    u = (np.arange(W) / W * TX)[None, :]
    rows = np.arange(H)
    boards = [(0.0, 1.80, 11, 1.25, 0.55, 0.068, (1.035, 1.0, 0.955), 0.00),
              (1.80, 3.35, 23, 1.45, 0.45, 0.074, (0.985, 0.99, 1.02), 0.05),
              (3.35, 5.00, 37, 1.10, 0.62, 0.064, (1.01, 0.995, 0.985), -0.03)]
    warp = noise(H, W, 1.6, 9, 101) * 0.9 + noise(H, W, 5, 45, 102) * 0.22
    fibre = noise(H, W, 14, 520, 103) * 0.6 + noise(H, W, 40, 1300, 104) * 0.4
    streak = noise(H, W, 2, 26, 105)
    mottle = noise(H, W, 12, 12, 106)
    t = np.zeros((H, W)); tint = np.ones((H, W, 3)); early = np.zeros((H, W))
    for z0, z1, seed, d, amp, spacing, hue, offset in boards:
        r0, r1 = int(z0 / TZ * H), int(z1 / TZ * H)
        rng = np.random.default_rng(seed)
        centre = (z0 + z1) / 2 + rng.uniform(-0.25, 0.25)
        v = (rows[r0:r1, None] / H * TZ) - centre
        phase1, phase2 = rng.uniform(0, 2 * np.pi, 2)
        # The board plane passes a tilted, wandering log: rings rise into cathedral arches.
        dist = d + amp * np.sin(2 * np.pi * u / TX + phase1) + 0.18 * np.sin(4 * np.pi * u / TX + phase2)
        radius = np.sqrt((v * 1.0) ** 2 + dist ** 2)
        phi = radius / spacing + warp[r0:r1]
        p = phi - np.floor(phi)
        # Earlywood: a sharp-edged porous band that fades into latewood.
        e = np.exp(-p / 0.22) + 0.45 * np.exp(-(1 - p) / 0.06)
        early[r0:r1] = e
        t[r0:r1] = 0.46 + offset + 0.12 * (e - 0.45)
        tint[r0:r1] = hue
    pores = stamp(H, W, int(H * W * 0.010), 0.25 + early, 5.0, 0.55, 107)
    t += 0.075 * fibre + 0.09 * streak + 0.025 * mottle + 0.30 * pores
    # A barely visible glue line between boards.
    for z in (1.80, 3.35):
        r = int(z / TZ * H)
        t[r - 1:r + 1] += 0.06
    t = np.clip(t, 0, 1)
    # Walnut palette, light sapwood-tan to dark chocolate; interpolated in linear light.
    stops = np.array([0.0, 0.32, 0.55, 0.78, 1.0])
    colours = srgb_to_linear(np.array([[152, 98, 60], [114, 70, 43], [82, 49, 31], [53, 31, 21], [27, 15, 11]], float))
    lin = np.stack([np.interp(t, stops, colours[:, c]) for c in range(3)], axis=-1) * tint
    img = linear_to_srgb(lin).astype(np.uint8)
    Image.fromarray(img, 'RGB').save(OUT / 'desk-color.webp', quality=86, method=6)
    return img


def detail():
    N = 1024
    fibre = noise(N, N, 6, 260, 201) * 0.7 + noise(N, N, 16, 480, 202) * 0.3
    pore_weight = 0.6 + 0.4 * (noise(N, N, 4, 40, 203) > 0)
    pores = stamp(N, N, int(N * N * 0.012), pore_weight, 4.5, 0.6, 204)
    height = 0.35 * fibre / 3 - 1.0 * pores
    # Slopes in texels; the strength sets how far pores break the sheen.
    strength = 2.2
    gx = (np.roll(height, -1, 1) - np.roll(height, 1, 1)) * 0.5 * strength
    gy = (np.roll(height, -1, 0) - np.roll(height, 1, 0)) * 0.5 * strength
    n = np.stack([-gx, gy, np.ones_like(gx)], axis=-1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    normal = ((n * 0.5 + 0.5) * 255).round().astype(np.uint8)
    Image.fromarray(normal, 'RGB').save(OUT / 'desk-normal.webp', lossless=True, method=6)
    rough = np.clip(0.62 + 0.30 * pores + 0.04 * fibre, 0, 1)
    g = (rough * 255).astype(np.uint8)
    Image.fromarray(np.stack([g, g, g], -1), 'RGB').save(OUT / 'desk-rough.webp', quality=90, method=6)


def coat():
    N = 512
    wipe = noise(N, N, 3, 9, 301)                 # long soft wipe marks along the grain
    smudge = noise(N, N, 14, 14, 302)
    wear = np.clip(noise(N, N, 2, 2, 303), 0, None)
    g = np.clip(0.62 + 0.14 * wipe + 0.06 * smudge + 0.12 * wear, 0.3, 1.0)
    g8 = (g * 255).astype(np.uint8)
    Image.fromarray(np.stack([g8, g8, g8], -1), 'RGB').save(OUT / 'desk-coat.webp', quality=90, method=6)


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    img = albedo()
    detail()
    coat()
    print('mean sRGB', img.reshape(-1, 3).mean(0).round(1))
    for name in ('desk-color', 'desk-normal', 'desk-rough', 'desk-coat'):
        path = OUT / f'{name}.webp'
        print(name, Image.open(path).size, path.stat().st_size)
