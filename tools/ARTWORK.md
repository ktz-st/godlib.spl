# Generated scene artwork: ABC2 STE, no dithering

All seven original generated scene images now use ABC2 v2.11, with `-bpc 4
-atari -ste -quantize -cpu` and **no dithering option**. Each scene has one
16-entry palette selected from the STE's 4096 colours. Colour fitting starts
from the original RGB image, not a previously quantized review or PI1.

| Original artwork | Master output | Examples using it |
|---|---|---|
| coast, space, forest | `wipe/COAST.PI1`, `SPACE.PI1`, `FOREST.PI1` | wipe; coast also palsplit, wobble and flagwave |
| panorama | `hscroll/PANORAMA.BIN` | hscroll, splitscreenh |
| tower | `vscroll/TOWER.BIN` | vscroll, splitscreen |
| castle | `water/assets/CASTLE.PI1` | water, reflect |
| winter | `snowfall/assets/WINTER.BIN` | snowfall |

The castle master matches the approved `abc2-comparison/CASTLE-STE-PLAIN.PI1`
byte for byte. The old comparison candidates are retained for review, not used
as runtime assets.

Constraints required by existing examples:

- Every slide and scrolling scene reserves index 0 for black and 15 for white
  captions/sprites (`-forcecolor 15 fff`, black entry 0 is ABC2's default).
- Snowfall has **eight background colours**, using `-bpc 3`. Its fourth plane
  is reserved for live snow, with indices 8..15 all white. Index 7 is white for
  the heading and index 4 is a light blue for text/painting. The converter
  preserves the exact original air/solid silhouette, clear header and closed
  edges, so changing colours cannot change where the snow settles.
- Water regenerates the surface strips using the new indices. REFLECT receives
  the same new palette and reconstructs its source only from castle rows 0..110.
- Wobble regenerates its entire preshift cache from the updated coast.
- Palsplit calculates 16-level greys in the STE's linear component order, then
  encodes the nibble shuffle. Its ST fallback still calculates eight grey levels.

ABC2 exports raw Atari interleaved bitplanes and STE palette words.
`abc2_assets.py` decodes every output pixel and checks it against ABC2's own
RGB444 preview. It also verifies packing and records conversion arguments,
source hashes, palette values and colour counts in `*-st.png.json` sidecars.
Preview PNG filenames retain their old `-st` suffix for existing documentation
links, but their contents now show the STE result.

## Rebuild

Build `../abc/abc2`, or set environment variable `ABC2` to a compatible ABC2
executable. The Python steps also require Pillow. From this repository:

```
python3 tools/rebuild_artwork.py
```

This regenerates the seven scenes, copies shared master assets, recalculates
water/REFLECT/wobble data and builds the eleven affected examples (release and
symbol/debug builds). Ordinary per-example `make` targets also track the
converter and copied master assets. Generated files ship ready to run, so the
converter is needed only when rebuilding artwork.

The full 4096-colour gamut is visible on STE. Examples that also run on the
original ST still work with its coarser palette interpretation. Font/sprite
sheets already supplied as indexed art, procedural graphics, and Spectrum's
special multi-palette test data are not RGB scene quantization inputs; their
indices and diagnostic palettes are preserved.

Target verification for this asset revision is recorded in
`tools/abc2-verification.json`. Older per-example CPU measurements and ST/TOS
screenshots refer to the earlier artwork revision unless explicitly refreshed;
this is an artwork change, not a new CPU benchmark.

Later additions `lens` and `torch` reuse the castle RGB source: the lens uses
16 colours and the torch uses eight bright colours plus eight dim variants.
Both conversions omit dithering.

`spritemask` is a deliberate exception: it uses a curated shared palette and
a five-shade sky blended offline with ordered dithering. Its separate ABC2
foreground mask preserves opaque black at index 0. There are no raster
interrupts or per-frame gradient writes. See its [palette and masking guide](../spritemask/README.md).

The subsequently added `flagwave` example also uses the coast master. Its own
full-frame tests and CPU measurements are under `flagwave/analysis/`; it was
added after the ten-example ABC2 conversion report above.
