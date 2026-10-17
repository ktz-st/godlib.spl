# godlib.spl

Small example programs for [GodLib](../godlib), built for Atari ST/STE with
`m68k-atari-mintelf-gcc`, `vasmm68k_mot` and `libcmini`.

The examples are intentionally compact: each directory is a standalone sample
with its own `Makefile`, source file, assets when needed, and a `run` target for
Hatari.

## Quick start

Build one example:

```sh
make -C sprite
```

Run it in Hatari:

```sh
make -C sprite run
```

Clean it:

```sh
make -C sprite clean
```

Most examples exit with `Space`. Input-oriented samples usually print their
own controls on screen or in the console.

See the [demo effects guide](DEMO-EFFECTS.md) for rendering techniques, hardware
requirements and links to controls, CPU measurements and verification.

## Examples

| Directory | Output | Shows |
| --- | --- | --- |
| `audio` | `AUDIO.TOS` | Basic sample playback through GodLib audio. |
| `blitter` | `BLITTER.PRG` | Blitter API, sprite drawing, CPU/blitter toggle. |
| [`checker`](checker/README.md) | `CHKFX.PRG` | ST/STE rotating and zooming checkerboard, 68000 span renderer, gradient, speed/reverse controls and CPU profiling. |
| `chunky` | `CHUNKY.TOS` | Draw into a byte-per-pixel buffer, then convert to ST four-plane graphics. |
| `cookiejar` | `COOKIJAR.TOS` | Reading Atari cookie jar values. |
| [`fastscroll`](fastscroll/README.md) | `FSCRL.PRG` | ST/STE plain BUGSY text scroll, one ASM shift pass and a 27-line planar strip, four speeds. |
| `font` | `FONT.PRG` | `Font8x8_Print` and coloured 8x8 font output. |
| `graphic` | `GRAPHIC.PRG` | `GraphicCanvas` primitives: pixels, lines, boxes and blits. |
| `hscroll` | `HSCROLL.PRG` | STE pixel-accurate horizontal scrolling on a larger virtual canvas, with vertical scrolling and sprite stride checks. |
| `iff` | `IFFSHOW.TOS` | IFF ILBM picture loading/display. |
| `joy` | `JOY.TOS` | IKBD joystick packets for joy0/joy1. |
| `lancemod` | `LANCEMOD.TOS` | ProTracker MOD playback with four activity bars in Amiga LRRL stereo order. |
| `leonard` | `LEONARD.TOS` | LeonardMod 12.5/25 kHz playback with four channel activity bars. |
| [`lens`](lens/README.md) | `LENS.PRG` | ST/STE 64x64 mouse/automatic magnifying lens over the castle, ASM inverse sampling and lookup C2P, measured CPU cost. |
| `pcmblock` | `PCMBLOCK.TOS` | Four-channel block mixer at 12.5/25 kHz, loops and ASM self-test. |
| `pcmlayer` | `PCMLAYER.TOS` | Four-layer mixer at 12.5 kHz: two loops and two one-shots. |
| `mixer` | `MIXER.TOS` | GodLib software audio mixer and panning controls. |
| `pcmvoice` | `PCMVOICE.TOS` | PCM Voice three-channel mixer, loops, queued one-shots, CPU raster and core self-tests. |
| `pcmframe` | `PCMFRAME.TOS` | PCM Frame three-channel SFX mixer, overlap and looping. |
| `mouse` | `MOUSE.TOS` | IKBD mouse position and button state. |
| [`nibble`](nibble/README.md) | `NIBBLE.PRG` | ST/STE original TLB NIBBLE sine scroller: 68000 ASM, LOST16 font, two waveforms, straight mode and measured CPU cost. |
| `music` | `MUSIC.TOS` | Legacy SSD/music sample playback. |
| `palsplit` | `PALFX.PRG` | ST/STE Timer B palette split: colour top half, greyscale bottom half, preloaded MOVEM palette write. |
| [`phasescroll`](phasescroll/README.md) | `PHASE.PRG` | STE tile-map phase scrolling: original scanwalk ASM, BLiTTER phase blocks, four speeds and a fixed HUD. |
| [`planemix`](planemix/README.md) | `LAYFX.PRG` | ST/STE two independent checkerboard bitplanes, palette translucency, per-layer freeze and measured CPU cost. |
| `picshow` | `PICSHOW.PRG` | Degas `.PI1` loading and screen copy. |
| `rasters` | `RASTR.PRG` | ST/STE animated raster bars: VBL-prepared list and 49 Timer B single-colour changes per frame. |
| `raw` | `RAWSHOW.PRG` | Uncompressed Amiga RAW picture display. |
| [`scroll8`](scroll8/README.md) | `SCROLL8.PRG` | ST/STE ASM 8x8 text scrollers using the GodLib font at 2 px/frame: MCoder 2560-byte cache / 4.12% CPU; optimized Griff 5376 bytes / 2.69% CPU on ST 8 MHz. |
| `screen` | `SCREEN.PRG` | Screen setup, palette and buffer update basics. |
| [`snowfall`](snowfall/README.md) | `SNOW.PRG` | ST/STE falling and accumulating snow over a generated winter scene, using Jason J Railton's planar ASM simulation. |
| [`spectrum`](spectrum/README.md) | `SPEC.PRG`, `SPEC4K.PRG` | ST/STE Spectrum 512/4096: original picture, full-colour test card, cycle-exact ASM palette stream. |
| `splitscreen` | `SPLIT.PRG` | STE Timer B split: 160 scrolling terrain rows and an independent fixed 40-row HUD. |
| `splitscreenh` | `SPLITH.PRG` | STE top HUD: fixed 16 rows above 184 horizontally scrolling rows, with independent palettes, fine scroll and stride. |
| `sprite` | `SPRITE.PRG` | Basic sprite creation, mask creation and clipped drawing. |
| `spriteinput` | `SPRINP.PRG` | Sprite controlled by mouse or joy1, switchable with `1`/`2`. |
| `spritechunk` | `SPRCHUNK.PRG` | Sprite background restoration with separate chunk lists for both screen pages. |
| [`spritemask`](spritemask/README.md) | `MOON.PRG` | Dithered bitmap night sky, orange/yellow crescent and twinkling stars using GodLib CPU/blitter sprites, independent ABC2 foreground mask and per-page restore. |
| `spritebg` | `SPRBG.PRG` | Sprite over a background with back-buffer restore and per-buffer dirty rect tracking. |
| [`starfield`](starfield/README.md) | `STARS.PRG` | ST/STE demOS three-plane 3D stars: generated ASM pixel routines, sparse erase, 96–768 stars and CPU profiling. |
| [`torch`](torch/README.md) | `TORCH.PRG` | ST/STE mouse-controlled light mask over an ABC2 eight-colour castle, per-page plane restore and CPU profiling. |
| `vscroll` | `VSCROLL.PRG` | STE vertical scrolling over a generated 320x400 tower with a flying masked bird. |
| [`flagwave`](flagwave/README.md) | `FLAG.PRG` | ST/STE ASM waving picture: mouse delay queue, automatic sine, per-page column reuse and measured CPU cost. |
| [`reflect`](reflect/README.md) | `REFL.PRG` | ST/STE Missing Link REFLECT: original 68000 row-wave algorithm and a live reflection of the castle above the lake. |
| [`water`](water/README.md) | `WATER.PRG` | ST/STE Ugh intro-style lake waves: repeated/skipped rows under a generated castle, full-width water and surface glints. |
| `wipe` | `WIPE.TOS` | Three generated pictures, individual ST palettes and 39 wipe effects in a slideshow. |
| [`wobble`](wobble/README.md) | `WOBBLE.PRG` | ST/STE dynamic picture waves: cached fine shifts, MOVEM row copies, per-page reuse and CPU profiling. |
| `wizzcat` | `WIZZCAT.TOS` | Wizzcat MOD playback with four ASM activity bars and automatic workspace sizing. |

