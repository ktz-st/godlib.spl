# DCK TAPIS CPU measurements

**Actual shipped DCKTAPIS.PRG**, Hatari-HRDB, STE / MC68000 / 8 MHz / PAL RGB /
1 MiB, German TOS 1.62. Profiles observe real callback executions in VBL;
there is no synthetic main-loop replay batch.

Included: all of `Tp_Vbl`, control snapshot, phase/direction/countdown, diagnostic
counters, period helper, all sixteen hardware colour writes and return.
Excluded: shared GodLib interrupt entry/callback dispatch/video updater, setup,
input/status text, Screen_Update and OS work. Percentages divide average cycles
per VBL by the **160000-cycle / 20 ms PAL frame budget**. These are emulator
instruction-cycle averages, not measurements on physical hardware.

| Mode | Palette changes/s | Cycles/VBL | CPU | Time/VBL |
|---|---:|---:|---:|---:|
| Every VBL, forward | 50 | 637.60 | **0.399%** | 79.70 µs |
| Every 2 VBLs, forward — default | 25 | 535.08 | **0.334%** | 66.88 µs |
| Every 4 VBLs, forward | 12.5 | 483.94 | **0.302%** | 60.49 µs |
| Every 2 VBLs, reverse | 25 | 530.70 | **0.332%** | 66.34 µs |
| Paused | 0 | 400.58 | **0.250%** | 50.07 µs |

Every VBL writes one complete palette, including when the phase is held.
The palette-selection/write/return portion costs approximately 260 cycles
(0.163% of a PAL frame). Pausing stops phase advance, rather than detaching
the callback. No framebuffer rendering or background copies occur during the
steady animation.

Each capture contains at least 1344 VBL calls, covering many complete
fourteen-phase cycles. Palette-write counts equal callback counts. Period
helper counts prove the selected update rate; paused captures have no phase
advances. `profiling.json` retains counts, components and the release hash.

## Ordinary application cadence

Separate normal-loop observation windows include Screen_Update and input.
All modes stayed at **50 FPS with no missed VBLs**:

| Mode | Frames observed | Missed VBLs |
|---|---:|---:|
| Every VBL | 609 | 0 |
| Every 2 VBLs | 599 | 0 |
| Every 4 VBLs | 624 | 0 |
| Reverse / 2 VBLs | 633 | 0 |
| Paused | 633 | 0 |

## Verification

- `verification.json`: **3072 real VBL snapshots** across all three periods
  and both directions. Each checks the full hardware palette against its
  original record, contiguous ticks, countdown, phase, wrap and all fourteen
  positions. A debug-only wrapper records after the ASM callback; it is not
  part of the shipped PRG or CPU profiles.
- The main loop is deliberately held during those six captures. Its frame
  counter stays fixed, VBL animation continues, and both complete screen pages
  remain byte-identical. Original artwork outside the four legend/status
  regions is checked against the original 32000-byte bitmap.
- Twenty-eight manual steps cover the full cycle in both directions, hardware
  colours and pause. Keyboard controls, callback detachment, restored VBL
  vector and no subsequent callback ticks are also checked.
- `release-smoke.json`: actual stripped PRG, STE / 1 MiB / German TOS 1.62,
  direct ASM callback registered, all speeds/directions/pause/step/resume,
  six complete screen-page comparisons and twenty-eight palette checks.
- `release-smoke-st.json`: the same shipped PRG and checks on plain ST without
  BLiTTER, 1 MiB, TOS 2.06. Its palette check compares the meaningful RGB333
  bits. This is a compatibility test; CPU figures above are from STE.
- Both release tests check callback removal, restoration of the old `$70`
  vector and a later observation window with no callback ticks after exit.

Release tests use a separate symbol link to inspect the shipped binary.
Code/data after the first `$A0` bytes of TEXT must match; the excluded prefix
contains ELF metadata that differs in stripped/unstripped links. Temporary
binaries and RAM logs remain under `/tmp`, not in `analysis/` directories.

The final PRG is **109933 bytes**, about 107.4 KiB. SHA-256:
`4c0fc903176c5cd28d6629867e31b1c4b33c59def3948806c2352d93a319f9c0`.
All verification and profiling reports record that same release hash.
