"""Binding atlas, leather grain and foil glitter for the book. Deterministic.

  python3 scripts/make-cover-textures.py

The binding (back board, rounded spine, front board, edges and turn-ins) is one
continuous skinned mesh in book.glb (scripts/blender/build_book.py, book()).
Its UV atlas is laid out here and in build_book.py from the same constants:

  U  0.00-0.01  back fore-edge round      V  0.000-0.012  head round (outer)
     0.01-0.43  back board (fore -> spine)    0.012-0.848  outer face, head -> tail
     0.43-0.57  spine (back -> front)         0.848-0.860  tail round (outer)
     0.57-0.99  front board (spine -> fore)   0.875-0.990  inner faces and turn-ins
     0.99-1.00  front fore-edge round

Writes (public/textures):
  cover-color.webp   3072 x 2160 sRGB albedo: tobacco leather, edge wear,
                     her 1942 photograph printed as a two-ink line screen,
                     brass-foil title, badge and spine lettering
  cover-orm.webp     R wear, G roughness, B foil (metalness)
  cover-normal.webp  foil deboss and bevel, ink and leather undulation (OpenGL)
  leather-normal.webp, leather-rough.webp   1024 tileable full-grain detail,
                     sampled at runtime in physical units (TEXCOORD_1)
  binding-glitter.webp  256 tileable foil flake normals

Requires numpy and Pillow (FreeType reads the site's WOFF fonts).
"""
from pathlib import Path
from collections import deque
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'public/textures'
FONTS = ROOT / 'node_modules/@fontsource/cormorant-garamond/files'
PORTRAIT = ROOT / 'assets/source/textures/simone-weil-portrait.png'
ENGRAVING = ROOT / 'assets/source/textures/simone-weil-spine.jpg'
rng = np.random.default_rng(1943)

# ---- Shared layout (keep in step with build_book.py) -----------------------
W, H = 3072, 2160
XJ, XF, BT, YH = 0.06, 2.49, 0.042, 1.645        # joint x, fore-edge x, board, half height
BOARD_FLAT = (XF - BT / 2) - XJ                   # 2.409 units of flat outer face
Y_FLAT = YH - BT / 2                              # 1.624
U_BACK, U_SPINE, U_FRONT = (0.01, 0.43), (0.43, 0.57), (0.57, 0.99)
V_OUT, V_IN = (0.012, 0.848), (0.875, 0.990)
SPINE_ARC = 0.6351                                # closed spine outer arc length

LEATHER = np.array([88, 48, 20]) / 255            # tobacco, sRGB albedo
LEATHER_DARK = np.array([40, 20, 9]) / 255
IVORY_INK = np.array([228, 214, 184]) / 255
SEPIA_INK = np.array([214, 188, 140]) / 255
ESPRESSO_INK = np.array([33, 20, 13]) / 255
FOIL = np.array([222, 186, 116]) / 255


def font(weight, size, italic=False):
    return ImageFont.truetype(str(FONTS / f'cormorant-garamond-latin-{weight}-{"italic" if italic else "normal"}.woff'), int(size))


def periodic_noise(n, cutoff, power=0.0, m=None):
    m = m or n
    white = rng.standard_normal((m, n))
    f = np.sqrt((np.fft.fftfreq(m)[:, None] * m) ** 2 + (np.fft.fftfreq(n)[None, :] * n) ** 2)
    field = np.real(np.fft.ifft2(np.fft.fft2(white) * np.exp(-(f / cutoff) ** 2) * np.maximum(f, 1) ** -power))
    return (field - field.mean()) / field.std()


def gblur(a, sigma):
    """Gaussian blur by FFT with reflective padding (no wrap-around)."""
    if sigma <= 0:
        return a
    pad = int(sigma * 3) + 2
    p = np.pad(a, pad, mode='reflect')
    fy = np.fft.fftfreq(p.shape[0])[:, None]
    fx = np.fft.fftfreq(p.shape[1])[None, :]
    k = np.exp(-2 * (math.pi * sigma) ** 2 * (fx * fx + fy * fy))
    return np.real(np.fft.ifft2(np.fft.fft2(p) * k))[pad:-pad, pad:-pad]


def wrap_normal(height, strength):
    gx = (np.roll(height, -1, 1) - np.roll(height, 1, 1)) / 2
    gy = (np.roll(height, -1, 0) - np.roll(height, 1, 0)) / 2
    n = np.dstack([-gx * strength, gy * strength, np.ones_like(height)])
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    return ((n * 0.5 + 0.5) * 255 + 0.5).astype(np.uint8)


