# CPU versus BLiTTER WIPE

Hatari-HRDB, STE / MC68000 / 8 MHz / PAL RGB / **1 MiB**, German TOS 1.62.
Each row covers **all 39 complete effects, 589 updates**, using the same COAST
image and canonical destination. These are frame-weighted averages.

| Direction | CPU cycles/update | CPU time | BLiTTER cycles/update | BLiTTER time | Speedup |
|---|---:|---:|---:|---:|---:|
| Wipe-in | 265929 | **33.24 ms** | 128996 | **16.12 ms** | **2.06×** |
| Wipe-out | 171345 | **21.42 ms** | 129049 | **16.13 ms** | **1.33×** |

The cost relative to one **160000-cycle / 20 ms PAL frame** is:

| Direction | CPU | BLiTTER |
|---|---:|---:|
| Wipe-in | 166.21% | 80.62% |
| Wipe-out | 107.09% | 80.66% |

A result above 100% means the work cannot fit in one 50 Hz frame; it is not
processor utilization above full capacity. BLiTTER reduces wipe-in time by
51.49%, wipe-out by 24.68%. Its HOG transfer stalls the CPU: **that wait is
included**, not presented as time available for other game work.

## Scope

Included: the complete `Wipe_Update` dispatcher, selected CPU/BLiTTER kernel,
shared hardware setup and idle/completion waits. Profiles assert 589 updater
entries and 589 entries of exactly the selected renderer. BLiTTER captures also
assert 589 hardware submissions and 1178 wait entries; CPU captures submit no
blits. The original mask data is unchanged.

Excluded: init/seed, backend setter, test-loop orchestration, ScreenBack-to-logic
copy, captions, Screen_Update/VBL waiting and OS handlers. The debug example
links the same library object as the shipped PRG; profiling bypasses the ABI
test wrapper and calls `Wipe_Update` directly. `profiling.json` records complete
component totals, call counts and executable/archive hashes.

The slideshow retains at least two VBLs per displayed step and additionally
copies its canonical Back buffer and draws captions. These renderer numbers
do not describe whole-program CPU usage or promise a 50 FPS slideshow. The
visible R stripe also brackets only the updater; it measures elapsed time and
can span more than one refresh in CPU mode.

## Correctness and compatibility

- `verification.json`: **3534 guarded 32000-byte buffer comparisons**, zero
  mismatches. All 589 mask frames, both directions, CPU, BLiTTER and alternating
  backends at every step. Checks cover completion timing, untouched source,
  both guard regions and preservation of D2–D7/A2–A6 across every update.
- The independent reference computes planar source AND mask for opening and
  destination AND the complement of accumulated masks for closing. It is not
  just a comparison between two implementations.
- `dirty-verification.json`: two additional complete-buffer checks after a
  caller edits pixels between updates. Opening must replace those old pixels;
  closing must preserve edits where the next mask does not clear them.
- The main test also checks unsigned invalid indices, all three final PI1
  images, hardware palettes, a held displayed-black palette seam, B/R/P/Space
  controls and clean exit/restoration of the old VBL vector.
- `release-smoke.json`: actual stripped WIPE.PRG on STE / 1 MiB / German
  TOS 1.62, both backends, both display pages, native images/palettes, a real
  keyboard B switch during a running transition and clean TOS exit.
- `release-smoke-st.json`: the same PRG on plain ST / 1 MiB / TOS 2.06 with
  BLiTTER explicitly absent. Startup and attempts to enable it remain CPU;
  all image/control/exit checks pass. CPU timing above is from STE.
- `ste-preview.json`: the raw compatibility entry is additionally checked
  with its corrected 32-byte frame stride: 236 native buffers, all 39 effects
  sampled and every frame of six effects. Preview GIF timing is normalized,
  not a performance measurement.

Release smoke tests use the shipped executable with separately linked symbols.
Code/data after the first `$A0` bytes of TEXT must match; the excluded prefix
contains differing embedded ELF debug metadata. Debug PRGs, staging folders
and dumps stay in `/tmp`, without recreating `analysis/` directories.

The library was rebuilt by replacing only `wipe_s.o` in the existing archive;
all unrelated members were verified byte-identical. The sample now uses its
already allocated ScreenBack, removing the old additional 32000-byte array.
The library adds no frame cache or heap allocation for the backend.

Shipped WIPE.PRG: **100583 bytes**, SHA-256
`c2a98c2120c9aeb7f8a3b6ec1331adb4e5b7acf6650876ace35e61d444e169cb`.
Measurement archive SHA-256:
`f106ac8fb4203bda0be7cdb01e4f944eb379d73c02663d24e506a67c564b3b46`.

Published archive SHA-256: `8836333b7a85448339f6668d5c2db899e4a71f7e4f4b056ccd7e4cfb5b5c9888`.
This archive replaces only `wipe_s.o` from main; the WIPE object is byte-identical
to the measured build. Local audio experiment symbols are excluded.
