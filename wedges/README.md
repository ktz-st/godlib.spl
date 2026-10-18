# Rotating wedges — SuperHex background

**This is the effect in the user's grab0201/grab0202 screenshots:** six
alternating light/dark sectors rotating around the screen centre. It is the
SuperHex title-screen background (`bg_render` / `bg_copy`), not its growing
hexagon transition (`iris_fill`). This example has no logo, music or colour cycle.
GodLib itself is unchanged.

Build and run:

```sh
make
make run
```

`make` builds two programs: `WEDGES.PRG` (cached CPU/blitter) and
`WEDGERT.PRG` (live CPU/ASM, no frame cache). Use `make run-live` for the latter.

`WEDGES.PRG` builds its mask cache in RAM at startup; no external runtime files
are needed. Controls:

- `P` or Space: pause/resume.
- `R`: reverse rotation.
- Up/Down: speed, 1..16 angle units per frame (default 6).
- `B`: switch CPU/blitter in `WEDGES.PRG` on STE; unused in the live ASM variant.
- Esc: return to TOS.

## Original method

Three lines through the centre divide the screen into six alternating wedges.
SuperHex pre-renders one 60-degree sector, then uses the blitter to copy a
single bitplane, inverting it on odd sectors. The prepared frames use the
original Q14 trigonometry, signed 8.8 cotangents, row-centre sampling, clipping
and inclusive horizontal spans.

`cache.c` generates 32 frames of 320x200 at angles `frame*8+4` once at startup,
matching the 32-frame version of SuperHex. They occupy **256000 bytes of
allocated RAM**, released on exit, rather than being embedded in the PRG.
C computes horizontal span endpoints; the startup-only `Wedges_Span` ASM
routine writes the word masks and interiors. The PRG embeds only a 3840-byte
Q14 sine table, not the 256 KB image cache.
The original 320x246 mask is cropped by 23 rows, exactly as `bg_copy` does for
a 200-line viewport centred at (160,100). One full turn has 1536 angle units;
sectors of 256 units select normal/inverted frames. Geometry and span filling
are done during initialization; animation uses no trigonometry, division or
per-pixel C raster loops. `prepare.py` also generates the same cache offline
as a verification fixture; `assets/FRAMES.BIN` is **not linked** into the PRG.

`wedges_s.s` copies the selected 8000-byte plane into **bitplane 2** of the
normal 320x200 four-plane ST screen (160-byte stride). Planes 0, 1 and 3 stay
untouched. On STE the assembly programs the blitter like SuperHex: source
increments 2/2, destination increments 8/8, source or NOT-source operation,
shared bus, interrupts enabled. The plain-ST fallback is an unrolled 68000
word-copy routine with optional inversion. Each display page remembers its
last mask, so paused or unchanged pages need no copy.

Palette entries 0/4 select the dark/light blue background. The static footer
lives in plane 1; both indices 2 and 6 are white, making it independent of the
rotating wedges. This also demonstrates how a logo could have its own colours,
but no logo is drawn here. No raster interrupts are used.

## Verification

```sh
make assets                 # Python stdlib; sine table + offline cache oracle
make debug
python3 analysis/verify-tables.py
python3 analysis/verify.py
```

The first check extracts and host-compiles the actual `bg_span` and `bg_render`
functions from `../../superhex_ste/src/main.c`, renders their original 246-row
frames, crops them, and compares **all 256000 bytes** with the example cache.
The native test additionally compares all 256000 bytes generated at startup
with that reference. The resulting checksum and source-function checksum are recorded in
`analysis/tables-verification.json`.

Native tests compare complete screen buffers for all 32 phases and both
inversion parities on both pages, with CPU and blitter on STE and CPU on ST.
They also check preserved planes, keyboard controls and clean exit. STE uses
German TOS 1.62; plain ST uses UK TOS 2.06 because TOS 1.62 is STE-only.
Both use a 68000 at 8 MHz, 1 MiB, PAL RGB. Reports and a decoded native-frame
preview are in `analysis/`. Tests prove the mask geometry and renderer; they do
not claim to reproduce the full game scene, overscan, logo or music timing.

Recorded native verification: **384 complete-frame comparisons**, covering
all 32 masks × 2 parities × 2 screen pages in each of STE/blitter, STE/CPU and
ST/CPU configurations. The report includes the tested program SHA-256.

## File size

Generating the cache at startup reduces `WEDGES.PRG` from **326436 to 73890
bytes** (252546 bytes / 77.4% smaller). RAM still holds the same 32 cached
phases, so the animation keeps the same copy method. See `analysis/size.json`.

## Measured animation cost

Measured with HRDB on STE / 68000 / 8 MHz / 1 MiB / PAL RGB, German TOS 1.62,
default speed 6. Both variants use the same screen layout and cache.

| Backend | Renderer cycles/frame | Time at 8 MHz | Share of 20 ms frame |
| --- | ---: | ---: | ---: |
| Blitter | 37039 | 4.63 ms | **23.15%** |
| CPU, equal normal/inverse weighting | 84779 | 10.60 ms | **52.99%** |

This includes `Wedges_Render` and `Wedges_Copy`, including shared-bus blitter
stalls and polling. It excludes VBL/input/Screen_Update and the main-loop
animation update. Percentages are rendering cost divided by the nominal
160000-cycle frame budget, not a profiler share of all executed instructions.
The blitter path waits for completion; these figures do not imply concurrent
useful foreground CPU work.

