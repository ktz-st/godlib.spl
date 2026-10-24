# CPU measurements

Hatari HRDB: STE 68000 at 8 MHz, PAL RGB, 1 MiB, German TOS 1.62.
Source: `tools/profile.py`, `tools/profile_spikes.py`. Results:
`profiling.json`, `profile-spikes.json`.

| Effect | All 4 planes | Plane 1 | Planes 0+2 |
| --- | ---: | ---: | ---: |
| Moving 128×64 block | 31.20% | 16.42% | 29.24% |
| Repeated rows | 84.60% | 47.55% | 87.63% |
| Skipped rows | 82.06% | 45.12% | 85.19% |
| Reverse destination / roll | 81.30% | 44.41% | 84.48% |
| 32×80 strips (average) | 8.48% | 5.21% | 7.71% |

Percent of a 160,000-cycle / 20 ms PAL frame. Scope includes ASM movement,
command construction, old-footprint/dropped-plane restoration, all copies and
register saves. Excludes C captions/input, Screen_Update and VBL/OS. Each
steady measurement spans 320 updates: two complete 160-step animation cycles.
No BLiTTER.

MOVE includes **both** restoring the old 128×64 rectangle and drawing the new
one. The other full-stage modes copy only the selected planes. Mask 5 selects
two nonadjacent planes; full-plane MOVEM copies can therefore be faster than
those two separate word streams.

The application loop maintained **50 FPS in all 15 mode/mask combinations**,
on both the actual ST and STE release runs. STRIPS changes arrangement every
16 ticks. Both pages copy the new arrangement once, then reuse it: its average
includes 2 redraws and 14 idle frames per 16 ticks. Paused settled modes cost
about **0.38–0.39%**, with no block-copy calls.

## Single-frame costs

These explicit measurements separate infrequent work from averages:

| Case | Cycles | Time at 8 MHz | PAL frame |
| --- | ---: | ---: | ---: |
| Strip redraw, mask 15 | 103,684 | 12.96 ms | 64.80% |
| Strip redraw, mask 2 | 61,924 | 7.74 ms | 38.70% |
| Strip redraw, mask 5 | 93,980 | 11.75 ms | 58.74% |
| Full effect → moving block | 153,464 | 19.18 ms | 95.92% |
| Full effect → strip window | 231,784 | 28.97 ms | 144.87% |
| Repeat: four planes → one | 234,876 | 29.36 ms | 146.80% |

The strip redraw itself fits within a frame. Changes of mode or mask may also
require restoring old planes/areas: the two measured ~29 ms cases need an
extra VBL once on each page. These one-time changes are outside the steady
50 FPS measurements. Header refresh is also outside the ASM timing above.
The table gives measured cases, not a maximum over every possible transition.

The visible R stripe measures elapsed time and can include interrupt time;
it is not identical to HRDB instruction-cycle attribution.