def edge_normal(height, strength):
    gy, gx = np.gradient(height)
    n = np.dstack([-gx * strength, gy * strength, np.ones_like(height)])
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    return n


def worley(n, cells, jitter=0.9):
    """Periodic F1/F2 cellular distances on an n x n tile with cells x cells sites."""
    pts = (np.arange(cells)[:, None, None] * 0 + rng.uniform(0.5 - jitter / 2, 0.5 + jitter / 2, (cells, cells, 2)))
    f1 = np.full((n, n), 9.0, np.float32)
    f2 = np.full((n, n), 9.0, np.float32)
    coords = (np.arange(n) + 0.5) / n * cells
    gy, gx = np.meshgrid(coords, coords, indexing='ij')
    cy, cx = np.floor(gy).astype(int), np.floor(gx).astype(int)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            ny, nx = cy + dy, cx + dx
            p = pts[ny % cells, nx % cells]
            d = np.sqrt((ny + p[..., 0] - gy) ** 2 + (nx + p[..., 1] - gx) ** 2).astype(np.float32)
            closer = d < f1
            f2 = np.where(closer, f1, np.minimum(f2, d))
            f1 = np.where(closer, d, f1)
    return f1, f2


# ---- Full-grain leather detail (sampled at 0.45 x TEXCOORD_1: 1.33 units/tile)
def leather_detail(n=1024):
    f1, f2 = worley(n, 64)                      # pebbles about 1.5 mm
    pebble = np.clip((f2 - f1) * 2.2, 0, 1) ** 0.55
    g1, g2 = worley(n, 16, 1.0)                 # larger creases between groups
    crease = np.clip((g2 - g1) * 3.5, 0, 1) ** 0.35
    wrinkles = periodic_noise(n, 15) * 0.5 + periodic_noise(n, 34) * 0.25
    pores = (periodic_noise(n, 440) > 2.35).astype(np.float32)
    pores = gblur(pores, 0.7)
    height = 0.58 * pebble + 0.30 * crease + 0.05 * wrinkles - 0.55 * pores
    height = (height - height.min()) / (height.max() - height.min())
    # Tops of the grain are slightly polished; creases and pores stay matte.
    rough = 0.60 + 0.16 * (1 - pebble) + 0.10 * (1 - crease) + 0.12 * pores + 0.02 * periodic_noise(n, 10)
    return height, np.clip(rough, 0, 1)


# ---- Portrait figure mask (the photograph's pale ground prints nothing) ----
def portrait_layers():
    im = Image.open(PORTRAIT).convert('L')
    g = np.asarray(im, dtype=np.float32) / 255
    L = gblur(g, 2)
    grad = np.abs(np.diff(L, axis=1, prepend=L[:, :1])) + np.abs(np.diff(L, axis=0, prepend=L[:1]))
    grad = np.asarray(Image.fromarray((grad * 1020).clip(0, 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5)), dtype=np.float32) / 255
    h, w = g.shape
    ok = (L > 0.62) & (grad < 0.10)
    bg = np.zeros((h, w), bool)
    q = deque([(y, x) for x in range(w) for y in (0, h - 1)] + [(y, x) for y in range(h) for x in (0, w - 1)])
    while q:
        y, x = q.popleft()
        if bg[y, x] or not ok[y, x]:
            continue
        bg[y, x] = True
        if y > 0: q.append((y - 1, x))
        if y < h - 1: q.append((y + 1, x))
        if x > 0: q.append((y, x - 1))
        if x < w - 1: q.append((y, x + 1))
    torso = Image.new('L', (w, h), 0)
    ImageDraw.Draw(torso).polygon([(92, 600), (200, 500), (470, 515), (575, 640), (640, 868), (40, 868)], fill=255)
    fig = Image.fromarray(((~bg) * 255).astype(np.uint8))
    fig = Image.fromarray(np.maximum(np.asarray(fig), np.asarray(torso)))
    # Close small holes, then pull the edge well inside the pale ground so no halo prints.
    fig = fig.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.MinFilter(9)).filter(ImageFilter.MinFilter(13)).filter(ImageFilter.GaussianBlur(4))
    return g, np.asarray(fig, dtype=np.float32) / 255


def resample(a, size):
    return np.asarray(Image.fromarray(a.astype(np.float32), 'F').resize(size, Image.BICUBIC), dtype=np.float32)


