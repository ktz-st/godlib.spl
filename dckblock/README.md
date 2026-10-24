# DCK planar block operations

`DCKBLOCK.PRG` demonstrates copying rectangular pieces of selected ST bitplanes
from our castle/lake picture. All runtime command building, animation,
restoration and copying runs in 68000 ASM. C provides GodLib setup, input and
captions. ST/STE, PAL RGB, 320×200, 1 MiB; no BLiTTER or raster interrupt.

## Controls and modes

- **1 — MOVE:** a 128×64 fragment from source X=96, Y=24 moves over the picture.
  X is aligned to 16 pixels; Y moves by individual rows.
- **2 — REPEAT:** ten full-width bands, each repeating one source row sixteen
  times. Source step is zero, destination step is +160 bytes.
- **3 — SKIP:** four moving 40-row bands sample every second source row;
  the lower two sample backwards. Source step is +320 or −320 bytes.
- **4 — FLIP:** vertically reversed picture, continuously rolled with wrap.
  Source advances normally; destination step is −160 bytes. The wrap is split
  into two rectangles; the empty rectangle at phase zero performs no access.
- **5 — STRIPS:** ten 32×80 vertical pieces in the middle of the picture are
  cyclically reassigned; alternate pieces read source rows backwards. A new
  arrangement is selected every sixteen ticks; unchanged pages are reused.
- **M:** all four planes → plane 1 → planes 0+2 → all four planes.
- **Space:** pause/resume; **N:** pause and advance one tick.
- **R:** elapsed-time stripe; **Esc:** clean return to TOS.

Plane indices are zero-based: masks are 15, 2 and 5. A partial-plane copy
replaces only those bits of the destination colour index. The other planes
retain the original picture, so moving a single plane creates colour changes
as well as displaced shapes. This is bitplane composition, not alpha blending.

The artwork is the existing ABC2 STE 16-colour `water/assets/CASTLE.PI1`.
The complete 320×200 composition is resampled to 320×160, displayed at Y=24;
header and footer occupy the remaining rows. Original source, indexed preview,
conversion, coordinates and SHA-256 are in `source/`, `tools/assets.py` and
`assets/source.json`.

## Connection to DCK

DCK4/LCK1's generator at TEXT `$0BC0–$0CCE`, called through `$198A`, handles
up to ten 28-byte configurations. It emits word copies for enabled planes and
independent signed source/destination row increments. A zero source increment
repeats a row; increments of two rows skip samples; a negative increment
reverses row order. It does not implement arbitrary bitmap rotation or a
continuous zoomer.

This example adapts that mechanism to GodLib rather than transplanting the
original whole engine. It reads from one immutable bitmap into the logical
screen. Its own compact commands are seven words (14 bytes):

| Word | Meaning |
| --- | --- |
| 0 | Source byte offset within the 25,600-byte picture |
| 1 | Destination byte offset within the stage at screen Y=24 |
| 2 | Width in 16-pixel groups: 2, 8 or 20 |
| 3 | Height in rows |
| 4 | Four-bit plane mask |
| 5 | Signed source row step in bytes |
| 6 | Signed destination row step in bytes |

Commands use aligned X coordinates and valid source/destination bounds.
The internal copier supports all sixteen masks for those three widths.
Zero mask, zero height and unsupported widths return without copying. It is
an example-local kernel, not a general GodLib blit/clipping API. Source and
destination are distinct; overlapping in-place copies are not implemented.

`tools/assets.py` emits **static assembly source** for the 48 width/mask
variants. Runtime generates only the small command list, never executable
code or animation frames. Partial masks retain DCK-style word copies; adjacent
planes share longword moves, and full-plane rows use MOVEM. Each rectangle
calls its kernel once, with the entire row loop inside that kernel. Narrow
copies use register-held strides and DBF; wide MOVEM copies keep three loop
words on the stack because the data transfer uses the free registers.

Each screen page stores its previous mode, mask, phase key and moving-block
offset. The old moving rectangle is restored from the original bitmap before
redrawing. Full-stage effects overwrite active planes directly; only dropped
planes need restoration. Entering a smaller effect also restores its previous
larger footprint. This preserves the original image through mode/mask changes.
Pausing settles both pages, then skips all rectangle copies.

## Build, memory and checks

```
make assets
make
make check
make profile
make debug-release
DB_SYMBOLS=/tmp/DBREL.PRG python3 tools/smoke_release.py
```

Build requires the neighbouring GodLib/libcmini, GCC ELF, vasm and, for asset
regeneration, Python/Pillow. `make profile` uses Hatari HRDB and also records
single-frame peaks; override `DB_HRDB_PORT` if using an isolated server port.
German STE TOS 1.62 is the default test ROM. The ST test uses TOS 2.06.

The release is **101,995 bytes**. ASM code including the static kernel table
is **5,418 bytes**, picture data 25,600 bytes, palette 32 bytes, position table
320 bytes. Command storage is 154 bytes and page history 16 bytes, plus small
control globals and normal GodLib screen allocations. There is no frame cache
or per-frame allocation. The GodLib library is unchanged by this example.

`verification.json` records **844 full-native-frame comparisons** against a
separate reference that recomposes the result directly from the original
picture, without reading ASM commands or history. Checks cover every phase of
the four moving modes, all strip arrangements and their idle ticks, all 16
masks across all three widths, both page histories, 48 arbitrary mode/mask
jumps, source/back preservation, unchanged headers/footers and controls.

The **actual stripped PRG** was tested separately on ST and STE, 1 MiB,
BLiTTER disabled. Each run compared another 60 full buffers across all five
modes and three masks, checked palette, pause/step/resume, input, and restoration
of the VBL vector on exit. See `release-smoke*.json`.

[CPU.md](CPU.md) reports both steady costs and expensive transition frames.
Measurements are from Hatari, not real hardware.
