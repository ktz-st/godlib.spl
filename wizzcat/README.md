# Wizzcat: four channel activity bars

Build with `make`, then run **WIZZCAT.TOS** next to **QUICKIE.MOD** on STE/MegaSTE.
The native source mixer is 25 kHz; stereo DMA runs at 50 kHz and interleaves
channels. This is GodLib's Metal Ages/Wizzcat source, not the stlibs4gcc binary.

Four bars show retrigger activity: CH1/CH4 left, CH2/CH3 right. They use the same
James Boulton STF_DEMO artwork and ASM renderer as Lance/Leonard. Each logical
screen has its own dirty-row cache; the background is only copied during setup.
These are activity ages, not amplitude meters.

- V: hide/show bars.
- F1: replay elapsed-time stripe through palette entry zero, saved/restored.
- 1/2: jump to first/last song position.
- Space/Esc: stop and exit.

QUICKIE's persistent module heap allocation is now **42478 B** instead of
**154409 B**. Its automatic extra workspace is 19140 B instead of the fixed
128 KiB. Preparation uses a transient 18148-byte scratch copy, freed before
playback. Static replay code/tables/DMA pages are separate from these figures.

The application uses `Platform_Init`, `Screen_Init` and `Wizzcat_Start`; playback
runs in GodLib's VBL queue. Stop removes the callback before module/screens are
freed. Reload raw MOD data before a second Init/Start because preparation is in
place. Only one DMA player may own the hardware at a time.

See [Wizzcat memory and lifecycle](../../godlib/music/wizzcat.md) for API details,
limits, initialization timings and baseline tests.

```sh
make debug
python3 analysis/verify-hatari.py
```

The native verifier defaults to German TOS 1.62 / STE / 8 MHz / 1 MiB. It compares
complete screen pages against the original artwork, checks all four channels,
both buffers, V/F1 controls, nonzero DMA PCM and clean exit.

Verified: 60 complete framebuffer comparisons, both pages/all channels, controls
and clean exit on German TOS 1.62.

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
