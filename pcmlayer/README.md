# PcmLayerMixer example

```sh
make -C ../../godlib
make
make run
```

Copy PCMLAYER.PRG and VOICE.RAW together to an STE/MegaSTE. The first screen
must show ASM self-test PASS. The example prepares a signed 12517-Hz voice at
quarter amplitude from the existing mixer demo and pads it to four bytes.

- F1/F2: toggle the base loop / additional loop.
- F3/F4: trigger either one-shot slot.
- F5: start all four (two loops and two one-shots).
- F6: stop every channel.
- F9: toggle the red raster CPU meter, matching LanceMod.
- ESC: stop DMA, remove the callback and return to TOS.

PCM Block and PCM Frame examples also use F9 for their audio CPU raster. This is a
visual duration indicator, not a numeric CPU percentage. For PCM Block select
12.5 kHz with F8 before comparing; its 512-byte refill happens roughly every
second VBL. Compare several frames with the same active channel count. For
PCM Layer, F1/F2 + F3 gives three simultaneous sources to compare with PCM Frame;
F5 exercises PCM Layer's four-layer case.

See ../../godlib/audio/pcmlayer.md for API restrictions and provenance.
`make debug` creates an unstripped analysis/PCMLYDBG.PRG and linker map.

The included `analysis/verify-hatari.py` uses the local hatari-debugging skill
helper and symbols from `make debug` for repeatable target checks.

The menu is drawn once; a static display page updates only changed status
fields, reducing unrelated graphics work during mixer comparisons.
