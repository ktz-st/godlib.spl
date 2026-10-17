# Palette split: colour above, greyscale below

```sh
make
make run
```

`PALFX.PRG` shows the coast picture from `../wipe` in PAL 320x200 low
resolution. Rows 0..99 use the original palette; rows 100..199 use a greyscale
palette. The Degas picture is embedded in the executable, so no external runtime
assets are needed. Space toggles the lower-half greyscale effect; Esc exits.

Works on ST and STE/Mega STE with a 68000 at 8 MHz and a colour monitor. It uses
ST-compatible three-bit RGB values, so there are eight possible grey levels on
both machines. TT/Falcon video is rejected by this compact example.

## Same installation as the screen split

`raster.c` follows the [screen split example](../splitscreen/README.md): save the
previous GodLib video callback and Timer B state, install the raster interrupt
with `Vbl_InstallTimerB()`, and wrap the original callback using
`Vbl_SetVideoFunc()`. Install/remove operations are protected by IPL 7.

Every VBL, GodLib rearms Timer B at display-enable event 99. The video wrapper
runs the original video updater and restores the original colour palette for
the top of the new frame. It also snapshots the effect-enable flag, so pressing
Space cannot change the interpretation of a frame halfway through rendering.

The critical handler in `raster_s.s` follows `Palette_HBL` from
`amberstar/src/NUCLEUS/HBI.ASM`:

```asm
movem.l (a0),d1-d7/a1       ; preload all 16 colour words BEFORE waiting
; restart Timer B with a dummy count and wait for the next DE falling edge
movem.l d1-d7/a1,(a2)       ; A2 = $FFFF8240, one 32-byte palette write
```

Seven data registers plus one address register hold eight longwords: the full
16-colour palette. There is no memory-to-memory MOVEM operation. Loading and
writing are separate instructions; doing both after synchronization would waste
the limited blanking time. Here only the final write happens in the right border
following picture row 99, so the first complete grey row is row 100.

The greyscale palette is prepared once in C at startup, using rounded integer
luminance `(77*R + 150*G + 29*B + 128) >> 8` and equal R/G/B components.
The picture's bitplane data and the display address never change for the effect.
The VBL colour restore is essential: without it, the next frame would start
with the grey palette left by the previous interrupt.

Like the screen split, this example owns Timer B and defers TOS Timer C until
the split handler finishes. It is not a general raster scheduler and should not
be combined unchanged with another Timer B user or Timer C-driven playback.
No blitter jobs or disk reads are started while the raster is active; all image
copies happen before installation. A program with active blitter work must also
account for blitter bus ownership at the raster boundary.

On exit, the previous callbacks/MFP Timer B state are restored, then the normal
colour palette and screen are presented before releasing screen storage and
letting Platform restore TOS state.

## Verification

```sh
make debug
python3 analysis/verify-hatari.py
```

The optional harness needs Pillow and the local hatari-debugging helper.
`HATARI_TOS` can override the default local TOS 2.06 path; `HATARI_TOS162`
selects the TOS 1.62 image. It runs ST/STE with TOS 2.06 and STE with TOS 1.62,
checks full displayed images with the split on/off/on, verifies all three
VRAM pages are byte-for-byte unchanged, checks exit and removal of the handler,
and inspects `video_color` traces for all 16 palette words inside horizontal
blank. Results go to `analysis/results.json`; logs/captures are ignored.
Emulator timing is not a physical-hardware guarantee.

Verified on 2026-10-16 in Hatari, 68000 at 8 MHz, PAL, using `PALFX.PRG`:
ST/TOS 2.06: 787 palette-split frames; STE/TOS 2.06: 794;
STE/TOS 1.62: 689. All 16 words stayed inside horizontal blank, cycles 428..504
at nHBL=162. Five full-screen captures per configuration matched the expected
colour/grey output; toggles, unchanged VRAM and five seconds after exit passed.

## TOS 1.62 exit and filename regression

The output is named `PALFX.PRG`. In the tested Hatari 2.6.1 + TOS 1.62 setup,
autostarting the old `PALSPLIT.PRG` name caused a ROM bus error after termination
(PC $E1FC9C, read at $4C4954F2). This is reproducible with a separate executable
containing only `int main(void) { return 0; }`, without GodLib or any raster code.
The identical payload under the shorter `PALFX.PRG` name returns successfully.
The full palette example also exits correctly under the shorter name. This is a
filename workaround for the observed autostart/desktop failure, not a change to
the palette ISR or a general diagnosis for every TOS crash.

`python3 analysis/verify-exit-name.py` reproduces the comparison and saves
`analysis/exit-name-results.json`, including the identical payload hash. The
normal image test now includes STE/TOS 1.62 and watches for faults for five
seconds after exit, in addition to checking callback removal and freed VRAM.
Use the newly built `PALFX.PRG`; an old downloaded `PALSPLIT.PRG` keeps its old
name and can still trigger this failure when autostarted.

## Artwork conversion update

Generated scene artwork now uses **ABC2, STE RGB444, without dithering**.
See the [shared artwork guide](../tools/ARTWORK.md) for reserved colours,
regeneration, shared copies and validation. Snowfall retains eight background
colours to leave its snow bitplane free. Older ST screenshots and CPU results
above refer to their original artwork revision.
