#!/usr/bin/env python3
"""Trace the Youth LaunchPad emblem (the bridge mark) from the logo PNG into
an SVG made of separate parts, so it stays sharp at any size and can be
animated piece by piece.

Input : site/images/logo-full.png  (transparent, keyed from source/NP logo.png)
Output: site/images/emblem.svg     (viewBox matches the traced region)
        tools/emblem-parts.json    (part id -> path data, used by build)

Run: python3 tools/trace_emblem.py
"""
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage
from skimage import measure

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "site/images/logo-full.png"
OUT_SVG = ROOT / "site/images/emblem.svg"
OUT_JSON = ROOT / "tools/emblem-parts.json"

GREEN = "#163a2b"
GOLD = "#bd9548"

img = np.asarray(Image.open(SRC).convert("RGBA")).astype(np.float32)
H, W = img.shape[:2]
# emblem = everything above the "THE" rule (~y 700 in the original, ~524 after crop)
EMBLEM_BOTTOM = 530
r, g, b, a = (img[..., i] for i in range(4))
solid = a > 110

# colour classes (bevel highlights are lighter tints of the same hue)
gold = solid & (r > b + 35) & (r > 95)
green = solid & ~gold & (g >= r - 8)
gold[EMBLEM_BOTTOM:] = False
green[EMBLEM_BOTTOM:] = False

# close small bevel gaps, drop specks
def clean(mask):
    mask = ndimage.binary_closing(mask, structure=np.ones((5, 5)))
    mask = ndimage.binary_opening(mask, structure=np.ones((3, 3)))
    mask = ndimage.binary_fill_holes(mask) if False else mask
    return mask

gold = clean(gold)
green = clean(green)


def components(mask, min_area=250):
    lab, n = ndimage.label(mask)
    out = []
    for i in range(1, n + 1):
        m = lab == i
        area = int(m.sum())
        if area < min_area:
            continue
        ys, xs = np.nonzero(m)
        out.append({
            "mask": m, "area": area,
            "cx": float(xs.mean()), "cy": float(ys.mean()),
            "x0": int(xs.min()), "x1": int(xs.max()), "y0": int(ys.min()), "y1": int(ys.max()),
        })
    return out


def to_path(mask, tol=0.75):
    """Trace a binary mask into an SVG path (outer + hole contours, evenodd)."""
    padded = np.pad(mask.astype(np.float32), 2)
    smooth = ndimage.gaussian_filter(padded, 0.8)
    d = []
    for c in measure.find_contours(smooth, 0.5):
        c = measure.approximate_polygon(c, tolerance=tol)
        if len(c) < 4:
            continue
        pts = [(x - 2, y - 2) for y, x in c]  # find_contours gives (row, col)
        d.append("M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + "Z")
    return " ".join(d)


def name_parts(parts, color):
    """Assign stable ids to components by position/size."""
    parts = sorted(parts, key=lambda p: -p["area"])
    named = {}
    if color == "gold":
        named["deck"] = parts[0]                     # the long arc
        rest = sorted(parts[1:], key=lambda p: p["cy"])
        named["fig-c-head"] = rest[0]
        named["fig-c-body"] = rest[1]
    else:
        named["arch"] = parts[0]                     # arch + piers
        rest = parts[1:]
        # road: the big shape low in the frame
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

# viewBox around everything, with a little breathing room
x0 = min(p["x0"] for p, _ in all_parts.values()) - 6
x1 = max(p["x1"] for p, _ in all_parts.values()) + 6
y0 = min(p["y0"] for p, _ in all_parts.values()) - 6
y1 = max(p["y1"] for p, _ in all_parts.values()) + 6

paths = {}
for pid, (part, color) in all_parts.items():
    d = to_path(part["mask"])
    paths[pid] = {"d": d, "fill": color}
    print(f"{pid:12s} area={part['area']:7d}  box=({part['x0']},{part['y0']})-({part['x1']},{part['y1']})")

OUT_JSON.write_text(json.dumps({"viewBox": [x0, y0, x1 - x0, y1 - y0], "paths": paths}, indent=1))

groups = {
    "deck": ["deck"],
    "arch": ["arch"],
    "road": ["road"],
    "fig-l": ["fig-l-head", "fig-l-body"],
    "fig-c": ["fig-c-head", "fig-c-body"],
    "fig-r": ["fig-r-head", "fig-r-body"],
}
svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0} {y0} {x1 - x0} {y1 - y0}" role="img" aria-label="The Youth LaunchPad Foundation emblem">']
for gid, ids in groups.items():
    svg.append(f'  <g id="{gid}">')
    for pid in ids:
        svg.append(f'    <path fill="{paths[pid]["fill"]}" fill-rule="evenodd" d="{paths[pid]["d"]}"/>')
    svg.append("  </g>")
svg.append("</svg>")
OUT_SVG.write_text("\n".join(svg))
print(f"viewBox {x0} {y0} {x1 - x0} {y1 - y0}; wrote {OUT_SVG.relative_to(ROOT)} ({OUT_SVG.stat().st_size // 1024} KB)")
