# Castle background generation

Generated using the built-in `image_gen` tool, not the fallback CLI.
Original tool output retained at:
`/Users/kriss/.codex/generated_images/01a09f6f-0177-7731-816b-78d8e1f6a93f/exec-c96259f6-e5c6-49fd-9fd4-9606d6aa83cd.png`

Project copy: `castle-source.png`. Atari conversion: `CASTLE.PI1`.
Final ST preview: `castle-st.png`.

## Submitted prompt

Use case: stylized-concept. Asset type: finished background for an Atari ST low-resolution 320x200 sixteen-colour game demo, landscape aspect ratio 8:5. Generate one beautiful classic pixel-art fantasy castle beside a lake at blue-hour twilight, with warm amber lit windows and subtle lavender sky. Large readable crenellated stone castle with several distinct towers in the upper-middle, distant hills behind the castle, simple vegetation confined ABOVE the waterline. CRITICAL COMPOSITION: a perfectly straight HORIZONTAL waterline exactly 60 percent down the image from the top, continuously across the FULL WIDTH, left edge to right edge. The entire bottom 40 percent must be uninterrupted open lake water, including BOTH bottom corners: no land, banks, rocks, reeds, foreground objects or shore protruding into that lower rectangle. The lake has a recognizable vertically mirrored reflection of the castle and sky directly below it, darker cool blue, with a few thin horizontal glints. Keep that reflection coherent and mostly calm because the game will animate the water afterwards by duplicating and skipping horizontal scanlines. Castle must fit completely in the top 60 percent; leave enough room above towers. Stylish 16-colour pixel-art economy with crisp readable clusters, restrained dithering, blue/teal shadows and warm gold accents; no photographs, no gradients requiring thousands of colours. Fill the whole canvas; no frames, no lettering, no logos, no watermark. Desired output composition scales exactly to 320x200; horizon y=120, water rows 120..199 across x=0..319.

The delivered composition uses a straight full-width waterline near 55.5% of
image height. The Atari conversion preserves it (surface y=111, animated lake
from y=112), satisfying the requested full-width horizontal lake.
