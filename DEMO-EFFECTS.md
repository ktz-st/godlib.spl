# Demo effects

These standalone GodLib examples use 68000 assembly for runtime rendering.
C handles setup, input and animation state. Each linked README describes the
controls, asset preparation, renderer limits and recorded Hatari tests.

From this repository, build with `make -C <directory>` and run with
`make -C <directory> run`. The local GodLib and libcmini builds and the GCC ELF /
vasm toolchain are required. All effects below embed their runtime assets.
Build-time table generation uses Python; rebuilding RGB artwork also requires
Pillow and ABC2. Source artwork and conversion scripts are included. REFLECT requires the accompanying GodLib reflection API.

## Scrollers

| Example | Hardware | Technique |
| --- | --- | --- |
| [Fast BUGSY](fastscroll/README.md) | ST/STE | Plain 32x27 text, one ASM conveyor shift per update, four speeds. |
| [NIBBLE](nibble/README.md) | ST/STE | Original Lost Boys nibble wave, two waveforms and a straight mode. |
| [8x8 comparison](scroll8/README.md) | ST/STE | GodLib font, MCoder versus optimized Griff at two pixels per frame; cache and CPU comparison. |
| [Phase scrolling](phasescroll/README.md) | STE + blitter | Scanwalk tile buffer, hardware fine scroll, fixed HUD and independent palettes. |

## Image distortion and water

| Example | Hardware | Technique |
| --- | --- | --- |
| [Wobble](wobble/README.md) | ST/STE | Preshifted rows, MOVEM copies and reuse of unchanged rows on each page. |
| [FLAGWAVE](flagwave/README.md) | ST/STE | Vertical strips with a mouse delay queue or automatic sine. |
| [Lens](lens/README.md) | ST/STE, 1 MiB | Mouse or automatic 64x64 magnifier, inverse mapping and lookup C2P. Uses the original renderer with 384,000 bytes of prepared source RAM. |
| [Ugh-style water](water/README.md) | ST/STE | Repeated/skipped lake rows and animated surface glints. |
| [Missing Link REFLECT](reflect/README.md) | ST/STE | Original row-wave algorithm, ASM library API and comparison against extracted original machine code. |

## Bitplanes, sprites and particles

| Example | Hardware | Technique |
| --- | --- | --- |
| [Checkerboard](checker/README.md) | ST/STE | Rotating and zooming checkerboard drawn from precomputed span commands. |
| [Two translucent boards](planemix/README.md) | ST/STE | Independently moving planes; their overlap colour comes from the palette. |
| [Torch](torch/README.md) | ST/STE | Mouse-controlled circle in the fourth plane selects dim/bright palette banks over an eight-colour castle. |
| [Masked moon and stars](spritemask/README.md) | ST/STE, 1 MiB | ASM cuts the foreground out of a work sprite; normal GodLib CPU/blitter sprites draw the crescent and four twinkling stars. Bitmap sky dithering, fixed palette, black index 0, 15 used colours. |
| [Snowfall](snowfall/README.md) | ST/STE | Word-based snow simulation, settling and drifts, directly in one displayed buffer. |
| [3D stars](starfield/README.md) | ST/STE | demOS projection tables, generated pixel routines and sparse per-page erase lists. |

## Palette effects and scrolling displays

[Spectrum 512/4096](spectrum/README.md) streams palettes with cycle-exact ASM.
It includes an original Spectrum picture and a generated full-gamut test card.
Unlike the bitmap gradient in `spritemask`, it depends on raster timing.

The [top HUD / horizontal scroll](splitscreenh/README.md) example now gives the
HUD and playfield separate palettes as well as separate fine-scroll/stride
settings. Related examples are [vertical split](splitscreen/README.md),
[palette split](palsplit/README.md) and [raster bars](rasters/README.md).

[Shared artwork notes](tools/ARTWORK.md) explain the ABC2 STE conversion,
reserved colours and regeneration of scrolling/slideshow pictures.

## CPU and verification

Per-example `analysis/` directories retain measurement scripts and compact
results, independent framebuffer comparisons, source provenance and selected
previews. Consult the README for the tested machine, ROM, memory and scope.
Measurements generally target a PAL ST/STE at 8 MHz; renderer-only cycle counts
exclude setup, input and VBL waiting. Visible timing bands show elapsed time,
which can include synchronization, so they are not interchangeable with HRDB
instruction-cycle measurements.

The restored lens records 59.19% renderer CPU in stationary mouse mode and
62.13% in automatic mode, with 294 full-screen comparisons. The optimized
Griff scroller records 2.69% versus MCoder's 4.12%. The moon example records
258 full-screen comparisons across the ST CPU and STE blitter paths, including
occlusion, both pages, animation transitions, clipping, palette and clean exit.
These are recorded emulator results; this documentation update does not claim
new hardware measurements.
