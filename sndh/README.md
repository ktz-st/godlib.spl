# SNDH — PSG visualizers

Standalone GodLib ST/STE example, 320×200, PAL 50 Hz. Plays the included
`popcorn.snd` ("Popcorn", mOdmate, 1996; SNDH conversion: Grazey).
The tune was supplied locally for this example.

## Build and controls

```sh
make
make run
```

Keep `popcorn.snd` beside `SNDH.TOS`. The shipped assets allow ordinary builds
without Python. `make assets` regenerates the note lookup, eight-pixel VU phase, keyboard masks,
scope phase increments, compiled circle kernels and colour-organ discs/palettes; `make debug` produces `build/SNDBG.PRG` with symbols.

- **O**: cycle through **VU → 80 note bands → piano → three synthetic scopes → rings → colour organ**.
- **V**: hide/show the selected visualization.
- **F1**: toggle the replay timing stripe (elapsed replay duration, not a numeric CPU meter).
- **Space / Esc**: stop playback and return to TOS.

This example accepts unpacked SNDH using the **TC** tag at 1–200 Hz. It uses
GodLib `Snd_GetInfo`, `Snd_TuneInit` and the existing Timer C scheduler; it does
not install another timer owner. Replay stops before tune memory is unloaded.
The supplied tune uses TC50. Timer A/B/D and VBL-tagged files need a matching
scheduler before being added to this example.

## Three VU bars

James Boulton's **STF_DEMO**, (C) 1993, supplies the 16×150 four-plane artwork.
Original source:
`Atari_ST_Sources/ASM/Various/James Boulton/STF_DEMO/STF_DEMO.S:238`.
The artwork and transition tables are the same as in the local LanceMod sample;
source hashes are in `assets/stf-source.json`.

The three bars represent PSG A/B/C. They are **16 px wide with 16 px gaps**,
centered at X=120/152/184, from Y=32. They are not duplicated at the screen edges.
Each page keeps its previous heights. ASM copies only changed rows from the
selected prepared frame. The eight-pixel horizontal phase uses `MOVEP.L` to
preserve the neighbouring half-words and the gaps.

Registers 8–10 select the graphical levels. Fixed-volume zero is blank;
nonzero values 1–15 select source-artwork states 1–15. Hardware-envelope mode
selects the full-scale state, matching STF_DEMO's clamp to 16. **ENV is an
activity indication, not the current envelope amplitude**, which these registers
do not expose. Channels with both tone and noise disabled show zero.

## 80 mirrored note bands

The algorithm follows **ADR NORTH** / Mac Sys Data's analyser:
`Atari_ST_Sources/ASM/Adrenalin U.K (ADR)/NORTH/MENU.S:653`, also present in POV93.

The 12-bit tone periods in R0–R5 map to 80 chromatic bands, C1–G7. A sounding
tone triggers height 12. Each frame subtracts one from nonzero heights, giving
trails after note changes. Noise-only channels do not trigger pitch bands.
Multiple channels hitting the same band share its peak.

Each band is 3 px wide with a 1 px gap, filling 320 px. ASM draws symmetrically
above and below the axis at the screen center between Y=99/100. Per-page delta drawing touches only
rows whose height changed and keeps the other bands in the same planar word.

The original NORTH lookup was prepared for a specific tune. `prepare.py`
generates a **general 4096-byte lookup** for a 2 MHz YM clock, using nearest
semitones and clamping the range endpoints. This is note activity, not FFT.

## Piano keyboard

An 80-note keyboard covers C1–G7, centered at X=19..300, Y=72..135.
Sounding tones illuminate their keys: A red, B green, C blue. Channels sharing
a note combine their colour bits (yellow, magenta, cyan or white). Noise-only
channels do not light keys. The same period-to-note table drives the piano and
note bands; out-of-range tones clamp to the nearest endpoint.

ASM updates only keys whose channel masks changed on the current display page.
Prepared word masks preserve the keyboard outlines and black-key overlaps.
Unlit keys restore their original artwork; the whole screen is not redrawn.

## Three synthetic oscilloscopes

A/B/C have separate red, green and blue square-wave traces, 256 pixels wide,
centered at Y=64/104/144. The displayed time window is **10.24 ms**, using
25 kHz synthetic sample positions and the PSG tone frequency `2000000/(16*period)`.
Each trace starts at a fixed phase, so a held note stays readable.

