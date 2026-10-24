# Wipe slideshow

Three generated pixel-art scenes (coast, space and forest), converted to
320x200 Degas PI1 with individual 16-colour STE palettes.

```sh
make
make run
```

On Atari ST/STE, keep `WIPE.PRG`, `COAST.PI1`, `SPACE.PI1` and `FOREST.PI1`
in the same directory. All pictures are preloaded. The example enables the
BLiTTER wipe backend when hardware is available; plain ST falls back to CPU.

- Space: next picture (queued if a transition is still running).
- P: pause/resume automatic slide changes. An active wipe still completes.
- B: switch CPU / BLiTTER, including during an active wipe. On ST without a
  BLiTTER the getter and caption remain CPU.
- R: elapsed `Wipe_Update` border stripe; it excludes the presentation copy
  and captions and is not a numeric CPU measurement.
- Esc: exit to TOS.

The current picture holds for 200 VBLs (four seconds at 50 Hz). Then
`Wipe_Out_Init()` + `Wipe_Update()` erase it to black. Once that black frame
has been displayed, the sample installs the next picture's palette and uses
`Wipe_In_Init()` to reveal it. Each slide advances the effect index modulo
`dWIPE_FX_LIMIT`, so all 39 effects are used over time. Caption indices are
1..39; the API indices are 0..38. Wipe steps are paced at least two VBLs apart.

The wipe module owns one global animation state. Call `Wipe_Update()` once
per frame and poll `Wipe_IsFinished()`; do not use Wipe_Update's return value.
Wipe-out changes pixels in place. This sample uses **ScreenBack** as its
canonical transition buffer, renders every mask there and copies it to logic
with GodLib's CPU ASM copy before `Screen_Update()`. This avoids missed masks
when display pages alternate and removes the old extra 32000-byte array.
Captions are drawn afterwards. Both backends share the same presentation path.
Every final wipe-in mask is full, so an extra source copy at completion is
unnecessary. The original scene files and 39 mask sequences remain unchanged.

Every palette reserves index 0 for black and index 15 for white captions.
Palettes are swapped after the black frame reaches the physical screen, so
colours in the old picture do not change during its wipe-out.

`assets/` contains the generated original PNGs and the final STE PNG previews.
`prepare_assets.py` uses Pillow to resize, then ABC2 to select each picture's
16-colour STE RGB444 palette without dithering and export Atari bitplanes.
The script independently decodes the output and checks every pixel. Rebuild
assets with `make assets`; rebuild one explicitly with
`python3 prepare_assets.py coast`. The PI1 files are supplied ready to run.
Image generation used the built-in image tool; prompts are in `assets/PROMPTS.md`.

## Library backend API

After `Platform_Init()` / `System_Init()`:

```c
Wipe_SetBlitterEnable(1);              /* selects CPU when hardware is absent */
U16 actualBackend = Wipe_GetBlitterEnable();
Wipe_In_Init(effect, sourcePixels);
/* Once per displayed step: */
Wipe_Update(Screen_GetpBack());
/* Poll Wipe_IsFinished(); present Back and swap pages as above. */
```

`Wipe_SetBlitterEnable(0)` forces CPU. The library defaults to CPU for existing
callers; this setting is independent of `Graphic_SetBlitterEnable`. Switching
does not restart or rewind the animation. Wipe-in replaces the destination
with source AND the current mask. Wipe-out preserves its cumulative operation
`destination &= ~mask`, including destination content changed by the caller.

The BLiTTER uses one synchronous 320×200 HOG transfer, with a 16×16 halftone
repeated across all four planes. In uses HOP=3 / OP=3; out uses inverted
halftone, HOP=1 / OP=1, without source-memory fetches. Buffers must be even,
in ST RAM, fixed stride 160, at least 32000 bytes. The call returns after BUSY
clears. No additional runtime mask/frame allocation is needed.

The old raw `Wipe_Render_STE` entry remains internal to low-level integration;
its frame offset now correctly advances **32 bytes**, rather than 16. Normal
code should use the public init/update API. Invalid unsigned effect indices
are ignored, including `0x8000..0xffff`.

## Verification and profiling

```sh
make debug
make check
make profile
make debug-release
```

Tests use the local `hatari-debugging` helpers and German STE TOS 1.62.
Debug PRGs, symbol files and RAM dumps live under `/tmp`; no `analysis/`
directory is recreated. `make run` uses STE / 1 MiB and accepts a `TOS` override.
All **589 mask frames** are verified in both directions with CPU, BLiTTER and
per-step switching: **3534 guarded full-buffer comparisons**, with callee-saved
register checks, exact completion state and unchanged source. UI tests cover
all three pictures, palette swap after a displayed black frame, controls and
TOS exit. Actual stripped-PRG smoke tests cover STE and plain ST without BLiTTER.

See [CPU.md](CPU.md) for cycles, measurement scope, hashes and limitations.
BLiTTER HOG stalls are included in its cost. The example also pays for a full
presentation copy and text, so renderer-only percentages are not whole-program
utilization or a promise of 50 FPS. The existing 2-VBL pacing is retained.

## Artwork conversion update

Generated scene artwork now uses **ABC2, STE RGB444, without dithering**.
See the [shared artwork guide](../tools/ARTWORK.md) for reserved colours,
regeneration, shared copies and validation. Snowfall retains eight background
colours to leave its snow bitplane free. Older ST screenshots and CPU results
above refer to their original artwork revision.
