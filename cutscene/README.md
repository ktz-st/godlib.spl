# Moonlit Passage — native GodLib cutscene with narration

`CUTSCENE.PRG` plays two scenes with castle/forest backgrounds, a moving twinkle,
four captions, palette fades and **four spoken lines** driven by the actual
GodLib text parser and cutscene runtime. On STE, AMIXER plays signed 8-bit mono
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

Edit `scene.txt` and run `make`. `CutScene_Parse()` parses it once at startup;
`CutScene_System_Update()` and `CutScene_System_Render()` run each display
update. `MAIN` calls `CASTLE_SCENE` and `FOREST_SCENE`. The native parser appends
`RETURN` at each script's closing brace.

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
already contain pointers and must not be relocated again.

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

TEXT_ANIM_SET/WAIT still do not implement a typewriter animation. They are not
used by this example. Original format documentation is
`../../godlib/docs/cutscene.txt`; the old TOOLBASE CUTBUILD host tool remains
unavailable in the local Python subset, so this example uses the native parser.

## Verification

```sh
make check
```

`analysis/verify.py` runs the real parser/player at 8 MHz / 1 MiB on STE with
German TOS 1.62 and plain ST with UK TOS 2.06 (1.62 is STE-only). It checks full
32000-byte frames against an independent background/twinkle/caption compositor,
both pages, all captions/animation frames, narration activity, natural finish,
and real-key skip/replay/restart/exit. Results/hashes: `analysis/verification.json`.

`analysis/verify-runtime.py` additionally tests both background pages without
callbacks/manual copies, repeated Render, multiline/tab/wrapped text, live page
replacement, long tokens, missing/empty/recursive scripts, the VAR parser,
two overlapping samples, volume/pan, loops, stealing, disable, wait including
the DMA tail, and clearing nonzero queued audio on Stop. It compares eight full
frames with an independent text compositor. Results: `analysis/runtime-verification.json`.
