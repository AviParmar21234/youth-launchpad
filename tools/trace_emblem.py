#!/usr/bin/env python3
"""Rebuild the Youth LaunchPad emblem (the bridge mark) as clean vector art.

The logo PNG has a bevelled, shadowed rendering, so a plain trace ripples.
Instead, the geometric parts are reconstructed from primitives measured on
the pixel data, and only the organic parts (the road and the three figures'
bodies) are traced, after smoothing.

  deck   gold crescent: circular arcs through its two tips and its apex
  arch   green crescent (same construction) + a ring concentric with the
         opening (the legs) + four rectangular piers hanging from the band
  heads  circles;  road, bodies  smoothed potrace curves

Input : site/images/logo-full.png
Output: site/images/emblem.svg  (parts grouped with ids for the hero animation)

Run: python3 tools/trace_emblem.py        (needs: pip install potracer)
"""
import math
from pathlib import Path

import numpy as np
import potrace
from PIL import Image
from scipy import ndimage
from skimage import color as skcolor

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "site/images/logo-full.png"
OUT_SVG = ROOT / "site/images/emblem.svg"
GREEN, GOLD = "#163a2b", "#bd9548"

# ----------------------------------------------------------------- masks
img = np.asarray(Image.open(SRC).convert("RGBA")).astype(np.float32) / 255.0
H, W = img.shape[:2]
hsv = skcolor.rgb2hsv(img[..., :3])
hue, sat, val = hsv[..., 0] * 360, hsv[..., 1], hsv[..., 2]
solid = img[..., 3] > 0.45
solid[530:] = False
gold = solid & (hue > 15) & (hue < 75) & (sat > 0.22)
green = solid & ~gold & (((hue > 80) & (hue < 200)) | (val < 0.3))


def disc(r):
    y, x = np.ogrid[-r:r + 1, -r:r + 1]
    return (x * x + y * y) <= r * r


def clean(m, r=3, blur=1.2):
    m = ndimage.binary_closing(m, structure=disc(r))
    m = ndimage.binary_opening(m, structure=disc(r))
    return ndimage.gaussian_filter(m.astype(np.float32), blur) > 0.5


gold = clean(gold)
green = clean(green)
green &= ~ndimage.binary_dilation(gold, iterations=1)


def parts(mask, min_area=250):
    lab, n = ndimage.label(mask)
    out = []
    for i in range(1, n + 1):
        m = lab == i
        if m.sum() < min_area:
            continue
        ys, xs = np.nonzero(m)
        out.append(dict(mask=m, area=int(m.sum()), cx=xs.mean(), cy=ys.mean(), x0=int(xs.min()), x1=int(xs.max()), y0=int(ys.min()), y1=int(ys.max())))
    return sorted(out, key=lambda p: -p["area"])


gp = parts(gold)
deck_m, cbody_m, chead_m = gp[0], *sorted(gp[1:3], key=lambda p: -p["cy"])
grp = parts(green)
arch_m = grp[0]
road_m = max(grp[1:], key=lambda p: p["area"])
figs = [p for p in grp[1:] if p is not road_m]
left = sorted([p for p in figs if p["cx"] < W / 2], key=lambda p: p["cy"])
right = sorted([p for p in figs if p["cx"] >= W / 2], key=lambda p: p["cy"])
lhead_m, lbody_m = left[0], left[1]
rhead_m, rbody_m = right[0], right[1]

YY, XX = np.mgrid[0:H, 0:W]


# ----------------------------------------------------------------- helpers
def f(v):
    return f"{v:.1f}"


def runs(arr):
    idx = np.nonzero(arr)[0]
    if not len(idx):
        return []
    out, s, p = [], idx[0], idx[0]
    for v in idx[1:]:
        if v != p + 1:
            out.append((int(s), int(p)))
            s = v
        p = v
    out.append((int(s), int(p)))
    return out


def circle3(p1, p2, p3):
    """Circle through three points -> (cx, cy, r)."""
    ax, ay = p1
    bx, by = p2
    cx, cy = p3
    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / d
    uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / d
    return ux, uy, math.hypot(ax - ux, ay - uy)


def fit_circle(pts):
    pts = np.asarray(pts, float)
    x, y = pts[:, 0], pts[:, 1]
    A = np.c_[2 * x, 2 * y, np.ones(len(x))]
    c = np.linalg.lstsq(A, x * x + y * y, rcond=None)[0]
    return c[0], c[1], math.sqrt(c[2] + c[0] ** 2 + c[1] ** 2)


