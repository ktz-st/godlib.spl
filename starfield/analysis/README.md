# Starfield checks

Build `make debug` in the sample directory first. The scripts resolve symbols
from `SDBG.PRG` and run the release `STARS.PRG`; the executable code/data match
(the embedded ELF symbol metadata differs). Requires local Atari cross tools,
Hatari, Hatari-hrdb, TOS ROMs, and the installed hatari-debugging skill helpers.

- `verify-hatari.py [st-2.06|ste-2.06|ste-1.62]`: independent projection / planar
  reference versus the complete target field, sparse erase, count changes,
  pause/resume, clean exit. Writes `results[-configuration].json` and screenshots.
- `profile.py`: one fresh ST 8 MHz, 1 MB, TOS 2.06 Hatari-hrdb process per count.
  Includes dynamically generated machine code in the draw total. Writes
  `profile.json` plus ignored raw per-instruction captures.

Frame rate uses target GodLib VBL and completed-frame counters. CPU cost is
cycles per render/erase call averaged over the capture window, expressed as
milliseconds at 8 MHz and a share of one 160,256-cycle PAL frame. The small
window-boundary differences in the frame/VBL counts are not additional runtime
work. C bookkeeping and VBL/input overhead are outside the kernel totals.

`preview.png` was captured during normal playback. On this Hatari build, repeated
CPU debugger stops can leave unchanged static regions black in subsequent
screenshots, despite the correct text remaining in screen RAM and a correct
palette. The verification script now captures its preview before the stops.
