# Mouse-controlled bitplane torch

`TORCH.PRG` illuminates our castle-and-lake picture with a mouse-controlled
filled circle. It runs on a plain ST or STE, 320x200, 68000, without a BLiTTER
or raster interrupt handler. All assets are embedded in the executable.

```sh
make
make run
```

| Key | Action |
| --- | --- |
| Mouse | Move the light; default mode |
| A | Automatic motion for demonstration/profiling |
| M | Return to mouse control at the current position |
| R | Toggle visible CPU timing band |
| Esc | Restore TOS |

The radius is 48 pixels. The centre is clamped to the screen, and the disk is
clipped at all four edges. Mouse position is written back after clamping, so
moving back from an edge responds immediately.

## Image and palette

`prepare.py` reuses `../water/assets/castle-source.png`, the existing generated
castle artwork. ABC2 converts it to **eight colours from the STE 4096-colour
palette, without dithering**, reserving index 7 for white captions. This
matches the other examples' converter choice. The source and conversion
arguments are recorded in [asset provenance](assets/provenance.json), and
[castle-8col.png](assets/castle-8col.png) previews the bright image.

Planes 0..2 store the picture. Plane 3 is exclusively the light mask. Palette
entries 0..7 are dimmed versions of the eight source colours; entries 8..15
contain the bright colours. The shifter selects the appropriate bank directly
from the mask bit. ST displays the compatible three-bit-per-channel subset;
STE preserves the full RGB444 palette. No pixel-colour blending runs per frame.
Captions form part of the three-plane image and are illuminated the same way.

## ASM renderer and restore

`torch_s.s` erases the previous light's word-aligned bounding rectangle on
**plane 3 only**, then draws the current disk as horizontal spans. Each screen
page has its own previous rectangle, so alternating pages do not leave trails.
Partial words use precomputed left/right masks; complete words use an unrolled
fill sequence. Only 194 bytes of circle half-widths are needed, without
preshifted circle images. The immutable picture planes remain untouched.

C handles lifecycle, mouse input, optional automatic position generation, and
records an eight-byte dirty rectangle per page. Both erase and raster drawing
are 68000 ASM. `Torch_Record` is included separately in the CPU total so that
the per-page bounds bookkeeping is accounted for. The renderer currently
assumes standard four-plane ST-low memory with a 160-byte stride.

## Measurements and verification

```sh
make debug
python3 analysis/profile.py
python3 analysis/verify-hatari.py
```

Profiling uses Hatari-HRDB, ST/68000 at 8 MHz, 1 MB, TOS 2.06, PAL, with the
CPU marker disabled. The script measures a stationary centred disk and a
moving disk on the automatic path. [profile.json](analysis/profile.json)
separates the wrapper, old-mask clear, disk draw and dirty-bounds bookkeeping.
The centred disk costs **47168 cycles / 5.896 ms / 29.43%** of a PAL frame.
Automatic movement averages **46676 cycles / 5.835 ms / 29.13%**, including
clipping near the top/bottom. Both captures show approximately **50 updates/s**.
C input/automatic positioning and VBL waiting are outside these kernel totals.

The optional CPU marker waits for visible row 8, then colours palette entry
zero during erase/draw. It restores the image's original palette entry after
the work. The synchronization wait is excluded from the profile.

The target harness compares all 32000 bytes with an independent circle
inequality and the clean image, checking that planes 0..2 never change.
Cases include all sixteen horizontal bit alignments, all edges and corners,
clamped out-of-range coordinates, alternating pages and automatic/mouse mode
switches. Input tests inject the IKBD coordinate state read by the real mouse
getters; they do not simulate host SDL mouse motion. IKBD command tracing
separately verifies that relative mouse mode is enabled. Configurations are
ST/TOS 2.06 and STE/TOS 2.06/1.62, 8 MHz / 1 MB. Results and screenshots are
in `analysis/`.

All three configurations passed: **294 complete-screen comparisons**,
with no missed VBLs. See [verification summary](analysis/verification-summary.json).

The visible timing band and palette restoration can be checked separately:

```sh
python3 analysis/verify-meter.py
```
