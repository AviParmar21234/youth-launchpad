#!/usr/bin/env python3
"""Trace the Youth LaunchPad emblem (the bridge mark) from the logo PNG into
an SVG made of separate parts, so it stays sharp at any size and can be
animated piece by piece.

Pipeline: classify pixels by hue (gold / green) -> clean each mask with
morphology and a light blur so bevel highlights and shadows don't ripple the
edge -> split into connected parts -> trace each part with potrace, which
emits smooth Bezier curves and keeps real corners sharp.

Input : site/images/logo-full.png  (transparent, keyed from source/NP logo.png)
Output: site/images/emblem.svg
        tools/emblem-parts.json    (part id -> path data)

Run: python3 tools/trace_emblem.py        (needs: pip install potracer)
"""
import json
from pathlib import Path

import numpy as np
import potrace
from PIL import Image
from scipy import ndimage
from skimage import color as skcolor

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "site/images/logo-full.png"
OUT_SVG = ROOT / "site/images/emblem.svg"
OUT_JSON = ROOT / "tools/emblem-parts.json"

GREEN = "#163a2b"
GOLD = "#bd9548"
SCALE = 3  # trace at 3x for smoother curves, then scale coordinates back

img = np.asarray(Image.open(SRC).convert("RGBA")).astype(np.float32) / 255.0
H, W = img.shape[:2]
EMBLEM_BOTTOM = 530  # everything above the "THE" rule

rgb, a = img[..., :3], img[..., 3]
hsv = skcolor.rgb2hsv(rgb)
hue, sat, val = hsv[..., 0] * 360, hsv[..., 1], hsv[..., 2]
solid = a > 0.45
solid[EMBLEM_BOTTOM:] = False

gold = solid & (hue > 15) & (hue < 75) & (sat > 0.22)
green = solid & ~gold & ((hue > 80) & (hue < 200) | (val < 0.3))


def clean(mask, radius=3):
    """Round off bevel ripple without eating corners: open/close with a disc,
    then a light blur re-thresholded at the midpoint."""
    y, x = np.ogrid[-radius:radius + 1, -radius:radius + 1]
    disc = (x * x + y * y) <= radius * radius
    m = ndimage.binary_closing(mask, structure=disc)
    m = ndimage.binary_opening(m, structure=disc)
    m = ndimage.gaussian_filter(m.astype(np.float32), 1.2) > 0.5
    return m


gold = clean(gold)
green = clean(green)
# gold wins where both claim a pixel (the deck sits in front of the arch)
green &= ~ndimage.binary_dilation(gold, iterations=1)


def components(mask, min_area=250):
    lab, n = ndimage.label(mask)
    out = []
    for i in range(1, n + 1):
        m = lab == i
        area = int(m.sum())
        if area < min_area:
            continue
        ys, xs = np.nonzero(m)
        out.append({"mask": m, "area": area, "cx": float(xs.mean()), "cy": float(ys.mean()),
                    "x0": int(xs.min()), "x1": int(xs.max()), "y0": int(ys.min()), "y1": int(ys.max())})
    return out


def upscale(mask):
    big = ndimage.zoom(mask.astype(np.float32), SCALE, order=1)
    return big > 0.5


def fmt(p):
    return f"{p.x / SCALE:.1f},{p.y / SCALE:.1f}"


def to_path(mask):
    """Trace a binary mask with potrace into an SVG path of Bezier curves."""
    # potracer treats nonzero as background, so hand it the inverse
    bmp = potrace.Bitmap(~upscale(mask))
    path = bmp.trace(turdsize=12, turnpolicy=potrace.POTRACE_TURNPOLICY_MINORITY,
                     alphamax=1.0, opticurve=True, opttolerance=0.6)
    d = []
    for curve in path:
        d.append("M" + fmt(curve.start_point))
        for seg in curve.segments:
            if seg.is_corner:
                d.append("L" + fmt(seg.c) + " L" + fmt(seg.end_point))
            else:
                d.append("C" + fmt(seg.c1) + " " + fmt(seg.c2) + " " + fmt(seg.end_point))
        d.append("Z")
    return "".join(d)


def name_parts(parts, which):
    parts = sorted(parts, key=lambda p: -p["area"])
    named = {}
    if which == "gold":
        named["deck"] = parts[0]
        rest = sorted(parts[1:], key=lambda p: p["cy"])
        named["fig-c-head"], named["fig-c-body"] = rest[0], rest[1]
    else:
        named["arch"] = parts[0]
        rest = parts[1:]
        road = max(rest, key=lambda p: p["area"])
        named["road"] = road
        rest = [p for p in rest if p is not road]
        left = sorted([p for p in rest if p["cx"] < W / 2], key=lambda p: p["cy"])
        right = sorted([p for p in rest if p["cx"] >= W / 2], key=lambda p: p["cy"])
        named["fig-l-head"], named["fig-l-body"] = left[0], left[1]
        named["fig-r-head"], named["fig-r-body"] = right[0], right[1]
    return named


gold_parts = name_parts(components(gold), "gold")
green_parts = name_parts(components(green), "green")
all_parts = {**{k: (v, GOLD) for k, v in gold_parts.items()}, **{k: (v, GREEN) for k, v in green_parts.items()}}

x0 = min(p["x0"] for p, _ in all_parts.values()) - 6
x1 = max(p["x1"] for p, _ in all_parts.values()) + 6
y0 = min(p["y0"] for p, _ in all_parts.values()) - 6
y1 = max(p["y1"] for p, _ in all_parts.values()) + 6

paths = {}
for pid, (part, fill) in all_parts.items():
    if pid.endswith("-head"):
        # heads are true circles: fit one instead of tracing pixels
        r = (part["area"] / np.pi) ** 0.5
        cx, cy = part["cx"], part["cy"]
        d = (f"M{cx - r:.2f},{cy:.2f} a{r:.2f},{r:.2f} 0 1,0 {2 * r:.2f},0 "
             f"a{r:.2f},{r:.2f} 0 1,0 {-2 * r:.2f},0Z")
    else:
        d = to_path(part["mask"])
    paths[pid] = {"d": d, "fill": fill}
    print(f"{pid:12s} area={part['area']:7d}  box=({part['x0']},{part['y0']})-({part['x1']},{part['y1']})")

OUT_JSON.write_text(json.dumps({"viewBox": [x0, y0, x1 - x0, y1 - y0], "paths": paths}, indent=1))

groups = {"deck": ["deck"], "arch": ["arch"], "road": ["road"],
          "fig-l": ["fig-l-head", "fig-l-body"], "fig-c": ["fig-c-head", "fig-c-body"], "fig-r": ["fig-r-head", "fig-r-body"]}
svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0} {y0} {x1 - x0} {y1 - y0}" role="img" aria-label="The Youth LaunchPad Foundation emblem">']
for gid, ids in groups.items():
    svg.append(f'  <g id="{gid}">')
    for pid in ids:
        svg.append(f'    <path fill="{paths[pid]["fill"]}" d="{paths[pid]["d"]}"/>')
    svg.append("  </g>")
svg.append("</svg>")
OUT_SVG.write_text("\n".join(svg))
print(f"viewBox {x0} {y0} {x1 - x0} {y1 - y0}; wrote {OUT_SVG.relative_to(ROOT)} ({OUT_SVG.stat().st_size // 1024} KB)")
