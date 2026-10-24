# DCK bobs — GodLib sprites on DCK trajectories

Standalone **DCKBOBS.PRG**, ST/STE, 320×200 PAL. Three original DCK coloured
balls follow one of eight original trajectory tables. Movement/frame orchestration
is 68000 ASM; pixels are drawn by the **existing GodLib sprite procedures**.
No new graphics code was added to the library.

```sh
make
make run
```

All runtime assets are embedded. Ordinary builds need GCC ELF, vasm, GodLib and
libcmini, with their existing `-mshort -mfastcall` ABI. `make assets` regenerates
the embedded data using Python and the included source assets.

## Controls

| Key | Action |
|---|---|
| 1 / 2 / 3 | Select 1 / 4 / 8 balls; default **4**. |
| P | Next DCK trajectory, eight in total; default NOEUD. |
| T | Switch clean background restoration / persistent trails. |
| B | Toggle GodLib CPU / BLiTTER sprite renderer. BLiTTER is selected on an STE; machines without one retain CPU rendering. |
| C | Clear both pages and restart the current trajectory. |
| Space | Pause/resume movement. |
| R | Toggle the green elapsed-render timing stripe; it is not a numeric CPU meter. |
| Esc | Return to TOS. |

Mode, path, density and backend changes restart the scene with clean pages.
Pause retains the accumulated trail. The grid makes transparency and background
restoration visible; it is drawn into the clean Back canvas only at scene setup.

## Sources and preparation

`source/BALLS.PI1` is the lossless conversion of DCK disk B's
`SPRITE/BALLS.PC1`. The red, blue and green cells at Y=0/27/54 are retained,
including their original palette. Each normal `sSprite` has a 32×27 footprint
with transparent index zero and a compact one-bit preserve mask. The visible
sphere is about 27 px across; the remaining columns are transparent padding.

The eight included DAT files are NOEUD, CERCLE, 2CERCLES, DOUBLE45, CER-45,
CER_45~1, GROS_CER and REBOND. Each contains 180 or 360 pairs of signed XY words.
They are not freshly generated sine waves. `tools/assets.py` preserves point
order and advances **one source point per completed update**. Phase separation
between balls is 12 source points; colours repeat red/blue/green.

Coordinates are fitted offline to the stage above the footer:
`x=floor(sourceX*24/25)`, `y=32+floor(sourceY*3/5)`. The point order/cadence is
original, but these displayed pixel coordinates are an adaptation. All sprite
rectangles remain inside 320×200; the ordinary unclipped GodLib path is valid.
REBOND is deliberately a vertical path: its original X is constant.

`assets/source.json` records source hashes, crops, lengths and the transform.
The embedded tables and sprite data occupy 9572 bytes, plus pointer/descriptor
records. There is **no cache of screen frames and no preshift cache**.

## ASM and GodLib integration

`dckbobs_s.s` handles indices, wrapping, positions, history and the ordered
restore/advance/draw/store frame. C handles Platform/Screen lifetime, input,
scene setup and selection of the current logical page.

- `Bobs_Advance` reads the prepared XY table. There is no runtime multiplication,
  division or trigonometry; indices advance by four bytes and wrap at the end.
- `Bobs_Draw` calls the current canvas `mpFuncs->DrawSprite` using the GCC ABI.
  `Graphic_SetBlitterEnable()` selects GodLib's ordinary CPU or BLiTTER backend;
  the example does not embed a replacement DCK sprite renderer.
- Restore mode calls **`Graphic_ChunkList_ReStore()`** before any new balls,
  then draws every current ball and calls **`Graphic_ChunkList_Store()`** for
  its rectangle. There is a separate list for each page. The library's ASM
  restore merges adjacent strips and copies clean pixels from ScreenBack.
- Each list has capacity 32; eight 32-pixel sprites need at most 24 strip
  records, including their horizontal phases. Rectangles are fully inside the
  canvas because Store itself does not clip.
- Restoration remains CPU ASM when sprite drawing uses the BLiTTER. Switching
  the renderer changes sprite drawing; it does not turn chunk restore into a
  BLiTTER routine.
- Normal frames do not copy the whole screen. Full copies and header/grid setup
  happen only at reset or selection changes. Screen owns the canvases' row
  tables and VRAM; borrowed descriptors are not freed independently.

### Stable trails with two screen pages

Trails use the same masked GodLib sprites and deliberately skip background
restoration. There is no separate GodLib "trail renderer".

Simply skipping restore would give each page only alternate positions, making
the accumulated image flicker. Each trail update therefore stamps the **previous
frame first, then the current frame** into the logical page. Both pages accumulate
every global position in the same order. Frame zero is seeded onto both pages
when resetting, so neither page permanently misses the first stamp.

This costs **two sprite draws per ball/update** in trail mode. Clean restoration
needs one draw plus chunk restoration/store. Overlapping balls retain normal
masked drawing order; trails are persistent paint, not alpha blending or fading.

## CPU and verification

See [CPU.md](CPU.md), `profiling.json` and `verification.json` for measured
cycles, observed cadence, build hashes and test scope. The default four-ball
BLiTTER configuration has enough headroom for both modes at 50 FPS. Eight balls
are a useful heavier comparison, especially on the CPU renderer.

Native tests compare **420 complete 32000-byte buffers** against independent
masked-sprite composition: all eight trajectories, 1/4/8 balls, CPU/BLiTTER,
restore/trails, both pages, every horizontal shift and overlapping sprites.
Separate assertions check all eight path wraps, pause, controls and exit.
The shipped PRG also passes 1 MiB smoke tests on STE/German TOS 1.62 and plain
ST/TOS 2.06, including automatic CPU fallback without a BLiTTER.

```sh
make check
make profile
make debug-release
BOBS_DEBUG="$PWD/DCKBOBS.PRG" BOBS_SYMBOLS=/tmp/BOBSREL.PRG python3 tools/smoke_release.py
```

Debug/test programs, maps and dumps live under `/tmp`, not `analysis/`.
The Hatari helpers come from the local `hatari-debugging` skill. Tests use German
STE TOS 1.62. HRDB defaults to port 56001; `BOBS_HRDB_PORT` can select an isolated
mapped server port. Profiles include BLiTTER stalls, not just register setup.

[Restore preview](preview-restore.png) · [Trails preview](preview-trails.png)
