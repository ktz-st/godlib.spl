# PcmVoiceMixer example

Build with `make`, run `PCMVOICE.TOS` on an STE/MegaSTE. Synthetic PCM is embedded;
there are no external asset files. GodLib Platform is initialized first and the
mixer is stopped and Platform restores TOS video/removes VBL users before screen
storage is freed.

- F1/F2/F3 toggle a loop on each channel.
- F4 plays three one-shot tones.
- F5 plays one tone followed by a queued second tone on channel zero.
- F6 stops all sources; buffered audio finishes shortly afterwards.
- F9 toggles the LanceMod-style palette-zero CPU stripe.
- Esc exits.

Startup runs the core/scheduler tests and reports PASS or FAILED. See
`../../godlib/audio/pcmvoice.md` for PCM constraints, packed-add arithmetic,
51-ms queue lead and recovery limitations.

`make debug` builds the symbol-bearing test target. Run
`python3 analysis/verify-hatari.py` for the automated STE test.

Set `HATARI_TOS` to a ROM path when the regression must use a specific TOS
version; otherwise it uses the current Hatari configuration.
The harness runs a copy named `PCMVOICE.TOS` in a private temporary directory.
This avoids a TOS 1.62 desktop fault seen after Pterm when the development
analysis directory itself is exposed as the Hatari GEMDOS drive; the identical
binary exits correctly from the isolated directory.
