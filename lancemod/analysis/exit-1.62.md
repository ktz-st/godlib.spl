# TOS 1.62: exit depends on program name and ROM variant

The original LANCEMOD.TOS saved before this change and the graphical version both
produce the same error after Space returns from playback, on Hatari 2.6.1,
STE / 1 MiB, using `TOS v1.62 (1990)(Atari Corp)(STE)(GB)[STE TOS, Rev 2].img`.

ROM SHA256: `7f8148b382c75aa4877324dac0efa030c213f5e7de07217d3f840abb4c60c8f4`.

```
WARN : Bus Error reading at address $4d4f44f2, PC=$e1fc9c addr_e3=e1fc9c op_e3=c68
```

No error is reported before Space. Full-screen comparisons on both pages and
all four activity channels, hide/show and F1 controls pass before exit. The error
also occurs with the original console-only example, so it is not introduced by
the activity-bar renderer. TOS 2.06 completes the exit check successfully.
Further comparison confirmed the filename dependency:

| ROM | Executable name | Rendering / controls | Return to desktop |
| --- | --- | --- | --- |
| GB Rev 2 | `LANCEMOD.TOS` | Pass | Bus error above |
| GB Rev 2 | `LM.TOS` | Runs, frame counter advances | Pass |
| German | `LANCEMOD.TOS` | Pass: 60 complete screen comparisons | Pass |
| German | `LM.TOS` | Runs, frame counter advances | Pass |

The short-name executable is a byte-for-byte copy of the same release binary;
there is no rebuild or code change between names. German ROM filename:
`TOS v1.62 (1990)(Atari Corp)(STE)(De).img`.

Use the German ROM or rename the executable to `LM.TOS` for GB Rev 2. This
comparison isolates the dependence on the name/ROM combination; the ROM's
internal root cause has not been investigated. The full verifier retains its
clean-exit assertion, so it still fails for the GB ROM and long name.

Evidence: `results-1.62-de.json`, `name-results.json`. Reproduce with
`python3 analysis/verify-hatari.py 1.62-de` and
`python3 analysis/verify-tos-names.py`.
