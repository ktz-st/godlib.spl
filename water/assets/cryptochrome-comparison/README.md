# Castle: CryptoChrome 16-colour comparison

Prepared from the original `../castle-source.png`, resized to 320x200 with
Lanczos in RGB, never from the previously quantized PNG/PI1.

Both variants use a single global 16-colour palette from the ST 512-colour
gamut. Each palette is fitted independently. The displayed PNGs are decoded
from the actual four-plane `pic_f0.pi1` outputs, not CryptoChrome's averaged
`preview.png`. Both contain exactly 16 RGB colours. The 2x copies use nearest
neighbour scaling, preserving the actual pixels and dither pattern.

- `castle-plain.png`: `-ccfields 1`, no dithering.
- `castle-dither.png`: `-ccfields 2`, one static dithered field; no frame
  alternation, temporal blending or extra colours.
- `CASTLE-PLAIN.PI1` / `CASTLE-DITHER.PI1`: standard 32034-byte PI1 files.

Tool: local `agtools/bin/Darwin/aarch64/pcs`, PhotoChrome/CryptoChrome v6.44.
Run separately in `plain/` and `dither/` (set fields to 1 or 2 respectively):

```
/Users/kriss/GCC.ELF/agtools/bin/Darwin/aarch64/pcs \
  -q -cd st -pc 4 -ccmode 1 -ccfields 2 \
  -ccpopctrl 0.5 -ccincap 512 -ccrounds 2 -ccthreads 1 -ccseed 1 \
  ../source-320x200.png
```

Then run `python3 decode.py` here. It decodes planar pixels, masks off the STE
extra palette bits (ignored by an ST), and renders the ST palette at full-range
RGB. It does not fit colours, change indices or apply its own dithering.
The pixel payload of each delivered PI1 is unchanged from PCS output.
`results.json` records colour counts and palettes. Native outputs/logs are
retained in each variant directory. Existing example assets/PRGs are unchanged.

CryptoChrome's `-h` explicitly documents `-ccfields 1` as normal/undithered and
`-ccfields 2` as dualfield/dithered. AGTCut is unnecessary for this static
comparison; it can also apply CryptoChrome solution-pair dithering when fed a
`.ccs` superpalette with `-ccf 2`.
