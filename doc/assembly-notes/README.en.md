# Board assembly — current revision

[Русский](README.md) · [Project overview](../../README.en.md) · [BOM](../../BOM.en.md)

All placement maps and wiring documents have been rebuilt from the current PCB and BOM. Maps use the actual footprint coordinates, rotations, F.Fab outlines and pad numbers in `640A_PowerAmp.kicad_pcb`, without copper tracks or zones. The old maps dated 5 November 2026 have been removed.

- [Detailed instructions, 13 stages, maps and checklists — Russian PDF](640A_PowerAmp_v2_assembly_instructions.pdf).
- [Compact sequence, 13 stages — Russian PDF](../640A_PowerAmp_v2_assembly_order.pdf).
- [Resistor value and power maps — Russian PDF](640A_PowerAmp_v2_resistors_by_value.pdf).
- [Full and enlarged placement drawings — Russian PDF](../640A_PowerAmp_v2_assembly.pdf).
- [Harness assembly and wiring — Russian PDF](../640A_PowerAmp_v2_wiring.pdf).
- [Connector pin map — PDF](640A_power_connector_wire_colors.pdf) · [PNG](640A_power_connector_wire_colors.png).
- [First power-up and bias adjustment, English](../v2/FIRST_POWER_UP_V2.en.md).

## Assembly sequence

The sequence progresses from low-profile parts to taller components. All 274 fitted positions appear exactly once. J4 is included as a chassis wire in the final stage; TP1–TP6 require no purchased components.

| Stage | Parts and procedure |
|---|---|
| 1 | Small resistors and diodes. Match paired resistors before soldering: R30/R31, R80/R81, R14/R15, R58/R59, R34/R79, and R36/R82/R102/R65. R102/R65 are fitted in stage 2. Check every diode's cathode marking and pin K against the schematic. |
| 2 | 0.25–0.66 W resistors and 1N4004 diodes. R88 is 11 kΩ / 0.25 W. R41/R43/R96/R98 are 150 Ω / 0.5 W fusible parts. R122/R123 now lie horizontally at 10.16 mm pitch: 47 Ω / 0.5 W, the initial snubber value. |
| 3 | DIP-8 ICs: U1/U6 NE5534, U7 LM393. Check pin 1 and package notch. Trial-fit C3/C52 before using sockets at U1/U7; sockets may interfere. |
| 4 | Low-profile ceramic and film capacitors. C16/C44 are DNP; C81 does not exist in this revision. Do not force formed leads beyond their factory bend. |
| 5 | Vertical R120/R121 only: 100 Ω / 0.25 W, 1%, 2.54 mm pitch. R122/R123 are already installed in stage 2. |
| 6 | TO-92 transistors. Matched pairs: Q7/Q8 and Q28/Q29 (MPSA92/93); Q9/Q10 and Q26/Q27 (MPSA42/43). Compare parts under identical test conditions; earlier matching targets were 5–10% for hFE and 2–3 mV for Vbe. Check the actual manufacturer's pinout; BC327/337 and MPSA packages may differ. |
| 7 | Main bridge and power resistors. D17–D20 are BY550-400. R44/R50 are 4.7 Ω / 3 W, about 3 mm above the PCB. R22/R52/R69/R100 are 0.22 Ω / 3 W. Fit before the large electrolytics. |
| 8 | Large film capacitors and trimmers. C18/C39: 2.2 µF / 100 V MKS2; C46/C48: 100 nF / 160 V Poly per BOM. R68/R116: 47 Ω / 0.5 W; set the minimum-bias starting position using the power-up procedure. |
| 9 | Small electrolytics. C13/C47 and C17/C41 are non-polar. C13/C47 and C22/C42 use Ø8 mm bodies and 3.5 mm pitch. Observe polarity on all polar parts. |
| 10 | JST connectors. CN20/CN21: 3-pin VH; CN23/CN24: 2-pin VH. Other connectors are XH per BOM. Solder one pin, check seating and key orientation, then finish. |
| 11 | TO-126 devices and regulators. U8=7805, U9=7815, U10=7915; use insulating pads, insulated mounting hardware and thermal compound per BOM. Check MJE340/MJE350 orientation and pinouts before soldering. |
| 12 | Large electrolytics, including C70/C71/C74/C75, now Ø10 mm / 5 mm pitch. Check polarity and enclosure clearance. Fit the eight 2200 µF reservoir capacitors last among the capacitors. |
| 13 | Output stage and J4. U2/U4: SAP15P; U3/U5: SAP15N; Q20: MJE340. Trial-fit heatsinks and insulated mounting hardware before soldering without mechanical strain. J4 connects to the chassis through the intended R97/C31 network; do not bypass it. |

Before power-up, check polarity, solder bridges, heatsink insulation, wiring and the minimum-bias trimmer setting. Continue with the [complete power-up procedure](../v2/FIRST_POWER_UP_V2.en.md).

## Source data and regeneration

The [manifest](source.json) records PCB/BOM SHA-256 hashes, coordinates, pad locations and stage membership. Run `python scripts/build_assembly_docs.py` from the repository root. It requires Python, ReportLab, PyMuPDF and DejaVu Sans. These maps describe the current source PCB; previously manufactured boards may have different geometry.
