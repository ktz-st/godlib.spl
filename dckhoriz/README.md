# DCK horizontal scroller — ESCALI

A simple full-colour horizontal text scroller using **ESCALI 16×16**, extracted
from DCK disk B. Run **DCKHOR.PRG**: all assets are embedded. Ordinary 68000
ST/STE, no BLiTTER, rasters, hardware fine scrolling or generated-code buffer.

```sh
make
make run
```

Space pauses/resumes, R toggles a green elapsed-render-time marker, Esc returns
to TOS. The original-style byte step is **8 pixels every 2 VBL**: 200 pixels/s
at PAL 50 Hz. The screen is updated at 50 FPS; text positions change at 25 Hz.
This is not a smooth 1–2 pixel scroller.

The ring of forty 8-pixel source-column pointers is mirrored so the visible
window is contiguous even when it wraps. Each new glyph contributes two slices.
`HS_Advance` changes a pointer and head on movement ticks. `HS_Draw` processes
two slices per iteration: longword font loads and `MOVEP.L` distribute their
four plane bytes to adjacent 8-pixel halves of each ST planar group. All font
colours and blank pixels are copied, replacing the previous frame's text.
The flat renderer needs no generated kernel and no bitmap/frame cache.

C handles setup/input; text advancement and runtime drawing are in
`dckhoriz_s.s`. GodLib owns double buffering, VBL, keyboard and TOS lifecycle.
Source artwork, original palette, text and converter are bundled; `make assets`
rebuilds the packed font without an external DCK checkout.

## Measured result

Hatari-HRDB, STE / MC68000 8 MHz / PAL RGB / 4 MB / German TOS 1.62:
32 completed Advance+Draw updates averaged **24944 cycles, 3.12 ms,
15.6% of a 160000-cycle PAL frame**. This includes ASM rendering and advancement
but excludes GodLib waits/input, startup and interrupt handlers. The normal
loop completed **6017 frames without a missed VBL: 50 FPS**.

Live output was checked against the original PNG atlas: 5120 pixels, zero
mismatches. Movement timing, ring mirroring, pause, resume and exit passed.
These are emulator observations, not physical-machine timing guarantees.

The font occupies 4736 bytes, mirrored pointers 320 bytes and stream state
24 bytes; ASM code is 590 bytes. GodLib screen buffers/library state are separate.
The original font artist beyond its presence in DCK has not been established.

`profiling.json`, `verification.json` and `preview.png` retain compact evidence.

```sh
make debug                       # /tmp/DCKHDBG.PRG
python3 tools/check.py            # controls/cadence, stock Hatari
python3 tools/profile.py          # pixels and CPU, Hatari-HRDB
```

Tools use local hatari-debugging skill helpers. HRDB defaults to port 56001;
set `HS_HRDB_PORT` if the emulator is configured/mapped to another port.
Temporary dumps and logs stay outside the repo. See also the six-stream
[multiscroll](../dckmulti/README.md).
