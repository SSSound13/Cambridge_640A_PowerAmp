# ALPS RK27 and repair-board review phase

These instructions apply to `alps-rk27-adapter/` and `volume-control-repair/`.

The user is currently agreeing the mechanical configuration: board contours, component positions, aligned mounting axes and the assembled 3D view. For subsequent review changes, do not route or reroute traces until the user explicitly starts the routing phase. Preserve the detours already made around the front-left mounting hole; the user accepted keeping that completed work.

`alps-rk27-adapter/build.py` currently regenerates and routes the upper PCB. Do not run it unchanged for future mechanical-only reviews. Make geometry changes while preserving existing tracks, and report any resulting routing conflicts for the later routing phase instead of silently resolving them. Connectivity/DRC findings may be inspected and reported during mechanical review.
