# STE split: fixed top HUD and horizontal scrolling

```sh
make
make run
```

Run `SPLITH.PRG` on an STE/Mega STE, 68000 at 8 MHz, PAL low resolution.
The panorama is embedded: only the executable is needed on the Atari.

- Top 16 rows: independent, fixed 320-pixel HUD (stride 160, fine scroll zero).
- Bottom 184 rows: a 320-pixel viewport over a 640x200 panorama (stride 320).
- Automatic scroll bounces between X=0 and X=320, including fine pixel scroll.
- Space pauses/resumes; Left/Right scroll manually while paused.
- 1 selects one pixel per frame; 2 selects four pixels per frame; Esc exits.

This is the top-HUD counterpart of [splitscreen](../splitscreen/README.md),
which puts a fixed 40-row panel below vertically scrolling terrain.
`PANORAMA.BIN` is copied from `../hscroll`: 16 ST palette words plus the 640x200
four-plane image. Both regions use that palette. The terrain begins at source
row zero immediately below the HUD; the last 16 source rows are not displayed.

## Split sequence

`split.c` and `split_s.s` follow `pacmad.ste/src/split.*`, extended to change
fine scroll and line skip as well as the live video address:

1. `Screen_Init(640,200,4PLANE,SCROLL_H)` and `Screen_SetScrollX` keep GodLib's
   normal logical/physical page handling and atomic terrain viewport update.
2. The wrapped VBL video callback calls GodLib's original video updater, then
   snapshots its queued terrain address and the corresponding hardware fine X.
   It derives the terrain line skip and selects the HUD base/live counter with
   fine scroll zero and line skip zero. The HUD buffer is 256-byte aligned.
3. GodLib's VBL rearms Timer B with 14. After entering two rows early, the ASM
   handler waits for the actual end address of the 16-row HUD, as in PacMad.
   This matches both the middle address byte and low-byte zero, avoiding an
   earlier low-byte wrap within a line.
4. During horizontal blank it writes the terrain address, fine X and line skip.
   All five values are preloaded in registers before waiting, making the final
   five writes short enough for the blanking interval.
5. Timer B stops, any suspended blitter resumes, and Timer C is unmasked if it
   was enabled. The next VBL restores the independent HUD setup.

STE line skip counts words after fetched display data. At X%16=0 it is 80;
nonzero fine scroll fetches an extra four-plane word group, so it becomes 76.
This keeps successive terrain rows 320 bytes apart. Applying the same fine X
or line skip to the HUD would shift/distort the panel, so both are reset in VBL.

The split owns Timer B and defers TOS Timer C until after the short HUD region.
Do not combine it unchanged with another Timer B user, Timer C-driven playback,
a different video mode or different strides. Installation/removal is protected
by IPL 7, and previous callbacks/MFP Timer B state are restored before the panel
or terrain storage is released. It requires STE video; it is not an STF split.

## Verification

```sh
make debug
python3 analysis/verify-hatari.py
```

The optional harness uses Pillow and the local hatari-debugging helper. Set
`HATARI_TOS` to a TOS 2.06 ROM when the default local path is unavailable.
It checks every displayed pixel against independent image/HUD references at
all 16 fine scroll phases and coarse/boundary X positions. It also checks fixed
HUD contents, controls, cleanup and the live-counter writes in `video_ste` traces.
Results go to `analysis/results.json`; logs/captures are ignored. Emulator checks
are not a guarantee of physical-hardware timing.

Verified on 2026-10-16 in Hatari STE / 68000 8 MHz / PAL / TOS 2.06:
all displayed pixels matched at 22 X positions (all fine phases, coarse steps
and X=319/320). Auto/manual controls, fixed HUD and clean exit passed. All five
transition writes stayed in horizontal blank, cycles 436..500 at nHBL=78, in
2501 traced frames. See `analysis/results.json` and `analysis/check_trace.py`.
