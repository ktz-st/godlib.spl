# ABC2 castle comparison

Same original RGB 320x200 source as the CryptoChrome comparison, resized from
`../castle-source.png` before any palette reduction. No changes to the water
or reflection example's existing assets/programs.

Local tool: `/Users/kriss/GCC.ELF/abc/abc2`, reports v2.11. Documentation:
`abc/readme.md`; source `abc/src/abc2.cpp`, `abc/src/ham.cpp`.

Run in `plain/`, and again in `floyd/` with the additional `-floyd` flag:

```
/Users/kriss/GCC.ELF/abc/abc2 ../source-320x200.png \
  -bpc 4 -atari -stf -quantize -cpu \
  -b castle.gfx -p castle.pal -preview tool-preview.png
```

Then run `python3 decode.py` in this directory. The delivered PI1 files wrap
the unmodified 32-byte palette and 32000-byte Atari planar output with the
standard mode word. The PNGs decode those actual outputs, rendering ST 3-bit
channels across 0..255. The 2x versions use nearest-neighbour enlargement.

Important distinctions:

- `-floyd` is applied in `ColorDepthQuantize444WithDitheringInt`, at the RGB888
  to RGB333 step for STF. It does not diffuse errors while matching each pixel
  to the final 16-colour palette. This differs from CryptoChrome's complementary
  solution-pair dithering.
- The current CPU `BestPaletteSearch` greedily adds palette entries, searching
  all 4096 RGB444 candidates for each entry after an initially black slot.
  The STF exporter then shifts RGB444 channels right by one. Thus palette
  fitting is not constrained to the 512 distinct STF colours throughout.
- `tool-preview.png` uses the internal RGB444 palette. It can differ from the
  actual STF export, so it is retained for analysis but is not the shown result.
- In these conversions, plain output uses 13 distinct rendered STF colours and
  Floyd output 14, despite the 16-entry/four-plane mode. Each exported palette
  has one duplicate pair and also has unused entries. No palette entries or
  pixels were manually replaced to conceal this behavior.

`results.json` records the actual palette words and colour counts. Original
outputs and conversion logs are retained in each variant directory. No ABC2
source or binary was modified.

## STE comparison

`ste-plain/` and `ste-floyd/` repeat the commands above with `-ste` instead
of `-stf`. They select one global palette of 16 colours from the STE's 4096
RGB444 colours. Both resulting images use exactly 16 distinct colours.
Dithering, when enabled, is applied at the RGB888-to-RGB444 stage.

`castle-ste-plain.png` / `castle-ste-floyd.png` decode the actual exported
palettes with the STE nibble order (`((n&7)<<1)|(n>>3)`). All 64000 pixels of
each decoded image match ABC2's native preview exactly. The `-2x.png` files
use nearest-neighbour scaling. `CASTLE-STE-PLAIN.PI1` and
`CASTLE-STE-FLOYD.PI1` contain the unmodified exported palette and bitmap.
