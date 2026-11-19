"""Chapter 3-12 paper theatres, rebuilt 18 November 2026 to the chapter 1-2 standard.

Every card stands on the right-hand page (x > 0), so the left page belongs to
the raised writing and nothing folds over it. Each spread has a rear backdrop
(y ~ 1.42), a hero construction (~1.0), a mid row, figures (~-0.2) and a low
foreground (~-1.0 to -1.4). Hinge contract, coordinates and materials are
those in docs/PIPELINE.md. All illustrations are cut meshes; no live physics.
"""
import math
import random

KIT = ['hinge', 'polygon', 'box', 'line', 'disk', 'text', 'facade', 'canopy', 'desk', 'steps', 'lamp', 'arch', 'window',
       'material', 'broadleaf', 'laurel_bush', 'person', 'kerb', 'flower_hedge', 'grass', 'park_bench', 'paving',
       'book_pile', 'lobed', 'leaf_shape', 'M']


def build(number, kit):
    globals().update({k: kit[k] for k in KIT})
    for name, colour in [('basalt', '4A4642'), ('ochre', 'C99B5E'), ('ochre_light', 'DDBB86'), ('brick', '8C4D39'),
                         ('olive_leaf', '7A8063'), ('olive_light', 'A9AC8E'), ('smoke', 'D9D3C7'), ('sea', '5E7B7E'),
                         ('sea_light', '9DB3AE'), ('candle', 'F2E7CF'), ('flame', 'E3AE4F'), ('newsprint', 'D8D1BF'),
                         ('cypress', '3E4A3A'), ('rust', 'A2603F'), ('night', '3B4450'), ('chalk', 'EDE7DA')]:
        if name not in M:
            material(name, colour)
    return {3: teaching, 4: power, 5: factory, 6: spain, 7: threshold,
            8: force, 9: attention, 10: roots, 11: unfinished, 12: legacy}[number]()


# ---- Shared cut-paper pieces ------------------------------------------------

def card(name, x, y, w, h, parent, mat='paper', z=0):
    return polygon(name, [(x - w / 2, z), (x + w / 2, z), (x + w / 2, z + h), (x - w / 2, z + h)], .014, y, mat, parent)


def stroke(name, x0, x1, z, y, parent, mat='ink_soft', seed=1, width=.0055, wave=.008):
    """One line of handwriting: a thin ribbon with a lively baseline."""
    rng = random.Random(seed)
    n = max(6, int((x1 - x0) / .02))
    top, bottom = [], []
    for i in range(n + 1):
        xx = x0 + (x1 - x0) * i / n
        zz = z + wave * math.sin(i * 1.9 + rng.random() * 2) * (0.4 + rng.random() * .6)
        w = width * (0.6 + rng.random() * .8)
        top.append((xx, zz + w))
        bottom.append((xx, zz - w))
    return polygon(name, top + bottom[::-1], .003, y, mat, parent)


def letter(name, x, y, w, h, parent, seed=1, mat='paper'):
    """A handwritten sheet with a folded corner and a margin rule."""
    fold = min(w, h) * .16
    polygon(name + ' sheet', [(x - w / 2, 0), (x + w / 2, 0), (x + w / 2, h - fold), (x + w / 2 - fold, h), (x - w / 2, h)], .010, y, mat, parent)
    polygon(name + ' folded corner', [(x + w / 2 - fold, h), (x + w / 2, h - fold), (x + w / 2 - fold, h - fold)], .004, y - .008, 'paper_shadow', parent)
    line(name + ' margin', (x - w * .36, y - .009, h * .08), (x - w * .36, y - .009, h * .92), .003, 'rust', parent)
    rng = random.Random(seed)
    rows = max(3, int(h / .07))
    for i in range(rows):
        z = h * .86 - i * (h * .74 / max(1, rows - 1))
        end = x + w * (.30 + .12 * rng.random()) if i != rows - 1 else x + w * rng.uniform(-.05, .15)
        stroke(name + ' handwriting', x - w * .30, end, z, y - .010, parent, 'ink_soft', seed * 31 + i)


def titled_book(name, x, y, w, h, parent, mat, title, year=None, seed=1, ink='brass'):
    """A standing book seen from the front: cloth board, foil frame and a real title."""
    polygon(name + ' page block', [(x - w / 2 + .02, .01), (x + w / 2 + .03, .01), (x + w / 2 + .03, h - .03), (x - w / 2 + .02, h - .03)], .010, y + .010, 'paper_light', parent)
    card(name + ' cloth board', x, y, w, h, parent, mat)
    for zz in (.05, h - .05):
        line(name + ' foil rule', (x - w * .40, y - .012, zz), (x + w * .40, y - .012, zz), .006, 'brass', parent)
    for xx in (x - w * .40, x + w * .40):
        line(name + ' foil rule', (xx, y - .012, .05), (xx, y - .012, h - .05), .006, 'brass', parent)
    size = min(.085, w * .17)
    text(name + ' title', title, (x, y - .013, h * .66), size, ink, parent)
    text(name + ' author', 'SIMONE WEIL', (x, y - .013, h * .30), size * .50, ink, parent)
    if year:
        text(name + ' year', year, (x, y - .013, h * .16), size * .45, 'paper_light', parent)


def bookcase(name, x, y, w, h, parent, seed=3):
    rng = random.Random(seed)
    card(name + ' back', x, y + .008, w, h, parent, 'bark')
    shelves = 4
    for k in range(shelves + 1):
        z = .03 + k * (h - .06) / shelves
        box(name + ' shelf', (x, y - .012, z), (w + .04, .022, .026), 'paper_light', parent, .002)
    for side in (-1, 1):
        box(name + ' upright', (x + side * (w / 2 + .01), y - .012, h / 2), (.03, .024, h), 'paper_light', parent, .002)
    colours = ['tobacco', 'slate', 'red', 'ink_soft', 'leaf_deep', 'paper_light', 'rust', 'night']
    for k in range(shelves):
        z0 = .045 + k * (h - .06) / shelves
        room = (h - .06) / shelves - .03
        xx = x - w / 2 + .02
        while xx < x + w / 2 - .04:
            bw = rng.uniform(.028, .05)
            bh = room * rng.uniform(.70, .96)
            lean = 0 if rng.random() > .12 else .018
            mat = colours[rng.randrange(len(colours))]
            polygon(name + ' spine', [(xx, z0), (xx + bw, z0), (xx + bw + lean, z0 + bh), (xx + lean, z0 + bh)], .010, y - .004, mat, parent)
            for band in (.18, .82):
                line(name + ' gilt band', (xx + .004 + lean * band, y - .011, z0 + bh * band), (xx + bw - .004 + lean * band, y - .011, z0 + bh * band), .0035, 'brass', parent)
            xx += bw + .004


