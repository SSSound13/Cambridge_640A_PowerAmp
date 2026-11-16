# Board wiring — current revision

[Русский](WIRING.md) · [Project overview](../../README.en.md)

Identify contacts by the numbers on the PCB. The wire-entry view and the mating-face view of a connector are mirrored.

| Connector | Pin 1 | Pin 2 | Pin 3 |
|---|---|---|---|
| CN20, main secondary winding, JST VH | Yellow | Red | Orange — centre tap |
| CN21, auxiliary secondary winding, JST VH | Green | Violet — centre tap | Grey |
| CN23, left output to relay board, JST VH | Red — signal | Black — PGND return | — |
| CN24, right output to relay board, JST VH | Red — signal | Black — PGND return | — |

**CN20 centre tap: pin 3. CN21 centre tap: pin 2.** Winding colours correspond to the recorded wiring of the amplifier. Red/black on the outputs is the project's chosen harness marking.

Viewed from above with the output transistors at the top: CN20 runs **1–2–3 from top to bottom**; CN21 runs **3–2–1 from left to right**. The square pad identifies pin 1. J4 connects to the chassis through the intended R97/C31 network; do not replace it with a direct PGND-to-chassis connection.

[Current connector map](../assembly-notes/640A_power_connector_wire_colors.png) · [Wiring PDF, Russian](../640A_PowerAmp_v2_wiring.pdf) · [Parts and mating housings](../../BOM.en.md)

## Harness assembly

1. Unplug the amplifier and label each wire before removing the original board. Verify each wire by continuity; schematic colours may differ from an individual amplifier's wiring.
2. Use VHR-3N housings for CN20/CN21 and VHR-2N for CN23/CN24. Contacts are SVH-21T-P1.1 per BOM. Select wire and crimp settings within the contact manufacturer's specification. XH and VH are not interchangeable.
3. Crimp with a suitable tool. Check conductor retention and contact locking in the housing. Match every cavity number to the key and the PCB pin-1 pad.
4. Check continuity from every connector contact to its destination. CN23 is the left output (RO), CN24 is the right output (LO); both returns are PGND. Check for unintended chassis connections.
5. Verify centre taps, component polarity, soldering and heatsink insulation, then follow the [first power-up procedure](FIRST_POWER_UP_V2.en.md).
