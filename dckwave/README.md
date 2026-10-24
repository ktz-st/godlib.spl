# DCK bitmap wave in 68000 ASM

Three selectable bitplane waves over our existing ABC2 16-colour castle/lake
picture. The 320×160 image stage is at Y=24..183; text above and below stays
still. This standalone GodLib example works on ST/STE without BLiTTER,
hardware scrolling, raster interrupts or a preshift/frame cache.

| Key | Action |
|---|---|
| 1 | Wave the complete picture: planes 0+1+2+3 |
| 2 | Wave only plane 1; the other three stay at their original positions |
| 3 | Wave planes 0+2; planes 1+3 stay still |
| Space | Pause / resume |
| N | Pause and advance one phase |
| R | Toggle elapsed renderer-time border stripe |
| Esc | Restore TOS and exit |

All selected planes share the same eight-pixel sine displacement. Moving only
some planes changes the combinations of palette bits, producing coloured
fringes and ghost images. This uses the ordinary fixed picture palette: there
is no RGB blending or palette animation. The original 16 indices are retained;
the header uses the picture's bright index 14.

The phase advances once per rendered update, with 256 positions and a spatial
step of two positions per row. At 50 FPS one period takes 5.12 seconds. Pause
and step retain per-page state, so the second buffer catches up to the same
target. Both pages are managed by the normal GodLib Screen loop.

## Relationship to DCK

Recovered DCK4/LCK1 TEXT `$0CE0–$1004` generates selected-plane copy and
`ROXR.W` / `ROXL.W` kernels; `$1990–$19F8` drives signed per-line shifts.
See [the DCK/LCK audit](../../DCK/EFFECTS-AUDIT.md) and the recovered
[generator](../../DCK/extracted/effects/bitmap-wave-generator.s).

This adaptation retains those word carry chains and rewrites their scheduling:

- Each page remembers its previous wave-table pointer and plane mask. Rows
  with the same displacement need no writes. An identical whole page returns
  immediately, making steady pause inexpensive.
- A one/two-pixel difference uses an unrolled chain across twenty words of
  one plane. The leftmost/rightmost incoming bit is fetched from the immutable
  original image, or zero outside its width. Repeated reversals therefore
  recover previously clipped pixels instead of eroding the picture.
- Larger jumps use a direct source path which joins adjacent original words
  with register shifts. Switching modes restores inactive planes as well as
  moving newly selected ones; neither display page needs a full reset.
- The 256-position, amplitude-eight table is prepared offline. It replaces
  DCK's configurable 360-degree setup, rather than claiming identical motion.
  No self-modifying kernel or privileged SR writes are required.

C owns setup, input and page selection; ASM owns phase advance and pixels.
The source image is fitted vertically from 320×200 to 320×160 by nearest-row
selection. `source/CASTLE.PI1`, its indexed PNG preview and
`assets/source.json` retain the original artwork/palette and provenance.

## Build and verification

```sh
make
make run
make assets             # Pillow: native picture, palette, sine table
make check              # native framebuffer comparisons in Hatari
make profile            # Hatari-HRDB instruction-cycle measurements
```

Uses the local GCC ELF / vasm / GodLib / libcmini toolchain and ABI. Test tools
import the installed `hatari-debugging` skill helpers. The default ROM is the
German STE TOS 1.62; `TOS` can override its path. Debug PRGs and RAM dumps stay
in `/tmp`. No GodLib library source changes are needed.

The ASM object has **912 bytes of renderer/setup code** and **26726 bytes of
embedded data**: one 25600-byte picture, a 32-byte palette, a repeated 768-byte
wave table, a 320-byte zero table and three plane masks. Page histories need
only two pointers and two words (12 bytes). GodLib supplies the usual display
pages and Back buffer; there is no additional animation-frame allocation.

See [CPU.md](CPU.md) for measured CPU/FPS and the verification reports.