def cypress(name, x, y, h, parent, seed=1):
    rng = random.Random(seed)
    for layer, (mat, scale) in enumerate([('cypress', 1.0), ('leaf_deep', .72)]):
        pts = []
        n = 26
        for i in range(n + 1):
            t = i / n
            r = h * .11 * scale * math.sin(math.pi * min(1, t * 1.15)) ** .8 * (1 + .12 * math.sin(i * 2.3) + rng.uniform(-.05, .05))
            pts.append((x + r, h * .06 + t * h * .94 * (1 - .02 * layer)))
        pts += [(x - (px - x), pz) for px, pz in reversed(pts)]
        polygon(name + ' cypress flame', pts, .007, y - .006 * layer, mat, parent)
    polygon(name + ' trunk', [(x - h * .015, 0), (x + h * .015, 0), (x + h * .012, h * .10), (x - h * .012, h * .10)], .007, y + .002, 'bark', parent)


def olive(name, x, y, h, parent, seed=1):
    broadleaf(name, x, y, h, parent, seed, .40, False, ('olive_leaf', 'olive_light', 'stone'))


def house(name, x, y, w, h, parent, wall='ochre', roof='terracotta', rows=2, cols=2, roof_kind='pitched', shutter='leaf', seed=1):
    """A plain southern house: rendered wall, shuttered windows, tiled roof."""
    polygon(name + ' wall', [(x - w / 2, 0), (x + w / 2, 0), (x + w / 2, h), (x - w / 2, h)], .014, y, wall, parent)
    for r in range(rows):
        z = .16 + r * (h - .22) / rows
        for c in range(cols):
            xx = x + (c - (cols - 1) / 2) * w / (cols + .4)
            ww, hh = w / (cols + 2.4), min(.20, (h - .22) / rows * .62)
            box(name + ' window', (xx, y - .010, z + hh / 2), (ww, .006, hh), 'night', parent, .001)
            for side in (-1, 1):
                polygon(name + ' shutter', [(xx + side * ww / 2, z), (xx + side * (ww / 2 + ww * .45), z), (xx + side * (ww / 2 + ww * .45), z + hh), (xx + side * ww / 2, z + hh)], .005, y - .014, shutter, parent)
            line(name + ' sill', (xx - ww * .7, y - .016, z - .008), (xx + ww * .7, y - .016, z - .008), .010, 'paper_light', parent)
    if roof_kind == 'pitched':
        polygon(name + ' tiled roof', [(x - w * .56, h - .01), (x + w * .56, h - .01), (x, h + w * .30)], .016, y - .004, roof, parent)
        for k in range(3):
            zz = h + .03 + k * w * .07
            half = w * .5 * (1 - (zz - h) / (w * .30))
            if half > .04:
                line(name + ' tile course', (x - half, y - .014, zz), (x + half, y - .014, zz), .004, 'brick', parent)
    elif roof_kind == 'flat':
        polygon(name + ' flat roof', [(x - w * .54, h - .01), (x + w * .54, h - .01), (x + w * .54, h + .05), (x - w * .54, h + .05)], .016, y - .004, roof, parent)


def figure_group(name, entries, parent):
    for x, y, h, kwargs in entries:
        person(name, x, y, h, parent, **kwargs)


def stone_wall(name, x, y, w, h, parent, seed=5, mat='stone'):
    rng = random.Random(seed)
    polygon(name + ' wall core', [(x - w / 2, 0), (x + w / 2, 0), (x + w / 2, h * .9), (x - w / 2, h * .9)], .012, y, 'paper_shadow', parent)
    for row in range(3):
        z0 = row * h * .30
        xx = x - w / 2 + (row % 2) * .03
        while xx < x + w / 2 - .03:
            sw = rng.uniform(.06, .11)
            sh = h * rng.uniform(.26, .34)
            pts = [(xx + sw * .1, z0), (xx + sw * .92, z0 + .004), (xx + sw, z0 + sh * .6), (xx + sw * .85, z0 + sh), (xx + sw * .12, z0 + sh * .96), (xx, z0 + sh * .5)]
            pts = [(min(x + w / 2, px), pz) for px, pz in pts]
            polygon(name + ' stone', pts, .006, y - .008, mat if rng.random() > .3 else 'paper_light', parent)
            xx += sw + .008


def waves(name, x, y, w, h, parent, seed=2):
    rng = random.Random(seed)
    for layer, mat in enumerate(['sea', 'sea_light']):
        pts = [(x + w / 2, 0), (x - w / 2, 0)]
        n = int(w / .05)
        for i in range(n + 1):
            xx = x - w / 2 + w * i / n
            pts.append((xx, h * (.62 - .25 * layer) + h * .22 * math.sin(i * 1.15 + layer) + rng.uniform(-.006, .006)))
        polygon(name + ' wave band', pts, .006, y - .007 * layer, mat, parent)


def rails(name, x, y, w, parent):
    polygon(name + ' ballast', [(x - w / 2, 0), (x + w / 2, 0), (x + w / 2, .04), (x - w / 2, .04)], .010, y, 'stone', parent)
    xx = x - w / 2 + .03
    while xx < x + w / 2 - .03:
        polygon(name + ' sleeper', [(xx, .03), (xx + .07, .03), (xx + .07, .06), (xx, .06)], .006, y - .007, 'bark', parent)
        xx += .11
    line(name + ' rail', (x - w / 2, y - .013, .072), (x + w / 2, y - .013, .072), .014, 'ink_soft', parent)


def crate(name, x, y, s, parent, mat='tobacco'):
    card(name + ' crate', x, y, s, s * .62, parent, mat)
    for k in range(3):
        line(name + ' plank', (x - s * .48, y - .010, s * (.12 + k * .19)), (x + s * .48, y - .010, s * (.12 + k * .19)), .005, 'bark', parent)
    line(name + ' brace', (x - s * .44, y - .011, s * .05), (x + s * .44, y - .011, s * .56), .008, 'bark', parent)


def candles(name, x, y, n, parent, spacing=.07, seed=4):
    rng = random.Random(seed)
    for i in range(n):
        xx = x + (i - (n - 1) / 2) * spacing
        hh = rng.uniform(.10, .19)
        card(name + ' candle', xx, y, .028, hh, parent, 'candle')
        polygon(name + ' flame', [(xx - .012, hh + .004), (xx + .012, hh + .004), (xx + .004, hh + .035), (xx, hh + .05), (xx - .004, hh + .035)], .004, y - .007, 'flame', parent)


