# DCK route-changing scroller

`DCKROUTE.PRG` shows one full-colour BIG 40×32 text stream changing between
DCK curve profiles, a straight horizontal strip and an upward letter column.
The ten curves come from the original `SCROLL_1.TRJ`. Embedded commands change
the route automatically; the same queued letters continue across each change.

ST/STE, 320×200, four planes, 8 MHz PAL, 1 MiB. CPU rendering in 68000 ASM;
no BLiTTER, raster interrupt, generated code or cached animation frames.
GodLib itself is unchanged by this example.

## Controls

- **N**: next demonstration route (curves 2/7/4, H, V, curves 0/9).
- **0–9**: choose a curve and enter P mode.
- **P / H / V**: curve, straight strip or vertical column.
- **Space**: pause/resume movement and route interpolation.
- **R**: visible elapsed-time stripe; **Esc**: return to TOS.

Commands and manual requests apply at the next glyph boundary, so switching
can take up to 0.8 seconds in V mode. Automatic commands remain active after
manual selection. P/H move eight pixels per frame; V moves one pixel per frame.

## DCK source versus this adaptation

The original text decoder at TEXT `$1688–$1806` uses `FE P/H/V`,
`FE '0'..'9'` (profile index, not speed), and `FF` (restart text).
This example retains that encoding and consumes commands when a new glyph is
appended. Nine glyphs are queued, so a command is read ahead of the visible
entering edge, especially in the shorter vertical window. It changes the
whole queued stream, rather than starting another message. Unsupported `FE L`
is ignored; its original semantics have not been established.

The original generators at `$076C–$0BC0` also build transition/copy kernels.
This example does **not** reproduce those kernels or their exact transfer
animation. It uses a shared glyph queue and its own live interpolation:
40 eight-pixel slices move toward the target curve by at most one row per
update. Changing between P and H therefore flattens/bends the current text.
P/H↔V rearranges the same glyph queue at a glyph boundary, without fading or
restarting it. The 32-row glyphs have an eight-row gap in V mode.

`source/SCROLL_1.TRJ` is the original 1,000-byte file: ten × forty signed Y
words, followed by the vertical/horizontal/row-step configuration records.
Only the curve section is used here. Curves are centred around Y=84; profiles
exceeding 120 rows are scaled down to leave room for the legends. The original
profile shapes are retained, while H uses fixed Y=84 and V uses fixed
X=144, Y=24, height=160. This does not implement the full TRJ area/modulo
configuration or the negative-Y gaps found in other TRJ sets.

`source/BIG.PI1` and `BIG.png` are lossless copies of DCK disk B's
`FONTES/BIG.PC1`. The 48-cell original atlas plus a blank glyph is packed in two
31,360-byte layouts: eight-pixel columns for `MOVEP.L`, rows for the vertical
`MOVEM.L`/`MOVEP.L` kernel. The fixed original palette colours all modes.
`assets/source.json` records hashes, original/adapted coordinates and text.

## Drawing and memory

C owns setup, input and captions. ASM decodes the text, advances the shared
nine-glyph queue, interpolates the route, erases the old footprint and renders.
Each GodLib screen page has its own previous mode and forty Y positions.
Stable strips overwrite all four planes, including zero pixels. When a strip
moves, only its exposed old top/bottom edge is cleared. A P/H↔V change clears
the complete previous footprint on each page once. No complete screen is
copied per frame; the background is black.

The ASM text section is **1,096 bytes**. Runtime queue/path/pointer history is
about 0.5 KiB, in addition to the two packed font layouts and 800-byte path
table. Normal GodLib screen allocations are separate. Release file size:
**135,651 bytes**. The two extra 32,000-byte test pages exist only in the
`ROUTE_BENCH` build under `/tmp`, not in the shipped PRG.

## Build and verification

```
make assets
make
make check
make profile
make debug-release
DR_SYMBOLS=/tmp/DRREL.PRG python3 tools/smoke_release.py
```

`make assets` needs Python/Pillow; build uses the neighbouring GodLib/libcmini,
GCC ELF and vasm. Use an HRDB-enabled Hatari for `make profile`; its server port
can be selected with `DR_HRDB_PORT`. Local tests used an isolated port remap.

`verification.json` records **293 full-native-frame comparisons** against an
independent indexed-atlas reference: all ten curves, all five horizontal and
forty vertical phases, both page histories, live curve interpolation, P/H/V
transitions, forty actual FE commands including FF text wraps, controls and
clean exit. `release-smoke*.json` records separate tests of the actual stripped
PRG on STE/TOS 1.62 German and ST/TOS 2.06, 1 MiB, with BLiTTER disabled.

See [CPU.md](CPU.md) for measured costs. These are emulator measurements,
not real-machine results.