The captures cover 422 and 423 rendered frames, with one bitplane copy per
frame at the default speed. CPU normal and inverted copies cost approximately
68172 and 100224 cycles respectively; the complete-rotation estimate weights
them equally. The actual CPU capture's mean was 52.92%; both figures and their
call counts are retained in `analysis/profile.json`. Lower speeds or pausing
can skip copies when a page already has the requested phase; they were not
used to reduce the headline figures. Blitter rendering uses about **56% less
of the frame budget**, or **2.29 times less time**, than the CPU path.

The startup RAM-cache generation is outside that animation measurement:
119 VBLs (~2.38 s) on STE and 118 VBLs (~2.36 s) on plain ST in the verification
runs. No geometry is generated during animation.

Reproduce with `make debug && python3 analysis/profile.py`. The report records
the tested PRG SHA-256; `analysis/verification.json` uses the same binary.

## Live ASM variant — no frame cache

`WEDGERT.PRG` computes and rasterizes the wedges on demand. Its build does not
link `cache.o` or `wedges_s.o` and never allocates or builds the 256000-byte
image cache. The normal GodLib display buffers are still present.

`live_s.s` contains the entire geometry and raster kernel. Three sorted Q8
cotangents feed Q16 intersections, advanced by addition for each scanline.
Only the intervals swept by the three rays are XORed into plane 2; the screen
is not cleared and repainted on every update. Each display page stores its
previous edge masks and offsets, so double buffering remains correct.

At a sector boundary the rays are matched cyclically, reversing that order
below the centre. Complementing the remaining interval accounts for the
normal/inverted sector change. When that interval spans the clipped viewport,
its complement is empty and no pixels need touching. This avoids a full-plane
inversion and the slow spikes at the start of a new sector. The span operations
are inlined, and a per-half dispatch selects the ordinary/forward/backward
path without repeated mode tests on every row.

The renderer stores **4808 bytes of per-page edge history in total** (two
headers plus 200×3 packed mask/offset records per page), **1476 bytes** of
cotangent/edge lookup data, and a six-byte code dispatch table. These are
geometry state and masks, not rendered frames. The kernel has 16 bytes of local
stack plus saved registers/call data; the normal GodLib display buffers remain.
No scratch bitmap or blitter is used. Planes 0, 1 and 3 remain untouched.

The same 32 angle phases are retained for an exact comparison with the cached
example. This version does not add finer angular resolution. At default speed
6 both pages require a new render on every update. Pausing or repeating a phase
can reuse a display page, as in the cached variant. Both pages are primed once
at startup; there is no 256 KB generation delay.

```sh
make debug
python3 analysis/verify-live.py
python3 analysis/verify-cadence.py
python3 analysis/profile-live.py
```

Native verification checks all 32 phases × 2 inversion parities × 2 pages,
plus forward/backward wrap and arbitrary parity jumps: **288 complete-frame
comparisons** on STE and ST against the cache already proved identical to the
original SuperHex code. It also checks pause, reverse, speed, preserved planes
and clean exit. `verification-live.json` records the tested PRG hash.

The uninterrupted cadence test uses main-loop frame, VBL and missed-VBL counters
over more than two full rotations per direction at default speed. This catches occasional
slow frames that an average renderer time alone would hide. STE uses German
TOS 1.62; plain ST uses TOS 2.06, both at 8 MHz with 1 MiB.

The profiling script uses an isolated HRDB bind port (56123), leaving other
emulator sessions untouched. A tiny macOS DYLD interposer changes only the
child's bind port. `hrdb-port.c` is host-only profiling support.

### Cached versus live: measured result

Same STE / 68000 / 8 MHz / German TOS 1.62, speed 6. Cached binary is unchanged
from its recorded measurement. The live capture contains 422 rendered updates.

| Variant | Frame cache | Renderer time/update | Nominal 50 Hz budget |
| --- | ---: | ---: | ---: |
| Cached + blitter | 256000 B | 4.63 ms | 23.15% |
| Cached + CPU, balanced rotation | 256000 B | 10.60 ms | 52.99% |
| Previous live ASM, full repaint | 0 B | 28.82 ms | 144.08% |
| **Live differential ASM** | **0 B** | **15.52 ms** | **77.61%** |

The new live renderer uses **46.1% less time** than its previous full-repaint
version. Native VBL counters confirm **50 updates per second with zero missed
VBLs**, on both ST and STE in both rotation directions at default speed 6. This is live geometry and pixel
updates, not a copy of prepared bitmap frames. Higher speed settings change
more pixels per update; the 50 FPS measurement applies to the tested default
speed, not a guarantee for every arbitrary phase jump.

`WEDGERT.PRG` is **71572 bytes**. Edge history uses 4808 bytes instead of a
256000-byte frame cache; geometric lookup tables add 1476 bytes and the code
dispatch table another six. A 64-byte diagnostic histogram records any late
angle phases; frame/VBL counters independently check cadence. The ordinary
GodLib screen buffers are separate and unchanged.

Renderer percentages include all live geometry, XOR writes and C render
dispatch, but exclude VBL/input/Screen_Update and main-loop animation control.
They divide measured cycles by the nominal 160000-cycle/20 ms frame budget.
The old 144% figure describes work per update, not literal CPU utilization
above 100%; that version ran at approximately 25 FPS.

See `analysis/profile-live.json`, `cadence-live.json`, `comparison.json` and
`verification-live.json`. Reports record the tested PRG SHA-256; the old live
profile is retained as `profile-live-before.json`. GodLib remains unchanged.
