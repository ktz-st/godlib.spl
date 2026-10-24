# DCK multiscroll

Three full-colour **BIG 40×32** scrollers follow different fixed curves: a sine,
a shallow arch and a zigzag. The original font/palette comes from DCK disk B,
`FONTES/BIG.PC1`. Runs on a 68000 ST/STE without BLiTTER or STE video registers.
Native verification and profiling used an STE, 8 MHz, PAL, 4 MB and German
TOS 1.62; physical hardware has not been tested.

```sh
make
make run
```

Launch **DCKSCRL.PRG**. All assets are embedded; no external runtime files.

| Key | Action |
|---|---|
| 1 / 2 / 3 | Draw one, two or all three scrollers; default three. |
| Space | Pause/resume text. |
| R | Toggle a green timing marker around Advance + Draw. |
| Esc | Return to TOS. |

The original DCK-style movement is **8 pixels per update**, 50 updates/s on
the tested configuration. The paths stay fixed; text flows along them. This
is deliberately not the smooth 1–2 pixel movement of the NIBBLE example.
The R marker is elapsed frame timing, not a separate CPU profiler.

## ASM implementation

DCK's TEXT $076C–$085C builds a specialized sequence of byte-copy instructions
for a fixed 40-column route. This example adapts that principle and visual
stepping, rather than embedding the original runtime or its interrupt takeover.

- `Dck_Build` emits three native 68000 instruction streams once at startup.
  Each column loads its source pointer, then performs 32 pairs of
  `MOVE.L (A0)+,D0` / `MOVEP.L D0,d16(A1)`. The displacement already contains
  the curve's Y, row stride and screen X position. No curve arithmetic or MULU
  remains in the per-pixel drawing path.
- `MOVEP.L` places four packed source bytes into destination bytes 0/2/4/6,
  the same eight pixels in all four interleaved bitplanes. A byte column
  therefore retains all 16 possible source palette indices.
- Unlike DCK's screen-to-screen shifting, each visible column points directly
  into a converted font. `Dck_Advance` updates a mirrored ring of 40 column
  pointers per lane; it does not copy a full text conveyor. All three streams
  continue advancing when fewer lanes are displayed.
- Source strips include background-zero pixels. Since the route never moves,
  drawing every column also replaces the complete previous footprint on each
  display page. No screen copy or per-frame full-band clear is required.
- GodLib owns Platform, Screen, IKBD, VBL and double buffering. C prepares the
  display and handles controls; the text advancement, code generator and
  runtime graphics are ASM. There are no custom raster interrupts.

This is a plain 68000 target. Code is written before its first execution;
accelerated CPUs with instruction caches would need their own cache handling.
The original DCK text-command interpreter and its other modes are not included.

## CPU and frame rate

Hatari-HRDB, MC68000 8 MHz, STE PAL RGB, German TOS 1.62. Each entry covers
**32 completed updates**, includes generated BSS code and both ASM routines,
and excludes input, GodLib screen waits, interrupt handlers and startup.
Percentages use the 160000-cycle / 20 ms PAL frame budget.

| Lanes | Cycles/update | Time | PAL frame budget |
|---|---:|---:|---:|
| 1 | 48202 | 6.03 ms | 30.1% |
| 2 | 94986 | 11.87 ms | 59.4% |
| 3 | 141741 | 17.72 ms | 88.6% |

The normal three-lane loop completed **5261 updates with zero missed VBLs**
(50 FPS) in a separate stock-Hatari cadence check. Most of the frame is used;
this is not a promise that an application can add substantial work and retain
50 FPS. These are emulator measurements, not physical-machine benchmarks.

## Memory and assets

- Converted font: 31360 bytes (49 cells including a blank space, five 8-pixel
  columns per 40×32 glyph, four plane bytes per row).
- Generated kernels: **23286 bytes**, 7762 per curve. This is executable code,
  not a cache of animation frames.
- Mirrored column pointers: 960 bytes; stream state: 48 bytes.
- Curve table: 240 bytes, plus palette/text; GodLib's screen allocations and
  other library state are separate.

`source/BIG.png` and `source/BIG.PI1` retain the losslessly extracted atlas.
`tools/assets.py` rebuilds packed font strips, palette, curves and text from
these bundled sources. No DCK checkout is needed for a normal build or asset
regeneration. Asset conversion is offline; runtime does not rasterize in C.
The original font attribution beyond its presence in DCK is not known.

## Verification

Native output was compared with an independent host reconstruction from the
font strips: **30720 effect pixels, zero mismatches**, covering all three
curves. Keys 1/2/3, pause with unchanged text state, resume and clean exit passed.
Results are in `profiling.json` and `verification.json`; `preview.png` is a
native capture. Temporary dumps/logs are kept outside the repository.

```sh
make assets
make debug                     # /tmp/DCKDBG.PRG and /tmp/DCKDBG.map
python3 tools/check.py          # stock Hatari controls/cadence
python3 tools/profile.py        # Hatari-HRDB, default port 56001
```

The tools use the local hatari-debugging skill helpers. If a local HRDB setup
uses another port, set `DCK_HRDB_PORT`; the emulator must expose the same port.
The recorded session used an isolated local port mapping. The profiler also
checks output pixels and exact native draw-call counts before reporting cycles.
