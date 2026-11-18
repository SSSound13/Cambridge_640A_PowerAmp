# Fabrication package — Cambridge 640A V1

[Русский](README.md) · [Download fabrication ZIP](Cambridge_640A_PowerAmp_production.zip) · [Checksums](SHA256SUMS.txt)

This Gerber X2 and Excellon archive belongs to an earlier board revision. Its source PCB was exported using KiCad 10. Export does not modify the source board. Its SHA-256 is recorded in the [manifest](manifest.json).

| Order parameter | Value |
|---|---|
| Outline bounding dimensions | 198.9259 × 129.9597 mm; routed shape defined by Edge.Cuts |
| Material / thickness | FR4 / 1.6 mm |
| Copper order, top to bottom | F.Cu → In1.Cu → In2.Cu → B.Cu |
| Design copper thickness | 70 / 35 / 35 / 70 µm; agree finished copper thickness with the manufacturer |
| Solder mask / silkscreen | Both sides |
| Plated holes | 648, separate PTH file |
| Non-plated holes | 8, separate NPTH file |
| Separate vias | 0 |
| Coordinates | Absolute, mm; same origin for Gerber and Excellon; no mirroring |

## Contents

- `gerbers/`: four copper layers, two solder masks, two silkscreens, outline and Gerber Job.
- `drill/`: separate PTH and NPTH Excellon files, two PDF drill maps and a tool report.
- `validation/`: native DRC with schematic parity and a report including accepted exclusions.
- [Fabrication notes](FABRICATION_NOTES.txt), [file manifest](manifest.json) and [SHA256 checksums](SHA256SUMS.txt).

Upload the complete ZIP when ordering. Do not mirror copper or drill data. Individual files are also available in the repository directories.

## Validation and regeneration

Native KiCad 10 checks: 0 active DRC violations, 0 unconnected items, 0 schematic parity issues. Accepted exclusions and project rule settings remain recorded in the report.

From the repository root: `python scripts/build_production.py`. KiCad 10 is required. Set `KICAD_CLI` to override the CLI executable path.

[Project overview](../README.en.md) · [BOM](../BOM.en.md) · [Assembly documents](../doc/assembly-notes/README.en.md)
