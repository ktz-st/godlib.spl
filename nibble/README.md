# NIBBLE scroller

ST/STE adaptation of **THE NIBBLE SCROLL** by Manikin / The Lost Boys,
concept by XXX, dated 19 April 1989. Runs on a plain 8 MHz 68000 ST;
no BLiTTER or STE scrolling registers are required.
Key `3` selects the same font and two-pixel text stream without a wave.

```sh
make
make run
```

Run `NIBBLE.PRG`. All assets are embedded; no external files are needed.

| Key | Action |
| --- | --- |
| `1` | Original NIBBLE waveform, 40-pixel vertical range |
| `2` | Original NIBBLE1 waveform, 24-pixel vertical range |
| `3` | Straight scroller, fixed Y=101 |
| `Space` | Pause/resume text and wave motion |
| `R` | Toggle green CPU timing marker in the border |
| `Esc` | Exit to TOS |

## Original algorithm

`nibble_s.s` contains the runtime text and drawing kernels, adapted to vasm
Motorola syntax and the GCC ELF calling convention. C initializes GodLib,
creates the static background, handles keys and alternates the display pages.

- The original LOST16 font has 32x16 glyph storage. The source renders 15 rows;
  its sixteenth font row is blank.
- A 600-byte, one-plane conveyor stores twenty 16x15 blocks in column order.
  `LSL.W` / `ROXL.W` chains advance all 320 pixels by **two pixels per frame**.
  A new glyph is consumed every 16 updates; text wraps at its terminator.
- The renderer splits each 16-pixel word into two independently positioned
  8-pixel strips. It copies their 15 bytes to plane zero, using the original
  precalculated Y-offset tables. Wave position advances one longword per update
  and wraps after 80 updates, as in the original.
- Sparse edge clearing follows the original routine and its movement limits.
  Switching waveform first clears the whole effect band on **each** display
  page, preventing remnants of the previous wave. The other planes and the
  static header/controls stay intact.

`Nibble_DrawFlat` draws the same conveyor at Y=101 using 15 word writes per
16-pixel block. It does not read sine tables or erase edges each frame.
Switching between a wave and flat mode clears the old text once per page.

The original program's hard-coded screen addresses, keyboard/VBL vectors and
TOS setup are replaced by GodLib Screen/IKBD/Platform lifecycle calls. The
baseline is moved from line 100 to line 80 to make room for on-screen controls.
The text is changed, while the font and both 640-byte wave tables are copied
unchanged. Their origin and SHA-256 hashes are in `assets/provenance.json`.

Source reference in the workspace:
`Atari_ST_Sources/ASM/The Lost Boys (TLB)/Mindbomb/Massacre/SCROLL/NIBBLE.S`.

## CPU measurement

Measured with Hatari-HRDB, ST, 68000 at 8 MHz, 1 MB RAM, TOS 2.06,
PAL 50 Hz. The timing marker is disabled during profiling.

| Mode | Advance text/wave | Draw | Combined | PAL frame budget |
| --- | ---: | ---: | ---: | ---: |
| Wave 1 | 11,297 cycles | 14,958 cycles | **3.282 ms** | **16.38%** |
| Wave 2 | 11,297 cycles | 14,958 cycles | **3.282 ms** | **16.38%** |
| Flat | 11,297 cycles | 5,340 cycles | **2.080 ms** | **10.38%** |
| Wave paused | 0 | 14,962 cycles | 1.870 ms | 9.34% |
| Flat paused | 0 | 5,340 cycles | 0.667 ms | 3.33% |

All three moving modes run at **50 updates/second**. These are instruction-cycle
costs of `Nibble_Advance` and `Nibble_Draw` / `Nibble_DrawFlat`, including
their register saves.
They exclude GodLib/input overhead, VBL waiting, startup prefill and the rare
full-band clear when selecting a different waveform. PAL percentage uses
160,256 CPU cycles per frame. Paused mode still redraws both display pages.
The border marker brackets the active update/draw path; it is a visual time
indicator, not the source of the cycle measurements.

Reproduce the measurement:

```sh
make debug
python3 analysis/profile.py
```

Raw per-instruction captures and results are in `analysis/profile-raw-*.json`
and `analysis/profile.json`. The scripts use the local Hatari debugging skill
helpers and installed TOS ROMs.

## Verification

```sh
make debug
python3 analysis/verify-hatari.py
```

The Hatari harness compares complete 32,000-byte rendered screens against an
independent pixel model built from the original font and wave tables. It also
compares the ASM conveyor with a horizontal glyph stream, exercises all 80
phases of both waves and the flat mode, checks both display pages, pause, waveform changes,
text wrap, timing-marker toggle and clean exit. Target configurations are ST
with TOS 2.06 and STE with TOS 2.06/1.62, all at 8 MHz and 1 MB RAM.

All three configurations passed: **774 complete screen comparisons**, both
pages and all wave phases, with zero missed VBLs in the verification runs.
See `analysis/verification-summary.json` and `analysis/results-*.json`.
