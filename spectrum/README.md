# Spectrum 512 / 4096

Two standalone GodLib examples for PAL Atari ST/STE, 68000 at 8 MHz, 1 MB RAM:

- `SPEC.PRG`: the original Spectrum picture from `stsys10/spec512/pic.spu`.
- `SPEC4K.PRG`: a generated RGB test card displaying all 4096 STE colours;
  reducing it to the ST palette leaves exactly 512 distinct colours.

Both use the same 320x199 Spectrum display kernel. The first visible line is
blank because it is used to establish horizontal synchronization.

```sh
make -C /Users/kriss/GCC.ELF/godlib.spl/spectrum
```

Controls:

- `1`: ST palette (3 bits per component, 512 possible colours).
- `2`: STE palette (4 bits per component, 4096 possible colours), on STE only.
- Space: toggle Spectrum rasters / a single fixed 16-colour palette.
- Esc: restore the desktop.

ST starts in mode 1; STE starts in mode 2. The original picture uses 205 distinct
STE palette words (204 after ST reduction); the test card demonstrates the
complete palette. The picture's bitmap stays unchanged when switching modes.

## How it works

The renderer is adapted from Dead Hackers Society's September 2011 Synclock
Demosystem, specifically `stsys10/spec512/spec512.s` and `sys/common.s`
(ae / DHS). The original picture is retained with its source attribution.
The self-generated test card is produced by `tools/chart.py`.

The shifter still reads four bitplanes and has 16 colour registers. During
199 scanlines, the CPU streams three sets of 16 palette words per line. These
48 writes happen at staggered horizontal positions; they are not 48 freely
selectable colours at every X. The names 512 and 4096 refer to the hardware
colour pool; the test card uses different colours on successive lines to show
the complete pool across the image.

Each unrolled line takes exactly 512 cycles:

- eight memory-to-memory `MOVE.L` instructions: 160 cycles;
- five NOPs and three address-register moves: 32 cycles;
- another sixteen `MOVE.L` instructions: 320 cycles.

The code is repeated 199 times, with one final RTS, matching the original
stsys10 code copier. There is no per-line branch, runtime bitmap conversion,
blitter operation or screen copying. A faster MOVEM palette write cannot simply
replace this stream: its different timing would move the horizontal colour
boundaries relative to the SPU bitmap.

C sets up the display and snapshots the selected palette in GodLib's VBL video
callback. Timer A (/50, count 180) fires before the first visible line. Its ASM
handler uses STOP/HBL and the live shifter counter at `$FFFF8209` for hard sync,
then executes the palette stream with interrupts masked. The preamble retains
stsys10 timing: 33 NOPs plus an absolute pointer load instead of 35 NOPs plus LEA.
The Makefile deliberately omits linker `--relax` so critical call timings cannot
change during linking.

Timer A, the HBL vector, GodLib video/HBI callbacks and Timer C's mask are saved
and restored. Timer B is not used. Timer C is deferred during display, so TOS's
200 Hz time does not advance normally; it must not be used to measure this
sample. This renderer owns Timer A and the visible display period; integrating
sound playback, another raster owner or active blitter work requires explicit
scheduling. Keyboard bytes arriving during the critical section are deferred.

## SPU assets and references

`tools/prepare.py` splits the original 51,104-byte SPU into a 32,000-byte bitmap
and 19,104-byte palette streams. ST palette generation removes the STE low-bit
extensions with `& 0x777`; STE retains the original 12-bit register values.
`tools/chart.py` emits the analogous test-card assets. All conversion is offline.

The independent host decoder follows Steve Belczyk's public-domain `FindIndex`
formula, December 1990, reproduced in
[ST NEWS: ST Picture Formats](https://st-news.com/issues/st-news-volume-7-issue-3/ed-lit/st-picture-formats).
The bank depends on both screen X and the pixel's 4-bit colour index. Component
values in reference PNGs use Hatari's RGB expansion (ST: component * 34; STE:
rotate the extra component bit into bit zero, then multiply by 17).

## Verification and CPU cost

```sh
make -C /Users/kriss/GCC.ELF/godlib.spl/spectrum debug
python3 /Users/kriss/GCC.ELF/godlib.spl/spectrum/analysis/verify-hatari.py
python3 /Users/kriss/GCC.ELF/godlib.spl/spectrum/analysis/verify-hatari.py --chart
python3 /Users/kriss/GCC.ELF/godlib.spl/spectrum/analysis/profile.py
```

The harness compares all 64,000 displayed pixels with an independent SPU
reference, checks the two palette modes, fixed-palette comparison, re-enabling
rasters, clean exit and restored Timer A/HBL vectors. Palette traces verify
all 9,552 colour-word writes in every complete captured frame: the first is at
line 63, cycle 404, with a fixed 512-cycle interval between corresponding writes
in consecutive image rows. Results are stored under `analysis/`.

Hatari-hrdb measurements, 68000 8 MHz / 1 MB / TOS 2.06:

| Hardware | Palette stream | Whole Timer A handler | Time at 8 MHz | PAL frame budget |
|---|---:|---:|---:|---:|
| ST | 101,904 cycles | ~104,680 cycles | 13.09 ms | 65.3% |
| STE | 101,904 cycles | ~104,673 cycles | 13.08 ms | 65.3% |

The stream total includes the final RTS; the whole-handler figure includes
register save/restore and hard synchronization. It excludes the main loop,
VBL and input overhead. Measurements are from emulation, not physical hardware.
The same instruction stream runs in every palette mode and in both programs.

Verification passed for both programs on ST / TOS 2.06, STE / TOS 2.06 and
STE / TOS 1.62 at 8 MHz with 1 MB RAM. Across these six runs, 30 full displayed
frames matched the independent reference, and 26 complete timing frames passed
(all 9,552 word writes each). The displayed test-card colour counts were verified
as exactly 512 on ST and 4096 on STE. See `analysis/verification-summary.json`
and the individual `analysis/results*.json` files.
