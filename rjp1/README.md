# RJP1 — Richard Joseph / VectorDean

Build with `make` and run **RJP1.PRG** alongside the two `.SNG` / `.INS` pairs.
PAL Atari STE/MegaSTE, DMA stereo; verified using German TOS 1.62.

- **1 / 2 / 3**: restart at 12.5 / 25 / 50 kHz (50 kHz is Lance only).
- **B**: switch Lance / Leonard, reloading the song for that backend. Switching
  from Lance 50 kHz selects Leonard 25 kHz.
- **N**: next subsong, including slot 0 (not always silent).
- **M**: switch JON / WARX4. JON is unpacked from the existing RNC assets; WARX4 comes from `cfintro.rjp/music`.
- **F1**: palette CPU bracket around mixing and sequencing.
- **Esc / Space**: stop and return to TOS.

Four separated bars show the sequencer's channel volumes, not sample peaks.
Audio runs from a GodLib VBL callback independently of rendering. See the
[library API](../../godlib/music/rjp1.md) for ownership, loading and limits.

## What changed from cfintro.rjp

The original Makefile actually uses the **VectorDean ASM** sequencer; the
ScummVM-derived `rjp1_player.c` is unused. Its active path is:

```
VectorDean -> fake Amiga AUD registers -> C polling translator -> Lance Paula
```

The new native trigger/volume/period writes go directly to the shared GodLib
Paula backend selected at load time. This eliminates polling and its ambiguous “pointer changed”
note detection. Repeated notes retrigger even when the instrument/address is
unchanged; one shots stop and real sustains loop. Attack data and loop guards
are prepared explicitly for Lance. Lance PCM alone is reduced to 7 bits; modulation waveforms
are not accidentally attenuated with the sample bank.

RJP modulation can exceed Lance's 1024-entry period lookup array. The Lance path
caps its output at the existing table's maximum supported period, 907. The
old polling translator left those values unchecked. The mixer also retains its
existing minimum period 108. This is a pitch-range limit, not an extension of
Lance to all Paula periods.

## Memory

The original `cfintro.rjp/lancepaula.s` reserves **265170 bytes** in its nine
large fixed buffer/table/code arrays, regardless of rate. GodLib allocates:

| Output | Shared resident workspace | Saved against those fixed arrays |
|---|---:|---:|
| 12.5 kHz | 142146 B | 123024 B |
| 25 kHz | 176320 B | 88850 B |
| 50 kHz | 218440 B | 46730 B |

Initialization additionally needs 500 / 1000 / 2000 temporary bytes, freed
before playback. A common owner lease prevents LanceMod, LeonardMod and either RJP1 backend
from using DMA simultaneously; linking this player does not pull in the ProTracker sequencer.
The generated mixer is built in RAM rather than stored as large zero arrays
inside the PRG.

Prepared songs are separate from that workspace:

| Song | Original SNG + INS | Lance prepared | Leonard prepared |
|---|---:|---:|---:|
| JON | 135467 B | 244156 B | 135496 B |
| WARX4 | 230977 B | 275874 B | 231006 B |

Lance prepared data includes metadata, deduplicated 7-bit attacks/sustains, original
modulation arrays and 664-byte guards per unique sample. It can exceed the raw
files: the guards and explicit loop boundaries are required for safe block
mixing. Suffix sustains reuse the attack; this saves **12662 B** on INTBASE
compared with always copying the sustain separately (historical INTBASE test, before replacement by JON). `Rjp1_GetInfo()` reports
the actual allocation. Original files are released after preparation.

Leonard retains the original full 8-bit INS bank and relocated song, without
PCM guards or duplicate attack/sustain buffers. Its workspaces are **61134 B**
at 12.5 kHz and **91134 B** at 25 kHz. Backend preparation is done outside VBL.
Both backends advance the RJP sequencer every PAL VBL, including VBLs where
Leonard does not need to generate another DMA block.

## Lance / Leonard comparison

Measured with HRDB on **68000 8 MHz, PAL STE, 4 MiB, German TOS 1.62**.
Each window lasts about 12 seconds, starting roughly 20 seconds into subsong 1.
CPU includes the sequencer, adapter, native mixer, wrappers and generated code
in RAM; it excludes loading and drawing. Windows are comparable tune regions,
not exact frame-aligned traces or worst-case budgets.

| Song | Rate | Lance CPU | Leonard CPU | Lance RAM | Leonard RAM |
|---|---:|---:|---:|---:|---:|
| JON | 12.5 kHz | 17.79% | 30.49% | 386302 B | 196630 B |
| JON | 25 kHz | 20.99% | 44.00% | 420476 B | 226630 B |
| WARX4 | 12.5 kHz | 18.93% | 35.84% | 418020 B | 292140 B |
| WARX4 | 25 kHz | 21.97% | 41.29% | 452194 B | 322140 B |

