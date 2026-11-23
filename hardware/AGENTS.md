# Volume control project

The user explicitly authorized trial routing after geometry changes and required removal of all old tracks. Width is 1.00 mm, no neckdowns. Prefer at most three straight segments per pad-to-pad branch; permit four only as fallback. Leave connections unrouted if no such path is found. Do not silently relax these limits. ROUTING_RULES.md describes proposed supporting clearances and remaining decisions.

Preserve approved geometry and six factory-aligned edge contacts. Three supports H1-H3; H4 deleted. H2 source position (63.75,114) mm. Only H1 physically passes through the small repair overlay; H2/H3 go directly into main PCB. Factory copper is removed only beneath repair outline X60..91 Y36.5..109.5.

VolumeControl is an assembly visualization; ALPS_Adapter and Repair_Reference are editable boards. Regenerate assembly explicitly using sync_mechanical.py after changes. It preserves current tracks. verify_project.py checks geometry, widths and route segment counts. Existing routing attempt is incomplete, not manufacturing-ready.

H1 was subsequently moved toward the header: upper (64,131), lower (67.5,77.7) mm. Keep the resulting two-track corridor at the front edge; see H1-routing-corridor.json. Six-pin header remains fixed.

Latest user revision (2026-11-23): preserve user-completed manual routing. Upper F.Cu/B.Cu were exchanged exactly; do not reroute or enforce old segment counts. Lower has an intentional-to-preserve 0.2 mm segment and a dangling-track warning to review, not silently fix. Screws measured 2.7 mm shank / 4.5 mm head; standard MountingHole_3mm clearance holes, 5.5 mm copper keepout diameter. ASSEMBLY_NOTES.md records confirmed resistor variants and future-tuning note. sync_mechanical.py now rebuilds assembly without editing source boards.
