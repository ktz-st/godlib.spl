# NIEZW TV power-off: binary findings and adaptation

Reference: `GCC.ELF/NIEZW/NIEZW.TOS`, SHA-256
`e40bb6c690fd320718154f169b1baebc7afb71dda38e056b0e69258cce63f168`.
Unpacked TOS executable: TEXT 50796, DATA 0, BSS 236960, 2103 relocations.
These findings are from static disassembly of the supplied binary, not an
assertion that the original game was run through every transition.
The original file is unchanged.

## Address ledger

| Routine | TEXT-relative | File offset (28-byte TOS header) | Runtime |
| --- | ---: | ---: | --- |
| Simple TV-off variant | `$6CE8` | `$6D04` | `p_tbase + $6CE8` |
| Glowing TV-off used by intro | `$6E8A` | `$6EA6` | `p_tbase + $6E8A` |
| Thin glowing line | `$682A` | `$6846` | `p_tbase + $682A` |
| Centred vertical squash | `$6A5C` | `$6A78` | `p_tbase + $6A5C` |
| Copy a 160-byte source row to a destination row | `$699C` | `$69B8` | `p_tbase + $699C` |
| Generic memory copy / clear | `$45F0` / `$4690` | `$460C` / `$46AC` | add `p_tbase` |
| 32-bit multiply / signed divide helpers | `$0054` / `$00B2` | `$0070` / `$00CE` | add `p_tbase` |

`niezw-tv-off.s` and `niezw-vertical.s` are rg-dis excerpts. Their `org` is
TEXT-relative, absolute operands are unrelocated TEXT/BSS offsets and `_Lxxxx`
labels inside each sliced listing are slice-local. Do not run or reassemble
these excerpts as a standalone program. Hardware annotations on low absolute
addresses in raw listings are incidental, not evidence of vector access.

## Reference correction: the glowing variant and supplied screenshots

The first investigation examined the simpler routine at TEXT+$6CE8. There is
also a richer TV-off routine at **TEXT+$6E8A / file+$6EA6**, called from the
intro near TEXT+$679E. This distinction was missed when preparing the first
adaptation. The simpler routine alone does not explain the user's reference.
`niezw-tv-glow-off.s` and `niezw-glow-line.s` preserve the relevant excerpts.
The richer variant boosts RGB channels as it squashes, excludes palette entry
zero from that boost, and uses `$682A` to draw a four-row dim halo around a
two-row bright core. The width follows a quadratic curve. Its original code
also has a small central afterglow sequence, but the requested version follows
the supplied screenshots: **a short horizontal afterglow, no round dot**.

The original game was booted in Hatari and its noise/intro screens observed;
the full TV-off sequence was not recorded from a natural playthrough. The
user supplied four actual reference frames, preserved in `reference/`:

| Reference | Non-black bounds in a 320x200 crop (half-open) |
| --- | --- |
| grab0197 | X=0..320, Y=76..126 (320x50) |
| grab0198 | X=0..320, Y=92..110 (320x18) |
| grab0199 | X=0..320, Y=100..102 (320x2) |
| grab0200 | X=140..180, Y=100..102 (40x2) |

The crop uses screenshot rectangle (96,56)..(736,456), sampled at half size;
the one-pixel centre offset depends on the screenshot viewport origin.
These are visual references, not measurements of time between stages.

## Current optimized implementation

`crt_tv.s` keeps the centred nearest-neighbour row selection but specializes
it to the fixed 320x200 four-plane canvas. C selects the stage and queues its
palette with `Video_SetNextPalST` immediately before `Screen_Update`; no raster
interrupts or mid-screen palette changes are used.

- **11 image heights**: 200,168,138,106,78,54,36,22,12,6,2 when closing.
  This replaces the earlier 20 unique height stages. Each stage is drawn once
  on each screen page: 22 VBLs / about 0.44 seconds for image compression.
- During compression, add up to 12/15 to each RGB444 component, saturating at
  15. Both actual black entries (0 and 8, the dark-bank black) stay black.
  All stage palettes are precomputed; opening reverses the brightening.
- After the picture reaches two rows, a white **two-pixel core** with a dim
  one-row halo above/below narrows through widths 320,264,208,144,96,64,40.
  The final **40x2 horizontal line fades** through RGB444 intensities 12,8,4,1
  to black. No round-dot code or circle tables remain.
- There are **22 total stages**, including black, about **0.88 seconds per
  direction** at 50 Hz. `N` closes the current scene, holds black briefly,
  switches scene/palette and opens the other. Startup plays opening only.
  `N` is ignored during a transition; `P` freezes normal interference only.
- Offline row maps remove software division from the frame loop. Copy only
  visible rows with four 40-byte MOVEM bursts per changed row. An independent
  200-word history for each page skips rows already containing that source.
- Clear only newly uncovered top/bottom strips. The line renderer clears at
  most four rows and fills spans with word edge masks. No per-pixel loops.
- The step/map/palette data total **3230 bytes**; per-page row histories take
  800 bytes and height histories four bytes. Back is reused as the TV source,
  with no extra 32000-byte snapshot. Normal CRT rendering retains its guarded
  BLiTTER sources and brightness-mask history.

This is a screenshot-guided adaptation, not a cycle-identical clone of either
original routine. The original NIEZW executable remains unchanged.

## Evidence

`tv-verification.json`: two N-key cycles, every stage in both directions on
both pages, both pictures, displayed palette/page synchronization, black
background throughout, normal renderer after scene swap and clean exit.
`verification.json` covers the normal CRT effect separately.
`tv-transition.gif` is a sampled native Hatari visual preview, not a timing
measurement. `tv-profile.json` measures **90 transition updates**, averaging
**34416 cycles / 4.30 ms / 21.51%** of an 8 MHz PAL frame. The figure includes
ASM and TV command preparation; VBL/input and one-time scene/font preparation
are excluded. It is not a worst-case figure or an original-versus-port speedup.