def text_mask(size, draws):
    layer = Image.new('L', size, 0)
    d = ImageDraw.Draw(layer)
    for fn in draws:
        fn(d)
    return np.asarray(layer, dtype=np.float32) / 255


def tracked(draw, x, y, text, fnt, tracking, anchor='ls', fill=255, align='left'):
    widths = [draw.textlength(ch, font=fnt) for ch in text]
    total = sum(widths) + tracking * (len(text) - 1)
    if align == 'right':
        x -= total
    elif align == 'center':
        x -= total / 2
    for ch, wd in zip(text, widths):
        draw.text((x, y), ch, font=fnt, fill=fill, anchor=anchor)
        x += wd + tracking
    return total


# ---- Front board design ----------------------------------------------------
def front_design(pw, ph, S=2):
    """Front board face, pw x ph final pixels covering BOARD_FLAT x 2*Y_FLAT units.
    Returns (ivory ink, espresso ink, foil) coverage at final resolution."""
    sw, sh = pw * S, ph * S
    ppu = sw / BOARD_FLAT                        # supersampled pixels per unit
    X = lambda u: u * ppu                        # from the spine-side joint
    Y = lambda u: (u - (YH - Y_FLAT)) * ppu      # from the head edge of the board

    # Portrait: centred, low on the board, fading out at its lower edge.
    g, fig = portrait_layers()
    pw_u = 1.80
    ph_u = pw_u * g.shape[0] / g.shape[1]
    left, top = (2.43 - pw_u) / 2 - 0.02, 0.86
    box = (int(X(left)), int(Y(top)), int(X(left + pw_u)), int(Y(top + ph_u)))
    size = (box[2] - box[0], box[3] - box[1])
    tone = resample(g, size)
    mask = resample(fig, size)
    yy = (np.arange(size[1])[:, None] / ppu) + top
    xx = (np.arange(size[0])[None, :] / ppu) + left
    fade = np.clip((3.12 - yy) / 0.42, 0, 1) ** 1.4          # dissolve into the leather near the tail
    fade = fade * np.clip((xx - left) / 0.10, 0, 1) * np.clip((left + pw_u - xx) / 0.10, 0, 1)
    mask = mask * fade
    # Tone curve: lift the face, keep the hair rich.
    L = np.clip((tone - 0.10) / 0.82, 0, 1) ** 0.95
    pitch = ph_u / 118 * ppu                                  # 118 lines over the photograph
    phase = (np.arange(size[1])[:, None] + 0.5) / pitch
    # Lines bow very slightly with the face, as an engraver's line screen does.
    phase = phase + 0.12 * np.sin((xx - left) / pw_u * math.pi)
    d = np.abs(phase - np.floor(phase) - 0.5) * pitch         # distance to line centre (px)
    width = np.clip(L, 0, 1) ** 1.35 * pitch * 0.80
    ivory = np.clip((width / 2 - d) / 1.1 + 0.5, 0, 1) * (width > 0.6)
    ivory *= mask
    dark = np.clip((0.24 - L) / 0.20, 0, 1) * mask * 0.55     # second ink: deep shadow only
    ivory_full = np.zeros((sh, sw), np.float32)
    dark_full = np.zeros((sh, sw), np.float32)
    y0, x0 = box[1], box[0]
    y1, x1 = min(sh, box[3]), min(sw, box[2])
    ivory_full[y0:y1, x0:x1] = ivory[: y1 - y0, : x1 - x0]
    dark_full[y0:y1, x0:x1] = dark[: y1 - y0, : x1 - x0]

    # Foil: small title, small details, a square badge. Generous negative space.
    title = font(500, 0.150 * ppu)
    small = font(600, 0.062 * ppu)
    italic = font(500, 0.088 * ppu, italic=True)
    mono = font(600, 0.105 * ppu)
    margin = 0.30

    def draw_title(d):
        d.text((X(margin), Y(0.47)), 'The Life of', font=title, fill=255, anchor='ls')
        d.text((X(margin), Y(0.64)), 'Simone Weil', font=title, fill=255, anchor='ls')

    def draw_details(d):
        tracked(d, X(margin), Y(3.10), '1909 – 1943', small, 0.016 * ppu)
        d.text((X(2.43 - margin), Y(3.10)), 'A life in 12 chapters', font=italic, fill=255, anchor='rs')

    def draw_badge(d):
        s = 0.205
        bx, by = 2.43 - margin - s, 0.28
        d.rounded_rectangle((X(bx), Y(by), X(bx + s), Y(by + s)), radius=0.012 * ppu, fill=255)
        inset = 0.020
        d.rectangle((X(bx + inset), Y(by + inset), X(bx + s - inset), Y(by + s - inset)), outline=0, width=max(2, int(0.0045 * ppu)))
        d.text((X(bx + s / 2), Y(by + s / 2 + 0.004)), 'SW', font=mono, fill=0, anchor='mm')

    foil = text_mask((sw, sh), [draw_title, draw_details, draw_badge])

    def down(a):
        return resample(a, (pw, ph))
    return down(ivory_full), down(dark_full), down(foil)


