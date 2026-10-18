# CRT CPU / rendering cost

Hatari-HRDB, STE, 68000 at 8 MHz, 1 MiB, RGB PAL 50 Hz,
German TOS 1.62. Program hash, raw routine totals and frame counts are stored
in [analysis/profile.json](analysis/profile.json). The normal-renderer table
comes from the preceding two-scene build; its measured routines are unchanged.
The current thin-line transition is measured separately below.

| Mode | Cycles/update | Time at 8 MHz | Share of 20 ms frame |
| --- | ---: | ---: | ---: |
| Moving bright band, no image jitter/tearing | 4806 | 0.60 ms | **3.00%** |
| Normal automatic jitter and occasional tearing | 12202 | 1.53 ms | **7.63%** |
| Continuous tearing (`G`) | 91903 | 11.49 ms | **57.44%** |

The steady window contains 423 updates; the other two contain 422 each. Costs include C command and random
number generation, ASM register preservation, changed picture blits, blitter
busy/restart waiting and the scanline-mask update. These are rendering-budget
costs, including bus stalls while the BLiTTER runs, rather than a measurement
of CPU instructions alone with the blitter cost removed. Input, OS/VBL work,
Screen_Update waiting, startup and initial screen copies are excluded.
Percentages use 160000 cycles at 8 MHz / 50 Hz.

Continuous tearing deliberately changes every strip repeatedly. It typically
copies all three picture planes over 176 rows, with many separate blit starts.
The normal automatic mode spends most frames updating only the brightness
mask; its average depends on the jitter/burst schedule and random sequence.
The continuous-tearing number is a representative stress average, not a
mathematical worst-case bound for every command pattern.

The final mask kernel works on the difference between two bright-band intervals
rather than scanning 88 candidate rows. In the earlier implementation the mask
alone averaged about 9600 cycles/update; now it costs about 2060–2110 cycles.
Each screen page retains its own prior interval. The final data in profile.json
were captured after this change.

## TV off/on transition

[analysis/tv-profile.json](analysis/tv-profile.json) measures one actual `N` key
cycle, including all 90 off/black/on updates. The specialized MOVEM renderer
and command update average **34416 cycles / 4.30 ms / 21.51%** of a PAL frame.
The average spans both large image copies and thin-line/black frames; it is not
a worst-case bound. VBL/input (including the queued palette API), scene loading into Back and font setup are outside
the measured ranges. Scene loading and font preparation happen once at the
black midpoint.
The idle display resumes the normal CRT costs listed above.

This is a new renderer measurement, not a benchmark of the original NIEZW
binary. [NIEZW-TV.md](analysis/NIEZW-TV.md) records the structural changes:
offline row maps, visible-row MOVEM copying, per-page row reuse and incremental
clearing instead of a 200-row scan with generic software division/copy/clear.

## Verification

[analysis/verification.json](analysis/verification.json) records **188 complete
32000-byte frame comparisons**, on both alternating screen pages, using an
independent shifted-pixel reference. Cases cover all 16 supported horizontal
shifts (-7..+8), all vertical shifts (-1..+2), uniform/coalesced and independently
shifted bands, scanlines on/off, clipped/overlapping/disjoint/wrapped band
intervals and preservation of Back and captions. The harness also exercises
the actual input path and clean exit to TOS.
[TV verification](analysis/tv-verification.json) adds 180 complete transition
frames, every stage on both pages, both palettes, synchronized brightening with black preserved,
normal rendering after scene changes and clean exit.

```sh
make debug
python3 analysis/verify-hatari.py
python3 analysis/verify-tv.py
python3 analysis/profile.py
python3 analysis/profile-tv.py
```

These tests use the German TOS 1.62 image configured in the Makefile. No real
hardware measurements were made. Screenshots: [normal](analysis/preview.png),
[tearing](analysis/tearing.png).
