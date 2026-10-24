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

## Seventh mode: DCK volume histogram (2026-10-24)

This new mode was measured separately on the seven-mode build with Popcorn,
using the same 8 MHz PAL STE / German TOS 1.62 / 1 MiB configuration.
`histogram-results.json` contains instruction counters, 2079 profiled frames,
96-frame fixture verification and exact build hashes. The earlier six-mode
results above remain historical measurements of their identified binaries.

| Component | Cycles/frame | PAL frame share |
|---|---:|---:|
| Histogram decay/trigger | 902 | 0.56% |
| Per-page delta drawing | 2021 | 1.26% |
| New histogram subtotal | 2923 | **1.83%** |
| Shared snapshot, PSG and animation processing | 7340 | 4.59% |
| Visualization subtotal | 10264 | **6.41%** |
| Music separately | 7677 | 4.80% |

Mode-change copies/reset, C dispatch and OS wrappers are excluded. There were
2634 normal frames around this profiling window with zero missed VBLs. New
rendering cost depends on how many volume buckets change and on their heights.

The histogram object is 276 bytes of code/constant rows plus 16 bytes of
counters; C keeps another 32 bytes of page history and a 32-byte palette.
The shipped PRG grew from 174226 to 174938 bytes in this checkout, including
mode integration, axis labels and captions. No frame cache or runtime heap
allocation was introduced. Replay code and all existing renderer objects are
unchanged; this mode consumes only the existing coherent RAM register snapshot.

## Four DCK PSG bar modes (2026-10-24)

Measured on the eleven-mode build, same 8 MHz PAL STE / German TOS 1.62 /
1 MiB setup with Popcorn. Instruction-range counts exclude C dispatch, OS
wrappers, one-time scene copies/reset and labels. Visualization totals include
the shared snapshot, note/level decoding and existing animation bookkeeping.
Music is measured separately. All values are song-dependent averages.

| Style | Frames | ASM drawing | Peak update + drawing | Visualization subtotal |
|---|---:|---:|---:|---:|
| Horizontal 256×10 | 1723 | 0.92% | 1.10% | 5.67% |
| Segmented 16 px | 1742 | 0.81% | 0.98% | 5.55% |
| Segmented 32 px | 1743 | 1.16% | 1.33% | 5.91% |
| Segmented 80 px | 1742 | 1.90% | 2.08% | 6.65% |

Music costs about 4.8% in each window. Peak update costs about 283 cycles/frame
(0.18%). All four run at 50 FPS; the measured normal windows total 9216 frames
with zero missed VBLs. The maximum-level fixture is correctness coverage,
not a worst-case CPU measurement.

New state is six bytes of peak levels. Existing VU per-page heights are reused;
there is no new frame cache or heap allocation. The PRG grows from the preceding
histogram build's 174938 to 175989 bytes. The 80 px variant uses four segments
per level rather than DCK's six, keeping the full bar clear of the 200-line UI.

`dck-psg-results.json` records hashes, counters, scope and 256 full-buffer fixture
checks. Live tests also verify both pages' header/footer, clean hide/show,
eleven-mode wraparound and exit. Native previews decode a complete display page;
control-debugger stops can interrupt the emulator's on-screen scanout.
