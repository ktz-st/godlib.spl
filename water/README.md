# Castle water / Ugh intro waves

`WATER.PRG` is a standalone GodLib example for Atari ST/STE, PAL 320x200,
68000 at 8 MHz, 1 MB RAM. A generated castle and its lake reflection use one
16-colour STE palette. The waterline is horizontal across the entire screen;
there is no foreground land inside the lake.

The castle/shore occupy rows 0..110, the flat surface is row 111, and the
animated full-width lake occupies rows 112..199. The source asset is also
available independently as `assets/CASTLE.PI1`.

```sh
make -C /Users/kriss/GCC.ELF/godlib.spl/water
```

Controls:

- Space: pause/resume.
- `N`: pause and advance by exactly one wave tick.
- `W`: toggle animated water / the original still picture.
- `1`, `2`, `3`: one, two or four wave ticks per VBL; default one.
- Esc: restore TOS.

## Wave model

This follows `ugh.agt/src/openugh/intro_water_wave.h` and
`mapRenderIntroWater()` in `ugh.agt/src/openugh/map.c`, rather than the older
phone port's horizontal water shifter. That intro recreates the Amiga
`LAB_07FC` Copper table using repeated and skipped source scanlines:

- modulo 160 with 40 fetched bytes: normal advance by one source line;
- modulo -40: repeat the source line;
- modulo 360: skip ahead by two source lines.

The 24 WAIT-distance/advance entries and their 84-tick cycle are retained.
The original AGT scene has water at y=240..255; this example moves the start
to y=112 and extends the same event sequence across 88 rows. The final hold
is moved from y=253 to y=197, keeping the original final-three-line rule.
Source reads are clamped to the lake, so no castle/shore line can appear in it.
The wave's period is 1.68 seconds at the default 50 Hz tick rate.

The surface additionally uses a three-frame glint sequence 0,1,2,1, changing
every five ticks (100 ms at default speed), like Ugh's three-frame surface
animation. These frames come from our own generated image's surface row with
small horizontal phase shifts; no original Ugh artwork is included.

## Renderer

All 84 source-row maps are built offline into `assets/ROWS.BIN`, followed by
identity and invalid-history tables. They occupy 15,136 bytes. C selects a
map and advances time from the GodLib VBL counter; the drawing is 68000 ASM.

After the two pages receive the clean picture at startup, only the 88 lake
rows and the one surface row are candidates for writes. The renderer reads
from the immutable embedded picture, never from a previously distorted live
page. Each page has its own previous row-map and surface pointers. A row with
an unchanged source selection is reused; changed rows use four 40-byte MOVEM
copies. This preserves complete bitplane groups and all 320 pixels of width.

There is no runtime per-pixel C drawing, bitmap preshifting, full-screen copy,
blitter requirement or raster/timer owner. Normal GodLib double buffering
presents the previous completed frame. The effect works on an ordinary ST as
well as STE; the lake's darker colour treatment is part of the artwork.

## Artwork

`assets/castle-source.png` was generated with the built-in imagegen tool.
The complete generation prompt and provenance are in `assets/PROMPT.md`.
The generated image placed its straight waterline slightly above the requested
60% position; the converter preserves its composition and uses the observed
surface at y=111 after resizing, rather than distorting the castle to move it.

`tools/prepare.py` resizes to 320x200 and uses ABC2 to select 16 colours from
the STE RGB444 gamut, without dithering, then emits four-plane Degas data.
This is the approved ABC2 STE conversion, with black at index 0. `assets/castle-st.png` previews that final palette.
The 88-row water map and three surface lines are generated at the same time.

## Checks and profiling

```sh
make -C /Users/kriss/GCC.ELF/godlib.spl/water debug
python3 analysis/verify-model.py
python3 analysis/verify-hatari.py
python3 analysis/profile.py
```

The model check independently reconstructs the WAIT/modulo event stream for
all 84 states, checks source bounds and the identity table, and compares the
constants with the local Ugh header when that checkout is available. A clean
build and target execution have no dependency on the Ugh project.

Hatari verification compares every one of the 32,000 screen bytes at eight
wave states, after still-picture toggling, stepping and while animating over
both pages. It checks that rows 0..110 remain identical, verifies phase against
VBL time, and exercises pause, speed controls and return to TOS. Configurations
are ST/TOS 2.06, STE/TOS 2.06 and STE/TOS 1.62, all 8 MHz with 1 MB RAM.

Profiling uses a fresh Hatari-hrdb process per mode and includes the ASM water/
surface work plus C map selection. Initial loading/copying, main-loop tick
advancement, VBL and keyboard overhead are outside these kernel totals.
Update rate is obtained from target frame/VBL counters, not host wall time.
These are emulator measurements, not a physical Atari benchmark.

### Measured on emulated ST 8 MHz, 1 MB, TOS 2.06

| Mode | Draw + map selection | PAL frame budget | Water rows copied/reused | Updates/s |
|---|---:|---:|---:|---:|
| Default, 1 tick/VBL | 4.68 ms | 23.4% | 42.8 / 45.2 | 50 |
| Fast, 4 ticks/VBL | 6.49 ms | 32.4% | 61.9 / 26.1 | 50 |
| Still picture | 0.60 ms | 3.0% | 0.0 / 88.0 | 50 |

The default frame redraws about 43 of the 88 water rows on average. All three
modes maintained 50 updates/s in the counter capture. The static castle/shore
never participates in the measured draw kernel. `analysis/profile.json` stores
the complete cycle and counter measurements.

Verification passed on all three configurations: 51 whole-frame comparisons
in total, both display pages, eight sampled wave states per machine, still-image
restoration, single-step, all speeds, VBL-driven animation and clean exit. The
independent model check covered all 84 wave states. See
`analysis/verification-summary.json` and `analysis/results.json`.

## Artwork conversion update

Generated scene artwork now uses **ABC2, STE RGB444, without dithering**.
See the [shared artwork guide](../tools/ARTWORK.md) for reserved colours,
regeneration, shared copies and validation. Snowfall retains eight background
colours to leave its snow bitplane free. Older ST screenshots and CPU results
above refer to their original artwork revision.
