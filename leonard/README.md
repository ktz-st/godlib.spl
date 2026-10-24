# Leonard: four ProTracker channel indicators

This example uses the public `godlib/music/leonardmod.h` API, 8-bit stereo on
STE/MegaSTE. The replay core, loader and memory management live in `libgod.a`.

```sh
make                                      # LEONARD.PRG, 25 kHz
make RATE=12 OUT=LEO12.PRG                 # LEO12.PRG, 12.5 kHz
```

Both programs use `LOSTPARO.MOD`, copied from `../lancemod`. Keep the MOD next to
the executable. `RATE` accepts 12 or 25; the two rates use separate C object files.
The ST-RAM workspace is **61134 B at 12.5K**, **91134 B at 25K**, and is freed on
exit. The original native engine reserved 194384 bytes. Loading a MOD adds only
its real patterns and sample bytes, without duplicate loop data. See
[LeonardMod](../../godlib/music/leonardmod.md) for accounting and API ownership.

There are exactly **four** indicators: **CH1 / CH4 on the left**, **CH2 / CH3 on
the right**, matching Amiga LRRL panning. Each channel has one bar. The drawing
code and original James Boulton STF_DEMO graphics are shared with `lancemod`.
`mt_Visualizer` reports retrigger ages, not waveform amplitude. Ages 0..15 map to
levels 16..1; older ages show an empty bar.

- F1: colour palette entry zero during the replay call (elapsed replay stripe).
- V: hide/show bars while replay continues.
- Space / Esc: stop and return to TOS.

Audio now runs in a PAL **VBL callback**, independently of the rendering loop,
following `ugh.agt`'s service. The existing `LeonardMod_Tick()` bridge preserves
the interrupted caller's USP, SR and registers across the native user-mode
mixing/trap sequence. The earlier note forbidding VBL use was incorrect.
The foreground performs Screen_Update, input, scope sampling and drawing;
it does not call Tick a second time.

Start itself still does not register a callback. The example checks registration
and protects add/remove with an interrupt mask. It removes its audio callback
before `LeonardMod_ShutdownPaula()` stops DMA/restores trap #0 and frees the
workspace, then unloads the MOD. Remove a caller-owned callback before any
restart/Stop/Shutdown too; the native mixer is not reentrant.

Start prepares writable samples in place, so load a fresh raw MOD before
starting it again. All per-song tracker channel/effect state is reset on init.
Empty sample slots use shared silence. The 12.5K mode keeps high notes in tune
with a looped fallback for source steps above one and short-loop overshoot.

The source notices/hashes are in `../../godlib/music/leonard-source.json`.
UGH uses Leonard + **TFMX**; this example uses Leonard + **ProTracker** and its
`mt_Visualizer`. They are different replay frontends.

Oscilloscope mode: **O** cycles bars → four traces → ICE stereo XY → stereo L/R → mono → five DCK bar styles; **V** hides/shows the selected
visualizer. The four 64-point traces use current channel sample position,
pitch and volume, drawn in ASM with independent history for both screen pages.
They are read-only source previews, not extracted stereo DMA channels. The
Leonard variant also works at 12.5 kHz. See
[shared oscilloscope API](../../godlib/music/modscope.md).

The third mode contains two ICE/Techwave `MODOSC.S` XY plots, using actual native
stereo PCM with a 64-frame delay, 100 points per side and ASM OR plotting.
V hides/shows any selected mode. Its source attribution and algorithm are
in the [shared scope documentation](../../godlib/music/modscope.md#ice-delayed-stereo-xy-plots).

Two additional time-domain modes are available: **separate L/R** and a
**single mono trace**, averaging signed PCM as `(L + R) / 2`. O cycles bars →
four channel traces → ICE XY → stereo L/R → mono → five DCK styles. V hides/shows the selected
mode. Each trace has 128 points from native PCM; stereo uses green/cyan and
mono uses white. Drawing and averaging are ASM and reuse existing PCM/history
buffers. Audio playback stays stereo.

## Verification

`make check` builds and tests both release rates and an 18-check native VBL
regression. During 64 VBLs at each rate, the foreground deliberately performs
no rendering or Tick calls and holds `USP=0x12345678`. The test checks one audio
callback per VBL, restored USP/SR mask, changing/nonzero mixed PCM, then removal
of the callback, restored trap #0, stopped DMA and complete RAM recovery.
The sentinel test is a separate diagnostic PRG, not a control in the player.

The earlier release tests covered the original five visualizer modes, hide/show, raster indication,
non-silent stereo WAV captures and clean TOS exit. Audio counters continue in
all modes; no callbacks remain after shutdown. Evidence is in
`verification-vbl.json` and per-rate PNG captures. Tests use STE /
68000 / 8 MHz / 1 MiB / German TOS 1.62 / PAL. WAV checks verify active stereo,
not subjective sound quality; these tests are not CPU measurements.

## Five additional DCK bar styles

`O` now cycles through **ten modes**. After the original mono scope come
DCK narrow 32, narrow 64, wide 64, wide 128 and horizontal bars. `V` hides/shows
any of them. Each native channel has its own colour; labels L1/R2/R3/L4 retain
the MOD stereo assignment. They use the existing 0..16 retrigger-activity
levels, not measured audio amplitude or an additional replay hook.

One shared ASM renderer draws only changed rows/blocks on each display page,
reusing the existing four-word page history. Playback remains under its
existing VBL owner. No frame cache, new heap buffer or library API is added.

See [DCK styles, verification and CPU](../lancemod/DCK-VISUALIZERS.md).
