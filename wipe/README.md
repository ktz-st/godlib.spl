# Wipe slideshow

Three generated pixel-art scenes (coast, space and forest), converted to
320x200 Degas PI1 with individual 16-colour STE palettes.

```sh
make
make run
```

On Atari ST/STE, keep `WIPE.PRG`, `COAST.PI1`, `SPACE.PI1` and `FOREST.PI1`
in the same directory. No blitter is required. All pictures are preloaded.

- Space: next picture (queued if a transition is still running).
- P: pause/resume automatic slide changes. An active wipe still completes.
- Esc: exit to TOS.

The current picture holds for 200 VBLs (four seconds at 50 Hz). Then
`Wipe_Out_Init()` + `Wipe_Update()` erase it to black. Once that black frame
has been displayed, the sample installs the next picture's palette and uses
`Wipe_In_Init()` to reveal it. Each slide advances the effect index modulo
`dWIPE_FX_LIMIT`, so all 39 effects are used over time. Caption indices are
1..39; the API indices are 0..38. Wipe steps are paced at least two VBLs apart.

The wipe module owns one global animation state. Call `Wipe_Update()` once
per frame and poll `Wipe_IsFinished()`; do not use Wipe_Update's return value.
Wipe-out changes pixels in place. This sample keeps a canonical 32000-byte
transition buffer, renders the wipe into it, and copies it to the logical
screen before `Screen_Update()`. This avoids stale masks when screen buffers
alternate. Captions are drawn afterwards and stay readable during transitions.

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

For the STE smoke test:

```sh
make debug
python3 analysis/verify-hatari.py
```

The test uses the local hatari-debugging skill's session helper. It checks all
three completed planar pictures against their PI1 data, hardware palettes,
auto/manual advance, pause and clean exit. It does not exhaust all 39 effects.

## Artwork conversion update

Generated scene artwork now uses **ABC2, STE RGB444, without dithering**.
See the [shared artwork guide](../tools/ARTWORK.md) for reserved colours,
regeneration, shared copies and validation. Snowfall retains eight background
colours to leave its snow bitplane free. Older ST screenshots and CPU results
above refer to their original artwork revision.
