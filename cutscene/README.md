# Moonlit Passage — compiled GodLib cutscene with narration

`CUTSCENE.PRG` plays two scenes with castle/forest backgrounds, a moving twinkle,
four captions revealed letter by letter, palette fades and **four spoken lines**
driven by the actual
GodLib cutscene runtime and a host-compiled `.CUT` asset. On STE, AMIXER plays signed 8-bit mono
samples through **12.517 kHz stereo DMA**. On plain ST the same scene runs
silently; sample waits do not hang when DMA playback is unavailable.

```sh
make
make run                    # STE, 1 MiB, RGB PAL, German TOS 1.62
```

- Space: skip to the end; on the end screen, replay.
- R: restart from the first scene.
- Esc: stop the scene/audio and return to TOS.

Everything is embedded in the PRG; no separate files are needed to run it.

## Script and audio

Edit `scene.txt` and run `make`. Host CUTBUILD compiles it to `assets/SCENE.CUT`;
the program relocates that embedded file once at startup.
`CutScene_System_Update()` and `CutScene_System_Render()` run each display
update. `MAIN` calls `CASTLE_SCENE` and `FOREST_SCENE`. CUTBUILD appends
`RETURN 0` at each script's closing brace, matching the native parser.

The script demonstrates ASSET, ANIMATION, SPRITE, PAGE, TEXT, SAMPLE, CALL,
background changes, fades, sprite movement/animation waits, timed pauses and
callbacks. The two `CALLBACK 0` commands merely yield control to the application
(result 2); they no longer synchronize or manually copy backgrounds.

```text
<SAMPLE NAME="SAY_ARRIVAL">
{
 ASSET = "VOICE_ARRIVAL"
 VOLUME = 255
 STEROPOS = 128
 FLAG_LOOP = 0
}

SAMPLE_ENABLE SAY_ARRIVAL
# ... movement, captions and other timed actions ...
SAMPLE_WAIT SAY_ARRIVAL
```

`SAMPLE_ENABLE` starts/restarts the named sample, applying its volume, pan and
loop flag. The application initializes AMIXER explicitly before starting a scene:

```c
AudioMixer_Init();
AudioMixer_SetFrequency(eAUDIO_FREQ_12); /* eAUDIO_FREQ_25 also works */
AudioMixer_Enable();
CutScene_System_AppInit();
CutScene_System_ScriptInit(scene, "MAIN");
```

AMIXER's **two voices are reserved exclusively for the cutscene** while it uses
samples. A third simultaneous sample steals the next voice in round-robin order;
a wait on a stolen sample completes. `SAMPLE_DISABLE` stops that named source;
previously mixed audio can remain queued for about 41 ms. `SAMPLE_WAIT` waits for
a one-shot source and an additional three VBLs for that queued tail. A looping
sample keeps waiting until disabled/stolen/stopped. Failed/unavailable playback
does not block the script.

`CutScene_System_Stop()` stops the script and discards its queued audio; call it
before skipping, unloading assets or switching players. ScriptInit, AppInit,
AppDeInit and natural root return also stop cutscene audio. The application
still owns AMIXER Init/DeInit and must keep all sample memory valid until stopped.
The example stops audio before releasing assets, and has no disk IO during play.

`BindAssets()` binds script names to native embedded objects. Each RAW asset is
wrapped in a native `sAudioDmaSound`; the script's FLAG_LOOP overrides the sound
descriptor's loop flag. An asset loaded from .SPL instead must be relocated by
the usual audio asset relocator. Native font/sprite objects and the parsed scene
already contain pointers and must not be relocated again. The example now embeds a writable precompiled `.CUT`, relocates it once and
does not free that embedded storage. Parser code and temporary parser allocations
are no longer needed in the release program.

## Narrator and asset generation

The four lines come directly from PAGE text. `voices.py` uses the installed
**macOS Daniel (en_GB)** speech voice at 145 words/minute, then ffmpeg and an
offline converter produce signed mono PCM at 12517 Hz. Peaks are normalized to
124, with short boundary ramps. The four RAW samples total **119009 bytes**
(about 9.5 seconds of speech). `assets/voices.json` records text, duration and
hashes. Normal builds use these prepared assets and need no speech service.