# ---- Spine design (composed upright as seen on the entrance spine) ---------
def spine_design(pw, ph, S=2):
    """pw x ph final pixels covering SPINE_ARC x 2*Y_FLAT units. Composed as the
    visitor sees the standing book (its tail uppermost, front board to the left),
    then rotated 180 degrees into atlas order (head first, back board first)."""
    sw, sh = pw * S, ph * S
    ppu_x, ppu_y = sw / SPINE_ARC, sh / (2 * Y_FLAT)
    cx = sw / 2
    # Engraved likeness: printed in warm sepia ink, its dark ground left as leather.
    eng = np.asarray(Image.open(ENGRAVING).convert('L'), dtype=np.float32) / 255
    lw = 0.40
    lh = lw * eng.shape[0] / eng.shape[1]
    top = 0.30
    size = (int(lw * ppu_x), int(lh * ppu_y))
    tone = resample(eng, size)
    yy, xx = np.mgrid[0:size[1], 0:size[0]]
    ell = ((xx / size[0] - 0.5) / 0.50) ** 2 + ((yy / size[1] - 0.47) / 0.53) ** 2
    vignette = np.clip((1 - ell) / 0.22, 0, 1)
    sepia = np.clip((tone - 0.30) / 0.45, 0, 1) ** 1.1 * vignette
    sepia_full = np.zeros((sh, sw), np.float32)
    x0, y0 = int(cx - size[0] / 2), int(top * ppu_y)
    sepia_full[y0:y0 + size[1], x0:x0 + size[0]] = sepia

    title = font(500, 0.150 * ppu_y)
    small = font(600, 0.058 * ppu_y)
    mono = font(600, 0.080 * ppu_y)
    # The title runs down the spine (rotate the line 90 degrees clockwise).
    line = Image.new('L', (int(2.0 * ppu_y), int(0.30 * ppu_x)), 0)
    d = ImageDraw.Draw(line)
    text = 'The Life of Simone Weil'
    tw = d.textlength(text, font=title)
    d.text((line.width / 2, line.height / 2 + 0.035 * ppu_x), text, font=title, fill=255, anchor='ms')
    rot = line.rotate(-90, expand=True)
    foil_img = Image.new('L', (sw, sh), 0)
    title_top = top + lh + 0.22 + (2.0 - tw / ppu_y) / 2 - (2.0 - tw / ppu_y) / 2
    foil_img.paste(rot, (int(cx - rot.width / 2), int((top + lh + 0.20) * ppu_y - (line.width - tw) / 2)))
    d = ImageDraw.Draw(foil_img)
    # Fine foil rules framing the likeness, and a small badge near the head.
    for yv in (top - 0.07, top + lh + 0.07):
        d.rectangle((cx - 0.11 * ppu_x, yv * ppu_y, cx + 0.11 * ppu_x, yv * ppu_y + max(2, 0.0045 * ppu_y)), fill=255)
    s = 0.15
    by = 2 * Y_FLAT - 0.30 - s
    d.rounded_rectangle((cx - s / 2 * ppu_x, by * ppu_y, cx + s / 2 * ppu_x, (by + s) * ppu_y), radius=0.01 * ppu_y, fill=255)
    d.text((cx, (by + s / 2 + 0.003) * ppu_y), 'SW', font=mono, fill=0, anchor='mm')
    foil = np.asarray(foil_img, dtype=np.float32) / 255

    def down(a):
        return np.rot90(resample(a, (pw, ph)), 2)
    return down(sepia_full), down(foil)