## Notes

Some samples need local assets in the same directory as the program. Examples:

- `picshow/RGLOGO.PI1`
- `sprite/SPRITE.PI1`
- `spriteinput/SPRITE.PI1`
- `spritebg/RGLOGO.PI1` and `spritebg/SPRITE.PI1`
- `lancemod/LOSTPARO.MOD` (copied by the `leonard` build as well)
- `wizzcat/QUICKIE.MOD`
- `raw/1.RAW`

The build system assumes this layout:

```text
<project_folder>/
  godlib/
  godlib.spl/
  libcmini/
```

Each sample links against `../godlib` and `../libcmini`, so build GodLib first
when changing library code.

## Installing the Linux Toolchain

On Linux, download the MiNT ELF toolchain packages into a temporary staging
directory and extract them into `/`. The extraction step needs `sudo` because
the archives install under system paths such as `/usr`.

```sh
mkdir -p /tmp/toolchain
cd /tmp/toolchain

wget -O binutils.tar.xz "https://tho-otto.de/download/mint/binutils-2.45-mintelf-20250812-bin-linux64.tar.xz"
wget -O gcc.tar.xz      "https://tho-otto.de/download/mint/gcc-15.2.0-mintelf-20250810-bin-linux64.tar.xz"
wget -O mintlib.tar.xz  "https://tho-otto.de/download/mint/mintlib-0.60.1-mintelf-20240718-dev.tar.xz"
wget -O fdlibm.tar.xz   "https://tho-otto.de/download/mint/fdlibm-20240425-mintelf-dev.tar.xz"
wget -O gemlib.tar.xz   "https://tho-otto.de/download/mint/gemlib-0.44.0-mintelf-20240425-dev.tar.xz"

sudo tar -C / -xJf binutils.tar.xz
sudo tar -C / -xJf gcc.tar.xz
sudo tar -C / -xJf mintlib.tar.xz
sudo tar -C / -xJf fdlibm.tar.xz
sudo tar -C / -xJf gemlib.tar.xz

rm -f /tmp/toolchain/*.tar.xz
```

