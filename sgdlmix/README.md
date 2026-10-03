# SGDL four-channel mixer example

```sh
make -C ../../godlib
make
make run
```

Copy `SGDLMIX.TOS`, `VOICE12.RAW` and `VOICE25.RAW` together to the Atari drive.
The example uses normal GodLib Platform, Screen and IKBD lifecycle. It first
runs a self-test of the actual 68000 mixer; the screen must report PASS.

- F1–F4: play the voice on a chosen channel.
- F5: play all four once.
- F6: loop all four.
- F7: stop all channels.
- F8: switch between 25033 and 12517 Hz; stops playback.
- ESC: remove the audio callback, free samples and return to TOS.

`prepare_sample.py` uses the existing mixer demo's signed 12517-Hz voice,
adds headroom, creates both rates (linear upsampling for the 25-kHz demo asset),
and pads each to 512 bytes. Upsampling preserves timing but cannot restore
high-frequency detail absent from the original recording. To assess quality,
use a higher-rate original recording and prepare both outputs offline.

See `../../godlib/audio/sgdlmix.md` for source provenance, API, buffer ownership
and overflow semantics. `analysis/original-snd_asm.txt` contains the original
relocated disassembly; `analysis/core-verification.txt` records byte identity.

F9 toggles the red raster CPU meter used by LanceMod. Palette colour zero
is red only while the audio callback executes, then its old value is restored.
This shows callback duration, not a numeric CPU percentage. SGDL at 12.5 kHz
mixes only on half-buffer changes, so compare multiple frames.

The included `analysis/verify-hatari.py` uses the local hatari-debugging skill
helper and symbols from `make debug` for repeatable target checks.

The menu is drawn once; a static display page updates only changed status
fields, reducing unrelated graphics work during mixer comparisons.
