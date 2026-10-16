# ST/STE raster bars through Timer B

```sh
make
make run
```

`RASTR.PRG` is a self-contained PAL 320x200 demo for ST and STE/Mega STE with a
68000 at 8 MHz. There are no asset files to copy. The short executable name also
avoids the TOS 1.62 autostart filename failure documented in `../palsplit`.

- Space freezes/resumes the raster animation.
- R enables/disables the raster effect.
- 1/2 selects one/two colour-table steps per frame.
- Esc removes the raster handlers and returns to TOS.

The bitmap is drawn once through GodLib ASM graphics/font routines. Its text,
stars and diamond use fixed palette entries. Only colour zero changes during
display (including the border background): VBL supplies the first band, then 49 Timer B interrupts create the
remaining four-line bands. A 64-entry table gives warm, cyan, purple and green
bars. Moving the table phase in VBL animates the bars without redrawing pixels.

## Relation to Amberstar

`amberstar/src/NUCLEUS/HBI.ASM` has a VBL-prepared HBL list with single-colour
(`Single_HBL`) and full-palette (`Palette_HBL`) events. The list stores relative
Timer B counts and advances after each event. This example follows that list
approach for a single colour register, using a fixed four-line spacing.

Each `sRasterStep` contains a byte delay, padding and a colour word. The delay is
the desired gap minus one because the interrupt enters one DE event early and
waits for the final boundary. The ASM handler consumes one record, preloads the
colour, uses Amberstar's dummy Timer B counter technique to wait for the next
DE falling edge, writes `$FFFF8240`, then arms the next record's delay.
The demo uses delay 3 throughout: changes occur at displayed rows 4,8,...,196.
There is no self-modifying code; the target colour register is fixed in ASM.

The installation is the same as the screen/palette split samples:
`Vbl_InstallTimerB()` and a wrapped `Vbl_SetVideoFunc()` callback. GodLib rearms
the first event every VBL. The callback builds the next list and resets its
cursor before visible display starts, then sets the base palette. List mutation
therefore cannot race a visible-display Timer B handler. The main loop only
updates controls and performs normal `Screen_Update()` page handling.

This is an educational raster list, not a general scheduling library. It owns
Timer B, uses the standard PAL DE edge and defers TOS Timer C until the last
raster event. Animation uses VBL phase rather than the affected 200 Hz clock.
Do not combine it unchanged with Timer C music, another Timer B user, active
blitter jobs or disk I/O during display. No blitter work is started after init.
Both callbacks and the previous MFP Timer B state are restored under IPL 7 before
screen memory is released. TT/Falcon video is rejected by this compact sample.

For a full 16-colour palette write instead of single-colour raster bars, see
[the colour/greyscale palette split](../palsplit/README.md).

## Verification

```sh
make debug
python3 analysis/verify-hatari.py
```

The optional harness uses Pillow and the local hatari-debugging helper. It runs
headless by default to isolate scripted input from the physical keyboard.
`HATARI_TOS` and `HATARI_TOS162` select TOS 2.06/1.62 images instead of the local
default paths. It checks all displayed pixels at phases 0,1,17,32,63, including
unchanged foreground colours; automatic animation, speed, pause and effect
toggle; callback removal and five seconds after exit. Palette traces must have
exactly 49 correctly positioned single-colour writes in each complete active
frame, all in horizontal blank. Results go to `analysis/results.json`.
These are Hatari checks, not physical Atari measurements or CPU cost profiles.

Verified on 2026-10-16 in Hatari at 8 MHz / PAL:

| Machine / TOS | Complete active raster frames | Colour-write cycles |
| --- | ---: | --- |
| ST / 2.06 | 1559 | 424..448 |
| STE / 2.06 | 1561 | 424..448 |
| STE / 1.62 | 1501 | 424..448 |

All 4621 active frames had the complete 49-event sequence at lines 4..196.
The five pixel-reference phases, animation controls, pause, effect off/on and
clean return to TOS passed in all three configurations.
