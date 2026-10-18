# Rotating hexagon iris — SuperHex

A standalone GodLib ST/STE example. **GodLib itself is unchanged.**
`N` grows a rotating black hexagon with a white outline, swaps pictures while
covered, then shrinks the hexagon to reveal the next scene. The mask occupies
bitplane 3; planes 0..2 contain the picture. This is a growing shutter, rather
than an aperture cut out of a black screen.

- `N`: next picture (ignored during a transition).
- `A`: automatic slideshow, initially off; four seconds between transitions at 50 Hz.
- `P`: pause/resume animation, including the rotation.
- `Esc`: return to TOS.

```sh
make
make run
```

The program embeds its two pictures and all tables. No external runtime files
are required. `make run` uses STE, 1 MiB, RGB PAL and **German TOS 1.62**;
plain ST also works. On STE, GodLib uses the blitter to restore the clean
background. On ST, it uses the CPU. The shutter fill is 68000 ASM in both cases.

## Algorithm and palette

Ported from `../../superhex_ste/src/main.c`: `iris_fill`, the transition block
and the clipping used by `draw_line_clip`. The original is described in
`../../superhex_ste/HANDOFF.md`, “Etap 4j”. No original game binary is needed.

`geometry.c` retains the original six half-plane equations: 1536 angles per
turn, Q14 sine/cosine, 28.4 X accumulators and additions per scanline. It prepares
200 horizontal span commands (800 bytes). `iris_s.s` ORs their inclusive edge
masks into plane 3 and writes full words between them, with eight bytes between
adjacent words of that plane. There are no per-pixel C raster loops. Geometry
is prepared once for each animation step and reused when paused.

The six edges are clipped before drawing through the existing GodLib ASM line
routine, avoiding a per-pixel walk outside the screen. Source pictures are
restored from Back before each mask, independently of the two alternating
screen pages. This also removes the previous outline from the image planes.
The example is fixed to 320x200, four interleaved planes, stride 160.

The palette is deliberately constrained:

| Indices | Meaning |
| --- | --- |
| 0..6 | Seven source-picture colours; 0 is black. |
| 7 | White, reserved for the edge. Never present in the clean picture/text. |
| 8..14 | Black copies of source colours under the mask. |
| 15 | White edge under the mask. |

An eight-colour picture using index 7 would leave white holes in the shutter.
`prepare.py` therefore uses ABC2 with two forced-black slots, folds slot 7 into
0, and reserves 7/15 for the outline. Both existing RGB artworks (castle from
`water`, forest from `wipe`) are converted to STE RGB444 without dithering;
provenance, converter options and previews are in `assets/`. The mask is a
palette-bank selection, not alpha transparency.

The apothem grows from 0 to 220 pixels in 40 increments and decreases again.
220 covers the viewport at any angle. Rotation includes the original signed
`step * 14` term plus a continuous two-unit phase. There are 41 displayed steps
per direction, including endpoints; actual elapsed time depends on rendering
cost. Palette changes happen only when the displayed frame is fully covered,
so the two pictures may use different source palettes.

The white edge here writes index 15 through normal four-plane GodLib lines;
the SuperHex version ORs planes 0/1 over its more specialized scene/palette.
This adaptation reserves a source index and gives the same solid white edge
with arbitrary seven-colour artwork. It is not a pixel-perfect replay of the
whole SuperHex scene.

## Rebuilding assets and verification

`make assets` uses Python/Pillow and the local `../../abc/abc2`; normal builds
use the checked-in binary assets. Sine values follow SuperHex's `tools/gensin.py`
(including its positive Q14 clamp).

```sh
make debug
python3 analysis/verify.py
```

The native test uses German TOS 1.62 on STE and UK TOS 2.06 on plain ST
(TOS 1.62 is STE-only). It compares complete VRAM
against an independent implementation of the SuperHex half-plane equations,
clipped edges and Bresenham lines, covers both pages and both pictures, checks
physical-page palette synchronization, pause and exit. Its report and decoded
native-frame preview are in `analysis/`. This example adds no public GodLib API.

Recorded verification: **250 complete-frame comparisons** (167 STE, 83 ST),
three transitions, both screen pages, paused-frame parity and clean TOS exits.
The report includes the tested program SHA-256.