def newspapers(name, x, y, s, parent):
    for k in range(5):
        polygon(name + ' folded paper', [(x - s * .5 + k * .006, k * .022), (x + s * .5 - k * .004, k * .022), (x + s * .5 - k * .004, k * .022 + .02), (x - s * .5 + k * .006, k * .022 + .02)], .008, y, 'newsprint' if k % 2 else 'paper_light', parent)
    card(name + ' front page', x, y - .010, s * .82, s * .55, parent, 'newsprint', .11)
    line(name + ' headline', (x - s * .32, y - .020, .11 + s * .45), (x + s * .30, y - .020, .11 + s * .45), .016, 'ink', parent)
    for k in range(4):
        line(name + ' column', (x - s * .32, y - .020, .11 + s * (.34 - k * .07)), (x + s * .30, y - .020, .11 + s * (.34 - k * .07)), .004, 'ink_soft', parent)


def chair(name, x, y, s, parent, facing=1):
    """A bentwood chair in profile, so it reads as a chair and not a ladder."""
    f = facing
    pts = [(x - .13 * s * f, 0), (x - .10 * s * f, 0), (x - .09 * s * f, .40 * s), (x + .10 * s * f, .40 * s), (x + .11 * s * f, 0), (x + .14 * s * f, 0),
           (x + .13 * s * f, .46 * s), (x - .10 * s * f, .46 * s), (x - .13 * s * f, .92 * s), (x - .16 * s * f, .92 * s), (x - .15 * s * f, .44 * s)]
    if f < 0:
        pts = pts[::-1]
    polygon(name + ' bentwood frame', pts, .010, y, 'bark', parent)
    polygon(name + ' cane seat', [(x - .10 * s * f, .40 * s), (x + .12 * s * f, .40 * s), (x + .12 * s * f, .45 * s), (x - .10 * s * f, .45 * s)][::f], .006, y - .007, 'flower', parent)
    for z in (.60, .76):
        line(name + ' back hoop', (x - .14 * s * f, y - .007, z * s), (x - .09 * s * f, y - .007, (z + .05) * s), .010, 'bark', parent)


def smoke(name, x, z0, parent, y=0, seed=8):
    rng = random.Random(seed)
    for i in range(4):
        r = .07 + i * .035
        cx = x + i * .09 + rng.uniform(-.02, .02)
        cz = z0 + i * .13
        polygon(name + ' smoke puff', lobed(cx, cz, r, r * .72, 7, .12, rng), .006, y - .004 * i, 'smoke', parent)


# ---- Chapters ----------------------------------------------------------------

def teaching():
    """Le Puy, 1931-34: teaching girls, marching with the unemployed stone-breakers."""
    rear = hinge('Le Puy skyline fold', 1.22, 1.42)
    # The volcanic needles of Le Puy: Saint-Michel d'Aiguilhe and Notre-Dame de France.
    polygon('Rocher Saint-Michel', [(-.86, .30), (-.66, .30), (-.69, .86), (-.74, 1.04), (-.80, .88), (-.84, .58)], .012, 0, 'basalt', rear)
    polygon('Chapel on the needle', [(-.78, 1.03), (-.69, 1.03), (-.69, 1.15), (-.735, 1.25), (-.78, 1.15)], .010, -.004, 'stone', rear)
    polygon('Rocher Corneille', [(-.54, .30), (-.18, .30), (-.24, .66), (-.34, .78), (-.46, .70)], .012, 0, 'basalt', rear)
    polygon('Notre-Dame de France statue', [(-.365, .76), (-.315, .76), (-.32, .94), (-.34, 1.0), (-.36, .94)], .008, -.004, 'rust', rear)
    canopy('Le Puy rooftops', .32, .006, 1.66, .46, rear, 'paper_shadow', 21)
    for i, (xx, hh) in enumerate([(-.98, .34), (-.62, .42), (-.20, .38), (.20, .46), (.58, .40), (.92, .34)]):
        house('Le Puy basalt house', xx, -.012, .30, hh, rear, 'basalt', 'terracotta', 1, 2, 'pitched', 'stone', i)
    school = hinge('Classroom portal fold', 1.50, 1.02)
    for x in (-.64, .64):
        card('Classroom pier', x, 0, .12, 1.56, school, 'stone')
        for z in (.10, 1.36, 1.48):
            box('Classroom capital', (x, -.013, z), (.20, .035, .055), 'paper_light', school, .002)
    polygon('Classroom lintel', [(-.74, 1.50), (.74, 1.50), (.74, 1.64), (-.74, 1.64)], .015, 0, 'paper', school)
    card('Chalkboard', 0, .014, 1.06, .94, school, 'slate', .30)
    for z in (.30, 1.24):
        line('Board frame', (-.54, -.009, z), (.54, -.009, z), .034, 'tobacco', school)
    text('Chalk lesson', 'Solidarité', (0, -.016, 1.00), .13, 'chalk', school)
    for i in range(3):
        stroke('Chalk sum', -.40, .26 - .10 * i, .78 - i * .13, -.016, school, 'chalk', 40 + i, .0045, .006)
    teacher = hinge('Teacher desk fold', .66, -.12)
    desk('Teacher desk', 0, 0, 0, teacher, 1.0)
    person('Teacher Simone', -.26, -.024, .74, teacher, 'bob', True, True, 'book')
    pupils = hinge('Pupils fold', 1.44, -.02)
    for xx, hh in ((-.18, .48), (.10, .52), (.36, .46)):
        person('Pupil', xx, 0, hh, pupils, 'bob', False, False, 'satchel')
    workers = hinge('Stone-breakers fold', 2.08, .34)
    person('Stone-breaker', -.12, 0, .74, workers, 'cap', False, False, 'pick')
    person('Stone-breaker', .18, -.01, .70, workers, 'short', False, False, None)
    heap = hinge('Broken stone fold', 1.86, -.98)
    stone_wall('Stone heap', 0, 0, .52, .16, heap, 13, 'basalt')
    street = hinge('Le Puy kerb fold', 1.22, -1.30)
    kerb('Le Puy cobbles', 0, 0, 2.26, street, 31)
    tufts = hinge('Square grass fold', .55, -1.08)
    grass('Square grass', 0, 0, .52, .14, tufts, 7)


