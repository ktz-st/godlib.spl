# Picture wobble in 68000 assembly

An Atari ST/STE software picture distortion: each of the 200 lines shifts
horizontally by a sine-table offset. The four-plane 320x200 COAST picture is
embedded in `WOBBLE.PRG`. No blitter, STE scroll registers or raster interrupt
are required. The image is the generated lighthouse/coast asset from `wipe`.

```sh
make
make run
```

- Space: pause/resume the wave.
- 0: unshifted picture (also exercises the copy-only fast path).
- 1/2/3: wave amplitudes 4/8/16 pixels; default 8.
- S: cycle phase speeds 1/2/4; default 2.
- Esc: exit to TOS.

## Rendering

The offline converter splits the ST picture into four packed bitplanes. Each
plane has 200 rows of 44 bytes: 320 source pixels with 16 zero pixels on either
side. This padding allows all offsets from -16 through +16 without out-of-range
reads or source wrap. Source colour 0 supplies uncovered edges (black here).
Generated data uses 35200 bytes; no preshifted animation frames are stored.

C prepares three words per line: coarse source-word offset, fine shift count and
kernel selection. It uses an integer sine table generated at build time; there
are no runtime floating-point calls or per-pixel C drawing loops.

`wobble_s.s` produces the complete four-plane image in ASM. It selects a direct
word-copy path when fine shift is zero. Otherwise it reads overlapping 32-bit
windows from each packed plane. Fine shifts 1..8 use LSL.L and SWAP; shifts 9..15
use LSR.L by 16-fine and take the low word, so no register shift exceeds eight.
Twenty word outputs per plane and line are unrolled. This writes every output
word; a separate clearing pass is unnecessary.

The example uses normal GodLib double buffering: Screen_Update presents a
complete frame while ASM renders into the logical page. Source width, height,
plane size and output stride are intentionally fixed for ST low resolution.
Changing resolution requires changing these constants and the asset converter.

## Checks and measurement

```sh
make debug
python3 analysis/verify-hatari.py
python3 analysis/profile.py
```

The functional check runs ST/TOS 2.06, STE/TOS 2.06 and STE/TOS 1.62 at 8 MHz with
1 MB RAM. It compares every byte in the output with an independent host planar
reference for amplitudes 0/4/8/16, covering all 33 horizontal offsets, left/right
clipping, pause, speed cycling, resume and clean exit with a five-second wait.
ROM overrides: HATARI_TOS and HATARI_TOS162.

The profiler requires hatari-hrdb and the installed Hatari helper. Rendering and
command-generation cycles are measured separately. Frame rate comes from target
frame/VBL counters, not from wall-clock script timing. Reported budget percentages
refer to one 160256-cycle PAL frame; a value above 100% means the software effect
cannot render at 50 Hz, rather than a physically impossible CPU utilisation.

## Results

Measured with hrdb on emulated ST PAL 68000 at 8 MHz, 1 MB, TOS 2.06, one fresh
emulator/profile capture per amplitude. Animation remained enabled. Timing is
averaged over complete/partial calls in the capture, so values are approximate.

| Amplitude | ASM draw cycles/update | C command cycles/update | Combined active time | Updates/s | Draw + commands share of captured cycles |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0 (copy benchmark) | 357944 | 59457 | 52.2 ms | 16.5 | 87.8% |
| 8 pixels (default) | 856405 | 60717 | 114.6 ms | 8.3 | 93.2% |
| 16 pixels | 728987 | 57728 | 98.3 ms | 10.0 | 97.0% |

The full-screen software effect does not fit a 20 ms PAL frame. Amplitude 16
can be cheaper than 8 because the sine distribution reaches more coarse,
word-aligned offsets, and the shifted paths have data-dependent shift counts.
The table reports the renderer plus command preparation, not a claim that these
functions are the only CPU work. Startup and reset are outside the capture.
This is not a hardware measurement.

`analysis/profile.json` stores the summaries; `profile-raw-*.json` stores address,
instruction and cycle samples. The profile driver also samples target frame/VBL
counters to determine the update rate independently of host wall time. The three
functional runs passed all 32000-byte comparisons and returned cleanly to TOS.
