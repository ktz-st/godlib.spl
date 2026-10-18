# Rotating hexagon iris — SuperHex

A standalone GodLib ST/STE example. **GodLib itself is unchanged.**
`N` grows a rotating black hexagon with a white outline, swaps pictures while
covered, then shrinks the hexagon to reveal the next scene. The mask occupies
bitplane 3; planes 0..2 contain the picture. This is a growing shutter, rather
than an aperture cut out of a black screen.

- `N`: next picture (ignored during a transition).
- `A`: automatic slideshow, initially off; four seconds between transitions at 50 Hz.
- `P`: pause/resume animation, including the rotation.
- `Esc`: return to TOS.

```sh
make
make run
```

The program embeds its two pictures and all tables. No external runtime files
are required. `make run` uses STE, 1 MiB, RGB PAL and **German TOS 1.62**;
plain ST also works. The optimized raster, sparse restore and strip copy use 68000 ASM on both
ST and STE; a blitter is not required. The `gIrisHasBlitter` debug
variable reports machine capability; the effect itself uses CPU ASM.

## Algorithm and palette

Ported from `../../superhex_ste/src/main.c`: `iris_fill`, the transition block
and the clipping used by `draw_line_clip`. The original is described in
`../../superhex_ste/HANDOFF.md`, “Etap 4j”. No original game binary is needed.

`geometry.c` retains the original Q14 sine values, six half-plane equations,
28.4 stepping, truncation and vertex rounding. It finds the active left/right
edge runs instead of testing all six equations on every scanline. Small native
`MULS.W`/`DIVS.W` helpers avoid general 32-bit arithmetic helpers when the
quotient is known to fit a signed word. `scan_s.s` emits the inclusive spans
using Q16 accumulators and `SWAP`; wholly empty or clipped-full runs have a
short constant-output path. C prepares coefficients/runs; raster work is ASM.

`live_s.s` compares the new spans with the previous spans of the **same display
page**. Only the two boundary intervals are XORed in plane 3. When a row enters
or leaves the polygon, one span is used rather than two overlapping intervals.
The XOR interiors are an unrolled instruction chain selected by word distance;
unchanged rows require no pixel writes. No animation bitmap cache is allocated
or generated.

The white outline is preserved pixel for pixel: the same clipped Bresenham
edges are drawn by an example-local ASM kernel specialized for white, fixed
160-byte stride, and X-major/Y-major left/right cases. Horizontal pixels are
accumulated into a word mask. Duplicating that mask in both halves of a longword
lets two `OR.L` operations colour all four planes at once.

Each touched four-plane word group appends a six-byte undo record: its address
and the old plane-3 word. Before rendering into that page again, records are
replayed backwards. Planes 0..2 come from the clean picture and plane 3 comes
from the saved word. Reverse order also handles shared vertices correctly.
This restores the outline without copying the full screen each animation tick.
The log has 512 records per page; a clipped convex hexagon needs fewer than
450. Native verification checks the capacity as well as displayed pixels.

Both embedded pictures receive their legends once during startup, in their
existing writable image storage. At a scene change, their palettes switch
under the closed shutter, and image planes 0..2 are copied in **50-row strips**
on each page. Plane 3 is preserved. Both pages finish their four strips before
uncovered picture pixels are displayed. Hidden image bits can differ during
that short copy; their displayed colour must remain identical black. There
are no extra full-screen clean-image allocations or prepared animation frames.

Per-page span history totals **1600 bytes**; sparse outline logs total **6144
bytes**. The X/mask lookup table is **1284 bytes**. The existing 800-byte span
command array, sine table and ordinary GodLib display buffers are separate.
All example-local storage belongs to the program; GodLib itself is unchanged.

The palette is deliberately constrained:

| Indices | Meaning |
| --- | --- |
| 0..6 | Seven source-picture colours; 0 is black. |
| 7 | White, reserved for the edge. Never present in the clean picture/text. |
| 8..14 | Black copies of source colours under the mask. |
| 15 | White edge under the mask. |

An eight-colour picture using index 7 would leave white holes in the shutter.
`prepare.py` therefore uses ABC2 with two forced-black slots, folds slot 7 into
0, and reserves 7/15 for the outline. Both existing RGB artworks (castle from
`water`, forest from `wipe`) are converted to STE RGB444 without dithering;
provenance, converter options and previews are in `assets/`. The mask is a
palette-bank selection, not alpha transparency.

