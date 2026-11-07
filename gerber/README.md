# Gerber / drill export, 2026-11-07

Source: PCB in the same commit as this export, based on `dc34d68d511573bbf8a1af9a689956af030c424d` with the R12 silkscreen correction.
PCB SHA256: `fab5ad2d169c11edd13225c05fcc267cca08748494c56a05c9273d19f9d117da`.
Generated using KiCad CLI 10.0.7. Only R12 reference moved down 0.8 mm; four user-approved silk-overlap exclusions added to the project. Copper, component positions, QR, U6 and schematic files are unchanged.

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
0 errors, 0 active warnings, 0 unconnected items, 0 schematic parity issues.
R12/C7 overlaps are fixed. R121/U4, R112/R50, R65/C78 and R25/Q18 are accepted as four specific KiCad exclusions.
The existing 142 courtyard exclusions and disabled rules remain unchanged.
With exclusions included: 146 excluded violations, of which 4 are the accepted silk overlaps.
Report: `doc/v2/validation/gerber_2026-11-07_drc.json` in the repository.
The source contains the v2 U6 correction; the historical 2026-10-03 archive does not.

Confirm component, heatsink and mounting fit before ordering.
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
