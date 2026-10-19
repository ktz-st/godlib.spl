# GodLib GEM/AES file selector

`FILESEL.PRG` exercises the existing `File_Selector()` from `godlib/file`, using
TOS's GEM file dialog. Select a file with the mouse or enter its name and press
Return. The example shows the returned full path, file size and a read-only
preview of up to 160 bytes (control/non-ASCII bytes become dots).

```sh
make
make run       # STE, 1 MiB, RGB, German TOS 1.62
```

After closing the dialog:

- O / Space: reopen with the previous directory and filename.
- T: reopen with `*.TXT` filter.
- A: reopen with `*.*` filter.
- Q / Esc: return to TOS.

Inside the dialog use **OK** to select or **ABBRUCH** (Cancel on German TOS)
to cancel. `HELLO.TXT` and `data/SECOND.TXT` are small test files;
`data/IGNORE.DAT` demonstrates the filter. The selector itself needs no resource
file. The example never writes to selected files.

## Integration boundary

This is the **system selector**, not GodLib's separate `GuiFS` widget system.
`File_Selector` chooses AES fsel_input/fsel_exinput according to AES version and
handles appl_init/appl_exit. `sFileIdentifier` retains directory, mask and filename;
`File_Identifier_ToFullName` returns an allocated string to free with mMEMFREE.
A positive selector result means OK, not necessarily that the file exists;
File_Open/File_GetSize must still be checked. Cancel opens no file.

**Keep the `.PRG` extension.** Under TOS 1.62, launching this as a text-mode
`.TOS` displays the dialog and accepts keyboard entry, but mouse clicks do not
reach its buttons. Launching as a GEM `.PRG` makes mouse selection/cancel work.

This example leaves GEM in charge of the display, mouse and interrupts. It uses
Memory_Init and File_Identifier_Init, and deliberately does **not** call
Platform_Init, Screen_Init or IKBD_Init. Do not call AES blindly while a game
owns custom screen buffers, IKBD or raster interrupts: restore a GEM-compatible
state first. This example tests the dialog on the desktop, not a live-game handoff.

## Verification

`make check` runs the release PRG in Hatari (STE 68000 / 8 MHz / 1 MiB / RGB PAL /
German TOS 1.62). It checks mouse cancellation, mouse selection, exact returned
path/size/preview, opening DATA, `*.TXT` versus `*.*`, repeated dialogs and clean
keyboard exit. The fixture hashes must remain unchanged. Evidence is saved in
`analysis/verification.json` and the PNG screenshots beside it.

The local macOS harness needs clang, SDL2/pkg-config, Pillow and the installed
hatari-debugging skill helper. A temporary SDL helper sends mouse motions to
only the child emulator; clicks use Hatari's normal double-click event. Atari
memory is read for assertions, never patched to simulate selector results.
Use `FSEL_HATARI` to override the native Hatari executable path; a launcher shell
can strip DYLD_INSERT_LIBRARIES and disable mouse injection. Normal builds and
manual use need only the cross compiler and GodLib/libcmini.
