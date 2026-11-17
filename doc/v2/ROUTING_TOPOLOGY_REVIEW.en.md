# Routing review: all four copper layers

17 November 2026. This revision supersedes the previous 1401-segment review. The entire PCB was checked for contacts, widths, angles, duplicates, filled zones and schematic parity. Component placement is unchanged.

## Manufactured-board segment baseline

The reference PCB is from commit [8b50969](https://github.com/SSSound13/Cambridge_640A_PowerAmp/commit/8b50969), associated with the 3 October “before ordering” CHANGELOG entry and 640A_PowerAmp_v2_fab_2026-10-03.zip in that revision. The PCB comes from the commit, not a reconstruction from Gerbers. The later 1888-segment manufacturing export was not used as the baseline.

| Metric | Reference | Current |
| --- | ---: | ---: |
| Track segments | 1368 | 1391 |
| Vias | 21 | 0 |
| Segment growth | — | 1.68% |
| Maximum allowed at +3% | — | 1409 |

Both counts use PCB segment objects, excluding vias and polygon vertices. The limit is met with 18 segments to spare. Segment count supplements connection and current checks; it is not a sufficient routing-quality metric by itself.

## Contact and routing corrections

- B.Cu PGND near (191.7, 79.5) mm previously relied on about 0.020 mm overlap between rounded track ends. The repaired joint joins centrelines and retains full conductor width. Similar contacts were checked across the board.
- The previous board had 121 endpoints outside their own pads, filled zones or another track centreline. These were suspect contacts, not 121 electrical opens. The final endpoint audit finds zero. Exact duplicates were removed; the Q33 branch now terminates inside its pad.
- The In1.Cu +45 V region at C26 previously served only one pad. It now forms a useful broad connection to D17.1. The second filled branch joins C25.1 and D20.1; both branches join the overall supply net through outer copper. One-pad SAP tongues were removed; SAP feeds remain on 2 mm outer tracks.
- The F.Cu return hook at D2 was removed. Board-wide branch optimization moved tee positions along trunks to shorten detours while retaining proper contacts. All 21 agreed translated whole-net pairs remain identical.
- Both wide upper PGND connections to the central In2.Cu region remain in one actual filled-copper component. The F.Cu output-return collector retains 2 mm branches and a 3.5 mm common path.

## Final checks

| Metric | Before this revision | Current |
| --- | ---: | ---: |
| Track segments | 1401 | 1391 |
| Total track length | 7745.00 mm | 7801.54 mm |
| Endpoints outside pads / zones / centreline contacts | 121 | 0 |

The small length increase restores reliable contacts and relocates the control route that split the supply polygon. It is reported separately from the segment reduction.

Layer counts: F.Cu 423, B.Cu 611, In1.Cu 236, In2.Cu 121. Widths remain 0.5 / 0.8 / 1 / 2 / 3.5 mm. Zero exact duplicates, acute centreline junctions outside pads or non-0°/45°/90° tracks outside pads. Four local segments shorter than 0.5 mm remain, listed in geometry-final.json. Centreline checks do not assert that every polygon boundary or footprint has no acute feature.

All 296 footprint blocks and 656 pads remain exactly unchanged, including Q20 and SAP. The 21 translated whole-net pairs contain 121 segments per side. All ten holes were checked. H9 track-to-hole-edge gap is 1.079 mm; H7/H8 track-to-copper-pad-edge gaps are 1.034 / 1.209 mm.

KiCad 10.0.7 reports zero copper violations, dangling tracks, unconnected items and schematic mismatches. Active findings remain: 199 silk_overlap, 44 silk_over_copper and one D2/R107 courtyard overlap. A separate report including existing exclusions lists 23 additional courtyard overlaps. No severities or exclusions were changed. Full DRC is not clean.

Outputs use 2 mm tracks on 70 µm outer copper; main transformer tracks use 3.5 mm outer copper. Output current sharing and central PGND resistance were recalculated. The 35 µm inner PGND model gives 0.670 / 0.657 mΩ at 0.25 / 0.125 mm grid spacing, or 0.066–0.067 W at an assumed 10 A. This models resistance, not prototype temperature or charging transients. [Current and width review](ROUTING_CURRENT_REVIEW.en.md).

The four-layer PDF shows top views without component bodies; a separate PDF provides enlarged before/after comparisons. Manufacturing outputs and the website were not rebuilt.
