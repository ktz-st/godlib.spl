# DCK wave CPU measurements

Hatari-HRDB: STE / MC68000 / 8 MHz / PAL RGB / **1 MiB**, German TOS 1.62.
Each moving-mode profile covers **512 steady updates**, two complete phase
cycles, after warming up both display pages. BLiTTER is disabled.

Included: ASM phase advance/table selection, page/mask dispatch and word
shifting. Excluded: startup/reset, initial picture copies, mode/header changes,
input, C page selection, Screen_Update, VBL and OS work. Percentages divide
average renderer cycles/update by the **160000-cycle / 20 ms PAL budget**.
These are cycle averages, not maximum costs or physical-hardware measurements.

| Mode | Moving cycles/update | CPU | Time at 8 MHz |
|---|---:|---:|---:|
| All four planes | 123497 | **77.19%** | 15.44 ms |
| One plane: 1 | 31448 | **19.65%** | 3.93 ms |
| Two planes: 0+2 | 62132 | **38.83%** | 7.77 ms |

After both pages reach a paused target, the early return costs approximately
265 cycles/update, **0.17%**, in every mode. That separate measurement checks
that no plane kernels are called; it is not an active-wave result.

The first version scanned and sign-extended old/new shifts even when equal.
Comparing bytes first reduced the four-plane moving cost from about 82.32%
to 77.19%. Skipping an identical whole page removed its 37.86% paused scan.
The final figures above come from the final shipped build, not that prototype.

## Ordinary main-loop cadence

These separate live windows run the normal application, with input and
Screen_Update enabled. Mode-change/header setup is allowed to settle first.
All three steady modes run at **50 FPS**, with no missed VBLs observed:

| Mode | Loop frames observed | Missed VBLs | FPS |
|---|---:|---:|---:|
| All | 1029 | 0 | 50.0 |
| One | 1197 | 0 | 50.0 |
| Two | 1099 | 0 | 50.0 |

Amplitude, spatial frequency and phase speed are fixed in this example. A
larger/faster wave or a different image height changes the workload. Mode
switches can use the direct source path to restore newly inactive planes;
their one-time cost is outside the steady profiles and cadence windows.

The `R` stripe brackets `Dw_Frame` in the main loop and shows elapsed renderer
time. It can include interrupt activity; it is not a numeric instruction-cycle
meter. The measurements above come from HRDB.

## Verification and shipped artifact

- `verification.json`: **849 complete 32000-byte framebuffer comparisons**,
  zero mismatches. All three masks, all 256 phases, wrap, both alternating
  pages, repeated paused targets and 60 arbitrary mode/phase jumps. The host
  reference shifts complete 320-bit rows, independently of the ASM carry
  chain. This checks zero clipping and recovery of source pixels on reversals.
- Live controls/palette checks cover all three modes, pause, single step,
  resume and clean return to TOS.
- `release-smoke.json`: the actual stripped `DCKWAVE.PRG` on STE with 1 MiB,
  German TOS 1.62; twelve full-buffer comparisons, all modes, pause/step/
  resume, CPU stripe and exit.
- `release-smoke-st.json`: the same actual PRG and checks on plain ST without
  BLiTTER, 1 MiB and TOS 2.06. This is a compatibility test; CPU numbers above
  are from the STE run.
- `profiling.json`: six 512-update profiles, asserted frame/plane call counts,
  component cycle totals and the three normal cadence windows.
- `preview-{all,one,two}.png`: complete native pages decoded with the STE
  palette. No screenshot interpolation is used for byte comparisons.

Release tests use the shipped executable with separately linked symbols.
Code/data after the first `$A0` bytes of TEXT must match; the excluded prefix
contains ELF metadata that differs in stripped/unstripped links. Temporary
debug binaries and memory dumps live under `/tmp`, not `analysis/` folders.

The final PRG is **98021 bytes**, about 95.7 KiB. SHA-256:
`8aff2d75b4695f1ceadb86254ab02c41264212e90f5622680eb612091f59b261`.
Every verification/profile report records this same release hash.
