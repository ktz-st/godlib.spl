# DCK multiscroll — six independent ESCALI streams

Run **DCKMULTI.PRG** for six full-colour, straight horizontal scrolls using
DCK's **ESCALI 16×16** font. Every lane has its own text, stream state, movement
timer and direction. Alternate lanes move left and right. Rightward streams
reverse the order in which glyphs and glyph slices enter, preserving the
normal left-to-right appearance of letters and words.

```sh
make
make run
```

| Key | Action |
|---|---|
| 1…6 | Number of visible lanes, default six. |
| Space | Pause/resume every stream. |
| R | Green elapsed-render-time marker around Advance+Draw. |
| Esc | Return to TOS. |

The six lanes start at Y=32/56/80/104/128/152 and each occupy 320×16 pixels.
They step **8 pixels every 2/3/4/2/3/4 VBL**, giving independent PAL speeds
of 200/133⅓/100/200/133⅓/100 pixels/s. Frames update at 50 Hz; text position
changes only on its lane's movement tick. This retains byte-based movement,
not smooth 1–2 pixel fine scrolling. Hidden streams keep advancing.

## ASM implementation

This is an adaptation of the DCK multiscroll concept with a compact new kernel,
not an embedded DCK executable. `HS_Advance` handles independent timers,
glyph decoding, text wrap and left/right movement. `HS_Draw` renders two
8-pixel slices at once with longword source reads and `MOVEP.L` writes to all
four interleaved bitplanes. Source zeros replace old glyph pixels. Each lane
has forty column pointers mirrored once, allowing a contiguous visible window
at either wrap point. No screen-to-screen text shift, generated code,
pre-rendered animation frames or per-pixel C drawing is used.

GodLib owns Platform, Screen/double buffering, VBL, input and teardown. C
prepares the static display and handles controls. Changing the visible lane
count clears each screen page once; ordinary updates draw only the font bands.
All colours come from one shared original palette. Font source files and the
asset converter are bundled; normal builds and `make assets` are self-contained.

## CPU and cadence

Hatari-HRDB, STE / MC68000 8 MHz / PAL RGB / 4 MB / German TOS 1.62.
32 completed updates per measurement, covering all ASM rendering and independent
stream advancement; excludes startup, GodLib waits/input and interrupt handlers.
All six stream timers advance even when fewer lanes are rendered.

| Visible lanes | Cycles/update | Time | PAL frame budget |
|---|---:|---:|---:|
| 1 | 25791 | 3.22 ms | 16.1% |
| 3 | 73940 | 9.24 ms | 46.2% |
| 6 | 146114 | 18.26 ms | **91.3%** |

A separate normal-loop check completed **4683 frames with zero missed VBLs:
50 FPS** for six lanes. The remaining frame budget is small. The R marker
shows elapsed drawing time; it is not an independent profiler. These results
come from emulation, not a physical Atari. The renderer needs only a plain
68000 ST/STE: no BLiTTER, raster interrupts or STE scrolling registers.

## Verification and memory

Live output was independently reconstructed from the original PNG atlas:
**30720 pixels, zero mismatches**. Mirrored rings and every lane's head/timer
were checked through batches of 32 updates, including rightward movement.
All 1…6 selections, pause with unchanged stream state, resume and exit passed.

Font data: 4736 bytes; six mirrored pointer rings: 1920 bytes; stream state:
144 bytes; ASM code: 590 bytes. Screen buffers/library state are separate.
There is no generated-code allocation or additional scrolling bitmap.
The original font artist beyond its presence in DCK has not been established.

See `profiling.json`, `verification.json` and native `preview.png`.

```sh
make debug                       # /tmp/DCKMDBG.PRG
python3 tools/check.py            # controls/cadence, stock Hatari
python3 tools/profile.py          # pixels, directions/timers and CPU
```

Tools use local hatari-debugging skill helpers and Hatari-HRDB (default port
56001; `HS_HRDB_PORT` can override the client port when the emulator matches).
Temporary dumps/logs remain outside the repo. See also the simpler
[single horizontal scroller](../dckhoriz/README.md).
