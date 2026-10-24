# LCK bitmap transitions

Eleven LCK-inspired transition modes between two pictures, drawn in 68000 ASM without
a rendered-frame cache or BLiTTER. This is a standalone GodLib example; no
library changes are required. The image occupies 320×160 pixels at Y=24..183,
with persistent controls above and below it.

| Key | Action |
|---|---|
| Left / Right | Select any of the eleven modes, wrapping at both ends |
| 1 | Spiral of 8×8 cells |
| 2 | Fold with reversed source rows |
| 3 | Alternating rows entering from opposite sides |
| 4 | Snake of 16×10 blocks |
| N | Close the current picture, switch palette on black, open the other one |
| Space | Pause / resume |
| R | Show elapsed renderer time as a border colour stripe |
| Esc | Exit to TOS, including during a transition |

Effect selection is available while the picture is idle. The pause state is
retained when starting a transition. Progress is stored separately for both
display pages, so a paused second page can catch up without losing changes.
The palette is queued for VBL only after **both pages** have reached black.

## Original code and adaptations

The source is the recovered LCK4/LCK5 loader template, described in
[the DCK/LCK audit](../../DCK/EFFECTS-AUDIT.md). LCK4 TEXT offsets are `$1926`
(spiral), `$1B74` (fold), `$1CD6` (alternating rows) and `$1F7E` (snake).
These routines were rewritten for vasm and two display pages rather than
linked to the original GFA runtime. All **seven appear and seven disappear
entries** are now represented:

| Mode | Name | Original appear no. | Original disappear no. |
|---|---|---:|---:|
| 1 | Spiral 8×8 | 4 | added counterpart |
| 2 | Fold | 6 | added counterpart |
| 3 | Alternating lines | 7 | added counterpart |
| 4 | Snake 16×10 | added counterpart | 5 |
| 5 | Instant show / clear | 1 | 1 |
| 6 | Colour steps | 2 | 2 |
| 7 | Centre rows | 3 | 7 |
| 8 | Row smear | 5 | added counterpart |
| 9 | Interlaced rows | added counterpart | 3 |
| 10 | Vertical curtain | added counterpart | 4 |
| 11 | Interlaced columns | added counterpart | 6 |

- **Spiral:** the original inward angular/radius traversal selects 800 unique
  8×8 cells. Duplicate visits are removed when preparing the small offset
  table. All cells are covered without fallback entries. `MOVEP.L` copies or
  clears each selected byte across the four interleaved planes. Sixteen cells
  advance per update.
- **Fold:** a prefix of the picture is followed by reversed rows from farther
  down the source. The original source-row expression is `i + 2*h + 15 - j`,
  **not modulo 15**. The adapted fold shrinks every ten rows for a 160-line
  picture, clamps look-ahead to the last source row, and changes by two rows
  per update. Per-page row histories skip unchanged output rows.
- **Alternating rows:** even lines enter from the left, odd lines from the
  right. Each update adds one 16-pixel column; only new strips are copied or
  cleared using unrolled longword loops.
- **Snake:** 320 blocks traverse successive rows in alternating directions.
  Four blocks advance per update. Ten rows per block are unrolled in ASM.
- **Instant:** a complete image copy or clear on each display page. The shared
  full-area ASM kernel also handles initial/final copies for colour steps.
- **Colour steps:** enable scene palette indices in ascending order, or disable
  them in descending order, with five VBLs per step. The pictures have eight
  scene colours, so unused original palette slots are skipped and index 15
  remains white for the HUD. These are discrete colour steps, not an RGB fade.
  Immutable stage palettes are queued through GodLib for VBL. Both pages get
  the new bitmap while its palette is still black; closing clears their native
  pixels once all scene colours are black, before the normal scene swap.
- **Centre rows:** opening copies 79,80,78,81…; closing clears 0,159,1,158… .
  Two rows advance per update. Only newly changed rows are touched.
- **Row smear:** with `n=160-progress`, rows above n repeat source row n and
  rows from n down remain correct. The current row travels upward from the
  bottom. Four `MOVEM` passes load a 40-byte source chunk once and stamp it
  through the prefix; rows released from each page's old smear are restored.
  Closing reverses this state and finishes with a clear to black.
- **Interlaced rows:** pairs 0,159 / 2,157 / … / 158,1 are copied or cleared.
- **Vertical curtain:** pairs 0,319 / 1,318 / … / 159,160 advance inward.
- **Interlaced columns:** pairs 0,319 / 2,317 / … / 318,1 traverse both parities.
  Both column modes use four-plane word masks. Changed pixels in the same
  16-pixel group are merged before scanning its rows. There are no per-pixel C
  loops and no writes at the original GFA/VDI boundary X=320 or Y=200. The
  curtain endpoints are symmetrized to the valid 320×160 viewport.

Opening counterparts were added where needed. Closing spiral, alternating
rows and snake erase in their reveal order; closing fold reverses its reveal
state. Each phase includes one final update for the other display page.
At 50 Hz the first four phase lengths are 1.02 s / 1.62 s / 0.42 s / 1.62 s.
Centre, smear and interlaced rows take 1.62 s; both column modes 3.22 s;
colour steps 0.82 s. Instant uses two full-page updates, with a possible extra
VBL for the copy/status workload; see CPU.md.

The two post-apocalyptic scenes reuse the CRT example's ABC2 eight-colour
conversion. Indexed PNG sources, STE palettes and provenance are included in
`source/` and `assets/source.json`. Each scene has its own palette. Index 0 is
black; index 15 remains white for the text. Pictures use indices 0..7.

## Build and test

```sh
make
make run
make assets             # regenerate native images and geometry tables
make check              # build /tmp/LWDBG.PRG and compare native framebuffers
make profile            # requires Hatari-HRDB and the local hrdb_profile helper
```

The local GCC ELF, vasm, GodLib and libcmini builds are required. Python asset
and verification tools use Pillow. Test scripts use the local
`hatari-debugging` skill helpers. `make run` defaults to STE, 1 MiB RAM and
German TOS 1.62; `TOS` overrides its ROM path. See [CPU.md](CPU.md) for the
measurement scope, results and release smoke tests. Temporary debug PRGs,
symbol files and memory dumps stay under `/tmp`.

The renderer object contains 2514 bytes of code. Embedded pictures occupy
51200 bytes; geometry tables 6564 bytes, palettes 64 bytes, palette stages
576 bytes and speed/limit tables 44 bytes. Per-page progress and row histories
use 644 bytes, with another 40 bytes for column-mask merging.
GodLib Screen owns its ordinary display pages and Back buffer. There is no
runtime frame-cache allocation or generated drawing code.