def back_design(pw, ph, S=2):
    """A small blind-stamped badge, no colour: depth only."""
    sw, sh = pw * S, ph * S
    ppu = sw / BOARD_FLAT
    layer = Image.new('L', (sw, sh), 0)
    d = ImageDraw.Draw(layer)
    s = 0.16
    # Back board read from outside: the spine is on the right; badge low and centred.
    bx, by = BOARD_FLAT / 2 - s / 2 - 0.03, 2 * Y_FLAT - 0.45
    d.rounded_rectangle((bx * ppu, by * ppu, (bx + s) * ppu, (by + s) * ppu), radius=0.01 * ppu, outline=255, width=int(0.008 * ppu))
    d.text(((bx + s / 2) * ppu, (by + s / 2 + 0.003) * ppu), 'SW', font=font(600, 0.08 * ppu), fill=255, anchor='mm')
    return resample(np.asarray(layer, dtype=np.float32) / 255, (pw, ph))


def region(urange, vrange):
    return (int(round(urange[0] * W)), int(round(vrange[0] * H)), int(round(urange[1] * W)), int(round(vrange[1] * H)))


def build_atlas():
    u = (np.arange(W) + 0.5) / W
    v = (np.arange(H) + 0.5) / H
    U, V = np.meshgrid(u, v)
    # Physical distances (units) to the nearest board edge or joint, for wear.
    def lin(a, r, length):
        return (a - r[0]) / (r[1] - r[0]) * length
    dist = np.full((H, W), 9.0)
    outer = (V < V_OUT[1] + 0.012)
    vy = np.clip(np.minimum(lin(V, V_OUT, 2 * Y_FLAT), 2 * Y_FLAT - lin(V, V_OUT, 2 * Y_FLAT)), -0.05, 9)
    back = outer & (U < U_BACK[1])
    front = outer & (U >= U_FRONT[0])
    spine = outer & (U >= U_SPINE[0]) & (U < U_SPINE[1])
    bx = lin(U, U_BACK, BOARD_FLAT)                     # 0 at fore-edge
    fx = BOARD_FLAT - lin(U, U_FRONT, BOARD_FLAT)       # 0 at fore-edge
    jx_back = BOARD_FLAT - bx                           # 0 at the joint
    jx_front = lin(U, U_FRONT, BOARD_FLAT)
    sx = lin(U, U_SPINE, SPINE_ARC)
    dist = np.where(back, np.minimum(np.minimum(bx, vy), 9), dist)
    dist = np.where(front, np.minimum(np.minimum(fx, vy), 9), dist)
    dist = np.where(spine, vy, dist)
    joint = np.where(back, jx_back, np.where(front, jx_front, np.where(spine, np.minimum(sx, SPINE_ARC - sx), 9)))
    wear_edge = np.exp(-np.clip(dist, 0, 9) / 0.022)
    wear_joint = np.exp(-np.abs(joint - 0.025) / 0.03) * 0.55
    mott = periodic_noise(W, 14, m=H) * 0.5 + periodic_noise(W, 60, m=H) * 0.5
    wear = np.clip(wear_edge + wear_joint * (0.6 + 0.4 * np.clip(mott, -1, 1)), 0, 1)
    inner = V > V_IN[0] - 0.01
    wear = np.where(inner, 0.25, wear)

    base = LEATHER[None, None, :] * (1 + 0.025 * mott[..., None])
    color = base * (1 - wear[..., None] * 0.42) + LEATHER_DARK[None, None, :] * wear[..., None] * 0.18
    color = np.where(inner[..., None], LEATHER[None, None, :] * 0.80 * (1 + 0.04 * mott[..., None]), color)
    rough = 0.60 - 0.16 * wear + 0.03 * mott
    metal = np.zeros((H, W), np.float32)
    height = 0.10 * gblur(rng.standard_normal((H, W)), 22)  # gentle undulation of leather over board

    # Ink breakup: ink skips the deepest pores of the grain.
    breakup = 1 - 0.12 * np.clip(periodic_noise(W, 700, m=H) - 1.2, 0, 1.5)

    # Front board.
    fx0, fy0, fx1, fy1 = region(U_FRONT, V_OUT)
    ivory, dark, foil = front_design(fx1 - fx0, fy1 - fy0)
    sl = (slice(fy0, fy1), slice(fx0, fx1))
    c = color[sl]
    dk = (dark * breakup[sl])[..., None]
    c = c * (1 - dk) + ESPRESSO_INK * dk
    iv = (ivory * breakup[sl] * 0.92)[..., None]
    c = c * (1 - iv) + IVORY_INK * iv
    color[sl] = c
    rough[sl] = rough[sl] * (1 - ivory * 0.92) + 0.56 * ivory * 0.92
    rough[sl] = rough[sl] * (1 - dark * 0.8) + 0.50 * dark * 0.8
    height[sl] += 0.25 * ivory          # ink sits a hair proud of the grain

    # Spine.
    sx0, sy0, sx1, sy1 = region(U_SPINE, V_OUT)
    sepia, sfoil = spine_design(sx1 - sx0, sy1 - sy0)
    ss = (slice(sy0, sy1), slice(sx0, sx1))
    sp = (sepia * breakup[ss] * 0.95)[..., None]
    color[ss] = color[ss] * (1 - sp) + SEPIA_INK * sp
    rough[ss] = rough[ss] * (1 - sepia) + 0.55 * sepia
    height[ss] += 0.2 * sepia

    # Back board blind stamp.
    bx0, by0, bx1, by1 = region(U_BACK, V_OUT)
    blind = back_design(bx1 - bx0, by1 - by0)
    bs = (slice(by0, by1), slice(bx0, bx1))
    height[bs] -= 2.2 * gblur(blind, 1.2)
    color[bs] = color[bs] * (1 - 0.20 * blind[..., None])
    rough[bs] = rough[bs] - 0.15 * blind

    # Foil: pressed into the leather with a crisp bevelled wall, then gilt.
    foil_full = np.zeros((H, W), np.float32)
    foil_full[sl] = foil
    foil_full[ss] = sfoil
    deboss = gblur(foil_full, 1.1)
    halo = gblur(foil_full, 5.0)
    height -= 2.6 * deboss + 0.6 * halo
    color = color * (1 - 0.22 * np.clip(halo - foil_full, 0, 1)[..., None])   # pressed leather darkens
    fm = np.clip(foil_full, 0, 1)[..., None]
    foil_tone = FOIL * (0.92 + 0.08 * gblur(rng.standard_normal((H, W)), 3)[..., None])
    color = color * (1 - fm) + foil_tone * fm
    rough = rough * (1 - foil_full) + 0.20 * foil_full
    metal = np.maximum(metal, foil_full)

    color = np.clip(color, 0, 1)
    normal = edge_normal(height, 1.0)
    return color, np.dstack([wear, np.clip(rough, 0.05, 1), metal]), normal