Install `vasm` as well:

```sh
mkdir -p /tmp/vasm
cd /tmp/vasm

wget -O vasm.tar.gz "http://sun.hasenbraten.de/vasm/release/vasm.tar.gz"
tar -xzf vasm.tar.gz

cd vasm
make CPU=m68k SYNTAX=mot
make CPU=m68k SYNTAX=std

sudo install -m 0755 vasmm68k_mot /usr/local/bin/vasmm68k_mot
sudo install -m 0755 vasmm68k_std /usr/local/bin/vasmm68k_std
sudo ln -sf /usr/local/bin/vasmm68k_std /usr/local/bin/m68k-atari-vasmm68k_std

cd /
rm -rf /tmp/vasm
```

## Building GodLib

Clone GodLib into the expected project layout:

```sh
PROJECT_FOLDER=<project_folder>
git clone git@github.com:ktz-st/godlib.elf.git "$PROJECT_FOLDER/godlib"
```

Build it with `make`:

```sh
make -C "$PROJECT_FOLDER/godlib"
```

## Building libcmini

The samples expect libcmini to be installed in:

```text
<project_folder>/libcmini
```

Build it from the upstream source:

[freemint/libcmini.git](https://github.com/freemint/libcmini.git)

Suggested checkout layout:

```text
<project_folder>/
  src/libcmini/
  libcmini/
```

Clone, build with the MiNT ELF toolchain, and install:

```sh
PROJECT_FOLDER=<project_folder>
mkdir -p "$PROJECT_FOLDER/src"
git clone https://github.com/freemint/libcmini.git "$PROJECT_FOLDER/src/libcmini"
make -C "$PROJECT_FOLDER/src/libcmini" COMPILE_ELF=Y
make -C "$PROJECT_FOLDER/src/libcmini" COMPILE_ELF=Y PREFIX="$PROJECT_FOLDER/libcmini" install
```

The important installed files for these examples are:

```text
<project_folder>/libcmini/include/
<project_folder>/libcmini/lib/mshort/mfastcall/libcmini.a
<project_folder>/libcmini/lib/mshort/mfastcall/crt0.o
<project_folder>/libcmini/lib/mshort/mfastcall/minicrt0.o
```

## Input reminders

- `spriteinput`: `1` selects mouse, `2` selects joy1, joy fire recentres, `Space` exits.
- `spritebg`: same input as `spriteinput`, plus background restore from the back buffer.
- `wizzcat`: four ASM activity bars, `V` hides/shows them, `F1` shows replay time, `1`/`2` jump to first/last song position, `Space`/`Esc` exit. See [its README](wizzcat/README.md).
- `lancemod`: plays a MOD through Lance Paula with STF_DEMO activity bars; F1 toggles the replay CPU indicator, V hides/shows bars, Space/Esc exits. See `lancemod/README.md`.
- `leonard`: uses the same four-bar display with GodLib LeonardMod + ProTracker; 12.5/25 kHz, dynamic ST-RAM workspace, F1 CPU/V bars/Space or Esc exit. See `leonard/README.md`.

## Project style

These programs are examples, not a shared framework. Prefer keeping each sample
self-contained, easy to copy, and close to the GodLib API it demonstrates.

## Notes for AI Agents

When working on this repository, treat `godlib.spl` as a collection of small,
standalone examples for the sibling `godlib` checkout. Keep changes narrow and
avoid turning the examples into a shared framework unless the user asks for it.

Useful defaults:

- Build GodLib with `make -C <project_folder>/godlib` after changing library code.
- Build one sample with `make -C <project_folder>/godlib.spl/<sample>`.
- Use the existing sample directories as patterns before inventing new setup code.
- Keep generated Atari binaries and local run artifacts out of source changes unless
  the user explicitly asks for them.
- Preserve Atari-specific assumptions: 320x200/320x240 screen buffers, planar
  graphics, big-endian data, IKBD input, VBL timing, and ST/STE hardware limits.
- If editing sprite/background examples, be careful with dirty rect handling and
  per-buffer state; logical, physical and back buffers can intentionally differ.
- Prefer ASCII text in source and README files unless existing content needs
  otherwise.



PCM mixer names and migration from the historical names are documented in
[`godlib/audio/pcm-mixers.md`](../godlib/audio/pcm-mixers.md).

Generated RGB scene artwork normally uses [ABC2, STE colours, no dithering](tools/ARTWORK.md).
The [moon example](spritemask/README.md) uses an intentionally dithered sky
and an independent ABC2 foreground mask.

LanceMod, Leonard and Wizzcat also support **O** to switch between their four
activity bars, four ASM traces, two ICE XY plots, separate stereo traces and
a single mono trace `(L+R)/2`; **V** hides/shows the selected visualizer.
See [oscilloscope API and verification](../godlib/music/modscope.md).
