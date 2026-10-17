# Snowfall

An Atari ST/STE snow simulation over a generated winter scene, 320x200,
four planes. `SNOW.PRG` embeds its picture and palette; it needs no external
files, STOS runtime, blitter, STE scrolling or raster interrupts.

```sh
make
make run
```

- Space: pause/resume.
- S: one simulation step while paused, without adding flakes.
- 1/2/3: emit 4/8/16 flakes per simulation update.
- C: reset the original scene and initial shower.
- Left/right mouse button: paint/erase small obstacles in the scene. Paint marks
  show the current mouse position; the TOS cursor is not used.
- Esc: return to TOS.

## How it works

`snow_s.s` adapts Jason J Railton's `SNOWMOVE.S`, dated 12 December 1996 for the
ICTARI user group, from
`Atari_ST_Sources/STOS/Jason J Railton (Falcon)/SNOWFALL/M_CODE/`.
The original author/date and algorithm comments are retained. The wrapper
preserves C registers and reads the simulation screen pointer from C. Empty
source words are skipped before any collision-mask reads. If all flakes in a
word can move straight down, the routine skips diagonal processing altogether.
Neighbour masks are read only when needed; the original fall/slide priority is
preserved exactly.

The first three bitplanes contain the static eight-colour picture. Plane four
is snow (colour 8); any nonzero pixel acts as an obstacle. The kernel scans from
bottom to top, right to left, moving snow down, then diagonally right, then
left when blocked. Snow piles on scenery and on other flakes. It handles
16 pixels at once with word/long operations; C only controls emission, input
and scene setup through existing GodLib drawing kernels.

The simulation runs directly on **one displayed 32000-byte buffer**, aligned to
256 bytes and allocated with GodLib screen memory helpers. `GraphicCanvas` draws
into it, `Video_SetPhysic` displays it, and `Vbl_WaitVbl` paces updates. There is
no per-update screen copy, page flip, extra display page or ScreenBack. The
picture is copied once at setup and again on reset. This also reduces allocated
screen memory from three pages to one. The original kernel assumes stride 160,
width 320 and height 200. Closed side edges and a solid bottom prevent the linear
neighbour scan from wrapping particles across screen boundaries.

The kernel may take longer than a PAL frame and writes to the active display.
Unlike double buffering, this does not promise an atomic image change: a scanout
can catch a flake between its destination write and source clear. Static scenery
is not cleared or redrawn during ordinary snowfall. This is a deliberate tradeoff
for this particle effect, not a claim of tear-free general-purpose rendering.

## Measured cost

Hatari hrdb instruction-cycle profiles, ST PAL 68000 at 8 MHz, 1 MB, TOS 2.06,
default emission (8 flakes/update), using the same profile driver:

| Operation | Initial version | Optimized single-buffer version |
| --- | ---: | ---: |
| Snow simulation, average cycles/update | 546087 | 328573 |
| Display copy, average cycles/call | 147709 | 0 |
| Simulation calls in ~6.45 emulated seconds | 64 | 114 |
| Updates per emulated second | 9.9 | 17.7 |

Measured update throughput improves **1.78x**. Simulation plus copy active cost
falls from about 694000 to 329000 cycles (about 86.7 to 41.1 ms at 8 MHz).
The remaining time includes interrupts and VBL pacing. Emission/rendering of new
flakes is much smaller than the simulation and was not the main bottleneck.

These are evolving scenes, not identical-input timing samples: a faster version
emits more flakes over the same interval. Dense settled piles can change the
cost. `analysis/performance.json` keeps the raw summary and this caveat.
`analysis/profile.py` uses the hrdb cycle profiler; wall-clock script duration
includes debugger overhead and is not used to compute update rate.

## Artwork

`assets/winter-source.png` is AI-generated pixel-art-style winter artwork made
for this example: a cabin, evergreen trees and an empty navy sky. Offline
`tools/prepare.py` resizes it to 320x200, assigns seven foreground colours plus
sky colour 0, and writes ST planar data and a palette. The fourth plane is
initially empty; colours 8..15 are white for moving snow. Sky is mapped to colour
0 so it does not block the simulation. Objects and distant scenery all count as
solid; this example has no separate collision mask.

The original generated artwork and the converted `assets/winter-st.png` preview
are included. Regeneration needs Python 3 and Pillow; generated planar data is
embedded with vasm. No runtime per-pixel image conversion is performed.

## Verification

```sh
make debug
python3 analysis/verify-hatari.py
```

The harness runs ST/TOS 2.06, STE/TOS 2.06 and STE/TOS 1.62 with 1 MB RAM at
8 MHz. It checks animation, pause, a single step without emission (snow pixel
count conserved, vertical movement, static planes unchanged), closed boundaries,
density selection, reset, resume and clean exit followed by five seconds of
observation. Set HATARI_TOS and HATARI_TOS162 to override ROM locations.
`make verify` builds `analysis/SVER.PRG`. Run
`python3 analysis/verify-equivalence.py` to compare the optimized kernel against
the previous implementation over 1200 identical evolving inputs, including
dense snow, new platforms, an erased gap and accumulating piles. Every screen
byte must match; the completed run reports zero mismatches. The reference kernel
and scratch buffer exist only in this verification executable, not SNOW.PRG.
This does not claim 50 simulation steps per second or a real-hardware test.

To reproduce the profiles (requires hatari-hrdb and the installed profiling helper):

```sh
make baseline debug
python3 analysis/profile.py baseline
python3 analysis/profile.py optimized
```

The preserved baseline source is in `analysis/baseline.c` and `analysis/baseline_s.s`.
Only the optimized kernel is linked into the normal example.

## Artwork conversion update

Generated scene artwork now uses **ABC2, STE RGB444, without dithering**.
See the [shared artwork guide](../tools/ARTWORK.md) for reserved colours,
regeneration, shared copies and validation. Snowfall retains eight background
colours to leave its snow bitplane free. Older ST screenshots and CPU results
above refer to their original artwork revision.
