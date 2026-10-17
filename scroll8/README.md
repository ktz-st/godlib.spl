# MCoder versus Griff — 8x8 ASM scrollers

Run `SCROLL8.PRG` on an ordinary ST or STE. Both scrollers use GodLib's
`gFont8x8`, the same text, all eight font rows, a 320-pixel viewport, one
bitplane and a fixed speed of **2 pixels per frame**. Neither requires a
BLiTTER or hardware fine scrolling.

```sh
make
make run
```

| Key | Action |
| --- | --- |
| `1` | MCoder only, top strip |
| `2` | Griff only, lower strip |
| `3` | Both, synchronized; default |
| `Space` | Pause/resume |
| `R` | Toggle visible CPU timing bands |
| `Esc` | Return to TOS |

Changing mode restarts the common text position and resumes animation.
The binary is self-contained. No fonts or other assets need to be loaded.

## Algorithms and adaptation

`scroll8_s.s` adapts two existing 68000 kernels:

- **MCoder**, `SCROL2.S`, The Lonely Coder.
  Four phases at shifts 0/2/4/6, eight 80-byte rows per phase, **2560 bytes**
  of cache. Each row contains a 40-byte circular strip and its duplicate.
  The renderer copies 40 bytes per row using byte loads/stores, which remain
  valid when the ring cursor is odd. It then updates one incoming byte and
  its duplicate per row using the original `MOVEP.W` / `ROL.W` sequence.
- **Griff / Martin Griffiths**, Electronic Images `bufsc8.s`, September 1990.
  Eight 672-byte phases at shifts 0/2/4/6/8/10/12/14: **5376 bytes**
  of cache plus eight guard bytes. Each row has a 42-byte ring and its
  duplicate; the extra word beyond the 40-byte viewport is needed when
  combining the incoming character pair. The screen copy uses twenty
  word moves per row.

MCoder retains its original multiply/address calculations and byte-copy loop.
Griff is optimized for this example's fixed speed of 2 pixels per frame:
unused odd phases are no longer generated or stored, the ring is shortened,
only registers actually touched are saved, and both eight-row loops are
unrolled. This preserves the displayed pixel stream, rather than changing
its resolution, font or speed. The original Griff used a 16384-byte cache;
the new cache saves **11008 bytes (67.2%)**. Its original 16-phase layout
would be needed for arbitrary one-pixel phase selection.

The differing text formats are replaced by common ASCII minus 32 indexing
into the font already linked from GodLib; `analysis/provenance.json` records
source files and hashes.

Both draw only plane zero, leaving the static background in the other planes.
The kernels update 320 pixel bytes on screen per strip. C handles GodLib
lifecycle, mode selection, frame synchronization and counters. No per-pixel
rendering is implemented in C.

The algorithms have different pipeline latency. Reset first clears their caches
in BSS and warms MCoder for 169 updates and Griff for 168. Both then display
text pixel 16 at the left edge; subsequent updates stay exactly synchronized.
Warmup and the full-screen copies used only on mode changes are excluded from
steady-state CPU measurements.

MCoder overwrites its outgoing cache byte *after* copying the displayed strip.
For pause, a separate ASM routine copies the two completed plane-zero strips
from the latest physical page to the next logical page. Thus both pages freeze
on the same image, without adding a snapshot-copy cost to the moving kernels.

## Measured CPU cost

Hatari-HRDB, plain ST, 68000 at **8 MHz**, **1 MB RAM**, TOS 2.06, PAL.
Both kernels were profiled in the same capture, with identical font, text
position and speed; the border marker was disabled.

| Kernel | Update/cache | Copy to screen | Total | Time | PAL frame budget |
| --- | ---: | ---: | ---: | ---: | ---: |
| MCoder | 1,239 cycles | 5,360 cycles | **6,598 cycles** | **0.825 ms** | **4.12%** |
| Griff optimized | 1,556 cycles | 2,756 cycles | **4,312 cycles** | **0.539 ms** | **2.69%** |

The original Griff measured **5,257 cycles / 0.657 ms / 3.28%** with the
same profiling harness. The optimized version uses **18.0% fewer cycles**
while shrinking its cache from 16384 to 5376 bytes. Compared with MCoder,
it uses about **34.7% fewer cycles**, with roughly twice the cache.
The word-copy path remains the largest cost. Both deliver **50 updates
per second**. The default mode runs both; the individual percentages above
are per kernel, not the combined cost of the demonstration.

### Griff before and after

