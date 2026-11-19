"""Deterministic, tileable paper stock for the book pages and paper pieces.

  python3 scripts/make-paper-texture.py

Writes (public/textures):
  paper-stock.webp       a near-white, slightly warm sheet that multiplies each
                         paper material's own colour: soft cloudy formation,
                         sparse fine fibres and very light tooth, not speckle
  paper-stock-edge.webp  the page-block edges: fine, uneven sheet lines in a
                         toned edge colour, with the olive endpaper sheets at
                         the board side (V = 0 is the top sheet, V = 1 the board)
  endpaper-color.webp    tileable printed endpaper: olive leaves in two inks
  binding-headband.webp  striped silk headband (U along the band)
Requires numpy and Pillow.
"""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'public/textures/paper-stock.webp'
N = 2048
rng = np.random.default_rng(1909)


def periodic_noise(cutoff, power=0.0):
    """Gaussian low-pass of white noise via FFT, so it tiles exactly."""
    white = rng.standard_normal((N, N))
    fy = np.fft.fftfreq(N)[:, None] * N
    fx = np.fft.fftfreq(N)[None, :] * N
    f = np.sqrt(fx * fx + fy * fy)
    spectrum = np.exp(-(f / cutoff) ** 2) * (np.maximum(f, 1) ** -power)
    field = np.real(np.fft.ifft2(np.fft.fft2(white) * spectrum))
    return (field - field.mean()) / field.std()


def fibres(count, length, alpha, margin=96):
    """Short curved fibres drawn with a margin, then wrapped so seams vanish."""
    size = N + 2 * margin
    layer = Image.new('L', (size, size), 0)
    draw = ImageDraw.Draw(layer)
    for _ in range(count):
        x, y = rng.uniform(margin, N + margin, 2)
        angle = rng.uniform(0, np.pi)
        span = rng.uniform(*length)
        bend = rng.uniform(-0.6, 0.6)
        points = []
        for step in np.linspace(-0.5, 0.5, 7):
            a = angle + bend * step
            points.append((x + np.cos(a) * span * step, y + np.sin(a) * span * step))
        draw.line(points, fill=int(rng.uniform(0.45, 1) * alpha), width=1)
    layer = layer.filter(ImageFilter.GaussianBlur(0.55))
    array = np.asarray(layer, dtype=np.float32) / 255
    core = array[margin:margin + N, margin:margin + N].copy()
    m = margin
    core[:m, :] += array[N + m:, m:N + m]
    core[-m:, :] += array[:m, m:N + m]
    core[:, :m] += array[m:N + m, N + m:]
    core[:, -m:] += array[m:N + m, :m]
    return core


cloud = 0.0055 * periodic_noise(7) + 0.0045 * periodic_noise(24) + 0.004 * periodic_noise(90)
tooth = 0.006 * periodic_noise(480)
light = fibres(7000, (12, 52), 170)
dark = fibres(1800, (8, 34), 150)
# Dark fibres stay faint: the sheet should read as smooth stock, never speckled.
luminance = 0.975 + cloud + tooth + 0.040 * light - 0.022 * dark

# A whisper of warmth that varies with formation, never a visible colour cast.
warm = 0.004 * periodic_noise(5)
rgb = np.stack([luminance + 0.006 + warm, luminance, luminance - 0.020 - warm], axis=-1)
rgb = np.clip(rgb, 0, 1)
Image.fromarray((rgb * 255 + 0.5).astype(np.uint8), 'RGB').save(OUT, 'WEBP', quality=88, method=6)
print(OUT.relative_to(ROOT), f'{OUT.stat().st_size / 1024:.0f} KiB', f'mean {rgb.mean(axis=(0, 1)).round(3)}')


# ---- Page-block edges --------------------------------------------------------
EW, EH = 2048, 512
def edge_texture():
    """Leaves seen edge-on: about 230 sheets, each with its own tone and a
    slight waviness along the edge, toned warmer toward the outer face."""
    sheets = 230
    v = (np.arange(EH) + 0.5) / EH
    u = (np.arange(EW) + 0.5) / EW
    out = np.zeros((EH, EW), np.float32)
    # Uneven sheet thickness: boundaries drift a little along the edge.
    widths = rng.uniform(0.6, 1.4, sheets)
    bounds = np.concatenate([[0], np.cumsum(widths)]) / widths.sum()
    wobble = [np.interp(u, np.linspace(0, 1, 9), rng.normal(0, 0.0009, 9)) for _ in range(sheets + 1)]
    tone = rng.normal(0, 1, sheets)
    vv = v[:, None]
    for i in range(sheets):
        top = bounds[i] + wobble[i][None, :]
        bot = bounds[i + 1] + wobble[i + 1][None, :]
        inside = np.clip((vv - top) * EH + 0.5, 0, 1) * np.clip((bot - vv) * EH + 0.5, 0, 1)
        # Each sheet is slightly darker at its boundary (the visible "line").
        mid = (top + bot) / 2
        half = np.maximum((bot - top) / 2, 1e-4)
        rim = np.clip(np.abs(vv - mid) / half, 0, 1) ** 3
        out += inside * (0.018 * tone[i] - 0.06 * rim)
    along = 0.010 * np.interp(u, np.linspace(0, 1, 40), rng.normal(0, 1, 40))[None, :]
    lum = 0.93 + out + along
    rgb = np.stack([lum * 0.985, lum * 0.945, lum * 0.865], axis=-1)   # toned ivory edge
    # Two coloured endpaper sheets lie against the board.
    end = np.clip((v - 0.975) * EH + 0.5, 0, 1)[:, None, None]
    olive = np.array([0.40, 0.42, 0.30])
    rgb = rgb * (1 - end) + olive * end * (0.95 + 0.05 * np.stack([lum] * 3, -1))
    return np.clip(rgb, 0, 1)