def power():
    """Germany 1932 and France 1934: who holds the power over the many?"""
    rear = hinge('Berlin skyline fold', 1.22, 1.42)
    # Brandenburg Gate, the Reichstag dome and the Red Town Hall, in silhouette.
    polygon('Gate attic', [(-.90, .64), (-.36, .64), (-.36, .74), (-.90, .74)], .012, 0, 'stone', rear)
    polygon('Gate pediment', [(-.84, .74), (-.42, .74), (-.63, .80)], .010, 0, 'stone', rear)
    for i in range(6):
        card('Gate column', -.88 + i * .098, 0, .040, .64, rear, 'stone')
    polygon('Quadriga', [(-.70, .80), (-.56, .80), (-.58, .92), (-.63, .97), (-.68, .92)], .008, -.004, 'ink_soft', rear)
    house('Reichstag block', .18, .004, .62, .56, rear, 'paper_shadow', 'stone', 2, 4, 'flat', 'paper_shadow', 3)
    polygon('Reichstag dome', [(.04, .60)] + [(.18 + .15 * math.cos(a), .60 + .20 * math.sin(a)) for a in [math.pi * (1 - i / 16) for i in range(17)]], .010, -.002, 'night', rear)
    polygon('Town hall tower', [(.74, 0), (.92, 0), (.92, .86), (.88, .96), (.78, .96), (.74, .86)], .012, .006, 'brick', rear)
    canopy('Tiergarten trees', 0, .010, 2.2, .40, rear, 'paper_shadow', 15)
    machine = hinge('Power mechanism fold', 1.48, 1.02)
    polygon('Machine arch frame', [(-.68, 0), (-.56, 0), (-.56, 1.44), (.56, 1.44), (.56, 0), (.68, 0), (.68, 1.58), (-.68, 1.58)], .023, .02, 'ink_soft', machine)
    for x, z, r in ((-.27, .52, .28), (.22, .86, .33), (-.28, 1.15, .19), (.32, .28, .18)):
        line('Wheel support', (x, .015, 0), (x, .015, z), .025, 'stone', machine)
        gear('Interconnected gear', x, 0, z, r, machine)
    for x in (-.62, .62):
        for z in (.08, .47, .86, 1.30, 1.62):
            disk('Frame rivet', x, -.023, z, .019, 'brass', machine)
    reader = hinge('Citizen with newspaper fold', .56, -.16)
    person('Citizen', 0, 0, .74, reader, 'cap', False, False, 'paper')
    study = hinge('Freedom essay desk fold', 1.56, -.10)
    desk('Essay desk', 0, 0, 0, study, .95)
    letter('Reflections on liberty', -.04, -.024, .30, .26, study, 4)
    person('Simone writing', .30, -.02, .70, study, 'bob', True, False, None)
    tree = hinge('Linden fold', 2.12, .55)
    broadleaf('Unter den Linden tree', 0, 0, 1.0, tree, 41, .30)
    stack = hinge('Newspaper stack fold', .76, -1.02)
    newspapers('Evening papers', 0, 0, .44, stack)
    street = hinge('Berlin kerb fold', 1.22, -1.30)
    kerb('Berlin setts', 0, 0, 2.26, street, 17)
    tufts = hinge('Kerb grass fold', 1.90, -1.10)
    grass('Kerb grass', 0, 0, .46, .14, tufts, 18)


def gear(name, x, y, z, r, parent, mat='gilt_dark'):
    pts = []
    for i in range(64):
        angle = i * math.tau / 64
        rr = r * (1 if i % 4 in (1, 2) else .84)
        pts.append((x + rr * math.cos(angle), z + rr * math.sin(angle)))
    polygon(name + ' toothed wheel', pts, .019, y, mat, parent)
    disk(name + ' recessed face', x, y - .020, z, r * .68, 'paper_shadow', parent)
    for i in range(6):
        a = i * math.tau / 6
        line(name + ' spoke', (x, y - .036, z), (x + r * .63 * math.cos(a), y - .036, z + r * .63 * math.sin(a)), .022, mat, parent)
    disk(name + ' axle', x, y - .052, z, r * .16, 'ink_soft', parent)


def clock_face(name, x, y, z, r, parent):
    disk(name + ' bezel', x, y, z, r, 'gilt_dark', parent)
    disk(name + ' ivory dial', x, y - .013, z, r * .91, 'paper_light', parent)
    for i in range(12):
        a = i * math.tau / 12
        line(name + ' hour mark', (x + r * .70 * math.sin(a), y - .025, z + r * .70 * math.cos(a)), (x + r * .83 * math.sin(a), y - .025, z + r * .83 * math.cos(a)), .008, 'ink', parent)
    line(name + ' minute', (x, y - .032, z), (x + r * .56, y - .032, z + r * .20), .011, 'ink', parent)
    line(name + ' hour', (x, y - .033, z), (x - r * .16, y - .033, z + r * .40), .016, 'ink', parent)


def factory():
    """Alsthom, Carnaud and Renault, 1934-35: the year on the machines."""
    rear = hinge('Industrial skyline fold', 1.22, 1.42)
    polygon('Sawtooth workshop', [(-1.04, 0), (1.04, 0), (1.04, .64), (.62, .90), (.62, .64), (.20, .90), (.20, .64), (-.24, .90), (-.24, .64), (-.66, .90), (-.66, .64), (-1.04, .64)], .021, 0, 'paper_shadow', rear)
    for xx in (-.86, -.44, -.02, .40, .82):
        box('North-light glazing', (xx, -.014, .77), (.26, .006, .10), 'night', rear, .001)
    for xx in (-.82, -.41, 0, .41, .82):
        window('Workshop glazing', xx, -.02, .14, .24, .36, rear)
    for cx in (.58, .82):
        card('Brick chimney', cx, .015, .13, 1.12, rear, 'brick')
        for z in [.17 + i * .09 for i in range(11)]:
            line('Chimney course', (cx - .06, -.006, z), (cx + .06, -.006, z), .004, 'stone', rear)
    smoke('Chimney smoke', .56, 1.14, rear, -.004, 3)
    smoke('Chimney smoke', .80, 1.16, rear, -.006, 9)
    press = hinge('Factory press fold', 1.16, 1.02)
    for x in (-.65, .65):
        card('Press upright', x, 0, .17, 1.70, press, 'slate')
        for z in (.15, .43, .73, 1.02, 1.43):
            disk('Press bolt', x, -.025, z, .024, 'brass', press)
    for z, h in ((.14, .20), (1.48, .22)):
        box('Heavy press crossbeam', (0, -.012, z), (1.50, .035, h), 'ink_soft', press, .01)
    card('Press ram', 0, -.010, .32, 1.45, press, 'paper_shadow')
    box('Press head', (0, -.043, .81), (.97, .035, .20), 'slate', press, .008)
    box('Press table', (0, -.045, .38), (1.14, .035, .11), 'stone', press, .004)
    clock_face('Factory clock', 0, -.040, 1.56, .22, press)
    wheel = hinge('Flywheel fold', 2.06, .30)
    gear('Press flywheel', 0, 0, .50, .34, wheel, 'ink_soft')
    line('Flywheel stand', (0, 0, 0), (0, 0, .50), .054, 'ink_soft', wheel)
    worker = hinge('Simone at the press fold', .58, -.12)
    person('Simone at the machine', 0, 0, .70, worker, 'scarf', True, False, None)
    line('Work apron', (-.06, -.014, .28 * .70), (.06, -.014, .28 * .70), .05, 'paper_shadow', worker)
    mates = hinge('Fellow workers fold', 1.52, -.06)
    person('Fellow worker', -.12, 0, .72, mates, 'scarf', False, False, None)
    person('Foreman', .18, -.01, .78, mates, 'cap', False, False, 'paper')
    timeclock = hinge('Time clock fold', 2.12, -.42)
    card('Time clock case', 0, 0, .22, .52, timeclock, 'gilt_dark')
    clock_face('Time clock', 0, -.016, .40, .08, timeclock)
    for k in range(4):
        card('Time card', -.06 + k * .04, -.018, .025, .10, timeclock, 'newsprint', .08)
    crates = hinge('Parts crates fold', 1.18, -1.00)
    crate('Parts crate', -.30, 0, .30, crates)
    crate('Parts crate', .06, -.006, .26, crates, 'bark')
    letter('Factory journal', .42, -.008, .24, .20, crates, 9)
    floor = hinge('Factory floor fold', 1.22, -1.30)
    rails('Trolley track', 0, 0, 2.26, floor)