| Property | Original adaptation | Optimized adaptation |
| --- | ---: | ---: |
| Cached phases | 16 | 8 (even shifts only) |
| Bytes per row, including duplicate | 128 | 84 |
| Cache size | 16384 bytes (16 KiB) | 5376 bytes (5.25 KiB) |
| Guard storage, in addition to cache | 8 bytes | 8 bytes |
| Total measured cycles per update | 5257 | 4312 |
| Time at 8 MHz | 0.657 ms | 0.539 ms |
| PAL frame budget | 3.28% | 2.69% |

Removing odd-phase generation saves both work and storage. Shortening the
ring saves additional storage; saving only used registers and unrolling the
row loops reduce the remaining instruction overhead. The smaller cache is
not a reduction in image quality. These measurements apply to the fixed
320x8 strip at 2 pixels per frame, with the timing bands disabled.

The baseline source and measurements are retained in
`analysis/baseline-griff/`; current measurements are in `analysis/profile.json`.

Numbers include the complete ASM update and screen copy, function calls and
each kernel's register saves. They exclude GodLib/input/C counter overhead, VBL
waiting, startup and mode-change warmup. Percentages use 160,256 cycles per
PAL frame. With `R` enabled, a debug-only wait places the start near visible row 32 (normal interrupts can shift it slightly).
Green brackets MCoder, orange brackets Griff, and grey brackets the paused
strip copy. The wait itself is uncoloured and excluded from the kernel costs;
the marker is not a total-system CPU meter or the source of the cycle figures.
Mode-change warmup frames are not marked. `R` starts disabled, so normal
benchmarking retains its original frame schedule.

The previous version marked the work around hardware lines 4..28, wholly
inside vertical blank (active display begins at line 63). That explains why
the marker was invisible despite the kernels taking about 13 and 10 raster
lines. `analysis/verify-meter.py` now checks real palette-write timing and
visible screenshot pixels in every mode, including pause and off.

Reproduce the comparison:

```sh
make debug
python3 analysis/profile.py
```

The script also measures each kernel alone and checks that the inactive kernel
has no calls. Results are in `analysis/profile.json`; raw per-instruction
captures are in `analysis/profile-raw-*.json`.

## Reusing the example kernels

These routines are local to the example, not new public GodLib APIs. They
use GodLib's existing `gFont8x8` glyph data. `gTinyScreen` selects the logical
page; the ASM screen copies currently assume the standard **160-byte stride**
and fixed strip positions (MCoder at y=88, Griff at y=120). They draw one
bitplane in a four-plane ST-low screen. Adapting them to a virtual screen
requires changing the destination row steps and strip offsets.

The optimized Griff advances by exactly **2 pixels per call**. Changing only
the phase increment to 1 is insufficient: odd phase data has been removed.
The ring must retain its extra word beyond the 40-byte viewport; a 40-byte
ring corrupted the incoming character boundary in pixel-reference tests.
Keep the eight guard bytes around the cache for the negative-offset stores.

Warmup runs after clearing the caches and on mode changes, rather than every
frame. If changing the ring layout, also recalculate warmup and text latency:
the current left-edge text positions are `2 * MCoderSteps - 322` and
`2 * GriffSteps - 320`. Counts 169 and 168 therefore align both at pixel 16.

## Verification

```sh
make debug
python3 analysis/verify-hatari.py
```

The harness uses the original GodLib font bytes and an independent horizontal
pixel-stream model. It compares all 32,000 bytes of each completed screen,
including the background, both strips and every font row. It verifies equal
text positions in combined mode, every reachable phase, all 40 MCoder and 21
Griff ring positions, both screen pages, pause, all three modes, complete
message wrap, timing-marker toggle and clean exit.

Target configurations: ST/TOS 2.06 and STE/TOS 2.06/1.62, all at 8 MHz with
1 MB RAM. Scripts use the installed Hatari debugging skill helpers and local
TOS ROMs. Per-target results are in `analysis/results-*.json`.

All three configurations passed: **819 complete screen comparisons**, all
phase/ring positions, message wrap, mode switches, pause and exit. No missed
VBLs were recorded. See [verification-summary.json](analysis/verification-summary.json).
The before/after cycle and cache figures are also recorded in
[griff-optimization.json](analysis/griff-optimization.json).

### Visible timing bands

For accurate raster colours on a plain ST in Hatari, use `--spec512 1`.
`make run` and the meter verification script now set it explicitly. With the
previous default renderer setting, ST palette-write traces were correct but
some screenshot bands were omitted; forcing Spec512 rendering reproduced the
orange band. STE captures passed without this override. This emulator option
does not change the emulated CPU speed or the kernel cycle measurements.

```sh
python3 analysis/verify-meter.py
```
