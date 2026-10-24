# LCK wipe CPU measurements

Hatari-HRDB, STE / MC68000 / 8 MHz / PAL RGB / **1 MiB**, German TOS 1.62.
The renderer runs on the CPU with BLiTTER disabled. Every profile covers one
complete opening or closing phase, including the other display page catching up.

Included: ASM `Lw_Render` dispatch, the active kernel, shared full-area / row /
column kernels and colour-stage selection. Excluded: setup/show, C Advance /
PublishPalette, status/input, hardware palette writes in GodLib VBL,
Screen_Update, VBL and OS work. Percentages divide average cycles per update
by the **160000-cycle / 20 ms PAL budget**. These are averages, not peak costs
or physical-hardware measurements.

| Mode | Open CPU | Close CPU | Open / close cycles per update | Updates per phase |
|---|---:|---:|---:|---:|
| Spiral 8x8 | 8.85% | 4.77% | 14153 / 7626 | 51 |
| Fold | 18.55% | 18.51% | 29673 / 29615 | 81 |
| Alternating lines | 11.68% | 10.87% | 18689 / 17388 | 21 |
| Snake 16x10 | 3.31% | 2.84% | 5293 / 4541 | 81 |
| Instant | 81.59% | 40.72% | 130548 / 65156 | 2 |
| Colour steps | 4.17% | 2.17% | 6665 / 3476 | 41 |
| Centre rows | 2.45% | 2.41% | 3918 / 3853 | 81 |
| Row smear | 24.56% | 23.54% | 39304 / 37663 | 81 |
| Interlaced rows | 2.43% | 2.39% | 3889 / 3817 | 81 |
| Vertical curtain | 47.82% | 18.20% | 76517 / 29113 | 161 |
| Interlaced columns | 50.29% | 19.09% | 80467 / 30552 | 161 |

Colour steps hold each of eight scene indices for five VBLs. Their profiles
include those held updates and the two initial source copies / final clears;
they are not a claim that an individual full-area copy takes only 4% CPU.
The immutable palette pointer is published from C and applied by GodLib in
VBL. That API/hardware cost is outside these renderer-only numbers.

Row smear loads each 40-byte source chunk once and stamps it through its
prefix with MOVEM; released rows are restored separately for each page.
Column modes merge changed pixel masks in each 16-pixel group before scanning
all rows. Opening needs masked source bits; closing only clears bits.

## Normal application cadence

Separate ordinary-loop windows exercise a complete close / swap / open cycle,
including header changes and palette queuing. Idle frames are also present,
so missed-VBL counts are the relevant observation: all animated modes had
zero misses and ran at **50 FPS**. Instant mode recorded one missed VBL while
a full-page copy shared an update with status work. It is a two-page transfer,
not sustained animation; its average FPS across an idle-heavy window would
hide that single extra 20 ms interval.

| Mode | Loop frames observed | Missed VBLs |
|---|---:|---:|
| Spiral 8x8 | 920 | 0 |
| Fold | 932 | 0 |
| Alternating lines | 902 | 0 |
| Snake 16x10 | 926 | 0 |
| Instant | 924 | 1 |
| Colour steps | 944 | 0 |
| Centre rows | 944 | 0 |
| Row smear | 927 | 0 |
| Interlaced rows | 927 | 0 |
| Vertical curtain | 862 | 0 |
| Interlaced columns | 925 | 0 |

The `R` border stripe brackets the ASM renderer and shows elapsed time at that
screen position. It can include interrupts and does not replace HRDB cycles.

## Verification and artifacts

- `verification.json`: **4324 complete 32000-byte framebuffer comparisons**,
  zero mismatches, two pictures, eleven modes, opening/closing and both pages.
  Fold/smear check every row target; column tests include every normal batch
  boundary and extra odd targets to exercise single-column masks. Repeated
  targets check pause and page catch-up. Colour steps also check every sampled
  hardware palette against an independent stage calculation.
- Eleven live cycles hold the black seam: both image areas must be zero before
  replacement, then both pages must equal the exact next picture. Hardware
  palettes are checked before and after; colour mode uses its black stage at
  the seam. Selection during a transition, pause/resume and exit are checked.
- `release-smoke.json`: actual stripped PRG on STE, 1 MiB, German TOS 1.62;
  all eleven cycles, both final pages, pause and exit during a paused transition.
- `release-smoke-st.json`: same shipped PRG/checks on plain ST without BLiTTER,
  1 MiB, TOS 2.06. CPU measurements above are from the STE run.
- `profiling.json`: twenty-two complete ASM phase profiles with asserted entry
  counts, both final page-progress counters and eleven real-loop windows.
- `preview-*.png`: complete native pages decoded to indexed PNG. Colour-step
  previews use their stage palette, while HUD index 15 stays white.

Release smoke tests use the shipped executable with separately linked symbols.
Code/data after the first `$A0` bytes of TEXT must match; the excluded prefix
contains ELF metadata differing in stripped/unstripped links. Debug PRGs and
RAM dumps stay under `/tmp`, not in `analysis/` directories.

The PRG is **139282 bytes** (136.0 KiB), an increase of **5706 bytes** over the
four-mode build. Its two pictures occupy 51200 bytes; no frame cache was added.
SHA-256:
`44d63c6e879cae8389b7410f51f15843ccbc68cce8faca9076779f23c6d1399a`. All reports record that same release hash.
