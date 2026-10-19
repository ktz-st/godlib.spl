# FE — scripted game menu

Native GodLib FE example: MAIN / OPTIONS pages, difficulty selection, volume,
CALL actions and palette fade transitions. The layout and links come from
[menu.txt](menu.txt), compiled offline by [host FEBUILD](../../godlib/tools/febuild/README.md)
into `assets/MENU.FED`. The program does not parse menu text at runtime.

## Controls

- Arrows up/down select a control; left/right change its value.
- Enter, Space or joystick 1 fire activates a control.
- Difficulty cycles EASY / MEDIUM / HARD, including wrap in either direction.
- Volume steps by 10 between 0 and 100; holding left/right repeats.
- TEST SOUND plays a short chime through AMIXER at the selected gain on STE.
  This is a real volume control for the test sound, not just a visual slider.
- BACK TO MAIN retains difficulty, volume and the selection of each page.
- START GAME triggers a native FE CALL; the application reports the chosen
  settings in the main heading. It deliberately stays in the menu: this sample
  does not contain a game.
- QUIT TO TOS or F10 exits.

Graphics target ST low resolution, 320x200 / four planes / double buffering.
DMA sound requires STE; the menu remains usable on ST without the chime.
The supplied run/test configuration is STE / 68000 / 8 MHz / 1 MiB / German
TOS 1.62. Arrows, labels and title are drawn by the GodLib FE renderer and
existing sprite/font graphics routines. Font assets use GodLib's built-in 8x8
shapes converted offline to fixed-width BFBs; backgrounds are simple offline
planar artwork, with no runtime C pixel rasterizer.

## Build

```sh
make
make run
make check
```

Output: **FE.PRG**, approximately 199 KiB, with FED, fonts, backgrounds, cursor
and the chime embedded; no companion files are required at runtime. `make`
recompiles MENU.FED when the script/compiler/schema changes. `make assets`
regenerates the other assets using Python's standard library, then `make`
reassembles/relinks them.

## Integration

1. Relocate FED, BFB and BSB assets before use. The example first verifies that
   FED relocation/delocation returns the original bytes, then relocates for use.
2. Initialize the hash tree and publish three S32 variables: FE/DIFFICULTY,
   FE/VOLUME and FE/ACTION. Values <=4 bytes require an explicit initial write.
3. Create a static asset context before `Fed_Init()`. It registers native asset
   clients; this self-contained sample then binds embedded assets by filename.
   A packaged game can instead publish assets through its package/context system.
4. Initialize RenderFed, start MAIN and feed `sInput` into `Fed_Update()`.
   Seed the combined input from the keyboard every frame before adding the
   joystick; the legacy Input_Combine helper does not clear inactive keys.
5. Render once per frame with `RenderFed_Update(logic, back)`. FE owns the clean
   background buffer and handles two-buffer cursor/text restore and redraw.
6. Handle CALL results in the application. TEST SOUND maps 0..100 to AMIXER's
   0..255 gain; 70 becomes 178. No music player or raster interrupts are used.
7. Stop AMIXER, deinitialize FE clients, remove the context, clear variable
   bindings, and restore screen/platform state before returning to TOS.

Intro uses a 12-VBL fade to the destination page palette; outro fades to black
in 10 VBLs. Both are native FE transitions. Renderer completion now waits for
transition startup before accepting menu input. Wipes are not used here.

## Verification

`analysis/verify.py` drives actual IKBD keys in Hatari and checks exported state,
then saves `main.png`, `options.png`, `adjusted.png` and `start.png` plus
`verification.json`. It verifies page links/fades, list wrap, slider repeat and
clamps, chime gain, CALL handling, retained settings, repeated visits, no CPU
exceptions and exit to TOS. Teardown leaves zero variable bindings and zero
asset-context references. The chime's gain is checked programmatically; this
is not a recorded-audio comparison or a CPU profile.
