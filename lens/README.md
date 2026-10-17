# Mouse-controlled lens — 68000 ASM

A circular 64x64 magnifying lens over our castle picture, in ST-low 320x200,
16 colours. Works on ST and STE at 8 MHz with 1 MiB RAM; no blitter, fine scroll
or raster interrupt is required. The image is converted by ABC2 to the STE
4096-colour palette without dithering; a plain ST displays its RGB333 subset.

```
make
make run
```

Output: `LENS.PRG`. The short name also works with Hatari / TOS 1.62 autostart.

- **Mouse:** move the lens (default).
- **A:** automatic sine motion.
- **M:** return to mouse control, with its position synchronized to the lens.
- **R:** toggle the green elapsed-render raster band.
- **Escape:** exit to TOS.

The centre is clamped to x=32..287, y=32..167, keeping the complete lens inside
the screen. There is no clipping kernel. Horizontal motion remains pixel-accurate.
The faint white rim uses palette entry 15; all four bitplanes remain available.

## Renderer

The implementation follows the inverse-map / shifted-source / lookup C2P idea
in SMFX Motus `lens.s`, but is a new self-contained kernel, not a verbatim port.
It does not include Motus's animated eyes, flare, music, borders or screen system.

For an offset (dx,dy) inside radius 32:

```
r2 = dx*dx + dy*dy
factor = 1 / (1 + (1-r2/1024)^1.25)
source = centre + round((dx,dy) * factor)
```

This gives approximately 2x magnification in the centre and returns smoothly to
identity at the edge. Pixels at radius >=31.3 and <32 form the white rim.
`prepare.py` computes the mapping and generates eight unrolled ASM kernels,
one per x modulo 8. Nothing evaluates this formula in the frame loop.

`Lens_Init` converts the clean background, including captions, once in ASM to
three word arrays containing colour*4, colour*64 and colour*1024. For each group
of eight output pixels, the draw kernel gathers eight samples and uses three
lookup tables to combine their colours into four planar bytes. `MOVEP.L` writes
those bytes directly to the destination planes. Partial boundary groups sample
unchanged background outside the circle, preserving the surrounding image.
Splitting even/odd byte groups handles both halves of an ST word without sixteen
separate kernels or per-frame code patching.

Each logical page keeps its own old word-aligned rectangle. `Lens_Clear`
restores 64 rows of four or five 16-pixel groups from the clean background with
`MOVEM.L`; the full screen is never restored in the frame loop. The generated
sampler writes only byte groups intersecting the lens. C owns input, position,
page selection and the dirty-rectangle descriptor; runtime raster operations
and the initial planar conversion are in ASM.

## Memory and assets

This prioritizes speed over executable size and RAM:

- Three shifted source arrays: **384,000 B** in BSS.
- C2P lookup tables: **33,792 B**.
- Sampler and ASM support: **175,936 B** of code, mostly eight phase kernels.
- Castle: **32,000 B**, plus the normal GodLib screen pages/background.
- Standalone `LENS.PRG`: **312,452 B**.

The executable's text/data/BSS total is about 701 KB before dynamic GodLib
allocations. All recorded target tests use 1 MiB successfully. This is the
original renderer, restored in preference to the faster variant that needed
64,000 B more prepared source RAM. The default libcmini stack reserve is used.

Canonical picture: `../water/assets/castle-source.png`. Run `python3 prepare.py`
to regenerate the ABC2 conversion, lookup tables and kernel include. Source
hash, conversion settings and per-phase group counts are in
`assets/provenance.json`. Build-time Python may rasterize assets; the frame loop
has no C pixel/bit loops.

## CPU cost

Measured with HRDB instruction-cycle profiles on **ST 8 MHz, 1 MiB, TOS 2.06**:

| Mode | Rendering + restore + bookkeeping | PAL frame share |
| --- | ---: | ---: |
| Stationary centred mouse | 94,854 cycles / **11.86 ms** | **59.19%** |
| Automatic sine | 99,560 cycles / **12.45 ms** | **62.13%** |

The automatic case averages a mix of horizontal phases and four/five-word
restores. Both update at approximately **50 Hz**. This is CPU time for
`Lens_Render`, `Lens_Clear`, `Lens_Draw` and `Lens_Record`; input, VBL waiting,
initial conversion and the optional raster synchronization wait are excluded.
The green band shows elapsed render time rather than replacing the cycle profile.

```
make debug
python3 analysis/profile.py
python3 analysis/verify-hatari.py
python3 analysis/verify-meter.py
```

`analysis/profile.json` contains per-kernel costs. The verification harness
compares the entire 32,000-byte planar output with an independently evaluated
pixel reference, including untouched pixels and old-page trails. It covers all
16 horizontal ST word alignments, clamped edges/corners, both pages, automatic
motion, mouse return, controls, explicit IKBD mouse setup and clean exit. Input
positions are injected at the IKBD input state, not into renderer coordinates;
this does not claim host SDL mouse-motion injection coverage.

Recorded verification: **294 complete-screen comparisons** across ST/TOS 2.06,
STE/TOS 2.06 and STE/TOS 1.62, with zero missed VBLs. The visible CPU band,
marker-off image and palette restoration also passed a separate ST test. See
`analysis/verification-summary.json` and `analysis/meter-results.json`.
