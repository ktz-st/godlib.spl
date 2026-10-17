# Rotating and zooming checkerboard

`CHKFX.PRG` draws a rotating checkerboard with a continuous 2:1 zoom on
an ordinary ST or STE. The animated area is 320x96 pixels inside a standard
320x200 four-plane screen. No BLiTTER, STE fine scrolling or Timer B is needed.
The static colour bands give the board a blue-to-white gradient.

```sh
make
make run
```

| Key | Action |
| --- | --- |
| Space | Pause/resume |
| 1 / 2 / 3 | Advance 1 / 2 / 4 animation phases per frame |
| D | Reverse rotation and zoom animation |
| R | Toggle visible green CPU timing band |
| Esc | Return to TOS |

## Rendering

This is an original example-local 68000 span renderer, rather than a port of
the DHS Drone fullscreen checkerboard. The source survey also found SMFX's
checkerboards and its small parallax example; those are separate effects.

A checkerboard is the XOR of two perpendicular families of stripes. The
build-time generator rotates and scales their boundary equations, merges the
boundary positions on each scanline and emits horizontal span commands.
At runtime `checker_s.s` fills complete words and combines partial edges with
word masks. No per-pixel drawing runs in C, and there are no pre-rendered
bitmap frames. C handles GodLib setup, input and selection of a command list.

The animation uses 128 phases. Nominal cell size varies between 56 and 112
pixels; this range avoids the excessive edge count of the initial dense
version. Phase commands use **325412 bytes**, plus a **512-byte index**.
This deliberately trades precomputed geometry storage for CPU time. The
program is self-contained and is tested with 1 MB RAM. `PARAMS.BIN` contains
3584 bytes of coefficients for independent verification and is not linked
into the executable. Runtime raster code is 200 bytes, including the timing
synchronization helper; the unstripped debug build also contains symbols.

The renderer writes plane zero at y=56..151 with a fixed 160-byte destination
stride. Other planes hold the static background. Changing viewport dimensions,
cell sizes or phase count requires regenerating the commands and updating the
renderer constants. Free mouse-controlled rotation is not implemented by this
precomputed animation.

## CPU and verification

```sh
make debug
python3 analysis/profile.py
python3 analysis/verify-hatari.py
```

The profile uses Hatari-HRDB, ST/68000 at 8 MHz, 1 MB, TOS 2.06, PAL,
with the raster marker disabled. Results are in `analysis/profile.json`.
The current capture averages **90224 cycles / 11.28 ms / 56.30%** of a PAL
frame. The 128-phase animation is updated at approximately **50 Hz** in this
configuration; cost varies with the number of boundaries at each angle and scale.

The measured kernel includes its command decoding, span fills and register
saves, while input, VBL waiting and the C frame loop are outside that range.

`R` waits until visible row 8 and brackets drawing with palette colour zero.
It shows elapsed draw time rather than the percentage for the entire program.
`make run` uses Hatari's `--spec512 1` for accurate raster colours on ST.
The synchronization wait is excluded from the kernel profile.

The verification harness reconstructs pixels from the affine coefficients,
independently of the command stream, and compares all 32000 screen bytes.
It covers all 128 phases on ST, both screen pages, pause, three-speed selection,
reverse direction, marker toggle and clean return to TOS. Additional runs use
STE with TOS 2.06 and 1.62. All three passed: **277 complete-screen
comparisons**, with no missed VBLs and clean exit under the short filename.
See [verification-summary.json](analysis/verification-summary.json).
Results and screenshots are in `analysis/`.

`analysis/baseline-runtime/` preserves the first version, which prepared edge
lists during each frame. It is not the current renderer or a second build mode.

## TOS 1.62 autostart filename

Use the short output name `CHKFX.PRG`. The identical payload under the original
`CHECKER.PRG` name produced a desktop ROM bus error after program termination
in Hatari 2.6.1 with TOS 1.62 (PC `$E1FC9C`, read at `$455288F2`). This matches
the previously isolated [palsplit filename regression](../palsplit/README.md#tos-162-exit-and-filename-regression).
It occurs without the CPU marker and after the example has completed cleanup.
`analysis/smoke-exit.py` checks the shorter name; payload identity and the
before/after result are recorded in `analysis/exit-name-results.json`.