These are **synthesized from registers, not recorded audio**: volume sets a
linear graphical amplitude, envelope mode uses maximum activity, and noise-only
or muted channels show a flat line. They do not reconstruct the noise generator,
hardware envelope, SID/digi effects or the YM's nonlinear volume curve.

ASM compares phase-step/amplitude pairs with the current page's history and
skips unchanged traces. It computes horizontal runs directly: one division per
trace obtains the half-cycle quotient/remainder, then remainder carries locate
successive edges. Unrolled vertical spans and masked horizontal words XOR the
old/new waveforms. Reverse phase preserves the original sampled positions even
above Nyquist. There are no 256-sample buffers or per-pixel scans.

## Expanding rings on note changes

Each channel has its own colour and origin: A at (80,100), B at (160,100),
C at (240,100). A new sounding note triggers an expanding outline circle.
A held note does not retrigger; silence followed by the same note does.
Changes in volume alone do not trigger rings. Noise-only channels are excluded.

There are four ring slots per channel. A fifth trigger reuses the oldest slot.
Radii grow from 2 to 48 pixels over 24 frames (0.48 seconds at 50 Hz), then vanish.
Offline midpoint-circle masks generate native 68000 kernels (`assets/RINGS.S`).
The normal two-frame page revisit uses a fused old/new XOR delta; retriggers,
expiry and arbitrary jumps use standalone erase/draw kernels. Common word masks
stay in registers. Each page keeps its own previous ages. Intersections combine channel
colours; overlapping outlines within one channel use XOR.
Animation state advances once per rendered frame, including while another mode
is selected or the visualization is hidden.

## RGB colour organ

The sixth mode shows three stationary filled discs, radius 28, centered at
(80,100), (160,100), (240,100). A is red, B green, C blue. Each disc occupies
one separate plane/palette entry (1, 2, 4). The static mono stamp is drawn in
ASM only when entering the mode and copied to both display pages once.

Every subsequent frame, `PsgOrgan_Update` writes only those **three palette
words**. Fixed PSG volume 0..15 selects the corresponding brightness; envelope
mode shows maximum activity, as with the VU bars. Mixer/noise gating follows
the same existing channel activity values. STE uses all 16 intensity steps;
ST hardware quantizes these to its eight intensities. These are register-based
activity lights, not measured audio peaks or instantaneous envelope amplitude.

The **V** key blacks/restores the three lamp colours without clearing/copying
VRAM. Labels and instructions have separate palette entries and stay readable.
Changing mode restores that mode's full palette normally. No raster interrupt
or per-frame circle drawing is involved. Palette updates cost about **0.09% CPU**
on the tested 8 MHz STE; shared PSG/animation processing brings the visualization
subtotal to **4.57%**, with music measured separately.

## Replay integration

`PsgVis_Snapshot` runs immediately after the SND replay via its chaser callback.
It briefly masks interrupts and reads R0–R10, without writing PSG sound data.
`PsgVis_Update` takes a coherent RAM copy and updates levels in ASM; all
six visualizations run in the main loop on the logical page. Mode/visibility changes
restore each page from Back once. Normal frames do not copy the whole screen.

The supplied Popcorn tune was verified against a build without the snapshot.
This is not a guarantee for every SNDH: players whose timer routines depend on
the PSG address latch require a dedicated capture path.

## Verification and CPU

Measured on Hatari-hrdb, STE 68000 / 8 MHz / 1 MiB, RGB PAL, German TOS 1.62,
playing `popcorn.snd`. See `CPU.md` and `cpu-profile.json` for cycle results.

Native verification compares complete 32000-byte planar frames with independent
references on both pages. Targeted optimization sweeps cover 60 scope frames and
84 ring frames, including extreme/random tone periods, volume/mixer states,
reverse phase, all ring ages, overlapping rings and arbitrary frame jumps.
O/V mode and visibility switching and clean TOS exit are exercised.

Current optimized averages are about **15.8% CPU for scopes and 19.3% for rings**,
plus about 4.8% for playback, on the profiled Popcorn passages. The expanded ring
kernels trade approximately **19 KiB extra resident memory** for speed; scope
sample/history buffers shrink from 2304 to 36 bytes. See `CPU.md` for full
before/after measurements and limitations.