def spain():
    """Barcelona and the Aragon front, 1936: a cause and its cruelty."""
    rear = hinge('Aragon sierra fold', 1.22, 1.42)
    polygon('Far sierra', [(-1.1, 0), (1.1, 0), (1.1, .78), (.80, 1.05), (.52, .86), (.18, 1.16), (-.16, .92), (-.48, 1.10), (-.80, .84), (-1.1, .96)], .012, .02, 'paper_shadow', rear)
    polygon('Ochre ridge', [(-1.08, 0), (1.08, 0), (1.08, .52), (.66, .76), (.20, .54), (-.24, .82), (-.66, .58), (-1.08, .66)], .012, 0, 'ochre_light', rear)
    for k in range(5):
        z = .12 + k * .09
        stroke('Olive terrace', -1.0, 1.0, z, -.010, rear, 'olive_leaf', 70 + k, .006, .02)
    village = hinge('Aragon village fold', 1.16, 1.02)
    for i, (x, w, h) in enumerate([(-.64, .44, .72), (-.10, .56, .92), (.50, .50, .76)]):
        house('Aragon house', x, 0, w, h, village, 'ochre' if i % 2 else 'ochre_light', 'terracotta', 2, 2, 'pitched', 'leaf_deep', i)
    card('Bell tower', .86, .010, .20, 1.30, village, 'ochre_light')
    polygon('Bell tower cap', [(.74, 1.30), (.98, 1.30), (.86, 1.48)], .012, .006, 'terracotta', village)
    arch('Bell opening', .86, -.004, 1.06, .09, .16, 'night', village)
    militia = hinge('Militia fold', 1.48, -.08)
    person('Militia volunteer', -.20, 0, .76, militia, 'cap', False, False, None)
    person('Simone in the militia', .10, -.01, .70, militia, 'cap', True, False, 'book')
    person('Militia volunteer', .40, 0, .74, militia, 'short', False, False, None)
    camp = hinge('Camp fire fold', .58, -.20)
    for side in (-1, 1):
        line('Tripod leg', (side * .14, 0, 0), (0, 0, .34), .014, 'bark', camp)
    polygon('Cooking pot', [(-.10, .14), (.10, .14), (.08, .27), (-.08, .27)], .012, -.008, 'ink_soft', camp)
    for k, (dx, hh) in enumerate(((-.07, .10), (0, .14), (.07, .09))):
        polygon('Fire flame', [(dx - .04, 0), (dx + .04, 0), (dx + .01, hh), (dx, hh + .03), (dx - .01, hh)], .006, -.014 - .002 * k, 'flame', camp)
    tree = hinge('Aragon olive fold', 2.00, .46)
    olive('Aragon olive', 0, 0, .88, tree, 66)
    post = hinge('Letter to Bernanos fold', 1.18, -.62)
    letter('Letter to Bernanos', 0, 0, .34, .30, post, 21)
    wall = hinge('Dry stone wall fold', 1.22, -1.28)
    stone_wall('Dry stone terrace', 0, 0, 2.24, .14, wall, 8)
    scrub = hinge('Scrub fold', .52, -1.06)
    grass('Thyme scrub', 0, 0, .50, .16, scrub, 30)


def threshold():
    """Póvoa de Varzim, Assisi and Solesmes, 1935-38: at the threshold."""
    rear = hinge('Umbrian hillside fold', 1.22, 1.42)
    canopy('Umbrian hills', 0, .03, 2.18, .62, rear, 'olive_light', 3)
    # Assisi above the valley: the basilica's long nave and bell tower.
    house('Basilica of Saint Francis', -.20, .004, .70, .44, rear, 'paper_light', 'stone', 1, 4, 'pitched', 'stone', 2)
    card('Basilica bell tower', .24, .002, .14, .78, rear, 'paper_light')
    polygon('Tower cap', [(.16, .78), (.32, .78), (.24, .88)], .010, -.002, 'stone', rear)
    for xx in (-.86, -.62, .62, .88):
        cypress('Umbrian cypress', xx, -.010, .82, rear, int(xx * 100))
    chapel = hinge('Chapel portal fold', 1.17, 1.02)
    r, spring = .55, 1.0
    for x in (-.64, .64):
        card('Chapel pier', x, 0, .18, spring, chapel, 'stone')
        for z in (.08, .21, .95):
            box('Chapel capital', (x, -.012, z), (.27, .042, .05), 'paper_light', chapel, .004)
    for i in range(28):
        a, b = i * math.pi / 28, (i + 1) * math.pi / 28
        polygon('Chapel arch stone', [(r * math.cos(a), spring + r * math.sin(a)), (r * math.cos(b), spring + r * math.sin(b)), ((r + .17) * math.cos(b), spring + (r + .17) * math.sin(b)), ((r + .17) * math.cos(a), spring + (r + .17) * math.sin(a))], .025, 0, 'paper' if i % 2 else 'stone', chapel)
    polygon('Chapel pediment', [(-.84, 1.56), (.84, 1.56), (0, 1.88)], .020, .026, 'paper', chapel)
    line('Stone cross upright', (0, -.017, 1.62), (0, -.017, 1.84), .023, 'gilt_dark', chapel)
    line('Stone cross arm', (-.08, -.017, 1.76), (.08, -.017, 1.76), .022, 'gilt_dark', chapel)
    stairs = hinge('Chapel steps fold', 1.14, .42)
    steps('Chapel stair', 0, 0, 1.06, .34, stairs, 6)
    lectern = hinge('Solesmes lectern fold', 1.86, -.10)
    line('Lectern stem', (0, 0, 0), (0, 0, .50), .022, 'bark', lectern)
    polygon('Lectern desk', [(-.20, .48), (.20, .48), (.18, .56), (-.18, .56)], .012, -.004, 'bark', lectern)
    polygon('Chant book', [(-.24, .55), (0, .58), (.24, .55), (.24, .78), (0, .80), (-.24, .78)], .008, -.012, 'paper_light', lectern)
    for side in (-1, 1):
        for k in range(4):
            line('Neume stave', (side * .03, -.018, .60 + k * .045), (side * .21, -.018, .595 + k * .045), .003, 'rust', lectern)
    visitor = hinge('Simone at the threshold fold', .62, -.12)
    person('Simone at the threshold', 0, 0, .72, visitor, 'beret', True, True, None)
    poem = hinge('Herbert poem fold', 1.32, -.66)
    letter('Love (III) by George Herbert', 0, 0, .30, .28, poem, 33)
    candle = hinge('Votive candles fold', .62, -1.02)
    candles('Votive candles', 0, 0, 5, candle)
    court = hinge('Cloister paving fold', 1.22, -1.30)
    paving('Cloister flags', 0, 0, 2.26, court, 41)
    cyp = hinge('Chapel cypress fold', 2.16, .58)
    cypress('Chapel cypress', 0, 0, 1.15, cyp, 7)


