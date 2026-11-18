# Routing review for all four copper layers

18 November 2026. **Board under testing.** This revision starts from the manually edited board with 1378 segments. All component positions, including SAP and Q20, and all 656 pads are preserved.

## Corrections

- Removed the 3 mm B.Cu jumper between NT1–NT3. Their PGND pads share the In2.Cu plane.
- Restored full junctions in the −45 V routes at C11 and U2. Removed stubs and acute junctions in LOCLIP, ROCLIP and digital. Improved pad entries at D23/D24 and CN6.
- Applied the manual LICLIP and Q9 changes to the corresponding channel nodes. All 21 whole-net pairs match in width, layer and geometry after translation.
- The 23 segments in the TP1–TP6 measurement branches use 0.5 mm tracks. KiCad allows this width for the named groups. The shared D10–TP5–R52 path still uses 2 mm tracks.

## Power distribution

On In1.Cu, each continuous rail connects its four 2200 µF capacitors and two rectifier diodes. +45 V links C23/C25/C26/C29 with D17/D20. −45 V links C21/C30/C62/C63 with D18/D19. Outer tracks feed the channels. Some parallel −45 V paths remain around the SAP devices and protection diodes.

On In2.Cu, the common PGND connects all eight reservoir capacitors to CN20.3. The upper ground bands were removed. C11, C45, C64 and C65 connect through 2 mm tracks. F.Cu carries the loudspeaker returns to the common point and links the separate C79/C80 PGND region to CN20.3.

## Verification

| Measure | Result |
| --- | ---: |
| Track segments | 1365 |
| Vias | 0 |
| Copper violations, unconnected items and schematic mismatches | 0 |
| Loose ends, exact duplicates and acute junctions outside pads | 0 |

The manufactured reference [8b50969](https://github.com/SSSound13/Cambridge_640A_PowerAmp/commit/8b50969) has 1368 segments. This revision has three fewer and is below the 1409 limit. The geometry report lists three short local segments. The LOCLIP jog near C32 preserves clearance between the signal and power copper.

KiCad 10.0.7 reports the existing 199 silkscreen overlaps, 44 silkscreen-over-copper findings and the D2/R107 courtyard overlap. The report with exclusions lists 23 additional excluded courtyard overlaps. The current review gives the modelling assumptions. The fabrication package belongs to the earlier revision.

[Four-layer PDF](routing-review/routing-review.pdf) · [Before-and-after comparison](routing-review/routing-comparison.pdf) · [KiCad report](routing-review/final-drc.json) · [Geometry](routing-review/geometry-final.json)
