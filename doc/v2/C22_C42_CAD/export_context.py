"""Export SolidWorks reference geometry for C22 and C42 from the KiCad v2 PCB.

Run: python doc/v2/C22_C42_CAD/export_context.py
Requires cadquery and ezdxf. STEP and DXF use millimetres, X right, Y up,
Z up; the origin is the positive through-hole on the PCB top surface.
"""

import json
import math
import re
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import cadquery as cq
import ezdxf


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
PCB = ROOT / "640A_PowerAmp.kicad_pcb"


def parse(text):
    tokens = iter(re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+', text))

    def section():
        result = []
        for token in tokens:
            if token == ")":
                return result
            result.append(section() if token == "(" else json.loads(token) if token.startswith('"') else token)
        return result

    return section()[0]


def children(tree, name):
    return [item for item in tree if isinstance(item, list) and item and item[0] == name]


def child(tree, name):
    return next(iter(children(tree, name)), None)


def xy(tree):
    return float(tree[1]), float(tree[2])


tree = parse(PCB.read_text())
footprints = {}
all_pads = []
for fp in children(tree, "footprint"):
    properties = {p[1]: p[2] for p in children(fp, "property")}
    ref = properties.get("Reference")
    if not ref:
        continue
    at = child(fp, "at")
    px, py = xy(at)
    angle = math.radians(float(at[3]) if len(at) > 3 else 0)

    def transform(item):
        x, y = xy(item)
        return (px + x * math.cos(angle) + y * math.sin(angle),
                py - x * math.sin(angle) + y * math.cos(angle))

    pads = []
    for pad in children(fp, "pad"):
        size = child(pad, "size")
        drill = child(pad, "drill")
        rec = {
            "ref": ref,
            "number": pad[1],
            "center": transform(child(pad, "at")),
            "size": (float(size[1]), float(size[2])),
            "drill": float(drill[1]) if drill else 0.0,
        }
        pads.append(rec)
        all_pads.append(rec)

    shapes = []
    for key in ("fp_circle", "fp_rect"):
        for shape in children(fp, key):
            if child(shape, "layer")[1] != "F.Fab":
                continue
            if key == "fp_circle":
                center = transform(child(shape, "center"))
                radius = math.dist(center, transform(child(shape, "end")))
                if radius > 1.1:  # omit the small polarity mark
                    shapes.append(("circle", center, radius))
            else:
                a, b = transform(child(shape, "start")), transform(child(shape, "end"))
                shapes.append(("rect", (min(a[0], b[0]), min(a[1], b[1])),
                               (max(a[0], b[0]), max(a[1], b[1]))))
    footprints[ref] = {"pads": pads, "shapes": shapes}


def main_shape(ref):
    shapes = footprints[ref]["shapes"]
    return max(shapes, key=lambda item: math.pi * item[2] ** 2 if item[0] == "circle"
               else (item[2][0] - item[1][0]) * (item[2][1] - item[1][1]))


vias = []
for via in children(tree, "via"):
    vias.append({"ref": "VIA", "number": "", "center": xy(child(via, "at")),
                 "size": (float(child(via, "size")[1]),) * 2,
                 "drill": float(child(via, "drill")[1])})


CONTEXTS = {
    "C22": {
        "crop": (-20.0, -21.0, 21.0, 22.0),
        "neighbors": {"C17": 11.5, "C18": 16.0, "C21": 35.5,
                      "C23": 35.5, "R39": 2.5, "R42": 2.5},
        "body_center_global": (112.5551, 116.3654),
    },
    "C42": {
        "crop": (-15.0, -18.0, 7.7660, 18.0),
        "neighbors": {"C41": 11.5, "C43": 16.0, "R75": 2.5, "R77": 2.5},
        "body_center_global": (239.60, 108.20),
    },
}

BOARD_THICKNESS = 1.6
BOARD_EDGE_X = 248.9259
CAP_DIAMETER = 8.0
CAP_HEIGHT = 11.5
CAP_LEAD_PITCH = 3.5
CAP_BOTTOM_Z = 3.0
ENVELOPE_DIAMETER = 8.5  # design allowance, not a Nichicon tolerance


def export_one(ref, spec):
    positive, negative = (p["center"] for p in footprints[ref]["pads"])
    x0, y0 = positive

    def local(point):
        return (point[0] - x0, y0 - point[1])

    xmin, ymin, xmax, ymax = spec["crop"]
    if ref == "C42":
        xmax = BOARD_EDGE_X - x0
    cap_center = local(spec["body_center_global"])
    footprint_center = (0.0, -1.25)
    cap_plus = (cap_center[0], cap_center[1] + CAP_LEAD_PITCH / 2)
    cap_minus = (cap_center[0], cap_center[1] - CAP_LEAD_PITCH / 2)

    # The cropped solid is a CAD working area. Its left/top/bottom boundaries
    # are artificial; the C42 right boundary is the real Edge.Cuts line.
    board = (cq.Workplane("XY")
             .box(xmax - xmin, ymax - ymin, BOARD_THICKNESS, centered=True)
             .translate(((xmin + xmax) / 2, (ymin + ymax) / 2, -BOARD_THICKNESS / 2)))
    nearby_pads = [p for p in all_pads + vias if xmin < local(p["center"])[0] < xmax
                   and ymin < local(p["center"])[1] < ymax]
    for drill in sorted(set(p["drill"] for p in nearby_pads if p["drill"] > 0)):
        centers = [local(p["center"]) for p in nearby_pads if p["drill"] == drill]
        board = board.faces(">Z").workplane().pushPoints(centers).hole(drill)

    assembly = cq.Assembly(name=f"{ref}_SolidWorks_context_mm")
    assembly.add(board, name="PCB_crop_top_Z0_thickness_1p6",
                 color=cq.Color(0.17, 0.47, 0.28))

    for neighbor, height in spec["neighbors"].items():
        shape = main_shape(neighbor)
        if shape[0] == "circle":
            center = local(shape[1])
            part = cq.Workplane("XY").center(*center).circle(shape[2]).extrude(height)
        else:
            a, b = local(shape[1]), local(shape[2])
            xlow, xhigh = sorted((a[0], b[0]))
            ylow, yhigh = sorted((a[1], b[1]))
            part = (cq.Workplane("XY")
                    .box(xhigh - xlow, yhigh - ylow, height,
                         centered=(True, True, False))
                    .translate(((xlow + xhigh) / 2, (ylow + yhigh) / 2, 0)))
        assembly.add(part, name=f"{neighbor}_body_height_{height:g}mm",
                     color=cq.Color(0.39, 0.63, 0.78))

    cap = (cq.Workplane("XY").center(*cap_center).circle(CAP_DIAMETER / 2)
           .extrude(CAP_HEIGHT).translate((0, 0, CAP_BOTTOM_Z)))
    assembly.add(cap, name=f"{ref}_UKL_47u_50V_body_bottom_Z3",
                 color=cq.Color(0.88, 0.29, 0.25))
    assembly.save(str(OUT / f"{ref}_SolidWorks_context.step"), exportType="STEP")

    dxf = ezdxf.new("R2010", setup=True)
    dxf.units = ezdxf.units.MM
    dxf.header["$MEASUREMENT"] = 1
    colors = {
        "BOARD_CROP": 7, "BOARD_EDGE_REAL": 1, "DRILL": 8,
        "COPPER_PAD": 2, "TARGET_PAD": 3, "NEIGHBOR_BODY": 5,
        "OLD_FOOTPRINT": 9, "CAP_BODY": 1, "CAP_ENVELOPE": 6,
        "CAP_LEAD_EXIT": 4, "CENTER": 3, "LABEL": 7,
    }
    for layer, color in colors.items():
        dxf.layers.new(layer, dxfattribs={"color": color})
    msp = dxf.modelspace()
    msp.add_lwpolyline([(xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax)],
                       close=True, dxfattribs={"layer": "BOARD_CROP"})
    if ref == "C42":
        msp.add_line((xmax, ymin), (xmax, ymax),
                     dxfattribs={"layer": "BOARD_EDGE_REAL"})
    for pad in nearby_pads:
        center = local(pad["center"])
        layer = "TARGET_PAD" if pad["ref"] == ref else "COPPER_PAD"
        msp.add_circle(center, max(pad["size"]) / 2, dxfattribs={"layer": layer})
        if pad["drill"]:
            msp.add_circle(center, pad["drill"] / 2, dxfattribs={"layer": "DRILL"})
    for neighbor in spec["neighbors"]:
        shape = main_shape(neighbor)
        if shape[0] == "circle":
            msp.add_circle(local(shape[1]), shape[2],
                           dxfattribs={"layer": "NEIGHBOR_BODY"})
            label = local(shape[1])
        else:
            a, b = local(shape[1]), local(shape[2])
            msp.add_lwpolyline([(a[0], a[1]), (b[0], a[1]),
                                (b[0], b[1]), (a[0], b[1])],
                               close=True, dxfattribs={"layer": "NEIGHBOR_BODY"})
            label = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        msp.add_text(neighbor, dxfattribs={"height": 0.75,
                                          "insert": label, "layer": "LABEL"})
    msp.add_circle(footprint_center, 3.15,
                   dxfattribs={"layer": "OLD_FOOTPRINT"})
    msp.add_circle(cap_center, CAP_DIAMETER / 2,
                   dxfattribs={"layer": "CAP_BODY"})
    msp.add_circle(cap_center, ENVELOPE_DIAMETER / 2,
                   dxfattribs={"layer": "CAP_ENVELOPE"})
    for symbol, center in (("+", cap_plus), ("-", cap_minus)):
        msp.add_circle(center, 0.3, dxfattribs={"layer": "CAP_LEAD_EXIT"})
        msp.add_text(symbol, dxfattribs={"height": 0.8,
                                        "insert": (center[0] + 0.4, center[1]),
                                        "layer": "LABEL"})
    msp.add_line((cap_center[0] - 0.4, cap_center[1]),
                 (cap_center[0] + 0.4, cap_center[1]),
                 dxfattribs={"layer": "CENTER"})
    msp.add_line((cap_center[0], cap_center[1] - 0.4),
                 (cap_center[0], cap_center[1] + 0.4),
                 dxfattribs={"layer": "CENTER"})
    msp.add_text(f"{ref}.1 +  ORIGIN (0,0)", dxfattribs={"height": 0.8,
                  "insert": (xmin + 0.6, ymax - 1.5), "layer": "LABEL"})
    msp.add_text("UNITS mm  PCB TOP Z=0", dxfattribs={"height": 0.8,
                  "insert": (xmin + 0.6, ymax - 2.7), "layer": "LABEL"})
    dxf.saveas(OUT / f"{ref}_SolidWorks_top_view.dxf")

    print(f"{ref}: {len(nearby_pads)} holes; cap XY {cap_center}; "
          f"lead exits +{cap_plus}, -{cap_minus}")


for ref, specification in CONTEXTS.items():
    export_one(ref, specification)

with ZipFile(OUT / "C22_C42_SolidWorks_reference.zip", "w", ZIP_DEFLATED,
             compresslevel=9) as archive:
    for filename in ("README.md", "C22_SolidWorks_context.step",
                     "C22_SolidWorks_top_view.dxf", "C42_SolidWorks_context.step",
                     "C42_SolidWorks_top_view.dxf", "C22_C42_mobile_render.png"):
        archive.write(OUT / filename, arcname=filename)
