# SNDH visualization CPU measurements

Hatari-hrdb, STE 68000 at 8 MHz, 1 MiB, RGB PAL 50 Hz, German TOS 1.62.
Included `popcorn.snd` (mOdmate), F1 stripe off. Both the saved previous build
and the optimized build were measured with the same script and boot/input
schedule. Raw counters and both build hashes: `cpu-profile.json`.

## Optimization comparison

| Visualization including PSG/animation work | Before | After | CPU reduction |
| --- | ---: | ---: | ---: |
| Three synthetic scopes | 44.52% | 15.83% | 64.5% (2.81× faster) |
| Expanding rings | 54.37% | 19.32% | 64.5% (2.81× faster) |

The earlier published averages were 42.66% / 54.94%; the fresh baseline differs
slightly with the sampled music passage and skipped VBLs. This table compares
fresh measurements of both builds rather than mixing those old figures with a
new run. Playback costs another approximately 4.8%, separately.

## Profiled modes

| Mode | Profiled frames | Visualization cycles/rendered frame | Visualization | Music separately |
| --- | ---: | ---: | ---: | ---: |
| Three VU bars | 322 | 23472 | 14.67% | 4.59% |
| 80 note bands | 322 | 16174 | 10.11% | 4.79% |
| Piano | 322 | 40976 | 25.61% | 4.79% |
| Three synthetic scopes | 322 | 25323 | 15.83% | 4.81% |
| Expanding rings | 322 | 30910 | 19.32% | 4.82% |
| RGB colour organ | 322 | 7311 | 4.57% | 4.66% |

Percentages are shares of the **160000-cycle budget** at 8 MHz / 50 Hz.
The subtotal includes the PSG snapshot, level/note updates, shared animation
state and active ASM renderer, including scope parameter preparation. Music is
attributed separately to its loaded code range. These are per-rendered-frame
costs; initialization, mode-change page copies, C dispatch and OS/interrupt
wrappers are excluded. All five optimized windows rendered 322 frames; the
previous scope window rendered 311. These are song-dependent averages, not
worst-case guarantees for every SNDH or every possible register state.

## What changed

Scopes no longer synthesize 768 samples or compare/copy per-page sample arrays.
They keep three phase-step/amplitude pairs per page and skip unchanged pairs.
Each changed trace draws horizontal word runs and unrolled vertical spans.
**One division per trace** obtains a half-cycle quotient/remainder; remainder
carries determine every following edge. Reverse phase handles steps above
Nyquist and preserves the old 256 sampled pixel positions exactly.

Rings use offline-generated native 68000 kernels in `assets/RINGS.S`.
The normal two-frame page transition fuses old/new circle masks into one XOR
per changed word. Retriggers, expiry and arbitrary frame jumps use standalone
erase/draw kernels. Common masks stay in registers; loops and per-word mask/
offset decoding are removed. There are still four slots per channel, the same
24 ages/radii, colours, positions and XOR overlap behaviour.

## Optimization build memory tradeoff and verification

The PRG grew from **151462 to 172471 bytes**.
Text+data+BSS grew by **19416 bytes (18.96 KiB)**
because the ring kernels are expanded code. Scope sample/history storage fell
from 2304 to 36 bytes. No runtime allocation or code generation is added.

Native reference checks cover **60 scope frames + 84 ring frames**, comparing
all 32000 screen bytes on both pages. Fixtures include forward/reverse phase,
periods 0/6/7/8/9/10/11/12/13, random periods/volumes, silence/envelopes,
all ring ages, overlapping rings, ordinary deltas, arbitrary jumps/retriggers,
expiry, mode/visibility changes and clean Esc exit. The integrated five-mode
136-frame test also passed before the final arithmetic/register-mask changes;
those final changes were checked by the targeted sweeps above.

Replay/snapshot code is unchanged by this optimization. The earlier comparison
of 2437 PSG writes with/without snapshot remains historical evidence for the
included tune; it is not a new audio measurement of this build.

## Sixth mode: palette-only RGB colour organ

The first five rows above retain their earlier optimized-build profile; the
new colour-organ row was measured separately on the six-mode build using the
same machine and per-instruction profiling method. Per-window build hashes
are stored in `cpu-profile.json`.

The lamp update costs **145 cycles/frame, 0.09% CPU**, writing only three palette
words. With the existing shared PSG snapshot, note/level decoding and animation
bookkeeping, the visualization subtotal is **4.57%**. Playback is another 4.66%
in this window. One-time static circle stamping and mode-entry page copies are
excluded. There are no steady-state circle draws or screen copies.

Native verification checks 43 palette states: every fixed volume, envelope
flags, mixer/noise gating, geometry of all three discs, and unchanged bytes in
both display buffers and Back throughout animation and V hide/show. Six-mode
wraparound and clean TOS exit pass on German TOS 1.62.