def inside(c):
    return (XX - c[0]) ** 2 + (YY - c[1]) ** 2 <= c[2] ** 2


def iou(a, b):
    return float((a & b).sum() / (a | b).sum())


def tip(mask, x):
    col = np.nonzero(mask[:, x])[0]
    return (float(x), float(col.mean()))


def circle_y(c, x, top=True):
    dy = math.sqrt(max(c[2] ** 2 - (x - c[0]) ** 2, 0))
    return c[1] - dy if top else c[1] + dy


def band(mask, top_pts, under_pts, margin=12):
    """A curved band: outer edge and underside are separate least-squares
    circles (so the thickness profile follows the original), ending in short
    flat tips at the mask's extreme columns."""
    cols = np.nonzero(mask.any(axis=0))[0]
    xl, xr = int(cols.min()) + 1, int(cols.max())
    outer = fit_circle([p for p in top_pts if xl + margin < p[0] < xr - margin])
    inner = fit_circle([p for p in under_pts if xl + margin < p[0] < xr - margin])
    tl, tr = (xl, circle_y(outer, xl)), (xr, circle_y(outer, xr))
    bl, br = (xl, max(circle_y(inner, xl), tl[1] + 3)), (xr, max(circle_y(inner, xr), tr[1] + 3))
    model = inside(outer) & ~inside(inner) & (XX >= xl) & (XX <= xr) & (YY < outer[1])
    path = (f"M{f(tl[0])},{f(tl[1])} A{f(outer[2])},{f(outer[2])} 0 0 1 {f(tr[0])},{f(tr[1])} "
            f"L{f(br[0])},{f(br[1])} A{f(inner[2])},{f(inner[2])} 0 0 0 {f(bl[0])},{f(bl[1])}Z")
    return outer, inner, model, path, (tl, tr)


def col_edges(mask, xs, which, limit=None):
    pts = []
    for x in xs:
        col = np.nonzero(mask[:, x])[0]
        if limit is not None:
            col = col[col < limit]
        if len(col):
            pts.append((x, col.min() if which == "top" else col.max() + 1))
    return pts


def arc_to(p0, pm, p1):
    """SVG arc from p0 to p1 passing through pm (as a circle3 arc)."""
    c = circle3(p0, pm, p1)
    cross = (p1[0] - p0[0]) * (c[1] - p0[1]) - (p1[1] - p0[1]) * (c[0] - p0[0])
    sweep = 1 if cross > 0 else 0
    return f"A{f(c[2])},{f(c[2])} 0 0 {sweep} {f(p1[0])},{f(p1[1])}"   # every edge arc is under 180 degrees


