# Gerber / drill export, 2026-11-07

Source: main commit `5dcab897b116dd5cd4a2f4a718dbb827556a5aa2`.
PCB SHA256: `d9af2641e284b8d14db9773f614da6ab3660ce755ededf99e6f408ab51a18f22`.
Generated using KiCad CLI 10.0.7. PCB, schematic and project files were not changed.

## Contents

- Four copper layers: F.Cu / In1.Cu / In2.Cu / B.Cu, in that order.
- Both solder masks and both silkscreens; Edge.Cuts.
- F.Paste and B.Paste are intentionally empty (through-hole board).
- Separate plated and non-plated Excellon drills: 669 PTH and 8 NPTH holes.
- Gerber drill maps and drill report are reference documents, NOT additional board layers.
- Gerber job and IPC-D-356 electrical test netlist.
- SHA256SUMS.txt authenticates all generated fabrication files.

Gerber and drill coordinates use the same absolute origin, millimetres, without mirroring.
Gerbers use X2 attributes, 4.6 precision; solder-mask openings are subtracted from silkscreen.
Nominal PCB thickness is 1.6 mm; specified copper thickness is 70/35/35/70 µm.
Confirm the actual stackup and surface finish with the fabricator: the project has no finish selected.

## Validation and limitations

Zone check/refill was enabled for export. Independent DRC with zone refill and schematic parity:
0 errors, 23 silk_overlap warnings, 0 unconnected items, 0 schematic parity issues.
Existing project exclusions and disabled rules remain in effect; no new exclusions were added.
Report: `doc/v2/validation/gerber_2026-11-07_drc.json` in the repository.
The source contains the v2 U6 correction; the historical 2026-10-03 archive does not.

Resolve/review the silkscreen warnings and confirm component, heatsink and mounting fit before ordering.
Protection, thermal performance, insulation and operation of the physical amplifier still need validation.

`gerber.zip` and root `640A_PowerAmp_v2_fab_2026-11-07.zip` contain the same current files.
The root `640A_PowerAmp_v2_fab_2026-10-03.zip` is preserved only as historical evidence:
DO NOT ORDER it; it contains the old incorrect U6 connection to +15 V.

## Reproduce

Run from the project root with KiCad 10.0.7 (use a fresh output directory):

```sh
kicad-cli pcb export gerbers -o export/ -l F.Cu,In1.Cu,In2.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,F.Paste,B.Paste,Edge.Cuts --no-protel-ext --subtract-soldermask --check-zones 640A_PowerAmp.kicad_pcb
kicad-cli pcb export drill -o export/ --excellon-separate-th --generate-map --map-format gerberx2 --generate-report --report-path export/640A_PowerAmp-drl.rpt 640A_PowerAmp.kicad_pcb
kicad-cli pcb export ipcd356 -o export/640A_PowerAmp.d356 640A_PowerAmp.kicad_pcb
kicad-cli pcb drc --refill-zones --schematic-parity --format json -o drc.json 640A_PowerAmp.kicad_pcb
```
