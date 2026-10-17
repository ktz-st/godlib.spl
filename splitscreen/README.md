# STE split screen: scrolling terrain and a fixed bottom panel

```sh
make
make run
```

Run `SPLIT.PRG` on an STE/Mega STE with a 68000 at 8 MHz in PAL low resolution.
The picture is embedded in the executable, so no runtime asset files are needed.
Plain ST, TT and Falcon video are rejected; this example writes the STE live
video counter and is not an STF sync-scrolling implementation.

- Top: 320x160 viewport scrolling over a 320x400 tower.
- Bottom: an independent 320x40 HUD, with its own 256-byte-aligned buffer.
- Space toggles automatic scrolling; Up/Down scroll manually while paused.
- 1 selects one pixel per frame; 2 selects four pixels per frame.
- Esc exits and restores the previous handlers before releasing screen memory.

`TOWER.BIN` is a copy of the generated image in `../vscroll`; it consists of
16 STE palette words followed by four-plane pixels. Both display regions use
the same palette and the same 160-byte stride. The white first/last HUD rows
make the exact split boundary easy to inspect.

## How it works

`Screen_Init(320,400,4PLANE,SCROLL_V)` retains the 320x200 video mode and creates
432 rows of virtual storage. `mViewportHeight` is set to 160 because only the
upper part uses the terrain. The demo limits scrolling to 0..240, staying inside
the 400 picture rows rather than exposing the allocation's 32 reserve rows.
GodLib continues to own the normal page flips and video update in VBL.

The local `split.c`/`split_s.s` follow `river-raid-st/src/split.*` (and its
`river-raid/stage5-godlib` predecessor). That code was based on
`pacmad.ste/src/split.*`. PacMad uses a 16-line HUD at the top, then changes to
terrain; this example uses River Raid's inverse arrangement, terrain then HUD.

1. GodLib's VBL rearms Timer B in display-enable event-count mode with 159.
2. The wrapped video callback defers TOS Timer C, whose IPL 6 handler could
   otherwise delay the split. The original video callback still runs.
3. Timer B enters after terrain row 158 and pauses an active blitter if present.
4. The ASM handler waits for the next DE decrement, marking the end of row 159.
5. During horizontal blank it writes the three live-counter address bytes at
   `$FFFF8205/07/09`, redirecting the remaining 40 rows to the HUD.
6. It stops Timer B, resumes the blitter and unmasks Timer C if it was enabled.
   The next VBL selects the next normal terrain page and starts the sequence again.

Installing and removing the split is protected by IPL 7. The previous GodLib
video callback, Timer B callback/scanline and MFP Timer B settings are restored
on exit. The panel storage remains alive until after the split is removed.

This compact example owns Timer B and changes when Timer C can run. It is not a
shared raster scheduler; do not combine it unchanged with another Timer B user,
Timer C-driven playback, horizontal fine scrolling or different row strides.
Asset preparation and initial drawing finish before the split is installed.
It changes the source address, not the screen borders or the 200-line video mode.

## Verification

```sh
make debug
python3 analysis/verify-hatari.py
```

The optional harness uses the local hatari-debugging helper and Pillow. Set
`HATARI_TOS` to a TOS 2.06 image if the default local path is unavailable.
It compares all 320x200 displayed pixels at multiple fine/coarse scroll offsets
against the picture plus HUD memory, tests controls and cleanup, and checks
`video_ste` traces for all three counter writes inside the horizontal blank.
Results are written to `analysis/results.json`; captures/logs are ignored.
These are emulator checks, not a real-hardware timing guarantee.

Verified on 2026-10-16 in Hatari STE / 68000 8 MHz / PAL / TOS 2.06:
all displayed pixels matched at Y=0,1,7,8,15,31,239,240; auto/manual control,
1/4-pixel speed selection, fixed HUD and exit passed. All three counter writes
were in horizontal blank (cycles 436..508, nHBL=222) in 1491 traced split frames.

For a fixed top HUD and horizontal fine scroll, see [splitscreenh](../splitscreenh/README.md).

## Artwork conversion update

Generated scene artwork now uses **ABC2, STE RGB444, without dithering**.
See the [shared artwork guide](../tools/ARTWORK.md) for reserved colours,
regeneration, shared copies and validation. Snowfall retains eight background
colours to leave its snow bitplane free. Older ST screenshots and CPU results
above refer to their original artwork revision.
