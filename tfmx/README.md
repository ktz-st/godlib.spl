# TFMX — UGH! / selectable Lance and Leonard

Run **TFMX.PRG** with `SOUNDS.MDT` and `SOUNDS.SMP` in the same directory.
The bank is copied unchanged from `ugh.agt/assets/res`; default is the title
music, subsong **0**. It also contains the other six UGH! cues.

- **B**: switch Lance / Leonard (reloads the private song representation).
- **1 / 2**: restart at 12.5 / 25 kHz.
- **N**: next subsong, slots 0..6.
- **F1**: CPU palette bracket around sequencing, voice bridge and mixing.
- **Esc / Space**: stop and return to TOS.

Audio is driven by PAL VBL independently of drawing. Four separated bars show
channel volumes, not sample amplitude. The Amiga sequencer stays in ASM. See
[the GodLib API](../../godlib/music/tfmx.md) for format/rate/ownership limits.

## CPU and RAM

| Rate | Lance CPU | Leonard CPU | Lance RAM | Leonard RAM |
|---|---:|---:|---:|---:|
| 12.5 kHz | 29.73% | 32.53% | 185246 B | 101546 B |
| 25 kHz | 33.68% | 44.00% | 219420 B | 131546 B |

For this measured title window Lance is faster at both rates after bypassing
source-window copies when a full contiguous segment remains. Leonard still
uses less RAM. Lance previously used 40.09% / 43.94% CPU at 12.5 / 25 kHz; the
optimized path uses 29.73% / 33.68%, with unchanged allocations. RJP1 results
cannot be extrapolated to TFMX.


RAM is requested resident song + mixer workspace; common PRG, screens and
allocator overhead are excluded. CPU is HRDB instruction cycles for the title
track on 68000 8 MHz PAL STE, 4 MiB, German TOS 1.62, measured over approximately
12 seconds after approximately 20 seconds of playback. It includes sequencing,
voice adapter, generated mixer code, native DMA handling and block-copy/division
helpers; loading and rendering are excluded. These are tune-window averages,
not worst-case bounds or exact frame-aligned comparisons.

The native UGH! path uses Leonard. Lance reserves four small stitched source
windows to preserve live macro loop changes, adding 2688 B of RAM. It only
copies into them when the next source window crosses an attack/reload boundary.
It retains its 108..907 period limit; Leonard is preferable if notes fall outside
that range. Neither backend includes ProTracker or RJP1 sequencing code.

## Leonard / UGH! callback cadence

The Leonard path now invokes TFMX from its accepted-PCM-block callback, exactly
where UGH! advances the tracker. VBL still owns playback, independently of the
foreground. When the DMA ring buffer is busy, both mixing and sequencing wait;
a note or retrigger can no longer be consumed without producing its PCM block.
The previous adapter ran the sequencer before this decision and could discard
musical steps. Lance retains its one-step-per-VBL path.

`analysis/cadence-before.json` and `cadence-result.json` compare 1000 PAL VBLs
per rate with realtime audio enabled: sequence steps must equal accepted blocks,
and steps without a block must be zero. Before the fix, 16 steps at 12.5 kHz
and 9 at 25 kHz had no corresponding PCM block; after the fix both counts are
zero. These are not fast-forward tests.

## Lance instrument-dropout correction

UGH! TFMX envelopes often write volume **65**, while native Lance accepts only
**0..64**. Passing 65 unchanged corrupts its volume-ratio selection and can
silence the other instrument in a stereo pair; hardware-volume lookup also
reads past its table. Leonard already clamps these values. The Lance bridge
now saturates to 64 as well, without altering sequencer state or sample data.
The four displayed channel volumes also report the saturated values.

`analysis/volume65-before.json` records the regression failing on the previous
binary (stage 18). `analysis/mixer-core-result.json` tests that same case after
the fix at both rates. The 28000-step sequence test records raw volume maxima
and counts for all seven cues; the title alone contains 5647 values above 64
in its 4000-tick run. The source-window regression also rejects out-of-range
volumes reaching the native mixer.

The earlier DMA timing correction was a separate defect; it did not resolve
these instrument dropouts.

## Lance playback timing correction

The old callback prepared source windows before starting the already mixed
one-shot DMA buffer. Variable preparation cost shifted adjacent DMA starts by
up to **53840 cycles (6.73 ms)** in a 15-second title trace, producing gaps or
cutting the previous buffer short. The callback now starts DMA first, before
sequencing/stitching/mixing. The new trace peaks at **2620 cycles (0.328 ms)**;
remaining variation includes hardware-volume writes and interrupt latency.
This is DMA-register timing evidence, not a subjective listening verdict.
Lance's 7-bit PCM, resampling and hardware volume can still sound different
from Leonard's 8-bit software-volume path.

## Build and tests

```sh
make -C ../../godlib -j4
make
make check
make profile
```

- `analysis/sequence-result.json`: **28000** native sequence steps across all
  seven slots compared against the unmodified UGH! assembly's register output
  (addresses normalized to each private sample bank). Test-only reference code
  is not linked into the release.
- `analysis/mixer-core-result.json`: all four mixer/rate cases, **128 sequence
  steps** while the foreground spins (Lance: 128 VBL; Leonard may need more
  VBLs because of its block gate), USP preservation, same-address
  DMA retrigger, current/reload window contents and source advancement,
  all seven subsongs, ownership rejection, DMA/trap/callback cleanup and full
  restoration of free RAM.
- `analysis/verification-mixers.json`: final release controls, all seven slots,
  both rates/backends, changing non-silent stereo WAV and clean exit to TOS.
- `analysis/window-result.json`: 4000 title ticks; all four source windows match
  the expected sample/reload sequence byte for byte, and source consumption is
  within one byte of the PAL period-derived count per tick.
- `analysis/dma-timing.json`: final release DMA-start jitter regression;
  `dma-timing-before.json` preserves the failing baseline.
- `analysis/profile-mixers.json`: cycle components and allocations; sequencer
  calls equal VBL calls for Lance and accepted PCM blocks for Leonard.
  `profile-before-dma-fix.json` preserves the pre-optimization baseline.

`make check` needs the local read-only `../../ugh.agt` reference source and
Hatari skill helpers. Release builds/playback are independent of that directory.

Native tests report no source-window faults. Signal checks do not replace
listening or tests on a physical STE. The original `ugh.agt` game was not changed.

The replay is derived from the existing IRA-disassembled UGH! TFMX engine;
[provenance/hashes](../../godlib/music/tfmx-source.json) identify the local source
and input assets. Existing game music is not newly licensed by this example.