```sh
make voices                 # Regenerate narration on macOS (say + ffmpeg)
make assets                 # Regenerate images/font/twinkle
make
```

`assets/narration.wav` is a listening preview of all four lines at the target
sample quality, before AMIXER gain/pan. Individual WAV previews are also supplied.
AIFF/16-bit intermediate files are temporary and are not runtime assets.

`prepare.py` reuses the castle from `water`, forest from `wipe`, FONT6X6.PI1
from `font`, and twinkles from `spritemask`. Background conversion uses
**ABC2 / STE RGB444 / no dithering** and a black footer from row 168. Existing
GodLib 8x8 text supplies static labels; the cutscene draws captions with the
sprite-based 6x6 font. Drawing uses GodLib's ASM/blitter APIs.

## Library fixes exercised here

- BG_GFX_SET/CLEAR update clean Back once and both display pages by dirty bitmask.
  The script waits for both pages before proceeding, preventing early palette
  fades from exposing a stale page. No application background-copy workaround.
- Text consumes CR/LF/CRLF/tabs, bounds word buffers, clips to its rectangle and
  wraps against X + WIDTH. The example passes PAGE strings through unchanged.
- TEXT_PAGE_SET/FONT_SET refresh both pages while text remains enabled. Dirty
  flags track actual pages, so repeated Render calls on one page cannot consume
  work for the other. Sprite damage requests redraw of overlapping captions.
- ScriptInit resets sprite/text definitions, enable flags, dirty rectangles,
  animation start frame, stack and waits. The example has no manual flag reset.
- Stop/no-script/empty/missing-script cases finish safely. Natural return and
  call-stack/instruction limits prevent old hangs/stack overwrites.
- The VAR parser member table now has its missing terminator.

The example reveals captions with `TEXT_ANIM_SET CAPTION,2` (about 25 source
bytes/s at 50 updates/s), then `TEXT_ANIM_WAIT CAPTION` before the narration
wait. `0` selects immediate text. Whole-word measurement keeps wrapping stable;
page changes and disable/re-enable restart the reveal. The wait includes the final
redraw on both pages. Empty, missing and disabled text cannot hang it. Existing
runtime fields store progress, so the serialized `.CUT` layout is unchanged.

BG_GFX_DISABLE clears the background while retaining the selected asset and
allowing sprites/captions to continue. Setting an asset while hidden keeps it
hidden; BG_GFX_ENABLE restores the latest selection. Both toggles wait for both
pages; repeating the current state is a no-op.

`make` compiles `scene.txt` into `assets/SCENE.CUT` with the local host compiler:

```sh
python3 ../../godlib/tools/cutbuild/cutbuild.py scene.txt assets/SCENE.CUT
```

Original format documentation is `../../godlib/docs/cutscene.txt`; compiler usage,
validation and original TOOLBASE compatibility evidence are in
`../../godlib/tools/cutbuild/README.md`. CutScene_Parse remains covered by the
runtime regression harness, but is not linked into the release PRG. Switching
from runtime parsing reduced this build from 325125 to 301592 bytes (23533 bytes).

## Verification

```sh
make check
```

`analysis/verify.py` runs the compiled CUT/player at 8 MHz / 1 MiB on STE with
German TOS 1.62 and plain ST with UK TOS 2.06 (1.62 is STE-only). It checks full
32000-byte frames against an independent background/twinkle/caption compositor,
both pages, partial and complete captions/animation frames, narration activity, natural finish,
and real-key skip/replay/restart/exit. Results/hashes: `analysis/verification.json`.

`analysis/verify-runtime.py` additionally tests both background pages without
callbacks/manual copies, repeated Render, multiline/tab/wrapped text, live page
replacement, long tokens, missing/empty/recursive scripts, the VAR parser,
two overlapping samples, volume/pan, loops, stealing, disable, wait including
the DMA tail, and clearing nonzero queued audio on Stop. It additionally covers
background enable/disable and hidden selection changes, typewriter timing, stable
wrapping, page replacement, immediate mode and final-page waits. It compares 28
full frames with an independent text compositor. Results: `analysis/runtime-verification.json`.
