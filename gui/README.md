# Native GodLib GUI and GuiFS

`GUI.PRG` is a 320x200 four-plane ST/STE example of GodLib's own widgets,
renderer, hash-tree bindings, line editor and file selector. It runs outside
GEM/AES, with a mouse cursor drawn by GodLib on both screen pages.

The control panel provides:

- A NAME text field: click, type, use Backspace/Delete/arrows, Enter or Tab to
  finish; Esc leaves editing (the native editor does not roll back typed text).
- A LEVEL slider from 0 to 100: drag the handle, click the track or hold arrows.
- APPLY displays a greeting, RESET restores ATARI and level 50.
- FILES opens a GuiFS dialog; X exits cleanly to TOS.

Button captions are centred. Text fields use vertically centred, left-aligned
text with a 4-pixel left margin.

In the selector, click a file and SELECT to accept, or CANCEL to return. A `>`
prefix marks a directory; click it to enter. UP goes to the parent directory.
The filename, directory, drive and mask fields are editable (accept with Enter).
The initial folder is DATA and the mask is `*.TXT`; change it to `*.*` to include
IGNORE.DAT. Drag/click the vertical scrollbar to see rows below the viewport.
The DATA fixtures include enough files to scroll, SUB/SECOND.TXT and an empty
folder. The example only selects a path; it never modifies the chosen file.

## Build and run

```sh
make
make run
```

Output: **GUI.PRG**. Use German STE TOS 1.62 for the supplied run target.
GUI.PRG embeds its font and cursor. Keep DATA next to it to explore the fixtures;
other drives/directories can also be browsed. `make assets` regenerates the cursor and copies the shared 6x6 font using
`prepare.py`; normal builds use the supplied assets. Normal execution does not require
Python, GUIBUILD or an external GUI definition file.

## Integration

`gui.c` constructs native writable `sGuiData` with windows, button styles, fills,
buttons, sliders and cursor/font assets. `Gui_DataAdd()` registers widget events
and string clients and opens the desktop window. A hash-tree string variable
stores an `sString*`; numeric slider bindings use S32 vars for value/min/max/steps.
Small hash-tree variables store their contents internally, so initialization
explicitly publishes their values with `HashTree_VarWrite()`.

The loop calls `Gui_Update()`, `Screen_Update()`, `IKBD_Update()` and
`RenderGui_Update(Screen_GetpLogicGraphic())`. Text/glyph/fill/sprite rendering
uses existing GodLib graphics routines; there is no replacement pixel renderer.
The font is the same 6x6 sprite font used by the cutscene example. The 16x16
cursor has an explicit mask so its dark outline remains opaque.

GuiFS expects the library's existing widget/event names: WND_FS, WND_FILELIST,
BUTT_FS_OK/CANCEL, BUTT_DRIVE, BUTT_FILEPATH, BUTT_FILENAME, BUTT_FILEMASK and
BUTT_FOLDERBACK, with GUI\\FS string bindings. The native windows supplied here
satisfy those bindings. `GuiFS_Open()` queues the dialog; `sGuiFSInfo.mpCB` receives
its accepted/cancelled result. SELECT/CANCEL have native GUI close actions.

Cleanup stops the GUI loop, removes application callbacks, releases GuiFS rows,
DTA storage and strings, unregisters GUI data/bindings and releases the font
before restoring Screen/Platform. The native objects themselves are static;
do not relocate or free them as serialized GUI data.

## Library repairs exercised

- GuiFS dynamic rows now have working modern hash-tree click bindings. Directory
  entry, file-name selection and live mask/path edits work.
- GuiFS publishes its small string-pointer variables correctly and writes the
  selected filename as an `sString*`, rather than copying a string descriptor into
  a pointer slot. NULL result callbacks are safe.
- Dynamic controls, row event clients/vars and DTA buffers are released on rebuild
  and DeInit; original file-window controls are restored. Empty lists reset scroll
  extent. Enumeration restores the previous GEMDOS DTA and allocations/counts are
  bounded before publishing controls.
- Closing nested windows sends CLOSE events, rather than OPEN events; a closed
  file list is not unnecessarily rebuilt.
- The renderer consumes slider redraw counters and repaints covering windows
  when lower widgets change, preventing controls from leaking through the dialog.

## Verification

```sh
make check
```

`analysis/verify.py` runs GUI.PRG at 8 MHz / 1 MiB / German TOS 1.62. It sends real
SDL mouse movements/buttons to the native Hatari child using a test-only input
helper, and IKBD keyboard events. It checks text editing, button callbacks, slider
arrows/drag/clamps, reset, file paths, filtering, nested/empty folders, scrolling,
repeated reopen/cancel, stable event-variable ownership, cursor clipping and exit.
Input fixture hashes are checked afterward. Result/executable hash:
`analysis/verification.json`; screenshots are stored beside it. The macOS input
helper requires clang, SDL2/pkg-config and the local Hatari helper; it does not
patch Atari RAM or form return values. Build/run of the PRG uses the usual cross
toolchain and does not depend on that test helper.
