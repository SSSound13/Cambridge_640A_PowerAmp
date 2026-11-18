# Track current and width review

Reviewed 17 November 2026. The current four-layer PCB specifies 70 µm outer and 35 µm inner copper. These are calculated currents and geometry checks, not measurements on an assembled amplifier.

## Operating cases

Cambridge Audio Azur 640A V1 service manual AP14676/1 specifies 65 W into 8 Ω and 100 W into 4 Ω per channel (page 1), F6.3AL main-secondary fuses and F500mAL auxiliary fuses (page 30). Calculations use a sine wave into a resistive load; shared paths assume two channels in phase. Reactive loads, clipping, quiescent/driver currents and transients need separate verification.

| Path | RMS current | Peak / qualification |
| --- | ---: | --- |
| One output, 65 W / 8 Ω | 2.85 A | 4.03 A |
| One output, 100 W / 4 Ω | 5.00 A | 7.07 A |
| One output transistor and emitter branch, 100 W / 4 Ω | 3.54 A | Half-wave, 7.07 A peak |
| One supply rail feeding one channel | 3.54 A | 2.25 A average; excludes idle/driver current |
| One shared rail feeding two in-phase channels | 7.07 A | 4.50 A average, 14.14 A peak |
| Shared return from both outputs | 10.00 A | 14.14 A peak |

I_RMS = √(P/R); I_peak = √2 × I_RMS. For a half-wave over the full period, RMS = I_peak / 2 and average = I_peak / π. Copper heating follows RMS current, not the instantaneous peak alone.

Each rail has four 2200 µF reservoir capacitors, 8800 µF total. Their charging current depends on transformer/wiring resistance, diode behaviour, ESR and conduction angle. Neither charging RMS nor inrush can be established from output power alone. A 6.3 A fuse is not an instantaneous current limiter. The 3.5 mm charging routes provide more copper than output branches, but charging waveforms still require measurement or a validated source model.

## Selected widths

| Width | Application | Screening current at ΔT = 20 °C, outer / inner copper |
| --- | --- | ---: |
| 0.5 mm | Signal and control | 3.24 / 0.98 A |
| 0.8 mm | Low-current Supply-class rails and signal returns | 4.56 / 1.38 A |
| 1.0 mm | Auxiliary winding and selected damping branches | 5.36 / 1.62 A |
| 2.0 mm | Output, emitter branches and local power branches; outer layers | 8.86 / 2.68 A |
| 3.5 mm | Main secondary and outer shared power/charging routes | 13.30 / 4.02 A |

Screening uses I = k × ΔT^0.44 × A^0.725, A in square mils, k = 0.048 outer / 0.024 inner. This IPC-2221-style empirical estimate is neither a guaranteed rating nor a completed IPC-2152 assessment. At ΔT = 10 °C, 2 / 3.5 mm outer traces screen at 6.53 / 9.80 A. Surrounding copper, enclosure, heatsink, neighbouring heat sources and actual copper thickness affect temperature.

Previously, LO carried the full 5 A through 2 mm inner-layer traces, whose 20 °C-rise screening value is only 2.68 A at 35 µm. The load paths in RO, LO, RE1, RE2, LE1 and LE2 use 2 mm outer copper. The separately grouped TP measurement branches use 0.5 mm. Main-secondary tracks use 3.5 mm outer copper. KiCad rules prohibit inner-layer tracks for these classes and reject widths outside the five selected values.

Shared power paths can change from 3.5 mm to a 2 mm lower-current branch at a junction. That is a deliberate current-based change, not an arbitrary width step along a series connection. C21–R41 and C30–R96 now use uniform 2 mm branches. Planes are assessed from their actual geometry and current path, not a netclass trace-width setting.

## Lower-current branches

