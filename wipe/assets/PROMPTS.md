# Generated artwork

Created with the built-in image generation tool. Original outputs were copied
into this directory; no external image service or API-key workflow was used.

The exact shared prompt was:

> Create one landscape illustration for an Atari ST slideshow. [SCENE] Wide 8:5 composition, crisp 1990s demoscene pixel art aesthetic, large readable shapes, tasteful ordered dithering, no text, no borders, no watermark. Restrict colors to this common 16-color palette: #000000 #222244 #444466 #666688 #8888AA #AAAACC #CCCCEE #EEEEEE #EE4444 #EEAA44 #EEEE66 #448866 #66CCCC #4466CC #AA66AA #AAAA66. Image will be downsampled to 320x200 pixels; keep details bold and recognizable.

Each call replaced [SCENE] with:

- `coast.png`: A lighthouse on jagged coastal cliffs, turquoise sea, distant mountains and a glowing sunset.
- `space.png`: A small retro spaceship above a mysterious ringed planet, a moon and a bright starfield.
- `forest.png`: An ancient stone tower in a luminous pine forest, a winding river and distant blue mountains.

After generation, the slideshow was changed to use each image's own palette:
the transition goes to black before changing colours. `prepare_assets.py`
therefore selects a separate ST palette per scene, reserving black and white.
The `*-st.png` files preview those final palette conversions.
