# DCK vertical BIG scrollers

Three independent full-colour text columns using DCK's **BIG 40×32** font.
Each moves upward by **one pixel per frame**, with eight blank rows between
letters. The left, centre and right streams have different texts.

```sh
make
make run
```

Run **DCKVERT.PRG**. All assets are embedded. The renderer uses ordinary 68000
instructions: no BLiTTER, hardware scrolling, rasters or custom interrupts.
It targets ST/STE; native verification used an STE at 8 MHz, PAL RGB, 4 MB,
with German TOS 1.62. Physical hardware has not been tested.

| Key | Action |
|---|---|
| 1 / 2 / 3 | Show one, two or three columns; default three. |
| Space | Pause/resume the text. |
| R | Toggle a green timing marker around ASM Advance + Draw. |
| Esc | Return to TOS. |

## Implementation

This adapts the visual behaviour of DCK's one-line vertical scroller with a new
GodLib-compatible kernel, rather than embedding DCK's global state or vector
handling. GodLib owns Screen, double buffering, IKBD, VBL and the TOS lifecycle.
C sets up the display and handles keys. `dckvert_s.s` handles text decoding,
advancement, wrap and all runtime effect rendering.

Each column has a mirrored ring of 144 source-row pointers. Advancing one pixel
replaces just one pointer and moves the ring head. A glyph contributes 32 rows,
followed by eight blank rows. All streams continue advancing when fewer columns
are displayed. Initialization primes the windows so text is visible immediately.

`Vert_Draw` copies a 40×144 window per active column. A converted font row has
20 bytes: two complete 16-pixel/four-plane groups and four bytes for the last
8 pixels. `MOVEM.L` copies the first 32 pixels; `MOVEP.L` writes the last eight
into the appropriate interleaved plane bytes. Zero source pixels replace the
previous glyphs on each display page, so ordinary drawing requires neither a
whole-screen copy nor an additional erase pass. Changing the visible column
count refreshes each page's static background once.

This is a vertical **stream of individual letters**, not a full-width credits
roller. The original palette is shared by all columns; the glyphs themselves
retain the original multiple colours. The 40-pixel columns begin at X=48,
144 and 240; their windows cover Y=28..171.

## Measured CPU cost

Hatari-HRDB, STE / MC68000 8 MHz / PAL / German TOS 1.62. Each measurement covers
32 completed `Vert_Advance` + `Vert_Draw` calls. Cycles include ASM loops and
memory traffic, but exclude startup, GodLib screen waits/input and interrupt
handlers. The denominator is 160000 cycles per 20 ms PAL frame.

| Columns | Cycles/update | Time at 8 MHz | PAL frame budget |
|---|---:|---:|---:|
| 1 | 22879 | 2.86 ms | 14.3% |
| 2 | 44327 | 5.54 ms | 27.7% |
| 3 | 65784 | 8.22 ms | **41.1%** |

A separate normal-loop cadence check completed **5962 frames with zero missed
VBLs: 50 FPS** with all three columns. The R marker shows elapsed render time,
not an independent CPU profile. Emulator results are not physical Atari timings.

## Memory and assets

The font uses 31360 bytes, the three mirrored pointer rings 3456 bytes and
stream state 48 bytes. There is no generated-code buffer, frame cache or
additional scrolling bitmap. GodLib's normal screen buffers and other library
state are separate.

`source/BIG.png` and `source/BIG.PI1` are lossless extracts of DCK disk B's
`FONTES/BIG.PC1`. `tools/assets.py` rebuilds row-packed font data, the original
palette and three text streams. Normal builds and asset generation require no
external DCK directory. The original font artist beyond its presence in DCK
has not been established.

## Verification

The native framebuffer was checked against the **original PNG atlas**, using
live row-pointer and ring-head state: 17280 effect pixels, zero mismatches.
Column selection, pause with unchanged stream state, resume and clean exit
also passed. Results are in `profiling.json` and `verification.json`;
`preview.png` is a native capture.

```sh
make assets
make debug                      # /tmp/DCKVDBG.PRG and /tmp/DCKVDBG.map
python3 tools/check.py           # stock Hatari: controls and cadence
python3 tools/profile.py         # Hatari-HRDB: pixels and exact call counts
```

The tools use the local hatari-debugging skill helpers and temporary files
outside the repository. HRDB defaults to port 56001; set `DCKV_HRDB_PORT` if
the emulator is configured or mapped to another port. The recorded profiling
session used an isolated local port mapping.