- R41/R43/R96/R98, 150 Ω / 0.5 W: √(0.5/150) = 57.7 mA is the continuous RMS budget from resistor power, not calculated stage consumption. The 2 mm feed has ample copper; downstream operating current depends on circuit voltage and load.
- Zobel R44/R50, 4.7 Ω / 3 W with C24/C28, 100 nF: about 0.25 A at 20 kHz / 20 V RMS, or 0.29 A at 22.8 V RMS. The resistor-power budget is approximately 0.80 A RMS. This does not cover ultrasonic oscillation.
- Snubbers R122/R123, 47 Ω / 0.5 W with C79/C80, 100 nF: continuous resistor-power budget about 0.103 A RMS; brief ringing pulses remain unknown. A 1 mm track covers this continuous budget.
- Auxiliary-secondary geometry is checked against a 0.5 A branch / 1 A shared-return budget, with 0.5 A fuses. This is not measured consumption of relays, controller or external tone circuitry. A 0.8 mm inner track screens at 1.38 A for a 20 °C rise.

## Return plane, necks and connectors

The 35 µm inner-layer sheet model at a 0.2 mm grid gives 5.31 mΩ for +45 V, 0.556 mΩ for −45 V and 0.665 mΩ for the central PGND. At an assumed 10 A RMS the corresponding copper losses are 0.531 W, 0.056 W and 0.066 W. The calculation combines the rectifier pads and the capacitor pads within each rail and excludes parallel outer copper. Charging pulses and temperature require prototype measurements. [Model data](routing-review/sheet-model.json)

Thermal spokes are 1 mm wide across a 0.5 mm gap, with at least two spokes. Two ideal 1 × 0.035 mm spokes, each 0.5 mm long, have about 0.123 mΩ combined resistance and 0.012 W loss at 10 A. This checks short-neck ohmic loss, not pad temperature. Hole plating thickness needs fabricator confirmation. One-pad +45 V SAP tongues were removed. SAP supplies use 2 mm tracks on 70 µm outer copper, with a calculated half-wave current of 3.54 A RMS. Each In1.Cu rail joins all four capacitors to both rectifier diodes of that rail.

JST specifies 10 A for the standard VH header with AWG16 wire. SVH-21T-P1.1 accepts only AWG22–18, so the previous crimp BOM did not substantiate a 10 A harness. The BOM now specifies seven SVH-41T-P1.1 contacts with AWG16 (about 1.25 mm²) for CN20/CN23/CN24, and three SVH-21T-P1.1 with AWG18 for CN21. Housings and PCB headers are unchanged. Connector rating does not validate unknown inrush or charging RMS; CN20 and crimp temperature need prototype checks.

## File verification

All 296 footprint blocks, including Q20/SAP, and 656 pads are preserved. All 21 translated whole-net pairs match. The current PCB has 1365 track segments, zero vias and 7436.54 mm total track length. The manufactured reference has 1368 segments. [Topology review](ROUTING_TOPOLOGY_REVIEW.en.md)

KiCad 10.0.7 DRC with all track errors and schematic parity reports zero copper violations, zero unconnected items and zero schematic mismatches. Existing findings remain: 199 silk_overlap, 44 silk_over_copper and one D2/R107 courtyard overlap. Severities and exclusions were not relaxed. A separate check including existing exclusions also lists 23 excluded courtyard overlaps. Full DRC is not clean; manufacturing outputs were not regenerated by this review.

Prototype validation still needs secondary/centre-tap RMS and inrush measurements; CN20, crimp, pad-transfer and copper temperatures with both channels driving 4 Ω in the enclosure; reactive-load and HF-stability checks.

## Sources

- [AP14676/1 service manual](../Cambridge_Azur_640A_V1_Service_Manual_AP14676-1.pdf), pages 1 and 30.
- [Official JST VH specifications](https://www.jst-mfg.com/product/index.php?lang=2&series=262) and [contact catalogue](https://www.jst-mfg.com/product/pdf/eng/eVH.pdf).
- [Official IPC-2152 contents](https://www.ipc.org/TOC/IPC-2152.pdf): identifies factors required for a full thermal assessment; it does not certify this project.

[All-layer topology review](ROUTING_TOPOLOGY_REVIEW.en.md).
