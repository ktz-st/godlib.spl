# Asset / Linkfile — loose files, archives and compression

`ASSETS.PRG` displays the ABC2 STE castle, prints with a loaded BFB font, and
animates three masked sparks from an eight-frame BSB sprite block. The three
sources contain the same assets and use the same `AssetClient` consumers:

| Key | Source | Files on disk |
| --- | --- | --- |
| **1** | Directory package | `UNLINK/SCENE/CASTLE.PI1`, `FONT.BFB`, `SPARKS.BSB` |
| **2** | Raw linkfile, loaded into RAM | `DATA/SCENE.LNK` |
| **3** | Whole linkfile compressed with GodPack | `DATA/PACKED.LNK` |

It starts in mode 3. **R** unloads/reloads the selected source; **U** unloads it;
**Escape** exits to TOS. Keep the DATA and UNLINK folders beside the PRG when
copying this example. Missing data displays an error; restore it and press R.

The package contains **44,129 bytes** of asset payload. With its FAT/alignment,
the raw LNK is **44,328 bytes**; the GodPack file is **25,775 bytes**, about **42%**
smaller. Compression is of the entire archive, not separately packed members.
Both linkfile modes retain the unpacked archive in RAM, so compression reduces
disk size, not the resident asset size. The source image/palette is reused from
`reflect/assets/CASTLE.PI1`; the font is GodLib's 8x8 glyph set, and prepare.py
constructs the masked animation frames offline.

## Build

```sh
make assets    # regenerate PI1/BFB/BSB, LNK and packed LNK
make
make run
make check
```

`prepare.py` uses the existing host TOOLBASE `MAKELINK` implementation and native
`godpack`, located through TOOLBASE's host-tool resolver. Its manifest is
`assets/build.json`. Archive members are at the root with short uppercase names;
no nested-folder or per-member-compression claims are made by this example.

## Runtime ownership

The example explicitly initializes `PackageManager`, the relocator registry and
BFB/BSB relocators. It does not require rebuilding Platform with the optional
`dGODLIB_PACKAGEMANGER` bootstrap flag. A static ASSETDEMO context hosts four
clients: picture, font, sprites, plus a second consumer of the same font.

`PackageManager_Load` / `Update` resolve files, invoke extension relocators, and
bind the client pointers/callbacks. The application never manually relocates the
BFB/BSB after the loader has already done so. PI1 is raw data with no pointers;
no PI1 relocator is needed. All sources share its existing palette.

Directory mode owns separate file allocations. In RAM linkfile modes, asset
pointers are borrowed addresses inside the unpacked archive. Do not free these
members separately. Unload first notifies clients and clears their pointers,
then delocates assets and frees the package. The background copied into ScreenBack
is independent screen storage. Rendering uses existing GodLib canvas sprite/font
kernels; the C code schedules frames and draw commands.

The panel checks hashes of the picture and the font/sprite graphics and masks
against the first load; RAM archive modes also check that member pointers lie
inside the archive. Unload checks that all client pointers are null and the
largest free TOS block returns to its baseline. This is a lifecycle check, not a
claim that GodLib's optional allocation counters track this release build.

Integration fixes in GodLib:

- Multi-client unload callbacks use the current client's asset, avoiding access
  through the already-cleared head client.
- Removing a non-head same-file client walks `mpNext`, rather than the context
  list's different link field.
- LNK packages now report their file count and mark loaded/unloaded asset bits.
- The earlier AssetClient_DeInit context-reference balancing repair is exercised
  here with shared clients and zero final context references.

## Verification and limits

`make check` uses disposable copies on **STE / 68000 / 8 MHz / 1 MiB / German
TOS 1.62**. It checks:

- 28 native cases: target GodPack decompression equals the entire raw archive
  byte for byte; disk-backed LNK reads, raw-RAM members and packed-RAM copies all
  match every loose file. Missing files/members, metadata, pointer ownership,
  free-block recovery and three-client callback/removal/refcount paths are covered.
- Interactive package switching, rendering PI1/BFB/BSB, automatic relocation,
  equal hashes across three sources, shared-font clients, repeated reload/unload,
  missing-pack retry, balanced callbacks and clean exit to TOS.

Evidence: `analysis/verification.json`, `packed.png`, `raw.png`, `loose.png` and
`unloaded.png`. These are emulator functional tests, not CPU measurements.
The bundled build outputs are trusted assets. Legacy LinkFile/relocator entry
points are not general validators for arbitrary malformed archives or sprite
files. Recursive package traversal and per-member compressed RAM packages are
outside this sample's scope.
