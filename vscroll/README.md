# STE vertical tower scrolling

```sh
make
make run
```

Keep `TOWER.BIN` beside `VSCROLL.PRG`. The example scrolls a generated 320x400
fantasy tower through a 320x200 viewport. It starts at the foot of the tower and
moves upwards, then bounces between Y=0 and Y=200. A masked white bird flies
across the view. Space switches auto/manual; up/down move manually; Esc exits.
STE video is required for scrolling by single lines.

```c
Screen_Init(320, 400, eGRAPHIC_COLOURMODE_4PLANE, eSCREEN_SCROLL_V);
Screen_SetScrollY(y); /* example uses 0..200 to remain within the picture */
Screen_Update();
```

The legacy V flag adds 32 reserve lines, so GodLib allocates 320x432 canvases,
with stride 160 and a library scroll limit of 232. The image occupies the first
400 rows; reserve rows remain black. The demo limits movement to 200 so only
artwork appears in the viewport. CPU graphics pointers stay at the complete
canvas base; hardware displays `buffer + y*160` without copying the image.

Sprite positions use world coordinates (`screenY + scrollY`). Each screen page
keeps its own previous bird rectangle, restored from the clean ScreenBack canvas
before the next draw. Unchanged positions in a page skip restoration and drawing.
Background data is copied to both pages once during setup.

`TOWER.BIN` is a custom raw four-plane image, not PI1: 16 big-endian ST palette
words followed by 64000 interleaved planar bytes (160 bytes per row, 400 rows).
The image is generated with the built-in image tool; the original and prompt
are saved in assets. `assets/tower-st.png` is the exact converted 320x400 preview.
`make assets` regenerates the binary using Pillow and `prepare_assets.py`; the
converter independently decodes and checks all 128000 packed pixels.

Run `make debug`, then `python3 analysis/verify-hatari.py` with the local
hatari-debugging helper. It checks automatic movement, manual up/down, every
visible pixel at Y=0/1/7/8/15/16/31/32/199/200, both sprite pages, transparency,
background restore, reserve rows and exit to TOS. Real hardware is untested.

## Artwork conversion update

Generated scene artwork now uses **ABC2, STE RGB444, without dithering**.
See the [shared artwork guide](../tools/ARTWORK.md) for reserved colours,
regeneration, shared copies and validation. Snowfall retains eight background
colours to leave its snow bitplane free. Older ST screenshots and CPU results
above refer to their original artwork revision.