# ---- Endpaper ----------------------------------------------------------------
def endpaper_texture(n=1024):
    """Olive ground with a quiet repeat of olive sprigs in two inks."""
    from PIL import ImageDraw as D
    base = np.array([96, 102, 74]) / 255
    img = Image.new('RGB', (n, n), tuple(int(c * 255) for c in base))
    layer = Image.new('RGBA', (n * 3, n * 3), (0, 0, 0, 0))
    d = D.Draw(layer)
    ink1, ink2 = (196, 182, 138, 255), (140, 128, 86, 255)
    def sprig(cx, cy, ang, ink, s):
        import math
        for k in range(5):
            t = k / 4
            bx, by = cx + math.cos(ang) * s * t, cy + math.sin(ang) * s * t
            for side in (-1, 1):
                a = ang + side * 0.75
                pts = []
                for j in range(13):
                    q = j / 12
                    r = math.sin(math.pi * q) * s * 0.11
                    px = bx + math.cos(a) * s * 0.34 * q - math.sin(a) * r
                    py = by + math.sin(a) * s * 0.34 * q + math.cos(a) * r
                    pts.append((px, py))
                for j in range(12, -1, -1):
                    q = j / 12
                    r = math.sin(math.pi * q) * s * 0.11
                    pts.append((bx + math.cos(a) * s * 0.34 * q + math.sin(a) * r, by + math.sin(a) * s * 0.34 * q - math.cos(a) * r))
                if not (k == 4 and side == 1):
                    d.polygon(pts, fill=ink)
        d.line([(cx, cy), (cx + math.cos(ang) * s, cy + math.sin(ang) * s)], fill=ink, width=3)
    step = n // 4
    for gy in range(-1, 5):
        for gx in range(-1, 5):
            off = step / 2 if gy % 2 else 0
            cx, cy = n + gx * step + off, n + gy * step
            sprig(cx, cy, -0.9 + 0.25 * ((gx + gy) % 3), ink1, step * 0.42)
            sprig(cx + step * 0.5, cy + step * 0.45, 2.3, ink2, step * 0.30)
    tile = layer.crop((n, n, 2 * n, 2 * n))
    img.paste(tile, (0, 0), tile)
    arr = np.asarray(img, dtype=np.float32) / 255
    grain = 0.03 * periodic_noise(60)[:n, :n] if N >= n else 0
    return np.clip(arr * (1 + grain[..., None]), 0, 1)


def headband_texture():
    """Two silk threads twisted around a core: diagonal oxblood and ivory beads."""
    w, h = 256, 64
    y, x = np.mgrid[0:h, 0:w]
    phase = (x / 8.0 + y / 24.0) % 1.0
    ox, iv = np.array([96, 40, 32]) / 255, np.array([196, 178, 146]) / 255
    pick = (np.floor(x / 8.0 + y / 24.0) % 2)[..., None]
    shade = (0.62 + 0.38 * np.sin(phase * np.pi) ** 0.6)[..., None]
    return np.clip((ox * pick + iv * (1 - pick)) * shade, 0, 1)


TEX = ROOT / 'public/textures'
Image.fromarray((edge_texture() * 255 + 0.5).astype(np.uint8), 'RGB').save(TEX / 'paper-stock-edge.webp', 'WEBP', quality=90, method=6)
Image.fromarray((endpaper_texture() * 255 + 0.5).astype(np.uint8), 'RGB').save(TEX / 'endpaper-color.webp', 'WEBP', quality=88, method=6)
Image.fromarray((headband_texture() * 255 + 0.5).astype(np.uint8), 'RGB').save(TEX / 'binding-headband.webp', 'WEBP', quality=92, method=6)
for name in ['paper-stock-edge', 'endpaper-color', 'binding-headband']:
    print(name, f'{(TEX / (name + ".webp")).stat().st_size / 1024:.0f} KiB')
