# LanceMod channel activity

Build with `make` and run `LANCEMOD.TOS` beside `LOSTPARO.MOD` on an
Atari STE/MegaSTE. Playback uses the 25 kHz Paula backend.

Exactly four indicators follow Amiga stereo panning: CH1/CH4 on the left and
CH2/CH3 on the right. Each channel is drawn once. They use the original
16 × 150, four-plane VU graphics and palette from James Boulton's
**ST Format Demo V1.0, (C) 1993 James Boulton**:
`Atari_ST_Sources/ASM/Various/James Boulton/STF_DEMO/{VU,PALETTE}.DAT`.
The source demo reads three PSG volume registers; this adaptation displays four
MOD channels using LanceMod's existing `mt_Visualizer` counters.

These are **activity indicators, not amplitude meters**. A retrigger produces a
large bar, which shrinks over the next 16 replay calls (about 320 ms at 50 Hz).
The replay's original trigger filtering is retained. A silent/idle channel has
no bar; a blank state was added before the 16 original graphical states.

- **F1**: toggle the existing replay CPU raster indicator.
- **V**: hide/show activity bars without stopping music.
- **Space / Esc**: stop playback and return to TOS.

`LanceMod_GetVisualizer(ages)` returns a coherent snapshot of four `U16` ages in
channel order. Ages saturate at `dLANCEMOD_VISUALIZER_IDLE` (`0x4000`); stopped
playback returns that value for every channel. Call from supervisor mode, like
the replay API. The getter does not reset counters or otherwise change playback.
The sample maps ages 0..15 to levels 16..1 and all older ages to zero.

`visual_s.s` renders the original graphics in ASM. Each screen page remembers its
own four levels. Unchanged bars cost no pixel writes; a precomputed table selects
the smallest vertical span covering the difference between old and new frames.
Each changed row writes one 16-pixel bar. The background is
copied only during initialization.

`assets/STF_VU.DAT` and `assets/PALETTE.BIN` preserve the original artwork.
`prepare.py` derives the 17 graphical states, transition table, preview and source
hashes. The shipped originals allow regeneration without the source collection;
Pillow is needed only for this asset preparation, not a normal build.

For target verification, run `make debug` and
`python3 analysis/verify-hatari.py`. The script uses the Hatari skill helper,
checks entire rendered framebuffers against the original artwork on both pages,
observes all four channels during actual MOD playback, and exercises hide/show,
the CPU indicator and exit. ROMs and the helper are local development dependencies.
Results are saved in `analysis/results.json`.

Validation: STE, 8 MHz, 1 MiB: TOS 2.06 and German TOS 1.62 pass rendering,
controls and exit with the original `LANCEMOD.TOS` filename. German 1.62 passed
60 complete framebuffer comparisons, covering both pages and all four channels.
British TOS 1.62 Rev 2 (GB) fails on exit with `LANCEMOD.TOS`, including the
original console-only example, but the identical binary renamed `LM.TOS` exits
cleanly on both GB and German ROMs. See `analysis/exit-1.62.md`.
Run `python3 analysis/verify-hatari.py 1.62-de` for the German ROM, and
`python3 analysis/verify-tos-names.py` for the short-name comparison.

The replay now allocates its tables/code/DMA workspace for the selected frequency;
module loading adds guards only for nonempty samples. Shutdown frees the complete
workspace. See `godlib/music/lancemod.md` for memory accounting and the PCM/guard
test matrix, including `BOOTUP.MOD` and `CANNONFO.MOD`.

`python3 analysis/verify-live-mods.py` runs the three supplied modules through the
normal 25 kHz VBL/DMA example, using temporary filename aliases so the source
assets are unchanged. All three passed on STE / 8 MHz / 1 MiB / German TOS 1.62:
activity advances, no missed VBLs, clean exit and DMA stopped. Results are in
`analysis/live-memory-results.json`.

Oscilloscope mode: **O** cycles bars → four traces → ICE stereo XY; **V** hides/shows the selected
visualizer. The four 64-point traces use current channel sample position,
pitch and volume, drawn in ASM with independent history for both screen pages.
They are read-only source previews, not extracted stereo DMA channels. The
Leonard variant also works at 12.5 kHz. See
[shared oscilloscope API and verification](../../godlib/music/modscope.md).

The third mode contains two ICE/Techwave `MODOSC.S` XY plots, using actual native
stereo PCM with a 64-frame delay, 100 points per side and ASM OR plotting.
V hides/shows any selected mode. Its source attribution, algorithm and tests are
in the [shared scope documentation](../../godlib/music/modscope.md#ice-delayed-stereo-xy-plots).

Two additional time-domain modes are available: **separate L/R** and a
**single mono trace**, averaging signed PCM as `(L + R) / 2`. O cycles bars →
four channel traces → ICE XY → stereo L/R → mono. V hides/shows the selected
mode. Each trace has 128 points from native PCM; stereo uses green/cyan and
mono uses white. Drawing and averaging are ASM and reuse existing PCM/history
buffers. Audio playback stays stereo. These modes are included in the shared
`lancemod/analysis/verify-scopes.py` full-frame tests.
