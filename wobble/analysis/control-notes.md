# Control hscroll investigation

Inspected `GCC.ELF/stos/CONTROL/EXTENSIO.NS/CONTROL.EXW`, Control V3.06b,
Copyright L.J.Greenhalgh, 1996. This is a TOS-format STOS interpreter extension,
with a 28-byte header and 26,290 text bytes. The original file is unchanged.
`inspect-control.py` reproduces the SHA-256, table lookup and disassembly;
`control-addresses.json` and `control-hscroll.s` record the findings.

All offsets below are TEXT-relative. File offset = TEXT offset + $1c.
A runtime address would be the extension's loaded TEXT base plus the offset;
no STOS runtime address is claimed from this static inspection.

- Tokenized `SOURCE/WOBBLE.BAS` calls `EXT W:$a8`. The keyword prefix in the
  extension dictionary is $a7. The dispatch table at file $266, indexed by the
  stored command token minus $80, points to TEXT $1a2c (file $1a48).
- $1a2c..$1aa6 parses the five parameters: screen, first/last Y, plane mask,
  signed pixel count. Y end is inclusive. The scanline pitch is hardcoded 160.
- Negative counts branch to the left-shift core at $1aa8. Positive counts branch
  to the right-shift core at $1c70. Zero skips the scroll.
- The generic left path, e.g. $1ac8 onward, reads individual plane words,
  LSL.L shifts them, ORs a carry from the previous group, stores the result,
  SWAPs to extract the next carry, and steps backwards by eight bytes.
  The right path uses LSR.L, a temporary address register and forward stepping.
  Twenty word operations are expanded per selected plane.
- Exactly one pixel has dedicated paths at $1c0a (ROXL.W) and $1e1a (ROXR.W).
  Each clears the X flag and performs an unrolled chain over the selected plane.
- The hscroll region ends at $1e7e. It accesses ordinary screen RAM and has no
  blitter-register access or branch through the `enable blit` flag. Control's
  documentation lists blitter use for bigcopy, bigcls, turbocopy and some image
  operations; it does not list hscroll. This hscroll is a CPU operation.

The BASIC wobble uses an array `sin(rad(i))*8`, i=0..180, and cycles its index
through 0..179. Before shifting the 200 individual lines it copies the centre
of its source image (X=48..256, 208 pixels wide) into the work screen. The index
advances once per line, hence 200 mod 180 = 20 positions between successive
frames. The old GodLib sample advanced only 2 positions of a full 256-entry sine
per rendered update, and rendered about 8.3 updates/s by default. Its animation
was therefore much slower in time as well as expensive to draw.

This investigation does not establish Control's actual frame rate. No STOS
benchmark is reported. It confirms the algorithm and explains why replacing
our renderer with its generic CPU shifter would not itself remove the per-word
shift work. The revised GodLib renderer instead uses a static-source preshift
cache and MOVEM copies, retaining the original full 320x200 picture. It also
uses an eight-step-per-VBL phase (0.64 seconds per full cycle at 50 Hz), so a
missed rendered frame cannot slow the motion's time base.