def force():
    """1939-40: the Iliad essay, and the flight from Paris to Marseille."""
    rear = hinge('Ancient wall fold', 1.22, 1.42)
    polygon('Broken Troy wall', [(-1.04, 0), (1.04, 0), (1.04, 1.02), (.85, 1.02), (.85, 1.22), (.58, 1.22), (.58, 1.03), (.23, 1.03), (.23, 1.28), (-.08, 1.28), (-.08, 1.08), (-.40, 1.08), (-.40, 1.20), (-.74, 1.20), (-.74, 1.03), (-1.04, 1.03)], .030, 0, 'paper', rear)
    for j in range(7):
        z = .09 + j * .135
        line('Ancient stone course', (-1.02, -.022, z), (1.02, -.022, z), .005, 'paper_shadow', rear)
        for i in range(7):
            x = -.92 + i * .30 + (j % 2) * .15
            if x < 1:
                line('Ancient stone joint', (x, -.023, z), (x, -.023, z + .13), .004, 'paper_shadow', rear)
    # A Greek frieze: helmeted warriors facing each other, cut in silhouette.
    for side in (-1, 1):
        cx = side * .40
        polygon('Frieze shield', [(cx + .10 * math.cos(a), .62 + .10 * math.sin(a)) for a in [k * math.tau / 24 for k in range(24)]], .006, -.030, 'rust', rear)
        polygon('Frieze helmet', [(cx - .05 * side, .76), (cx + .07 * side, .76), (cx + .06 * side, .86), (cx, .90), (cx - .04 * side, .86), (cx - .06 * side, .96)], .006, -.030, 'rust', rear)
        line('Frieze spear', (cx - .02 * side, -.034, .45), (cx + .18 * side, -.034, .98), .008, 'rust', rear)
    station = hinge('Railway station fold', 1.17, 1.02)
    for x in (-.80, .80):
        card('Platform iron column', x, 0, .06, 1.62, station, 'ink_soft')
        line('Station brace', (x, 0, 1.12), (x * .30, 0, 1.60), .025, 'ink_soft', station)
    polygon('Station canopy', [(-.96, 1.61), (.96, 1.61), (.86, 1.79), (-.86, 1.79)], .027, 0, 'slate', station)
    text('Station name', 'GARE DE LYON', (0, -.030, 1.69), .07, 'paper_light', station)
    line('Clock hanger', (0, 0, 1.30), (0, 0, 1.62), .020, 'ink_soft', station)
    clock_face('Station clock', 0, -.016, 1.20, .21, station)
    train = hinge('Carriage fold', 1.17, .40)
    card('Railway carriage', 0, 0, 1.76, .64, train, 'leaf_deep', .06)
    polygon('Carriage roof', [(-.90, .70), (.90, .70), (.84, .78), (-.84, .78)], .014, -.004, 'slate', train)
    for x in (-.59, -.20, .20, .59):
        window('Carriage window', x, -.018, .32, .24, .22, train)
    for x in (-.60, -.36, .36, .60):
        disk('Carriage wheel', x, -.016, .08, .08, 'ink_soft', train)
    travellers = hinge('Displaced travellers fold', .66, -.16)
    person('Simone leaving Paris', -.20, 0, .70, travellers, 'beret', True, True, 'case')
    person('Her mother', .14, -.01, .66, travellers, 'bob', False, True, None)
    family = hinge('Refugee family fold', 1.62, -.10)
    person('Father', -.16, 0, .76, family, 'cap', False, False, 'case')
    person('Child', .12, -.01, .44, family, 'bob', False, False, None)
    cases = hinge('Luggage fold', 2.10, -.56)
    crate('Trunk', -.06, 0, .28, cases, 'tobacco')
    card('Hat box', .18, -.006, .14, .12, cases, 'rust')
    track = hinge('Platform track fold', 1.22, -1.30)
    rails('Platform rails', 0, 0, 2.26, track)
    tufts = hinge('Platform weeds fold', .60, -1.08)
    grass('Platform weeds', 0, 0, .44, .12, tufts, 44)


