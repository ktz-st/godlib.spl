# DCK XOR stars — all four directional variants

Run **XORSTARS.PRG** for DCK-style one-bitplane XOR stars moving right, left,
down or up. Individual stars move at 1–4 pixels per update; all four original
cardinal-direction choices are selectable in one self-contained example.
The static coloured bands demonstrate reversible drawing over existing pixels.

```sh
make
make run
```

| Key | Action |
|---|---|
| 1 / Right arrow | Move right. |
| 2 / Left arrow | Move left. |
| 3 / Down arrow | Move down. |
| 4 / Up arrow | Move up. |
| 5 / 6 / 7 | Use 64 / 128 / 256 stars; default 256. |
| Space | Pause/resume motion. |
| R | Green elapsed-render-time marker. |
| Esc | Return to TOS. |

The 320×144 star window occupies Y=28..171. Position and speed initialization
is reproducible, using a fixed 16-bit LFSR seed. Directions can change without
resetting positions; wrapping stays inside the inclusive window bounds.

## Original and adaptation

DCK's TEXT $211E–$2202 erases/draws XOR points and uses six-byte x/y/speed
records. Its setup at $3A92–$3C48 patches the movement instructions for right,
left, down or up. This example reimplements those four behaviours in vasm
syntax with explicit mode kernels and bounded wrap; it does not embed or
relocate the original executable.

GodLib owns Platform, Screen, VBL, IKBD and double buffering. C orchestrates
setup/input and prepares the static background using existing GodLib graphics
kernels. Star initialization, movement and all point drawing/erasing are ASM.
No BLiTTER, raster interrupts or STE video features are required. The target
is an ordinary 68000 ST/STE; native tests used an STE at 8 MHz with German
TOS 1.62, 4 MB and PAL RGB. Physical hardware has not been tested.

Each display page keeps its own list of the previous word offsets and XOR
masks. Before rendering to that page again:

1. XOR its saved points a second time to restore the exact background.
2. Advance the current stars unless paused.
3. XOR the new points and save that page's offsets/masks and actual count.

The saved old count is independent of the new requested count, so reducing
256 stars to 64 still erases every old point on both pages. A single shared
save list would leave traces with double buffering.

Points toggle the second bitplane (mask value 2 in the colour index). Background
indices 0/1/4 have bright partner colours at 2/3/6. All other bitplanes remain
unchanged. Two stars on the same pixel cancel by XOR parity, and erasing both
restores the original pixel; this is the expected XOR behaviour.

The optimized plot kernel reads a precomputed 160-byte row-offset table and
16 word masks. Division occurs only during initialization. Neither whole-screen
copies nor full-area clearing occur in ordinary animation; startup copies the
clean background into both display pages once. Pausing stops movement but still
runs the reversible erase/draw passes.

## CPU measurements

Hatari-HRDB, STE / MC68000 8 MHz / PAL RGB / German TOS 1.62 / 4 MB.
Each entry covers 32 completed **Erase + Advance + Draw** updates, with density
changes primed outside the measured batch. Cycles include ASM memory traffic
but exclude startup, GodLib input/screen waits and interrupt handlers.
Percentages use 160000 cycles per 20 ms PAL frame; seeds/wrap phases affect cost.

| Direction | 64 stars | 128 stars | 256 stars | 256-star time |
|---|---:|---:|---:|---:|
| Right | 11.1% | 21.5% | 42.4% | 8.48 ms |
| Left | 10.8% | 20.9% | 41.1% | 8.22 ms |
| Down | 11.4% | 22.2% | 43.7% | 8.73 ms |
| Up | 11.4% | 22.2% | 43.7% | 8.73 ms |

The normal-loop cadence check at the default 256-star/rightward setting
completed **5243 frames with zero missed VBLs: 50 FPS**. The R marker displays
elapsed rendering time, not an independent profiler. Measurements come from
emulation, not a physical Atari.

## Memory and verification

Star records occupy 1536 bytes; both saved XOR lists together use 2048 bytes.
The ASM module is 830 bytes including row/mask tables. GodLib's normal screen
buffers and other library state are separate. No additional bitmap/frame cache
is allocated.

- 12 direction/density profiles, each with exactly 32 native draw calls.
- 25 full-frame reference comparisons against a clean background plus a host
  XOR reconstruction: zero differing bytes.
- Every active star's coordinates after each batch checked against an
  independent modulo-wrap reference; inactive stars remain unchanged.
- 28 additional full-frame comparisons cover both display pages after numeric
  and arrow mode changes, repeated density changes and pause: zero differences.
- Pause/resume, keys 1–7, all arrows and clean exit passed.

Compact evidence: `profiling.json`, `verification.json`, native `preview.png`.
Temporary dumps/logs remain outside the repository.

```sh
make debug                       # /tmp/XORDBG.PRG and /tmp/XORDBG.map
python3 tools/check.py            # stock Hatari controls, both pages, cadence
python3 tools/profile.py          # Hatari-HRDB pixels, movement and CPU
```

Tools use the local hatari-debugging skill helpers. HRDB defaults to port 56001;
`XOR_HRDB_PORT` can override the client port when the emulator is mapped to
match. The control test sends explicit hexadecimal scancodes: Hatari parses
numbers with base detection and rejects a zero-padded decimal `08` as octal.
