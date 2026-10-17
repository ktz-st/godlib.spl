# STE Phase Scrolling

`PHASE.PRG` adapts Jeffrey Young / TheNameOfTheGame's **horizontal phase
scrolling** to GodLib. A 320x160 playfield scrolls beneath a fixed 320x40 HUD
with its own palette. Requires STE video and a BLiTTER; MegaSTE should be run
at 8 MHz for the timings described here.

```sh
make
make run
```

All graphics and map data are embedded. Run the PRG on an STE; no extra files
are required. The display remains ordinary PAL 320x200, without open borders.

| Key | Action |
| --- | --- |
| `1`, `2`, `4`, `8` | Scroll speed in pixels per frame |
| `0` | Stop camera movement |
| `Space` | Reverse direction |
| Left / Right | Select direction |
| `R` | Toggle the border timing marker |
| `Esc` | Return to TOS |

The camera bounces at the map edges, X=0 and X=1984. Changing speed resumes
movement after `0`. The map is 144x100 tiles of 16x16 pixels; this horizontal
example uses rows 22..31, matching the upstream demonstration.

## How phase scrolling works

The STE fine-scroll register moves the view between 16-pixel tile boundaries.
A 184-byte-stride scanwalk buffer holds twenty visible tile columns, the extra
fine-scroll column and hidden update columns. Coarse movement changes its
starting pointer by eight bytes. A small extra tail permits the pointer to
walk across the map without copying the full playfield back to its origin.

Before an update column becomes visible, its tile graphics must be ready.
The original algorithm spreads that copying across the sixteen fine-scroll
phases. With a 160-row playfield, speed 1 prepares 10 scanlines of the hidden
column per update; speed 2 prepares 20, speed 4 prepares 40 and speed 8 prepares
80. The BLiTTER copies four planar words per scanline in HOG mode.

The original phase normalization, direction handling, fill gauge, gap
compensation and gap completion remain in `phase_s.s`. Those last two paths
fill missing portions when speed changes would otherwise expose unfinished
column data. This is a phased tile renderer, rather than a large pre-rendered
picture moved through RAM.

As upstream, speed zero stops the camera but lets phase processing idle using
the previous speed. It is not a zero-work pause. The runtime copy and scrolling
kernels are 68000 assembly; C handles setup, controls and publishing frame state.

## GodLib integration

- GodLib owns Platform, Screen, IKBD and the VBL handler. The original
  stand-alone supervisor, keyboard and interrupt takeover code is not used.
- Tile graphics occupy the first 32K of an allocated, 64K-aligned ST-RAM bank;
  the private scanwalk buffer occupies its second 32K. The original optimized
  low-word BLiTTER address writes therefore remain valid without hard-coded
  physical addresses. `Memory_ScreenCalloc(131071)` provides space to align a
  full 64K bank; the returned allocation is released on exit.
- The scanwalk playfield uses one buffer. GodLib's normal screen storage
  provides the fixed HUD and a normal display page for teardown.
- The local `split.c` / `split_s.s` adapt the tested `splitscreenh` integration
  to a 40-row HUD and 184-byte terrain stride. Timer B is rearmed by GodLib's
  VBL, not from the game loop. The HUD and terrain use independent palettes.
- Pointer, fine-scroll and camera coordinates are published together under a
  short IPL guard, then snapshotted by VBL for the following split. The live
  shifter writes are synchronized to horizontal blank.
- The split temporarily defers TOS Timer C. Animation uses VBL counts; HZ200
  is unsuitable for measuring this effect. Detach the raster before releasing
  its memory or calling Screen/Platform deinitialization.

This example owns BLiTTER configuration and Timer B while active. Integrating
it into a game also using GodLib BLiTTER drawing requires restoring these copy
parameters before the phase kernel and coordinating raster ownership.

## Source and assets

Upstream project: `jayoung99/Atari-STE-Hardware-Phase-Scrolling`.
The local source is in `Atari_ST_Sources/ASM/Various/Jeffrey Young
(TheNameOfTheGame)/Atari-STE-Hardware-Phase-Scrolling/HPSCROLL.S`, revision 1.01.
The original annotated algorithm is preserved in the adapted ASM.

Tile graphics are by **Simon Phipps / Core Design**, included solely for
this demonstration, as in the upstream project. `TDATA.BIN` and `LMAP.BIN`
are unchanged. `assets/provenance.json` records their hashes and source.
The HUD is drawn with GodLib's font and uses a separate palette.

## Verification and profiling

```sh
make debug
python3 analysis/verify-hatari.py
python3 analysis/verify-hatari.py --tos162
python3 analysis/profile.py
```

The verification builds an independent rectangular picture from the original
map and tiles. It compares the composed scanwalk view, all sixteen fine-scroll
phases, both directions, every speed, abrupt speed/direction changes, and
travel to both map edges. It also compares actual Hatari display pixels,
including the fixed HUD, checks live video-register timing and memory guards,
and verifies input handling, handler removal and clean exit to TOS.

Measurements use Hatari-HRDB, STE, 68000 at 8 MHz, 1 MB ST RAM, TOS 2.06,
PAL 50 Hz, with the border marker disabled. Kernel cycles include BLiTTER HOG
stalls; split ISR cycles are reported separately. GodLib/input/VBL overhead
and startup population are excluded. Raw captures and the resulting table are
in `analysis/profile-raw-*.json` and `analysis/profile.json`.

Steady-state results:

| Speed | Phase kernel | Kernel + HUD split | PAL frame budget, including split |
| --- | ---: | ---: | ---: |
| 1 px/frame | 0.203 ms | 0.385 ms | **1.92%** |
| 2 px/frame | 0.253 ms | 0.436 ms | **2.18%** |
| 4 px/frame | 0.354 ms | 0.537 ms | **2.68%** |
| 8 px/frame | 0.557 ms | 0.739 ms | **3.69%** |
| 0 (idle at previous speed 1) | 0.178 ms | 0.361 ms | **1.80%** |

All moving speeds deliver **50 updates/second**. The HUD split alone takes
1,460 cycles (0.183 ms). These are steady-state averages; abrupt speed changes
can require extra gap completion work. Percentages use 160,256 cycles per PAL
frame. These are emulator measurements, not a real-machine timing claim.

STE/TOS 2.06 and STE/TOS 1.62 both passed at 8 MHz with 1 MB RAM:
**1265 map comparisons**, 2494 synchronized split frames, both map edges,
unchanged HUD, all controls and clean exit. No missed VBLs were recorded.
See `analysis/verification-summary.json` and `analysis/results-*.json`.