def attention():
    """Marseille and the Ardèche, 1940-42: the work of attention."""
    rear = hinge('Marseille hill fold', 1.22, 1.42)
    polygon('Garde hill', [(-1.1, 0), (1.1, 0), (1.1, .30), (.42, .52), (.10, .66), (-.30, .54), (-1.1, .34)], .012, .02, 'paper_shadow', rear)
    # Notre-Dame de la Garde: nave, belfry and gilded Virgin above the port.
    house('Basilica nave', .06, .006, .36, .26, rear, 'stone', 'stone', 1, 3, 'flat', 'stone', 4)
    card('Belfry', .30, .004, .12, .62, rear, 'stone', .40)
    polygon('Belfry crown', [(.24, 1.02), (.36, 1.02), (.33, 1.10), (.27, 1.10)], .010, .002, 'stone', rear)
    polygon('Gilded Virgin', [(.285, 1.10), (.315, 1.10), (.31, 1.22), (.30, 1.25), (.29, 1.22)], .008, -.002, 'brass', rear)
    for i, (x, h) in enumerate([(-.90, .44), (-.62, .54), (-.34, .40), (.62, .46), (.90, .38)]):
        house('Vieux-Port house', x, -.012, .28, h, rear, 'ochre' if i % 2 else 'ochre_light', 'terracotta', 2, 2, 'pitched', 'sea', i + 10)
    harbour = hinge('Harbour boat fold', 1.12, 1.02)
    waves('Vieux-Port water', 0, -.010, 1.80, .16, harbour, 5)
    polygon('Pointu hull', [(-.78, .26), (.78, .26), (.60, .08), (-.58, .08)], .026, 0, 'sea', harbour)
    line('Gunwale', (-.78, -.016, .25), (.78, -.016, .25), .014, 'paper_light', harbour)
    line('Mast', (0, 0, .26), (0, 0, 1.80), .025, 'bark', harbour)
    polygon('Lateen sail', [(.04, .40), (.04, 1.66), (.76, .40)], .009, 0, 'paper_light', harbour)
    polygon('Fore sail', [(-.06, .42), (-.06, 1.46), (-.64, .42)], .009, .035, 'ochre_light', harbour)
    vines = hinge('Ardèche vineyard fold', 1.50, .34)
    for x in (-.62, 0, .62):
        line('Vine stake', (x, .015, 0), (x, .015, .82), .022, 'bark', vines)
    for z in (.32, .62):
        line('Vine wire', (-.66, .01, z), (.66, .01, z), .006, 'ink_soft', vines)
    rng = random.Random(9)
    for x in (-.46, .04, .50):
        for k in range(7):
            a = rng.uniform(0, math.tau)
            bx, bz = x + .14 * math.cos(a), .58 + .12 * math.sin(a)
            leaf_shape('Vine leaf', (x, .48), (bx, bz), .05, -.012 - .002 * k, 'leaf' if k % 2 else 'leaf_deep', vines)
        for dx, dz in ((0, 0), (.04, .03), (-.04, .03), (.02, -.05), (-.02, -.05), (0, -.09)):
            disk('Grape', x + dx, -.028, .36 + dz, .028, 'night', vines, 12)
    study = hinge('Writing table fold', .64, -.16)
    desk('Writing table', 0, 0, 0, study, 1.02)
    person('Simone writing her notebooks', -.26, -.023, .68, study, 'bob', True, False, None)
    letter('Notebook of attention', .06, -.026, .26, .20, study, 52)
    picker = hinge('Grape harvest fold', 1.90, -.20)
    person('Grape picker', 0, 0, .72, picker, 'scarf', False, False, 'basket')
    quay = hinge('Quay edge fold', 1.22, -1.30)
    kerb('Quay stones', 0, 0, 2.26, quay, 61)
    baskets = hinge('Harvest baskets fold', .70, -1.02)
    for k, dx in enumerate((-.14, .14)):
        polygon('Harvest basket', [(dx - .12, 0), (dx + .12, 0), (dx + .15, .14), (dx - .15, .14)], .010, -.004 * k, 'flower', baskets)
        for j in range(5):
            disk('Basket grape', dx - .08 + j * .04, -.012 - .004 * k, .16, .024, 'night', baskets, 10)


def roots():
    """New York and London, 1942-43: what gives us roots."""
    rear = hinge('Two cities fold', 1.22, 1.42)
    # New York on the left: setback towers and a needle spire.
    for x, w, h in ((-.92, .18, .82), (-.72, .20, 1.10), (-.50, .18, .76)):
        polygon('Manhattan tower', [(x - w / 2, 0), (x + w / 2, 0), (x + w / 2, h * .80), (x + w * .32, h * .80), (x + w * .32, h * .92), (x - w * .32, h * .92), (x - w * .32, h * .80), (x - w / 2, h * .80)], .012, 0, 'night', rear)
        for k in range(int(h / .09)):
            line('Lit floor', (x - w * .36, -.010, .06 + k * .08), (x + w * .36, -.010, .06 + k * .08), .006, 'flame', rear)
    line('Empire spire', (-.72, 0, 1.01), (-.72, 0, 1.24), .012, 'night', rear)
    waves('Atlantic between', -.05, -.006, .38, .14, rear, 11)
    # London on the right: Westminster's clock tower and terraces.
    card('Elizabeth Tower', .58, 0, .14, .92, rear, 'ochre_light')
    polygon('Tower spire', [(.50, .92), (.66, .92), (.58, 1.14)], .010, -.002, 'slate', rear)
    disk('Tower clock face', .58, -.010, .80, .045, 'paper_light', rear, 24)
    house('Westminster terrace', .88, .004, .30, .52, rear, 'ochre_light', 'slate', 2, 2, 'pitched', 'slate', 5)
    house('Whitehall terrace', .26, .004, .30, .46, rear, 'stone', 'slate', 2, 2, 'pitched', 'slate', 6)
    homes = hinge('Rooted houses fold', 1.42, 1.02)
    for x, w, h in ((-.50, .40, .74), (0, .50, .96), (.52, .42, .82)):
        for sign in (-1, 1):
            line('Branching root', (x, 0, .40), (x + sign * w * .42, 0, .04), .032, 'bark', homes)
            line('Fine root', (x + sign * w * .20, 0, .22), (x + sign * w * .49, 0, .13), .013, 'bark', homes)
        polygon('Rooted house wall', [(x - w / 2, .36), (x + w / 2, .36), (x + w / 2, h + .36), (x, h + .64), (x - w / 2, h + .36)], .019, 0, 'paper', homes)
        polygon('House roof', [(x - w * .56, h + .36), (x, h + .67), (x + w * .56, h + .36), (x + w * .48, h + .31), (x, h + .58), (x - w * .48, h + .31)], .020, -.008, 'slate', homes)
        window('Rooted home window', x, -.017, .64, w * .38, .27, homes)
    liner = hinge('Atlantic crossing fold', 1.13, .34)
    waves('Crossing swell', 0, -.020, 1.70, .12, liner, 3)
    polygon('Ocean liner hull', [(-.76, .30), (.76, .30), (.56, .06), (-.55, .06)], .02, 0, 'ink_soft', liner)
    box('Liner upper deck', (0, 0, .38), (1.04, .025, .17), 'paper_light', liner, .004)
    for x in (-.28, 0, .28):
        card('Steam funnel', x, .005, .12, .30, liner, 'rust', .44)
        line('Funnel band', (x - .06, -.004, .70), (x + .06, -.004, .70), .02, 'ink', liner)
    for x in (-.48, -.31, -.14, .03, .20, .37, .54):
        disk('Liner porthole', x, -.020, .22, .026, 'brass', liner, 16)
    office = hinge('Free French office fold', .62, -.18)
    desk('Office desk', 0, 0, 0, office, 1.0)
    person('Simone drafting', -.26, -.024, .70, office, 'bob', True, False, None)
    letter('The Need for Roots', .06, -.026, .26, .22, office, 64)
    tree = hinge('Rooted tree fold', 2.10, .30)
    broadleaf('Rooted oak', 0, 0, .96, tree, 12, .34)
    for sign in (-1, 1):
        line('Visible root', (0, -.004, .04), (sign * .22, -.004, .012), .012, 'bark', tree)
    walker = hinge('Londoner fold', 1.62, -.30)
    person('Londoner', 0, 0, .74, walker, 'short', False, True, 'paper')
    harbour = hinge('Harbour water fold', 1.22, -1.28)
    waves('Thames water', 0, 0, 2.24, .14, harbour, 8)
    bollards = hinge('Quay bollards fold', .52, -1.02)
    for k in range(3):
        card('Bollard', -.12 + k * .12, -.004 * k, .06, .12, bollards, 'ink_soft')


