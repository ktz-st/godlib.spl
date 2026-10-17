# STE split: top HUD with its own palette and horizontal scrolling

```sh
make
make run
```

Run `SPLITH.PRG` on an STE/Mega STE, 68000 at 8 MHz, PAL low resolution.
The panorama is embedded: only the executable is needed on the Atari.

- Top 16 rows: fixed 320-pixel HUD, stride 160, fine scroll zero, its own 16 colours.
- Bottom 184 rows: 320-pixel viewport over a 640x200 panorama, stride 320, original
  picture palette and fine pixel scrolling.
- Automatic scrolling bounces between X=0 and X=320.
- Space pauses/resumes; Left/Right scroll manually while paused.
- 1 selects one pixel per frame; 2 selects four pixels per frame; Esc exits.

Edit `gHSplitHudPalette[16]` in `splitscreenh.c` to change HUD colours. The demo
shows all 16 entries as top-row swatches, with a dark-blue background, orange
bottom rule and yellow text. No palette entry needs to be shared with terrain.
`PANORAMA.BIN`, copied from `../hscroll`, contains the terrain palette followed
by its 640x200 four-plane bitmap. Terrain source row zero begins below the HUD;
the final 16 picture rows are not displayed. The HUD and terrain remain separate
buffers. This does not change the 320x200 video mode or remove screen borders.

For a fixed bottom panel and vertical scroll, see [splitscreen](../splitscreen/README.md).
For palette-only or raster-list effects, see [palsplit](../palsplit/README.md) and
[rasters](../rasters/README.md).

## VBL and Timer B sequence

The local `split.c`/`split_s.s` are based on the top-HUD arrangement in
`pacmad.ste/src/split.*`, extended to change fine scroll, line skip and palette.

1. `Screen_Init(640,200,4PLANE,SCROLL_H)` and `Screen_SetScrollX()` retain GodLib's
   normal page handling and atomic terrain viewport update.
2. The wrapped VBL video callback calls the original video updater, snapshots
   its queued terrain address and matching hardware fine X, then selects the
   HUD base/live counter, fine X=0, line skip=0 and the complete HUD palette.
   Do not read the main loop's X for that snapshot: it may describe a later frame.
3. GodLib rearms Timer B with 14, entering two rows early. The handler pauses an
   active blitter if present and preloads every display value and all 32 terrain
   palette bytes before waiting. With the timer still running, count 12 marks
   the second DE falling edge, at the end of HUD row 15.
4. Write the live video address, fine X and line skip during the right border.
   `MOVEP.W` sends the address middle/low bytes to `$FFFF8207/09`, saving cycles
   over separate byte moves. No screen-base register is changed at this boundary.
5. One `MOVEM.L` writes all 16 terrain colours. The write starts in the right
   border and finishes in the following left border, before terrain pixel zero.
   It is a sequential 16-word bus transfer, not an instantaneous palette switch.
6. Stop Timer B, resume the blitter and restore Timer C's mask if it was enabled.
   The following VBL selects the HUD layout and palette again.

The critical code holds palette data in D5-D7/A0-A4, display values in D0-D3,
the DE count and saved blitter word in D4, and hardware pointers in A5/A6.
Palette loads and register saves happen before synchronization. All interrupted
registers are preserved; address registers used for palette data are not
subsequently dereferenced. The shorter polling loop and `MOVEP.W` leave a
measured margin before the first terrain pixel.

STE line skip counts words after fetched data. Terrain skip is 80 at fine X=0,
or 76 when fine scroll fetches an extra four-plane word group. HUD skip remains
zero. Applying the terrain stride/fine X to the HUD would shift/distort it.

The sample owns Timer B and defers TOS Timer C until the split completes. It is
not a shared raster scheduler: do not combine unchanged with another Timer B
user, Timer C playback or a different mode/stride. Heavy initialization and asset
preparation finish before installation. Installation/removal uses saved/restored
IPL 7; previous video/Timer B callbacks, scanline and MFP timer state are restored
before panel or screen memory is released. STE video is required, not plain ST.

## Verification

```sh
make debug
python3 analysis/verify-hatari.py
python3 analysis/verify-hatari.py --tos162
```

The optional headless harness needs Pillow and the local hatari-debugging helper.
`HATARI_TOS` and `HATARI_TOS162` can select TOS 2.06/1.62 images instead of the
local default paths. It compares every displayed pixel at 22 X positions,
including all fine phases and X=319/320. HUD expected pixels use its own palette;
terrain expected pixels use the picture palette. All 16 HUD swatches are checked.
It also checks auto/manual controls, unchanged HUD storage, handler removal and
five seconds after exit.

Combined `video_ste,video_color` traces must show the five display writes followed
by all 16 correct terrain palette words in each split frame. Use `video_hbl_w`,
not just `nHBL`, for palette writes: one MOVEM can cross a scanline boundary while
Hatari's instruction-level `nHBL` still names the preceding line. Geometry writes
must finish on line 78, before cycle 512. Palette writes may extend into line 79
but must finish before cycle 56, its first visible pixel. Recorded normalized
palette cycles are relative to the start of line 78: 512 means line 79/cycle 0.
Results go to `analysis/results.json` and `analysis/results-tos162.json`;
logs/captures are ignored. These are emulator checks, not a physical-hardware
timing guarantee or a CPU-only profile.

Verified on 2026-10-16, Hatari STE / 68000 8 MHz / PAL:
TOS 2.06 passed 2610 split frames; TOS 1.62 passed 2553. Both runs checked all
22 X positions, all 16 independent HUD colours, controls and clean exit. Display
writes were at cycles 428..484 on line 78. Palette writes were at normalized
cycles 480..556: the final colour finished by line 79/cycle 44, leaving at least
12 cycles before the first visible terrain pixel at cycle 56.

## Artwork conversion update

Generated scene artwork now uses **ABC2, STE RGB444, without dithering**.
See the [shared artwork guide](../tools/ARTWORK.md) for reserved colours,
regeneration, shared copies and validation. Snowfall retains eight background
colours to leave its snow bitplane free. Older ST screenshots and CPU results
above refer to their original artwork revision.