def body_shape(mask):
    """A figure's body: four corners (two raised arm tips, two base corners)
    joined by circular arcs through the measured mid-point of each edge."""
    from skimage import measure
    m = ndimage.gaussian_filter(mask.astype(np.float32), 1.5) > 0.5
    contour = max(measure.find_contours(np.pad(m, 1).astype(float), 0.5), key=len) - 1
    pts = contour[:, ::-1]                       # (x, y)
    poly = measure.approximate_polygon(pts, tolerance=6)   # coarse: one vertex per real corner
    if np.allclose(poly[0], poly[-1]):
        poly = poly[:-1]
    n = len(poly)
    angles = []
    for i in range(n):
        a, b, c = poly[i - 1], poly[i], poly[(i + 1) % n]
        v1, v2 = a - b, c - b
        cosang = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-9)
        angles.append(math.degrees(math.acos(np.clip(cosang, -1, 1))))
    corners = sorted(sorted(range(n), key=lambda i: angles[i])[:4])   # 4 sharpest, in contour order
    # locate each corner on the dense contour, and take the contour midpoint between consecutive corners
    idx = [int(np.argmin(np.hypot(pts[:, 0] - poly[i][0], pts[:, 1] - poly[i][1]))) for i in corners]
    cmds = [f"M{f(pts[idx[0]][0])},{f(pts[idx[0]][1])}"]
    for k in range(4):
        i0, i1 = idx[k], idx[(k + 1) % 4]
        if i1 > i0:
            seg = pts[i0:i1 + 1]
        else:
            seg = np.vstack([pts[i0:], pts[:i1 + 1]])
        pm = seg[len(seg) // 2]
        p0, p1 = pts[i0], pts[i1]
        # nearly straight edges become lines
        c = circle3(tuple(p0), tuple(pm), tuple(p1))
        if c[2] > 4000:
            cmds.append(f"L{f(p1[0])},{f(p1[1])}")
        else:
            cmds.append(arc_to(tuple(p0), tuple(pm), tuple(p1)))
    cmds.append("Z")
    return "".join(cmds)


# ----------------------------------------------------------------- deck
dm = deck_m["mask"]
xs = range(deck_m["x0"], deck_m["x1"] + 1, 2)
deck_outer, deck_inner, deck_model, deck_path, (tl, tr) = band(dm, col_edges(dm, xs, "top", limit=360), col_edges(dm, xs, "bot", limit=360))
print(f"deck   iou={iou(deck_model, dm):.3f}  tips=({tl[0]:.0f},{tl[1]:.0f})-({tr[0]:.0f},{tr[1]:.0f})")
for x in (60, 200, 443, 700, 860):
    col = np.nonzero(dm[:, x])[0]
    print(f"   x={x:3d} orig top/bot {col.min()}/{col.max() + 1}  model {circle_y(deck_outer, x):.0f}/{circle_y(deck_inner, x):.0f}")

# ----------------------------------------------------------------- arch
am = arch_m["mask"]
GROUND = arch_m["y1"] + 1
midx = W / 2
bars = runs(am[GROUND - 15, :])
left_bars = [b for b in bars if b[1] < midx]
right_bars = [b for b in bars if b[0] > midx]
piers = left_bars[:-1] + right_bars[1:]
leg_l, leg_r = left_bars[-1], right_bars[0]

# band: outer edge from every column; underside from columns where nothing hangs below it
top_pts = col_edges(am, range(arch_m["x0"], arch_m["x1"] + 1, 2), "top")
free_cols = []
for i in range(len(bars) - 1):
    if bars[i] is leg_l:
        continue
    free_cols += list(range(bars[i][1] + 4, bars[i + 1][0] - 3, 2))
free_cols += list(range(arch_m["x0"], bars[0][0] - 3, 2)) + list(range(bars[-1][1] + 4, arch_m["x1"] + 1, 2))
under_pts = [(x, runs(am[:, x])[0][1] + 1) for x in free_cols if runs(am[:, x])]
band_outer, band_inner, band_model, band_path, (bl, br) = band(am, top_pts, under_pts)
print(f"band   tips=({bl[0]:.0f},{bl[1]:.0f})-({br[0]:.0f},{br[1]:.0f})")
for x in (20, 106, 300, 443, 600, 778, 870):
    r = runs(am[:, x])
    print(f"   x={x:3d} orig top/under {r[0][0]}/{r[0][1] + 1}  model {circle_y(band_outer, x):.0f}/{circle_y(band_inner, x):.0f}")

# opening: circle through the legs' inner edges
op_pts = []
for y in range(GROUND - 4, 0, -2):
    r = runs(am[y, :])
    lefts = [b for b in r if b[1] < midx]
    rights = [b for b in r if b[0] > midx]
    if lefts and rights and lefts[-1][1] > leg_l[0] - 40 and rights[0][0] < leg_r[1] + 40:
        op_pts.append((lefts[-1][1] + 0.5, y))
        op_pts.append((rights[0][0] - 0.5, y))
opening = fit_circle(op_pts)
ocx, ocy, ri = opening[0], opening[1], opening[2]
# ring outer radius from the legs' outer edges at the ground
ro = ((ocx - leg_l[0]) + (leg_r[1] + 1 - ocx)) / 2
TOP_IN_BAND = circle_y(band_inner, ocx) - 10        # a line safely inside the band
hx = math.sqrt(max(ro * ro - (TOP_IN_BAND - ocy) ** 2, 0))
ring_path = (f"M{f(ocx - ro)},{f(GROUND)} A{f(ro)},{f(ro)} 0 0 1 {f(ocx - hx)},{f(TOP_IN_BAND)} "
             f"L{f(ocx + hx)},{f(TOP_IN_BAND)} A{f(ro)},{f(ro)} 0 0 1 {f(ocx + ro)},{f(GROUND)} "
             f"L{f(ocx + ri)},{f(GROUND)} A{f(ri)},{f(ri)} 0 1 0 {f(ocx - ri)},{f(GROUND)}Z")
ring_model = inside((ocx, ocy, ro)) & ~inside((ocx, ocy, ri)) & (YY <= GROUND) & (YY >= TOP_IN_BAND)

pier_paths, pier_model = [], np.zeros_like(am)
for (x0, x1) in piers:
    x1 += 1
    top = min(circle_y(band_inner, x0), circle_y(band_inner, x1)) - 5
    pier_paths.append(f"M{f(x0)},{f(top)} H{f(x1)} V{f(GROUND)} H{f(x0)}Z")
    pier_model[int(top):GROUND + 1, x0:x1] = True

arch_model = band_model | pier_model | ring_model
print(f"arch   iou={iou(arch_model, am):.3f}  piers={piers}  ring centre=({ocx:.0f},{ocy:.0f}) r_in={ri:.0f} r_out={ro:.0f}  ground={GROUND}")

# ----------------------------------------------------------------- organic parts
SCALE = 4


def trace(mask, blur):
    m = ndimage.gaussian_filter(mask.astype(np.float32), blur) > 0.5
    big = ndimage.zoom(m.astype(np.float32), SCALE, order=1) > 0.5
    path = potrace.Bitmap(~big).trace(turdsize=20, turnpolicy=potrace.POTRACE_TURNPOLICY_MINORITY,
                                      alphamax=1.0, opticurve=True, opttolerance=1.0)
    d = []
    for curve in path:
        d.append(f"M{f(curve.start_point.x / SCALE)},{f(curve.start_point.y / SCALE)}")
        for seg in curve.segments:
            if seg.is_corner:
                d.append(f"L{f(seg.c.x / SCALE)},{f(seg.c.y / SCALE)} L{f(seg.end_point.x / SCALE)},{f(seg.end_point.y / SCALE)}")
            else:
                d.append(f"C{f(seg.c1.x / SCALE)},{f(seg.c1.y / SCALE)} {f(seg.c2.x / SCALE)},{f(seg.c2.y / SCALE)} {f(seg.end_point.x / SCALE)},{f(seg.end_point.y / SCALE)}")
        d.append("Z")
    return "".join(d)


road_path = trace(road_m["mask"], blur=2.2)
body_paths = {k: body_shape(p["mask"]) for k, p in (("l", lbody_m), ("c", cbody_m), ("r", rbody_m))}


def head(p):
    r = math.sqrt(p["area"] / math.pi)
    return f"M{f(p['cx'] - r)},{f(p['cy'])} a{f(r)},{f(r)} 0 1,0 {f(2 * r)},0 a{f(r)},{f(r)} 0 1,0 {f(-2 * r)},0Z"


# ----------------------------------------------------------------- write
allm = [deck_m, arch_m, road_m, lhead_m, lbody_m, chead_m, cbody_m, rhead_m, rbody_m]
x0 = min(p["x0"] for p in allm) - 6
y0 = min(p["y0"] for p in allm) - 6
x1 = max(p["x1"] for p in allm) + 6
y1 = max(p["y1"] for p in allm) + 6

svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0} {y0} {x1 - x0} {y1 - y0}" role="img" aria-label="The Youth LaunchPad Foundation emblem">',
       f'  <g id="deck"><path fill="{GOLD}" d="{deck_path}"/></g>',
       f'  <g id="arch" fill="{GREEN}">',
       f'    <path d="{band_path}"/>',
       f'    <path d="{ring_path}"/>']
for pp in pier_paths:
    svg.append(f'    <path d="{pp}"/>')
svg += ['  </g>',
        f'  <g id="road"><path fill="{GREEN}" d="{road_path}"/></g>',
        f'  <g id="fig-l" fill="{GREEN}"><path d="{head(lhead_m)}"/><path d="{body_paths["l"]}"/></g>',
        f'  <g id="fig-c" fill="{GOLD}"><path d="{head(chead_m)}"/><path d="{body_paths["c"]}"/></g>',
        f'  <g id="fig-r" fill="{GREEN}"><path d="{head(rhead_m)}"/><path d="{body_paths["r"]}"/></g>',
        '</svg>']
OUT_SVG.write_text("\n".join(svg))
print(f"viewBox {x0} {y0} {x1 - x0} {y1 - y0}; wrote {OUT_SVG.relative_to(ROOT)} ({OUT_SVG.stat().st_size // 1024} KB)")