RAM means requested resident **song + mixer workspace**, excluding common PRG,
screens and allocator overhead. Lance uses less CPU; Leonard saves 46–49% RAM
for JON and 29–30% for WARX4. Both engines are linked in this selectable example,
but only the selected workspace and song representation are allocated.

```sh
make check-mixers
make profile-mixers
```

- `analysis/profile-mixers.json`: cycle breakdowns and allocation sizes for all
  eight cases. Sequencer calls equal VBL audio calls in every case.
- `analysis/mixer-core-result.json`: all eight cases run 128 VBL ticks while the
  foreground spins; USP survives; one-shot silence, loop boundaries and identical
  pointer retriggers pass; cross-player ownership is rejected; DMA/trap/callback
  and all free RAM are restored after shutdown.
- `analysis/verification-mixers.json`: release playback, both banks/rates/backends,
  stereo WAV checks, subsong changes, controls and clean return to TOS.
- LeonardMod's existing two-rate/five-visualization VBL regression also passes
  after sharing its native mixer. No ProTracker sequencer is linked into RJP1.

## Historical initial Lance measurements

`analysis/profile.json` contains HRDB instruction-cycle measurements, including
Lance's **generated code in the allocated workspace**. The sequence comparison
runs the original sequencer + polling translator and the native sequencer on
identical 50 Hz input, with voice snapshots/restores excluded from the measured
regions. It is a comparison of sequence/bridge cost; most audio work is still
sample mixing. The historical full-audio measurements below use INTBASE subsong 1 on an 8 MHz PAL
STE and vary with the tune, pitch and active voices; they are not universal
worst-case budgets. The UI and small outer wrappers are excluded.

The measured sequence/bridge cost fell from **6556 to 5050 cycles/tick**
(**23.0% less**). Full audio for the measured INTBASE window costs:

| Rate | Audio cycles per VBL | Share of an 8 MHz / 50 Hz frame |
|---|---:|---:|
| 12.5 kHz | 24477 | 15.3% |
| 25 kHz | 29377 | 18.4% |
| 50 kHz | 37459 | 23.4% |

Reproduce with:

```sh
make -C ../../godlib -j4
make check
make profile
python3 analysis/check-lance.py
```

`check` needs the read-only reference files in `../../cfintro.rjp` and the local
Hatari helper scripts. Release playback/building does not depend on cfintro.

- `core-result.json`: sequence steps across all subsong slots; original
  period/envelope/volume arithmetic compared against the native path (period
  output capped to the mixer range); direct one-shot, retrigger and sustain
  fixtures; all three rates; foreground with USP sentinel `0x12345678`;
  exclusive mixer ownership; DMA/trap/callback/RAM recovery; Lance restart.
- `verification.json`: actual release PRG, both banks, all rates, subsong changes,
  CPU toggle, stereo WAV peak/RMS checks and clean return to TOS.
- `lance-regression.json`: existing LanceMod PRG still plays stereo and supports
  its five visualization modes after extracting the shared mixer backend.
- `profile.json`: reproducible cycle counts and configuration.

Recordings prove changing/non-silent stereo, not subjective sound quality or
real-hardware certification. WARX4 deliberately starts with long rests on some
channels, so recordings extend beyond its introduction.

VectorDean retains its original Andi Smithers / Millennium 1992 attribution.
Music is copied from the user's existing cfintro assets; no new redistribution
licence is implied. Source hashes are recorded in
[`music/rjp1-source.json`](../../godlib/music/rjp1-source.json).

### Historical Lance WARX4 long playback check

`make check-war` measures at least five minutes of subsong 1 at each output
rate, using the actual example UI and a test-only VBL wrapper. HZ200 timestamps
are collected in RAM; no file writes or debugger operations occur inside the
callback. `analysis/war-timing.json` records cadence and callback duration in
5 ms bins. With that quantization, a 40 ms missed-VBL interval is distinguishable
from normal 20 ms spacing. This is a deadline/cadence check, not cycle profiling.
The test uses an 8 MHz PAL STE, 4 MiB, German TOS 1.62. Fast-forward affects host
speed only; playback is still scheduled by emulated PAL VBL.

`analysis/war-audio.json` records an additional 80-second stereo WAV check of
the unmodified release PRG at 25 kHz, with no debugger operations during capture.
Hatari audio was set to 50066 Hz, sound synchronization enabled and a 60 ms SDL
buffer. `war-signal.json` analyzes the first continuous 70 seconds for long
constant nonzero stereo holds. These checks found no missed audio callbacks,
callback overruns, long held stereo values or host audio warnings. They do not
replace subjective listening or a test on physical STE hardware.
