# Sprite background restore with chunk lists

A standalone variant of `spritebg`, using `Graphic_ChunkList_Store()` and
`Graphic_ChunkList_ReStore()` instead of a rectangular blit. Includes copies
of the original example's `RGLOGO.PI1` background and `SPRITE.PI1` sprite.

```sh
make
make run
```

Keep `SPRCHUNK.PRG`, `RGLOGO.PI1` and `SPRITE.PI1` together on Atari ST/STE.

- 1: mouse (initial mode).
- 2: joystick port 1; fire recentres the sprite.
- 3: arrow keys, one pixel per frame.
- Space: exit.

There is one `sGraphicChunkList` per logical screen index. ScreenBack contains
clean background pixels and the static instructions. Both screen pages get a
copy of this background during setup.

Whenever a page needs a new sprite position, the example does:

```c
index = Screen_GetLogicIndex();
Graphic_ChunkList_ReStore(&sChunkLists[index],
    Screen_GetpBackGraphic(), Screen_GetpLogicGraphic());
Screen_Logic_DrawSprite_Clip(&position, sprite);
Graphic_ChunkList_Store(&sChunkLists[index],
    Screen_GetpLogicGraphic(), &spriteRectangle);
```

`Store` saves offsets and heights, not pixel data. The 16x16 sprite occupies
one 16-pixel chunk when aligned, or two when shifted. `ReStore` merges adjacent
chunks of equal height and copies their rows using unrolled 68000 `MOVE.L`
instructions, then empties that page's list. Offsets are 32-bit, allowing virtual
buffers larger than 64 KiB. If the
sprite position already matches the page, no restore or draw is needed.

The sprite stays fully inside the canvas: `Store` does not clip rectangles.
Source and destination canvases have the same 160-byte stride and memory
layout. Background restoration uses the CPU assembly kernel on both ST and STE;
sprite rendering automatically uses the blitter when available and CPU otherwise.
The new chunk layout requires recompilation of programs using the list.

`gRestoredChunks[2]` counts processed chunks per page for debugger inspection.
It is diagnostic bookkeeping, not a cycle-cost measurement.

For automated checks, run `make debug`, then
`python3 analysis/verify-hatari.py`. This uses the local hatari-debugging skill
helper and runs ST/STE sessions. It checks both lists, motion, four edges,
stationary redraw skipping, and compares every pixel outside the current
sprite against the clean background in both screen pages. Keyboard input is
tested; injected scancodes do not test real mouse/joystick packets.

Kernel correctness and C/ASM timings: `godlib/graphic/tests/chunk`.
