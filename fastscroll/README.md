# Fast BUGSY scroller

A plain horizontal scroller for Atari ST/STE using the original STOS BUGSY
32x27 one-bit font. No sine wave, blitter or STE fine-scroll registers.
The 320x200 program embeds its font; launch `FSCRL.PRG` without external files.

```sh
make
make run
```

Space pauses; 1/2/3/4 select 1/2/4/8 pixels per VBL; Esc returns to TOS.
The default is 4 pixels/VBL. Both display pages already contain text at startup.

## Fast path

`scroll_s.s` shifts a packed 352x27 one-plane conveyor once per update using
32-bit overlapping reads and register shifts. The next source word supplies the
bits entering each destination word; processing left to right preserves those
source bits. Each row has 320 visible pixels and 32 hidden pixels for the next
glyph. A zero-filled right edge prevents unwanted wrap bits.

There is one shift pass at every normal speed, rather than one pass per pixel.
A change of speed can cross a glyph boundary mid-update; C splits that update at
the boundary, inserts the next glyph, and shifts the remaining pixels. Speeds are
restricted to 1/2/4/8 and all accesses remain word aligned on the 68000.

The planar drawing routine overwrites only plane zero of the 27-row text band,
with twenty unrolled word transfers per row. There is no separate clearing pass,
large dirty rectangle, full-screen copy, runtime trigonometry or per-pixel C
renderer. A yellow palette entry supplies the font colour. Other planes in the
text band are zero; this example is an opaque text strip, not transparent text
compositing over a picture. Destination stride is the fixed ST-low 160 bytes.

GodLib Screen_Update switches the two display pages at VBL. Only the text band
is rewritten; the static title, separators and controls stay on both pages.
This small effect has sufficient frame budget for double buffering on ST.

## Font

`assets/BUGSY.MBK` is copied unchanged from `stos/BIG/BUGSY.MBK`; the original
font designer is not identified in that bank. `tools/prepare.py` validates the
header and extracts 224 glyphs, 108 bytes each, from offset 282 into BUGSY.BIN.
This build step needs Python 3 only. Rendering requires no STOS runtime.

## Checks

```sh
make debug
python3 analysis/verify-hatari.py
python3 analysis/profile.py
```

The functional check runs ST/TOS 2.06 and STE/TOS 2.06/1.62 at 8 MHz with 1 MB.
It reconstructs the conveyor from the original glyphs and message, compares all
planar text words, checks all four speeds, pause/resume, message wrap, missed
VBL counters, and clean return to TOS. Debugger pauses stop emulated time.
The profile uses hatari-hrdb instruction-cycle counts, not host wall time.
ROM overrides: HATARI_TOS and HATARI_TOS162 for the functional check.

## Measured kernel cost

Hatari hrdb, ST PAL 68000 at 8 MHz, TOS 2.06, 1 MB. Averaged over 172 draw
calls per speed; these are active instruction cycles, not host wall time:

| Speed | Shift + draw + glyph insertion | Share of a 160000-cycle PAL frame |
| --- | ---: | ---: |
| 4 pixels/VBL (default) | about 40873 cycles | 25.5% |
| 8 pixels/VBL | about 45782 cycles | 28.6% |

These figures exclude orchestration, interrupts and VBL waiting; they are not
total application CPU percentages. Frame cadence is verified separately by the
VBL counter, not inferred from the sum of all profile entries (which includes
interrupt and wait paths). Raw measurements are in `analysis/profile.json`.

The completed ST/STE checks rendered 8442 frames across
the three ROM/machine configurations with **zero missed VBLs**, including
all four speeds and message wrap. This verifies a 50 Hz PAL update cadence
in these emulator runs; real-hardware verification is still separate.