def unfinished():
    """London and Ashford, 1943: the unfinished task."""
    rear = hinge('Kentish fields fold', 1.22, 1.42)
    polygon('Kentish downs', [(-1.1, 0), (1.1, 0), (1.1, .46), (.6, .62), (.1, .50), (-.4, .66), (-1.1, .48)], .012, .02, 'olive_light', rear)
    for xx in (-.70, .50):
        # Oast houses: round kilns with white cowls, a Kentish signature.
        card('Oast kiln', xx, .004, .20, .44, rear, 'brick')
        polygon('Oast roof', [(xx - .12, .44), (xx + .12, .44), (xx, .70)], .010, .002, 'night', rear)
        polygon('Oast cowl', [(xx - .03, .70), (xx + .05, .70), (xx + .06, .80), (xx, .82), (xx - .03, .78)], .008, -.002, 'chalk', rear)
        house('Oast barn', xx + .22, .006, .26, .34, rear, 'chalk', 'night', 1, 1, 'pitched', 'night', int(xx * 10))
    for xx in (-.98, -.20, .92):
        broadleaf('Hedgerow oak', xx, -.008, .62, rear, int(xx * 33 + 50), .30)
    window_h = hinge('Sanatorium window fold', 1.15, 1.02)
    for x in (-.74, .74):
        card('Window frame pier', x, 0, .16, 1.76, window_h, 'paper')
    for z in (.09, 1.68):
        box('Window lintel', (0, 0, z), (1.62, .033, .14), 'paper', window_h, .008)
    for x in (-.34, 0, .34):
        line('Glazing bar', (x, -.012, .16), (x, -.012, 1.61), .022, 'stone', window_h)
    for z in (.64, 1.16):
        line('Glazing rail', (-.66, -.012, z), (.66, -.012, z), .021, 'stone', window_h)
    for sign in (-1, 1):
        pts = [(sign * .64, .16), (sign * .50, .22), (sign * .57, .66), (sign * .46, 1.18), (sign * .41, 1.61), (sign * .66, 1.61)]
        polygon('Paper curtain', pts, .009, -.032, 'paper_light', window_h)
    polygon('Window sill vase', [(-.06, .16), (.06, .16), (.05, .32), (-.05, .32)], .008, -.036, 'sea', window_h)
    for k in range(5):
        leaf_shape('Sill flower stem', (0, .30), (-.14 + k * .07, .52 + .04 * (k % 2)), .02, -.040, 'leaf', window_h)
        disk('Sill flower', -.14 + k * .07, -.044, .53 + .04 * (k % 2), .025, 'flower', window_h, 12)
    table = hinge('Unfinished table fold', 1.10, .20)
    desk('Unfinished desk', 0, 0, 0, table, 1.40)
    chair('Empty chair', -.52, -.020, .82, table, 1)
    for k in range(3):
        letter('Unfinished page', -.16 + k * .16, -.028 - .003 * k, .20, .16, table, 80 + k)
    polygon('Tea cup', [(.30, .64), (.40, .64), (.38, .71), (.32, .71)], .008, -.030, 'chalk', table)
    pages = hinge('Last manuscript fold', .58, -.30)
    letter('Last manuscript', 0, 0, .40, .44, pages, 90)
    loose = hinge('Loose leaf fold', 1.62, -.46)
    letter('Loose leaf', 0, 0, .34, .26, loose, 91)
    bed = hinge('Garden bed fold', 1.74, -1.02)
    flower_hedge('Ashford garden bed', 0, 0, .90, .18, bed, 12)
    wall = hinge('Garden wall fold', 1.22, -1.30)
    stone_wall('Brick garden wall', 0, 0, 2.24, .12, wall, 19, 'brick')
    tree = hinge('Quiet laurel fold', 2.14, .40)
    laurel_bush('Quiet laurel', 0, 0, .82, tree, 93)


def legacy():
    """1947 onward: the pages keep opening."""
    rear = hinge('Library fold', 1.22, 1.42)
    bookcase('Library shelves', 0, 0, 2.10, 1.24, rear, 47)
    books = hinge('Posthumous books fold', 1.12, 1.02)
    titled_book('Gravity and Grace', -.62, 0, .44, 1.06, books, 'night', 'La Pesanteur\net la grâce', '1947', 1)
    titled_book('The Need for Roots', 0, -.004, .52, 1.42, books, 'leaf_deep', "L'Enracinement", '1949', 2)
    titled_book('Waiting for God', .62, 0, .46, 1.16, books, 'rust', 'Attente\nde Dieu', '1950', 3, 'chalk')
    opening = hinge('Open future pages fold', 1.12, .30)
    polygon('Open book wings', [(-.72, 0), (0, .06), (.72, 0), (.72, .70), (.38, .77), (0, .69), (-.38, .77), (-.72, .70)], .014, 0, 'paper', opening)
    line('Open book crease', (0, -.012, .06), (0, -.012, .69), .010, 'tobacco', opening)
    for sign in (-1, 1):
        for i in range(7):
            stroke('Printed line', sign * .09 if sign > 0 else -.61, .61 if sign > 0 else -.09, .18 + i * .068, -.013, opening, 'ink_soft', 100 + i + (10 if sign > 0 else 0), .004, .003)
    readers = hinge('Readers fold', .64, -.16)
    person('Young reader', -.14, 0, .62, readers, 'bob', True, False, 'book')
    person('Old reader', .18, -.01, .74, readers, 'short', True, True, 'book')
    student = hinge('Student fold', 1.66, -.10)
    chair('Reading chair', 0, 0, .80, student, -1)
    person('Student', .26, -.012, .66, student, 'scarf', False, False, 'paper')
    tree = hinge('Living olive fold', 1.98, .46)
    olive('Living olive', 0, 0, .90, tree, 103)
    pile = hinge('New editions fold', .80, -1.02)
    book_pile('New editions', 0, 0, .78, pile, 120)
    reading_lamp = hinge('Reading lamp fold', 1.70, -.90)
    line('Lamp stem', (0, 0, 0), (0, 0, .30), .012, 'brass', reading_lamp)
    polygon('Lamp shade', [(-.10, .26), (.10, .26), (.06, .36), (-.06, .36)], .010, -.004, 'leaf_deep', reading_lamp)
    polygon('Lamp foot', [(-.07, 0), (.07, 0), (.05, .03), (-.05, .03)], .010, -.004, 'brass', reading_lamp)
    floor = hinge('Library floor fold', 1.22, -1.30)
    paving('Library parquet', 0, 0, 2.26, floor, 77)
