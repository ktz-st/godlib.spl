# Two transparent checkerboard layers

`LAYFX.PRG` is a self-contained ST/STE example using two independent bitplanes.
The 320x128 effect occupies y=40..167 in a standard 320x200 low-resolution screen.
It needs a 68000, without a BLiTTER or STE scrolling registers.

```sh
make
make run
```

| Key | Action |
| --- | --- |
| 1 | Freeze/resume layer A |
| 2 | Freeze/resume layer B |
| Space | Pause/resume both layers |
| P | Switch additive / averaged overlap colours |
| R | Toggle the visible CPU timing band |
| Esc | Restore TOS |

Layer A uses 16x16 cells, moves right/down by one pixel per frame and writes
plane zero. Layer B uses 8x8 cells, moves left by one and down by two pixels,
and writes plane one. The colour index is `A + 2*B`: palette entry 0 is the
background, 1 and 2 are the individual layers, and 3 defines their intersection.
The initial palette makes the intersection additive magenta; `P` changes only
its palette entry to the red/blue average. This is palette-based translucency,
without alpha arithmetic over the framebuffer.

## ASM renderer

The approach follows the cyclic-pattern technique in Tom/SMFX's
`Atari_ST_Sources/ASM/SMFX/indecision.128/indecis.s` (August 2023). This
adaptation uses a normal GodLib lifecycle, two pages, separately controlled
layer offsets and two palette mixing styles, instead of the 128-byte demo's
custom VBL/supervisor setup.

`planemix_s.s` rotates a 32-bit pattern for A and a 16-bit pattern for B.
Their two alternating word pairs are prepared once per call. Each `MOVE.L`
writes one word of each layer; crossing a vertical cell boundary inverts the
appropriate half of each pair. The other two bitplanes are untouched.
There are no cached animation frames or full-screen copies during animation.
C handles input, offset advancement, palette selection and frame counters.
The current destination layout is fixed at a 160-byte stride.

## Measurements and verification

```sh
make debug
python3 analysis/profile.py
python3 analysis/verify-hatari.py
```

Hatari-HRDB, ST/68000 at 8 MHz, 1 MB RAM, TOS 2.06, PAL: the complete ASM
renderer averages **50343 cycles / 6.293 ms / 31.41%** of a PAL frame.
Animation runs at approximately **50 updates/s**. Input, VBL waiting and C
coordinate advancement are outside that kernel range; register saves and all
128 raster rows are included. Measurements use a disabled timing band.
See [profile.json](analysis/profile.json).

`R` places the coloured interval near visible row 8 using a shifter-counter
wait outside the measured work. `make run` uses `--spec512 1` so Hatari renders
ST palette changes accurately. The green band is elapsed renderer time, not
whole-program CPU usage.

The independent reference builds every pixel from the two checker equations
and compares all 32000 screen bytes. It covers a complete 32-frame joint
cycle, both pages, independent freezing, pause, palette change, the timing
marker and clean exit on ST/TOS 2.06 and STE/TOS 2.06/1.62, all 8 MHz / 1 MB.
Results are in `analysis/results*.json`.

The short output name also avoids the TOS 1.62 autostart filename regression
already documented by the [palette-split example](../palsplit/README.md#tos-162-exit-and-filename-regression).

All three configurations passed: **219 complete-screen comparisons**,
with no missed VBLs. See [verification summary](analysis/verification-summary.json).

The visible timing band and palette restoration can be checked separately:

```sh
python3 analysis/verify-meter.py
```
