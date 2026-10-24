# DCK bobs CPU measurements

Hatari-HRDB, STE / MC68000 / 8 MHz / PAL RGB / 4 MiB, German TOS 1.62.
Every row profiles one complete **360-position NOEUD cycle**. Percentages are
work per update divided by the **160000-cycle / 20 ms PAL frame budget**.
A result above 100% means the update cannot fit in one 50 Hz frame; it does not
mean the processor can run above full utilization.

Included: ASM trajectory/frame orchestration, the actual GodLib sprite calls,
chunk restore/store, and BLiTTER HOG/stall time. Excluded: setup/reset, headers,
input, C target selection, Screen_Update/VBL and OS activity. These are full-cycle
averages, not worst-case bounds. `profiling.json` keeps hashes and components.

| Balls | CPU restore | CPU trails | BLiTTER restore | BLiTTER trails |
|---|---:|---:|---:|---:|
| 1 | 20.62% | 32.73% | 10.73% | 12.94% |
| 4 | 78.26% | 127.70% | 38.66% | 48.57% |
| 8 | 155.11% | 254.33% | 75.97% | 96.03% |

Trajectory advance is almost constant at about 1126 cycles/update (**0.70%**):
all eight phases advance even when fewer balls are selected. Most work is in
GodLib sprite rendering. For the default four-ball BLiTTER restore case,
approximately 38269 cycles go to drawing, 18852 to chunk restoration, 3513 to
Store, plus the small movement/dispatch cost. Restore remains CPU ASM.

Trails draw twice per ball: the previous and current global frame are stamped
into the logical page. This keeps both accumulated pages coherent, including
paint order at intersections. Skipping the catch-up pass would be a different,
flickering workload. No full-frame copying is used during normal animation.

## Normal main-loop cadence

These separate live windows include the ordinary main loop and Screen_Update,
not the synthetic profiling batch. Each starts after a scene reset settles;
reset/header-copy cost is outside the window.

| Balls | Renderer | Mode | Frames observed | Missed VBLs | Approx. FPS |
|---|---|---|---:|---:|---:|
| 4 | cpu | restore | 1493 | 0 | 50.0 |
| 4 | cpu | trails | 778 | 779 | 25.0 |
| 4 | blitter | restore | 1550 | 0 | 50.0 |
| 4 | blitter | trails | 1478 | 0 | 50.0 |
| 8 | cpu | restore | 763 | 763 | 25.0 |
| 8 | cpu | trails | 507 | 1016 | 16.6 |
| 8 | blitter | restore | 1430 | 0 | 50.0 |
| 8 | blitter | trails | 718 | 666 | 25.9 |

The **default four balls with BLiTTER run at 50 FPS in both modes**, with no
missed VBLs in the measured windows. Four CPU balls also fit at 50 FPS in
restore mode; their coherent trails need about 25 FPS. Eight BLiTTER balls
restore at 50 FPS, while trails fluctuate around 26 FPS. Their 96% average
renderer share leaves too little headroom for peaks and the rest of the loop.
Eight CPU balls run around 25 FPS restore / 16.7 FPS trails.

Movement advances once per completed render update, so slower configurations
also traverse the path more slowly in wall-clock time. It is not driven from
VBL and does not install an independent interrupt owner. Different trajectory
coordinates/alignment can change rendering cost. These are emulator observations,
not measurements on physical hardware.

## Verification and artifacts

- `verification.json`: 420 full native buffer comparisons, 96 combinations of
  path/density/backend/mode, all 16 horizontal phases, overlap and outer legal
  positions, eight forced trajectory wraps, controls/pause and clean exit.
- `release-smoke.json`: the actual shipped PRG tested with **1 MiB RAM**, default
  four-ball BLiTTER mode, switches, pause and clean TOS exit. An external symbol
  file maps the same executable code/data; embedded ELF debug-section metadata
  differs between stripped/unstripped links and is not executable effect code.
- `release-smoke-st.json`: the same shipped PRG on plain ST / no BLiTTER,
  1 MiB, TOS 2.06; automatic CPU fallback, controls/pause and clean exit pass.
- `profiling.json`: twelve complete 360-update profiles and eight live windows.
  Sprite call counts are checked against the chosen renderer and trail mode;
  phase indices return to their starting values after each cycle.
- `preview-restore.png` / `preview-trails.png`: decoded complete planar pages.
  Both pages share the same mask/palette rules; screenshots are not used as a
  substitute for byte comparisons.

The PRG is 88083 bytes (about 86 KiB). Prepared paths/sprites/palette use 9572 B,
plus small descriptor tables. Two chunk lists use 392 B; current/previous
coordinates and phase indices use another 80 B. Screen owns its usual pages
and clean Back buffer. No frame cache or runtime sprite heap is allocated.
