# PCM Frameer example

Build GodLib, then this example:

```sh
make -C ../../godlib
make
make run
```

F1/F2/F3 trigger the voice on channels 1/2/3. F4 triggers all three together;
pressing the individual keys at different times demonstrates overlap better.
F5 toggles looping on channel 2, F6 stops all sources and ESC exits.

`prepare_sample.py` converts `../mixer/voice.raw` (signed 12517 Hz mono) to
`VOICE.RAW`: gain 1/4, padded to 23500 bytes / 94 blocks. No game assets are
required. Keep `VOICE.RAW` beside `PCMFRAME.TOS` when copying the example.
Use a PAL STE at nominal 50 Hz VBL (audio is 12517 Hz, not 50 kHz); the module owns DMA playback exclusively. See
`../../godlib/audio/pcmframe.md` for the API and scheduling limitations.

F9 toggles the red raster CPU meter used by LanceMod. Palette colour zero
is red only while the audio callback executes, then its old value is restored.
This shows callback duration, not a numeric CPU percentage. For comparison with PCM Block at 12.5 kHz, remember that PCM Block mixes only on
half-buffer changes, so inspect multiple frames.

The included `analysis/verify-hatari.py` uses the local hatari-debugging skill
helper and symbols from `make debug` for repeatable target checks.

The menu is drawn once; a static display page updates only changed status
fields, reducing unrelated graphics work during mixer comparisons.
