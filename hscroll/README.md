# STE horizontal hardware scrolling

```sh
make
make run
```

`HSCROLL.PRG` needs STE video hardware. Keep PANORAMA.BIN beside the executable. It shows
an automatically scrolling 640x200 panorama through a 320x200 viewport, with
a flying bird rendered as a masked GodLib sprite.
Space toggles automatic movement. With automatic movement off, use left/right
for X. Esc exits. Every 16th pixel is a white grid line, so
fine-scroll alignment and row drift are easy to see.

Startup compares masked sprites on a 384-pixel canvas (192-byte stride) with
an independent reference: 35 positions through CPU and blitter paths, including
all fine alignments and edge clipping. A failure displays its result code.
The test takes a few seconds on an emulated 8 MHz 68000.

The public setup is:

```c
Screen_Init(640, 200, eGRAPHIC_COLOURMODE_4PLANE, eSCREEN_SCROLL_H);
if (!gScreenClass.mpMemBase) return 1;
Screen_SetScrollX(x); /* 0..320 */
Screen_Update();
```

Four-plane Screen_Init always uses a 320x200 viewport; its dimensions describe
canvas storage. H requires STE video. Width 320 with H retains a 32-pixel reserve
(352 total); larger widths are used directly. V preserves the original height+32
allocation, so Screen_Init(320,400,4PLANE,V) creates 320x432 with Y=0..232.
H+V supports both directions, e.g. Screen_Init(640,400,4PLANE,H|V).
The existing void return type is unchanged; unsupported geometry leaves
mpMemBase NULL. Call Screen_DeInit before reinitialising an allocated screen.

Fine scrolling is supported in STE low resolution only. The address receives
`y * stride + (x / 16) * 8`. Register `$FFFF8265` receives `x & 15`. Register
`$FFFF820F` skips `(virtualWidth - 320) / 4` words at the end of a line, reduced
by four words for nonzero fine scroll because STE fetches one extra group.
Address and fine scroll are queued atomically and applied together in VBL.

All drawing canvases and Screen_GetpLogic/Physic retain the base of the full
virtual buffer. Draw in virtual coordinates, with that canvas's stride. The
hardware viewport offset does not shift the CPU drawing pointers. A background
can be drawn once; changing the viewport does not copy the whole screen.

Canvas-based planar sprite rendering supports the wider stride. The standalone
Blitter helpers now recognise Screen-owned buffers and use their full stride.
For custom buffers use the Blitter_*Canvas entry points; raw pointers outside
Screen retain the old 320x200 defaults. Font8x8 still assumes a 320-pixel screen.
Sprite_Create/Masks accept their existing 320-pixel source-image layout. Chunk lists retain 16-bit offsets and
cannot represent regions beginning beyond 65535 bytes.

Four-plane canvas widths must be multiples of 16 in 320..1328; allocated heights
must be 200..2047 (including the V reserve). Widths above 320 require H and STE.
X/Y are clamped to the allocated bounds. Every buffer starts on a 256-byte
boundary. Other colour modes retain their requested viewport dimensions.
The enlarged sScreenClass requires rebuilding code that accesses it.

The panorama is generated with the built-in image tool, then converted by
`prepare_assets.py` to a custom raw file (not a standard PI1): 16 big-endian ST
palette words, then 64000 bytes of interleaved four-plane pixels, stride 320.
`assets/panorama-st.png` is the exact 640x200 converted preview; the original and
prompt are kept in assets. Run `make assets` to regenerate the binary with Pillow.
The bird uses transparent colour 0 and white colour 15. Each logical buffer has
its own saved position; canvas blits restore the old rectangle from ScreenBack
before drawing the bird at its new world coordinates.

Run `make debug`, then `python3 analysis/verify-hatari.py` for the 640x232 grid
verification, and `python3 analysis/verify-panorama.py` for the actual artwork
and sprite verification.
The local hatari-debugging helper is required. The test checks sprite references,
registers and every displayed pixel at fine/coarse boundaries and simultaneous
X/Y offsets, then exit to TOS. Real STE hardware has not been tested.

Legacy allocation/clamp checks are available with
`make analysis/MODES.PRG && python3 analysis/verify-modes.py`: NONE, V, H and
H+V, explicit 640x200/320x400/640x400 geometry, buffer alignment, X/Y bounds,
line offset and invalid widths.

## Artwork conversion update

Generated scene artwork now uses **ABC2, STE RGB444, without dithering**.
See the [shared artwork guide](../tools/ARTWORK.md) for reserved colours,
regeneration, shared copies and validation. Snowfall retains eight background
colours to leave its snow bitplane free. Older ST screenshots and CPU results
above refer to their original artwork revision.
