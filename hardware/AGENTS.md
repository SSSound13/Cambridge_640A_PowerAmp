# Volume-control mechanical review

These instructions apply to `volume-control/`.

The user is agreeing board contours, component positions, mounting axes and the assembled 3D view. Do not route or reroute traces until the user explicitly starts routing. Preserve existing detours. Report conflicts rather than silently resolving them.

`update_factory_layers.py` updates only manual reference graphics. `verify_project.py` checks mounting projection, model paths and preservation of existing copper. The main VolumeControl PCB is an assembly visualization; ALPS_Adapter and Repair_Reference are the editable board files. After mechanical changes, regenerate the lower-board model and assembly deliberately; they do not update automatically.
