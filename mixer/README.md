# AMIXER: volume, pan and 12.5/25 kHz

`MIXER.PRG` plays the included signed 8-bit `voice.raw` at 12.517 kHz through
GodLib's two-voice AMIXER. Keep `voice.raw` beside the executable. Output is
selectable 12.517 or 25.033 kHz signed 8-bit stereo (25 kHz by default).
Source sample rates are retained in both modes. A generated looping triangle
tone demonstrates the second voice.

- Space: replay the sample on voice 0.
- Up/down: voice 0 volume, 0..255.
- Left/right: voice 0 pan, 0..255.
- F1/F2/F3: left/centre/right.
- F4: switch output between 12.5 and 25 kHz, restarting the sample and active tone.
- 2: toggle the second voice (fixed volume/pan).
- Esc: exit.

```sh
make
make run       # STE, 1 MiB, German TOS 1.62
make check     # Native 68000 PCM regression and live DMA checks in Hatari
```

The mixer now adds scaled signed amplitudes with saturation to -128..127.
It no longer ORs/interleaves source samples. Linear pan at centre divides a
voice approximately equally between speakers; volume 255 is unity at either
hard-panned endpoint. Constant-power and historical pan-law tables remain
selectable through `AudioMixer_SetConfig()`.

```c
AudioMixer_Init();
AudioMixer_SetFrequency(eAUDIO_FREQ_12); /* or eAUDIO_FREQ_25 */
AudioMixer_Enable();
AudioMixer_PlayVoice(0, &sound, 192, eAMIXER_PAN_CENTRE);
AudioMixer_SetVoiceParams(0, 128, eAMIXER_PAN_RIGHT);
AudioMixer_IsVoicePlaying(0);
AudioMixer_StopVoice(0);
AudioMixer_DeInit();
```

Explicit voice numbers are 0 and 1. `PlayVoice()` returns 1 on success and
replaces that voice. `PlaySample()` and `PlaySampleDirect()` retain their old
signatures and use volume 255; Direct steals the voice nearest its end.
The descriptor's `mLoopingFlag` repeats the complete source sample.

Supported sources: **signed 8-bit mono**, 6258/12517/25033 Hz, nonempty byte
length (including odd lengths and odd addresses). 16-bit/stereo sources and
50066 Hz input are rejected. Slower sources are repeated (6.25 -> 12.5 kHz:
2x; 6.25/12.5 -> 25 kHz: 4x/2x). At 12.5 kHz output, 25 kHz sources select
every second byte. This is nearest-neighbour conversion without a low-pass
filter, so downsampling can alias. Odd-length loops retain their decimation
phase across wraps, including one-byte loops. There is no arbitrary-frequency
resampler.

`AudioMixer_SetFrequency(eAUDIO_FREQ_12/eAUDIO_FREQ_25)` returns 1 for a valid
output rate. `AudioMixer_GetFrequency()` returns the current enum. Call after
Init; the default is 25 kHz. A **real rate change stops both source voices and
clears queued audio**, preserving whether DMA was enabled or disabled. Replay
sources explicitly after switching (as F4 does here). Setting the same rate is
a no-op; invalid enums return 0 without touching playback. Configuration changes
through SetConfig also reset sources if the mixer was enabled. Output remains
8-bit stereo. The low-rate mode generates half as many output samples; no
25 kHz intermediary buffer is built.

The core now separates one-voice lookup/copy, two-voice mixing without clipping,
and per-byte overflow saturation. Each double-buffered gain bank contains 256
native stereo words plus 256 words with the right lane biased by 128.
**Tables total 4 KiB**; the old 512-byte clip table is gone. The DMA ring remains
8 KiB and silence scratch remains 4 KiB.

For summed L/R gains <=256, truncated signed PCM cannot clip. That path adds
packed words with an explicit right-to-left byte-carry correction; higher gains
use independent saturating ADD.B operations. Native loops are unrolled. There
are no gain multiplies or 32-bit span multiplies in the steady mixer. Unchanged
volume/pan/law tables are reused. Once a full silent ring revolution is zero,
idle refill skips redundant stores; new Play invalidates that state.

Controls remain non-reentrant main-thread/supervisor APIs. Stop and parameter
changes leave about 41 ms queued (1024 bytes at 12.5 kHz, 2048 at 25 kHz).
StopAll flushes it. The mixer owns DMA exclusively.

## Measured CPU cost

Hatari-HRDB, STE 68000 / 8 MHz / PAL / 1 MiB / German TOS 1.62. Includes the
actual VBL callback, C span controller, ASM and shared zero-fill/math helpers;
excludes common IRQ dispatch, Init/Play/gain preparation, graphics and IO.
Parameters stay constant during each approximately three-second run. Actual
callback counts and 160256 cycles per PAL VBL normalize the percentages; the
whole capture is checked against this budget.

| Output / active voices | Before | Optimized |
| --- | ---: | ---: |
| 12.5 kHz / 0 | 1.66% | 0.56% |
| 12.5 kHz / 1 | 24.14% | 7.72% |
| 12.5 kHz / 2 | 24.54% | 17.05% |
| 25 kHz / 0 | 2.49% | 0.57% |
| 25 kHz / 1 | 46.73% | 13.88% |
| 25 kHz / 2 | 47.16% | 32.15% |

Two-voice rows use volume 220/190, pan 32/224 (no clipping). At both volume 255
hard-left, measured cost remains about 24.6% / 46.7% at 12.5 / 25 kHz. Saturation
is therefore not promised to improve; cost depends on gains and input signal.
Two 12.5 kHz sources at 25 kHz output improve from 63.38% to 50.17%; two 25 kHz
sources at 12.5 kHz output improve from 35.79% to 20.49%.

One voice uses about 68–70% fewer cycles; two without clipping use about 31–32%
fewer. Tables shrink by 512 bytes, but code grows. Identical benchmark text,
data and BSS together increase by 404 bytes: a small code-RAM trade for CPU.

Baseline sources are frozen in `analysis/baseline/`, and build separately:

```sh
bash analysis/build-bench.sh baseline
bash analysis/build-bench.sh
python3 analysis/profile.py --baseline
python3 analysis/profile.py
```

`profile-before.json` and `profile.json` in `analysis/` contain binary/source
hashes, component cycles and ten cases (idle, voices, resampling, clipping).
The profiler uses private TCP port 56129. Results are emulator averages, not
physical STE worst-case bounds.

`analysis/check.c` compiles the production C implementation with its internal
refill function accessible; the same production ASM is linked from libgod.
`analysis/verify.py` independently checks output against arithmetic in Python,
then exercises actual DMA/VBL playback, ring wraps and reinitialization.
Other PCM mixers are unchanged.

Native STE verification covers 105 gain/pan/law combinations (all 256 signed
input values), eight additional low-rate cases and 586,240 exact PCM
bytes, including all 65,536 input pairs for each L/R saturation and safe packed
path (262,144 pairs total). It checks short/odd sources, clipping, source loops, rate expansion and
decimation, live controls, invalid inputs and legacy slot stealing. Another
16,384 bytes are checked after actual DMA ring wraps at both output rates,
including live 25 -> 12.5 -> 25 kHz changes, queue resets, one-shot completion,
reinitialization and shutdown. Results are in `analysis/verification.json`.

`analysis/verify-ui.py` exercises the release executable with real keyboard
events, compares both complete display pages before/after controls and both F4
switches (eight page checks), verifies the DMA rate register and return to TOS.
Results are in `analysis/ui-verification.json`. These are functional checks,
independent of the cycle benchmark above, and do not replace physical listening.
