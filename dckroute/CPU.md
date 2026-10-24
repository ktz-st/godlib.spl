# CPU measurements

Hatari HRDB, STE 68000 8 MHz, PAL RGB, 1 MiB, German TOS 1.62.
Source and results: `tools/profile.py`, `profiling.json`.

| Case | Cycles/update | Time at 8 MHz | PAL frame |
| --- | ---: | ---: | ---: |
| Curve, settled | 63,580 | 7.95 ms | 39.74% |
| Horizontal strip, settled | 62,932 | 7.87 ms | 39.33% |
| Vertical column | 30,389 | 3.80 ms | 18.99% |
| Curve 9 → 4, 128-update window | 65,062 | 8.13 ms | 40.66% |
| First curve → column frame | 93,884 | 11.74 ms | 58.68% |
| First column → curve frame | 68,108 | 8.51 ms | 42.57% |

Scope: ASM text advance, FE/FF decoder, interpolation, per-page erasure, drawing,
register saves and frame dispatch. Excludes C captions/input, Screen_Update,
VBL/OS and waiting. Normal cases average 128 updates; the morph window includes
updates after the curve has settled. The two mode-switch costs measure one
first frame without advance, including removal of the entire old footprint.
They are measured cases, not a bound on every possible route combination.

The regular application completed **3,643 frames without missed VBLs: 50 FPS**,
with automatic commands active. Rendering uses no BLiTTER. The visible R stripe
measures elapsed time and may include interrupts; it is not the same measure
as the instruction-cycle totals above.
