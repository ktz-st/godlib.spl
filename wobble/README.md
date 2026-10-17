# Dynamic picture wobble in 68000 ASM

Full-colour 320x200 picture waves for Atari ST/STE, 68000 at 8 MHz.
The COAST lighthouse picture from `wipe` is embedded in `WOBBLE.PRG`.
The revised renderer uses a preshift cache, MOVEM copies and per-screen-page
history; it needs no blitter, STE scroll registers or raster interrupt.
It has been designed and tested with 1 MB RAM.

```sh
make
make run
```

- Space: pause/resume the wave.
- 0: unshifted picture; after both pages are prepared, all lines are reused.
- 1/2/3: wave amplitudes 4/8/16 pixels; default 8.
- S: cycle phase speeds 4/8/16 **per VBL**; default 8.
- Esc: restore TOS.

At the default speed a complete wave cycle takes 0.64 seconds at 50 Hz. Phase
uses elapsed VBLs, so a slower rendered update does not slow the motion's time
base. Pause still records VBL time, avoiding a jump when resuming.

## What Control's hscroll does

`stos/CONTROL/EXTENSIO.NS/CONTROL.EXW`, Control V3.06b by L.J.Greenhalgh,
contains an ordinary CPU shifter. It processes the selected bitplanes with
unrolled word shifts and a propagated carry; exactly one pixel has separate
ROXL.W / ROXR.W paths. This procedure does not use the blitter. The extension's
`enable blit` setting applies to other drawing/copying commands.

Its `SOURCE/WOBBLE.BAS` example copies a 208-pixel-wide central picture strip,
then scrolls each of the 200 lines using a half-sine table of 180 positions.
Advancing that index once per line advances its starting phase by 20 positions
between rendered frames. Our old sample advanced only 2 positions in a full
256-position table per rendered frame, making the already slow renderer's
animation much slower still.

See `analysis/control-notes.md`, `control-addresses.json` and `control-hscroll.s`
for verified offsets, a reproducible static disassembly and the distinction
between file, TEXT and runtime addresses. `analysis/inspect-control.py`
reproduces them without modifying Control. These findings do not claim a
measured STOS frame rate.

## Revised renderer

`tools/prepare.py` prepares 16 fine-shift versions of every source line offline.
Each version is normal interleaved four-plane data, padded by 16 black pixels
on each side. The row-major cache is:

```
200 rows * 16 fine shifts * 176 bytes = 563,200 bytes (550 KiB)
```

A coarse word-group offset plus the selected fine version covers all 33 shifts
from -16 to +16 without reading outside the cache. The large cache trades ST
RAM and executable size for less CPU work; it replaces runtime word shifts.
The release embeds this cache and the palette, rather than another complete
copy of the original PI1. The original PI1 remains the offline source.

Four short cyclic lookup tables select source offsets for amplitudes 0/4/8/16.
Each repeats 256 entries three times, allowing phase + y*2 without runtime
modulo inside the renderer. A fifth table contains invalid offsets to force
both display pages to be fully drawn at startup. Per-frame C preparation now
selects a table pointer and snapshots phase/amplitude; it does not prepare 200
separate commands or touch pixels.

The ASM traverses rows bottom-to-top. Each changed row is copied in four
40-byte MOVEM chunks, right-to-left, retaining the correct word/register order.
All 200 line bodies are expanded by a macro to avoid loop/pointer overhead.
Each page retains its previous lookup cursor. If the current row's source
selection matches the last image on that same page, it needs no write.
A page's history is updated only for a completed render in this single-threaded
main loop; the pages use independent histories.

Normal GodLib double buffering presents a complete frame while the next page
is rendered. The source is static and the renderer owns both full image pages;
additional drawing into those pages would require invalidating their history.
Source width, height and strides are fixed for ST low resolution.

## Verification and profiling

```sh
make debug
python3 analysis/verify-hatari.py
python3 analysis/profile.py
```

Tests run ST/TOS 2.06, STE/TOS 2.06 and STE/TOS 1.62, 8 MHz, 1 MB RAM.
An independent host reference compares every one of the 32,000 output bytes
for amplitudes 0/4/8/16, covering all 33 offsets, zero-filled clipping and
amplitude/phase changes. Consecutive moving frames check both page histories
and verify phase increments against elapsed target VBLs. Controls and return
to TOS are checked, with a five-second wait for delayed exceptions.

The profiler requires Hatari-hrdb and the installed Hatari helper. It starts a
fresh emulator per amplitude, measures the ASM kernel and C preparation, and
counts copied/reused row paths through their instruction addresses. Update
rate uses target frame/VBL counters rather than host wall time. Percentages
refer to one 160,256-cycle PAL frame, excluding main-loop/VBL/input overhead.
The 0-amplitude measurement exercises reuse, not a full-screen copy benchmark.

The previous C/ASM, documentation and measurements are retained under
`analysis/baseline/`; those files are reference snapshots, not a separate build.
The old default used about 917,122 cycles per update (856,405 ASM + 60,717 C),
114.6 ms and approximately 8.3 updates/s. The new timing table is recorded below.

### Final measurements: emulated ST 8 MHz, 1 MB, TOS 2.06

| Amplitude | ASM cycles/update | C preparation | Draw + preparation | PAL frame budget | Updates/s | Rows reused/update |
|---|---:|---:|---:|---:|---:|---:|
| 0 px | 11517 | 285 | 1.48 ms | 7.4% | 50 | 200.0 |
| 8 px | 147302 | 316 | 18.45 ms | 92.1% | 50 | 18.7 |
| 16 px | 159043 | 317 | 19.92 ms | 99.4% | 25 | 3.1 |

The default animation improved from about 8.3 to 50 updates/s; draw plus
preparation dropped from 114.6 to 18.45 ms, roughly 6.2 times less work per
update. Its motion cycle changed from about 15.36 seconds to 0.64 seconds.
At 16-pixel amplitude the standalone program still runs at 25 updates/s: the
19.92 ms kernel leaves too little room for the remaining VBL/input/main-loop
work to meet a 20 ms frame. The zero-amplitude result reuses all 200 rows.

Final functional tests passed on all three configurations: four full image
comparisons per configuration plus six consecutive moving frames, both display
pages, all 33 shifts, VBL-based phase increments, controls and clean exit.
Adding exported profiling labels afterward changed no executable code or image
data; `analysis/build-validation.json` records the byte-identity check.

These are emulator measurements rather than a physical Atari benchmark.
`analysis/profile.json` and `analysis/results-*.json` contain the complete
measurements and verification records.

## Artwork conversion update

Generated scene artwork now uses **ABC2, STE RGB444, without dithering**.
See the [shared artwork guide](../tools/ARTWORK.md) for reserved colours,
regeneration, shared copies and validation. Snowfall retains eight background
colours to leave its snow bitplane free. Older ST screenshots and CPU results
above refer to their original artwork revision.
