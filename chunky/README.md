# Chunky to ST four-plane example

Build with `make`, run with `make run` or launch `CHUNKY.PRG` on an Atari ST/STE.
No external assets are needed. Space pauses/resumes the animation; Esc exits.

The sample draws a palette strip, checkerboard, moving box and lines into a
256x128 chunky canvas. Each byte is one palette index, 0..15. The backing array
uses U16 storage to keep the buffer even-aligned for the 68000 assembler.

`DrawChunky()` uses `ChunkySurface_DrawBox()` and `ChunkySurface_DrawLine()`.
`DrawFrame()` converts the whole canvas into the logical 320x200 ST screen:

```c
sGraphicRect source = {0, 0, 256, 128};
sGraphicPos destination = {32, 56};
ChunkySurface_To4Plane(Screen_GetpLogicGraphic(), &destination, &source, &sChunky);
Screen_Update();
```

The source stride is 256 bytes; the screen stride is 160 bytes. The conversion
uses the canvases' individual row offsets. Full 16-pixel blocks use assembler;
the wrapper also supports arbitrary X and partial blocks. Only the low four
bits of each chunky byte are used. Text is drawn in planar memory afterwards.

The chunky buffer itself is not a display mode: ST hardware displays the
converted four-plane buffer. The example does not require Falcon hardware,
a blitter, or rebuilding GodLib with `dGODLIB_CHUNKY`; it calls the chunky
functions directly. It demonstrates the pipeline, without a fixed FPS promise.

For the scripted ST smoke test, build with `make debug`, then run
`python3 analysis/verify-hatari.py`. It uses the local `hatari-debugging` skill's
session helper and checks animation, pause/resume, screenshots and exit to TOS.
