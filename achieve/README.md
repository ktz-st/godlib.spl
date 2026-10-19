# Achieve — players, scores, stats and awards

`ACHIEVE.PRG` demonstrates GodLib's real Achieve data model and persistence API,
with a small keyboard interface rendered using existing GodLib canvas/BFB font
routines. It does not replace the data model with application-side arrays.

## Controls

- **N:** enter a player name (up to 15 ASCII characters), Backspace to edit,
  Enter to select/create, Escape to cancel. Enter an existing name to switch
  back to that player's independent stats and awards. The demo allows 8 players.
- **Left/right:** adjust the simulated round score by 250, initially 750.
- **Enter:** submit a round to the shared TOP FIVE table; increment the player's
  round count, update their best score and evaluate achievements.
- **Tab:** switch between scores and the stats/achievement page.
- **A:** acknowledge the current player's newly unlocked awards.
- **S:** explicitly save all profiles/tables to **ACHDEMO.DAT** beside the PRG.
- **L:** reload the saved state into the other RAM buffer. It selects the first
  saved player; use N to select another. Missing/invalid loads preserve live data.
- **Escape:** exit to TOS. Exit does not save automatically.

Awards are FIRST ROUND (10 points), SCORE AT LEAST 1000 (25), and PLAY THREE
ROUNDS (50). New-award counts demonstrate the legacy session notification API;
selecting an existing player treats their existing awards as already seen.
The UI is a compact example, not a completion of the old Achieve login/show/
sign-in asset-driven UI flows or the unfinished Clone/Combine functions.

If ACHDEMO.DAT exists at startup, the program attempts to load it; otherwise it
starts with ATARI and seeded scores. There is no networking or account service.

## Build and implementation

```sh
make
make run
make check
```

The program embeds two BFBs made from GodLib's built-in fixed-width 8x8 font.
It needs no companion assets, except its optional save file. `make assets`
regenerates those BFBs with Python 3, using the shared host TOOLBASE serializer.
Runtime drawing uses `sGraphicCanvas` font/fill functions and redraws only the
changed state on each of the two display pages. C handles input/state, not pixels.

The app calls Achieve_AppInit/Create, configures a table/two stats/three tasks,
and selects a player. Definitions and profile data live in a caller-owned 16 KiB
arena. A second 16 KiB arena demonstrates loading under a different base address;
the sample is not claiming two arenas are required by the API. Stats and awards
belong to the selected player; the high-score table is shared by all players.
Machine specs are collected after creation with Achieve_GodLib_AppInit.

Save/load are explicit. Save reports creation/write/close failures and restores
the live relocated state even when writing fails. Save is a direct file write,
not a transactional filesystem replacement. Load reads into temporary storage,
checks serialized extents/strings/chains before relocating, then commits to the
requested arena. An existing live game requires matching game ID and stat/task/
table counts. There is no migration for malformed legacy snapshots containing
absolute pointers. Direct Achieve_Relocate still expects trusted serialized data;
it has no buffer-size argument.

## Verification

`make check` runs two 68000 programs in disposable GEMDOS directories, so it
never overwrites an existing player's save:

- **ACHTEST.PRG:** 29 checks covering zeroed allocations, two score-table sort
  orders, tie qualification, stats, exact player-name matching, task bits across
  a byte boundary, new-award indexing, points and specs. It saves/loads across
  different addresses, adds a player after loading, checks a second disk round
  trip, and rejects absent/truncated/oversized/invalid-offset files while keeping
  the active profile. Failed Save is also checked.
- **ACHIEVE.PRG:** actual IKBD name entry/Backspace, two distinct players,
  score submission, all three awards/85 points, acknowledgement, save, mutation,
  reload into the other arena and persistence of both players' stats. It exits
  cleanly to TOS with no CPU exceptions.

Evidence: `analysis/verification.json`, plus `scores.png`, `awards.png`, and
`loaded.png`. Configuration: STE, 68000, 8 MHz, 1 MiB, German TOS 1.62. These are
emulator tests, not physical-hardware measurements or a CPU profile.
