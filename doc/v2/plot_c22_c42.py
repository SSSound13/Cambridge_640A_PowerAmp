"""Draw top projections of the 47 uF capacitors against the v2 PCB.

Run from the repository root with: python doc/v2/plot_c22_c42.py
Uses only the KiCad PCB and matplotlib. Coordinates are millimetres.
"""

import json
import math
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle


ROOT = Path(__file__).resolve().parents[2]
PCB = ROOT / "640A_PowerAmp.kicad_pcb"
OUT = Path(__file__).resolve().parent


def parse(text):
    tokens = iter(re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+', text))

    def section():
        result = []
        for item in tokens:
            if item == ")":
                return result
            result.append(section() if item == "(" else json.loads(item) if item.startswith('"') else item)
        return result

    return section()[0]


def items(tree, name):
    return [x for x in tree if isinstance(x, list) and x and x[0] == name]


def one(tree, name):
    return next(iter(items(tree, name)), None)


def point(tree):
    return float(tree[1]), float(tree[2])


board = parse(PCB.read_text())
footprints = {}
for fp in items(board, "footprint"):
    props = {p[1]: p[2] for p in items(fp, "property")}
    ref = props.get("Reference")
    if not ref:
        continue
    at = one(fp, "at")
    x, y = point(at)
    angle = math.radians(float(at[3]) if len(at) > 3 else 0)

    def pos(local):
        a, b = point(local)
        return x + a * math.cos(angle) + b * math.sin(angle), y - a * math.sin(angle) + b * math.cos(angle)

    pads = [(p[1], pos(one(p, "at"))) for p in items(fp, "pad")]
    shapes = []
    for kind in ("fp_circle", "fp_rect"):
        for s in items(fp, kind):
            if one(s, "layer")[1] != "F.Fab":
                continue
            if kind == "fp_circle":
                c, edge = pos(one(s, "center")), pos(one(s, "end"))
                r = math.dist(c, edge)
                if r > 1.1:  # ignore the small polarity cross
                    shapes.append(("circle", c, r))
            else:
                a, b = pos(one(s, "start")), pos(one(s, "end"))
                lo = (min(a[0], b[0]), min(a[1], b[1]))
                hi = (max(a[0], b[0]), max(a[1], b[1]))
                shapes.append(("rect", lo, hi))
    footprints[ref] = {"at": (x, y), "pads": pads, "shapes": shapes}


def body_shape(ref):
    return max(footprints[ref]["shapes"], key=lambda s: math.pi * s[2] ** 2 if s[0] == "circle" else (s[2][0] - s[1][0]) * (s[2][1] - s[1][1]))


def draw(ax, target, center=None, title=""):
    oldpads = dict(footprints[target]["pads"])
    oldcenter = ((oldpads["1"][0] + oldpads["2"][0]) / 2,
                 (oldpads["1"][1] + oldpads["2"][1]) / 2)
    center = center or oldcenter
    limits = ((95, 131), (99, 134)) if target == "C22" else ((231, 253), (94, 124))
    ax.set_xlim(*limits[0])
    ax.set_ylim(limits[1][1], limits[1][0])
    ax.set_aspect("equal")
    ax.set_xticks(range(math.ceil(limits[0][0]), math.floor(limits[0][1]) + 1, 2))
    ax.set_yticks(range(math.ceil(limits[1][0]), math.floor(limits[1][1]) + 1, 2))
    ax.grid(color="#d5dce1", linewidth=0.45)
    ax.tick_params(labelsize=7)
    ax.set_title(title, fontsize=11, pad=9)
    if target == "C42":
        edge_x = 248.9259
        ax.axvspan(edge_x, limits[0][1], facecolor="#ececec", alpha=0.8, zorder=0)
        ax.axvline(edge_x, color="black", linewidth=1.5, zorder=9)
        ax.text(edge_x - 0.25, 123, "PCB edge", rotation=90, va="bottom", ha="right", fontsize=8)

    refs = ("C17", "C18", "C21", "C23", "R39", "R42") if target == "C22" else ("C41", "C43", "R75", "R77")
    for ref in refs:
        shape = body_shape(ref)
        if shape[0] == "circle":
            patch = Circle(shape[1], shape[2], facecolor="#9bc4d6", edgecolor="#35647c", linewidth=1)
            label = shape[1]
        else:
            lo, hi = shape[1:]
            patch = Rectangle(lo, hi[0] - lo[0], hi[1] - lo[1], facecolor="#9bc4d6", edgecolor="#35647c", linewidth=1)
            label = ((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2)
        patch.set_alpha(0.65)
        ax.add_patch(patch)
        ax.text(*label, ref, ha="center", va="center", fontsize=8, color="#123448", weight="bold")
        for _, pad in footprints[ref]["pads"]:
            ax.add_patch(Circle(pad, 0.39, facecolor="#393b3d", edgecolor="white", linewidth=0.4, zorder=4))

    ax.add_patch(Circle(oldcenter, 3.15, fill=False, edgecolor="#606c75", linestyle=(0, (3, 2)), linewidth=1.1, zorder=5))
    ax.add_patch(Circle(center, 4.25, fill=False, edgecolor="#a12619", linestyle=(0, (2, 2)), linewidth=1.2, zorder=7))
    ax.add_patch(Circle(center, 4.0, facecolor="#f67465", edgecolor="#a12619", alpha=0.6, linewidth=1.2, zorder=6))
    ax.plot(*center, marker="+", markersize=8, color="#971f12", zorder=8)
    for number, pad in oldpads.items():
        ax.add_patch(Circle(pad, 0.55, facecolor="#20a267" if number == "1" else "#7157ae", edgecolor="white", linewidth=0.7, zorder=10))
        ax.text(pad[0] - 0.8, pad[1] - 0.8, "+" if number == "1" else "−", fontsize=9, color="black", weight="bold", zorder=11)


fig, axes = plt.subplots(1, 3, figsize=(17, 7.3))
draw(axes[0], "C22", title="C22: body at original holes")
draw(axes[1], "C42", title="C42: body at original holes")
draw(axes[2], "C42", center=(239.60, 108.20), title="C42: body raised 3 mm over R75")
fig.suptitle("v2 PCB top view • Nichicon UKL 47 µF / 50 V • nominal Ø8, P3.5", fontsize=13, y=0.97)
fig.text(0.5, 0.07, "Blue: neighboring F.Fab bodies   •   Gray dashed: original Ø6.3   •   Red: Ø8 body   •   Red dashed: Ø8.5 planning envelope", ha="center", fontsize=9)
fig.text(0.5, 0.04, "Green and purple: existing +/− board holes. Black line: PCB edge. Grid labels and geometry are millimetres; X right, Y down.", ha="center", fontsize=9)
fig.subplots_adjust(left=0.05, right=0.98, bottom=0.16, top=0.88, wspace=0.18)
fig.savefig(OUT / "C22_C42_projections.png", dpi=200)
fig.savefig(OUT / "C22_C42_projections.pdf")
