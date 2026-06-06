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

## Examples

| Directory | Output | Shows |
| --- | --- | --- |
| `audio` | `AUDIO.TOS` | Basic sample playback through GodLib audio. |
| `blitter` | `BLITTER.PRG` | Blitter API, sprite drawing, CPU/blitter toggle. |
| `cookiejar` | `COOKIJAR.TOS` | Reading Atari cookie jar values. |
| `font` | `FONT.PRG` | `Font8x8_Print` and coloured 8x8 font output. |
| `graphic` | `GRAPHIC.PRG` | `GraphicCanvas` primitives: pixels, lines, boxes and blits. |
| `iff` | `IFFSHOW.TOS` | IFF ILBM picture loading/display. |
| `joy` | `JOY.TOS` | IKBD joystick packets for joy0/joy1. |
| `lancemod` | `LANCEMOD.TOS` | ProTracker MOD playback through Lance Paula replay. |
| `mixer` | `MIXER.TOS` | GodLib software audio mixer and panning controls. |
| `mouse` | `MOUSE.TOS` | IKBD mouse position and button state. |
| `music` | `MUSIC.TOS` | Legacy SSD/music sample playback. |
| `picshow` | `PICSHOW.PRG` | Degas `.PI1` loading and screen copy. |
| `raw` | `RAWSHOW.PRG` | Uncompressed Amiga RAW picture display. |
| `screen` | `SCREEN.PRG` | Screen setup, palette and buffer update basics. |
| `sprite` | `SPRITE.PRG` | Basic sprite creation, mask creation and clipped drawing. |
| `spriteinput` | `SPRINP.PRG` | Sprite controlled by mouse or joy1, switchable with `1`/`2`. |
| `spritebg` | `SPRBG.PRG` | Sprite over a background with back-buffer restore and per-buffer dirty rect tracking. |
| `wizzcat` | `WIZZCAT.TOS` | ProTracker MOD playback through Wizzcat STE replay. |

## Notes

Some samples need local assets in the same directory as the program. Examples:

- `picshow/RGLOGO.PI1`
- `sprite/SPRITE.PI1`
- `spriteinput/SPRITE.PI1`
- `spritebg/RGLOGO.PI1` and `spritebg/SPRITE.PI1`
- `lancemod/LOSTPARO.MOD`
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
- `wizzcat`: `1` jumps to the first song position, `2` jumps to the last one, `Space` exits.
- `lancemod`: plays a MOD through Lance Paula; use the on-screen/console prompts.

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