def glitter(n=256):
    """Random flake normals: each flake tilts a little in its own direction."""
    f1, f2 = worley(n, 48, 1.0)
    tilt = rng.normal(0, 0.35, (96 * 3, 96 * 3, 2))
    # Assign each pixel the tilt of its nearest site via a hash of F1 neighbourhood.
    ids = (np.round(f1 * 997 + f2 * 131) % (96 * 3)).astype(int)
    tx = tilt[ids, (ids * 7) % (96 * 3), 0]
    ty = tilt[ids, (ids * 13) % (96 * 3), 1]
    edge = np.clip((f2 - f1) * 6, 0, 1)
    nn = np.dstack([tx * edge, ty * edge, np.ones_like(tx)])
    nn /= np.linalg.norm(nn, axis=2, keepdims=True)
    return ((nn * 0.5 + 0.5) * 255 + 0.5).astype(np.uint8)


if __name__ == '__main__':
    color, orm, normal = build_atlas()
    Image.fromarray((color * 255 + 0.5).astype(np.uint8), 'RGB').save(OUT / 'cover-color.webp', 'WEBP', quality=90, method=6)
    Image.fromarray((orm * 255 + 0.5).astype(np.uint8), 'RGB').save(OUT / 'cover-orm.webp', 'WEBP', quality=90, method=6)
    Image.fromarray(((normal * 0.5 + 0.5) * 255 + 0.5).astype(np.uint8), 'RGB').save(OUT / 'cover-normal.webp', 'WEBP', quality=92, method=6)
    height, rough = leather_detail(1024)
    Image.fromarray(wrap_normal(height, 4.5), 'RGB').save(OUT / 'leather-normal.webp', 'WEBP', quality=90, method=6)
    Image.fromarray((rough * 255 + 0.5).astype(np.uint8), 'L').convert('RGB').save(OUT / 'leather-rough.webp', 'WEBP', quality=88, method=6)
    Image.fromarray(glitter(256), 'RGB').save(OUT / 'binding-glitter.webp', 'WEBP', quality=92, method=6)
    for name in ['cover-color', 'cover-orm', 'cover-normal', 'leather-normal', 'leather-rough', 'binding-glitter']:
        print(name, f'{(OUT / (name + ".webp")).stat().st_size / 1024:.0f} KiB')
