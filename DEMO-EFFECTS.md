# Demo effects

These standalone GodLib examples use 68000 assembly for runtime rendering.
C handles setup, input and animation state. Each linked README describes the
controls, asset preparation, renderer limits and recorded Hatari tests.

From this repository, build with `make -C <directory>` and run with
`make -C <directory> run`. The local GodLib and libcmini builds and the GCC ELF /
vasm toolchain are required. Most effects below embed their runtime assets;
the GodLib WIPE slideshow preloads its three supplied PI1 files from disk.
Build-time table generation uses Python; rebuilding RGB artwork also requires
Pillow and ABC2. Source artwork and conversion scripts are included. REFLECT requires the accompanying GodLib reflection API.

## Scrollers

| Example | Hardware | Technique |
| --- | --- | --- |
| [Fast BUGSY](fastscroll/README.md) | ST/STE | Plain 32x27 text, one ASM conveyor shift per update, four speeds. |
| [NIBBLE](nibble/README.md) | ST/STE | Original Lost Boys nibble wave, two waveforms and a straight mode. |
| [8x8 comparison](scroll8/README.md) | ST/STE | GodLib font, MCoder versus optimized Griff at two pixels per frame; cache and CPU comparison. |
| [DCK route changes](dckroute/README.md) | ST/STE, 1 MiB | One full-colour BIG stream, ten original TRJ curves, FE P/H/V and profile commands, live curve morphing and per-page edge erase; 50 FPS. |
| [DCK curved multiscroll](dckscroll/README.md) | ST/STE | Three full-colour BIG scrollers on fixed curves, generated ASM/MOVEP kernels, original 8-pixel step. |
| [DCK vertical](dckvert/README.md) | ST/STE | Three full-colour BIG letter columns, one pixel upward per frame, ASM row-pointer rings and MOVEM/MOVEP. |
| [DCK horizontal](dckhoriz/README.md) | ST/STE | Simple full-colour ESCALI 16x16 scroller, compact MOVEP ASM, byte stepping. |
| [DCK multiscroll](dckmulti/README.md) | ST/STE | Six straight ESCALI streams with independent texts, directions and timers; no generated code. |
| [Phase scrolling](phasescroll/README.md) | STE + blitter | Scanwalk tile buffer, hardware fine scroll, fixed HUD and independent palettes. |

## Image distortion and water

| Example | Hardware | Technique |
| --- | --- | --- |
| [Moonlit Passage / cutscene](cutscene/README.md) | ST/STE | Native GodLib parser/player: two scenes, sprites, captions/fades and four narrated lines through AMIXER; replay/skip. |
| [SuperHex wedges](wedges/README.md) | ST/STE | Six rotating light/dark sectors from the title screen; cached CPU/blitter copy or 50 FPS differential live ASM without frame cache; inverted on odd sectors. |
| [SuperHex iris](iris/README.md) | ST/STE | Growing/shrinking rotating hexagon; ASM active-edge scan, differential plane-3 spans, sparse undo of the white outline and a stripwise picture swap under black. |
| [CRT / Wasteland Relay](crt/README.md) | STE / BLiTTER | Two eight-colour scenes, bright scan band, strip tearing and NIEZW-style glowing thin-line TV off/on transitions; ASM per-page updates. |
| [LCK bitmap transitions](lckwipe/README.md) | ST/STE, 1 MiB | Eleven live ASM modes covering all seven LCK appear and seven disappear entries: spiral/fold/strips/snake, instant, colour steps, centre/smear/interlaced rows and two column wipes; per-page progress, palette changes on black, no frame cache. |
| [GodLib WIPE](wipe/README.md) | ST/STE, optional BLiTTER | 39 library mask transitions, public CPU/blitter selection through Wipe_Update, live B toggle and canonical ScreenBack; unchanged tile masks and palette-safe three-image slideshow. |
| [Wobble](wobble/README.md) | ST/STE | Preshifted rows, MOVEM copies and reuse of unchanged rows on each page. |
| [DCK block operations](dckblock/README.md) | ST/STE, 1 MiB | ASM selected-plane rectangles, repeated/skipped rows, signed source/destination strides, moving blocks and strip rearrangement; per-page restoration, no frame cache. |
| [DCK bitplane wave](dckwave/README.md) | ST/STE, 1 MiB | Live ASM ROXR/ROXL chains over all, one or two planes; per-page differences and source-edge refill, no preshift/frame cache. |
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
| [DCK bobs](dckbobs/README.md) | ST/STE, optional BLiTTER | ASM DCK trajectory playback, normal GodLib masked sprites, per-page chunk restore or coherent persistent trails. |
| [DCK XOR stars](xorstars/README.md) | ST/STE | Four cardinal directions, 64/128/256 stars, reversible single-plane XOR with per-page erase lists. |
| [3D stars](starfield/README.md) | ST/STE | demOS projection tables, generated pixel routines and sparse per-page erase lists. |

## Palette effects and scrolling displays

[DCK TAPIS](dcktapis/README.md) animates the original ceiling/floor artwork
using fourteen unchanged COL palettes in a 178-byte ASM VBL callback. The
bitmap stays static; direction, pause/step and 1/2/4-VBL periods are selectable.
This temporal palette example uses no HBL or overscan.

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

New examples retain measurement scripts under `tools/`, with compact results,
source provenance and selected previews alongside their README. Older
`analysis/` directories have been removed to save disk space; consult each
README for the evidence still available, tested machine, ROM, memory and scope.
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