The apothem grows from 0 to 220 pixels in 40 increments and decreases again.
220 covers the viewport at any angle. Rotation includes the original signed
`step * 14` term plus a continuous two-unit phase. There are 41 displayed steps
per direction, including endpoints; actual elapsed time depends on rendering
cost. Palette changes happen only when the displayed frame is fully covered,
so the two pictures may use different source palettes.

The white edge here writes index 15 through normal four-plane GodLib lines;
the SuperHex version ORs planes 0/1 over its more specialized scene/palette.
This adaptation reserves a source index and gives the same solid white edge
with arbitrary seven-colour artwork. It is not a pixel-perfect replay of the
whole SuperHex scene.

## Rebuilding assets and verification

`make assets` uses Python/Pillow and the local `../../abc/abc2`; normal builds
use the checked-in binary assets. Sine values follow SuperHex's `tools/gensin.py`
(including its positive Q14 clamp).

```sh
make debug
python3 analysis/verify.py
```

The native test uses German TOS 1.62 on STE and UK TOS 2.06 on plain ST
(TOS 1.62 is STE-only). It compares complete VRAM
against an independent implementation of the SuperHex half-plane equations,
clipped edges and Bresenham lines, covers both pages and both pictures, checks
physical-page palette synchronization, pause and exit. Its report and decoded
native-frame preview are in `analysis/`. This example adds no public GodLib API.

Recorded verification and timing are below; reports carry the final PRG hash.
For the strip copy while fully covered, tests compare displayed RGB colours
and require plane 3 to be completely set; otherwise they compare all 32000
framebuffer bytes exactly. Both source pictures, all 41 steps per direction,
both display pages, white edges, physical-page palettes, pause and clean exit
are checked.

## CPU measurements

On STE / 68000 / 8 MHz / 1 MiB / RGB PAL / German TOS 1.62, over complete
automatic grow/shrink transitions:

| Main procedure group | Original | Optimized |
| --- | ---: | ---: |
| Geometry C setup / old C scan | 27.68 ms | 2.73 ms |
| New ASM active-run scan | — | 2.71 ms |
| Fill / differential mask | 12.39 ms | 7.97 ms |
| Full background copy / hidden strips | 18.75 ms | 0.60 ms |
| Sparse outline undo | — | 2.81 ms |
| White outline ASM | 12.56 ms | 4.97 ms |
| Render dispatch / inline C clipping | 0.72 ms | 0.75 ms |
| Shared 32-bit arithmetic helpers | 1.26 ms | 0.48 ms |
| **Total measured main procedures** | **73.36 ms** | **23.02 ms** |

This is about **3.19 times faster**, or **68.6% fewer cycles per update**.
The optimized capture includes 164 geometry updates across two complete
transitions. These totals cover the named procedure ranges and shared math
helpers; they exclude VBL/Screen_Update/input, the small outer `Prepare` and
`Outcode` helpers, startup picture/font preparation, and unrelated library work.
They are average procedure costs, not a worst-case bound.

**Stable 50 FPS at 8 MHz has not been achieved.** The mean work already exceeds
the nominal 20 ms budget. Active transitions alternate 20/40 ms update intervals;
heavier middle steps run at 25 FPS. Measured transition-only cadence is about
**31 FPS** on ST/STE; idle holds are deliberately excluded. The raw frame/VBL
counts for both ST and STE are in `analysis/cadence.json`, including any late
step numbers and the explicit `achieved_50hz: false` result. No reduced outline,
skipped shape steps, duplicate-frame trick or animation bitmap cache is used.

`analysis/verification.json` records 249 completed output comparisons (166 STE,
83 ST) plus paused-buffer checks and clean exits. Source geometry and the white
outline remain identical to the original oracle; only the hidden lower planes
during a fully closed picture swap are compared by their displayed colours.

```sh
python3 analysis/profile.py
python3 analysis/verify-cadence.py
```

The profiler uses a private HRDB port (56124); the host-only DYLD interposer
in `analysis/hrdb-port.c` changes only its child emulator's bind port. It does
not connect to or pause another emulator session. `profile-before.json` is the
original binary from commit `c3b0b6f`; `profile-before.py` requires that exact
baseline build, so it cannot accidentally label the optimized build as before.
The same automatic-transition profiling procedure is used for both versions.
The counters include complete transitions and report active animation cadence
separately from the four-second holds; a high idle FPS is not a 50 FPS effect.
