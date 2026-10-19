# Input / Kernel — keyboard, joystick and replay

`INPUT.PRG` runs a real Kernel task (index **7**, no packages). Kernel owns the
screen-paced main loop and passes the task one combined `sInput`. The moving
square consumes only that action structure; keyboard and joystick movement use
exactly the same gameplay function.

## Controls

- **Cursor keys / joystick 1:** move the square (joystick 0 also joins the
  default Kernel input set when joystick mode is active).
- **Space / joystick fire:** change the square's colour and increment FIRE on
  **HIT**, once per press. Its centre lights while the action is **HELD**.
- **R:** start a new recording from the fixed initial scene; R again stops it.
- **P:** replay the recording from the same initial scene. P during replay
  aborts it. Live directions/fire do not affect playback.
- **S:** stop recording if necessary and explicitly write **INPUTS.KIP** beside
  the PRG. A direct file write replaces any existing file with that name.
- **L:** load INPUTS.KIP and start playback. A failed load keeps the recording.
- **C:** reset the scene in LIVE mode.
- **Escape / F10:** exit to TOS. This example does not save automatically.

The status panel shows LIVE/RECORD/REPLAY, recorded frames and used bytes,
coordinates, fire count, and action flags. `H`, `+`, `-` mean HELD, HIT and UNHIT;
`LRDUABPOQ` means left/right/down/up/fire A/fire B/pause/option/quit.
The outlined square marks the recorded endpoint.

A completed RAM replay checks the endpoint, fire count, colour and a rolling
hash of every simulated frame/action, then prints **REPLAY MATCH**. Loading a
file has no reference game-state hash, so it reports completion without claiming
the same internal comparison. This is input recording, not video or save-state
capture: replaying a real game also requires its initial state, RNG and update
schedule to be reproducible. This sample uses no gameplay RNG.

## Build

```sh
make
make run
make check
```

The executable is self-contained: fonts and drawing kernels come from GodLib;
no companion graphics are needed. Drawing uses existing ASM-backed canvas fills and GodLib Font8x8 routines,
with double buffering. The application C code updates game state and issues
draw calls.

## Runtime API and fixes

The example adds public controls for Kernel's existing recorder:

- `Kernel_InputRecordBegin(capacity)` allocates a recording buffer; allocation
  failure preserves the old recording. The example requests **32 KiB**.
- `Kernel_InputStop()` retains recorded frames and returns to live input.
- `Kernel_InputReplayBegin()` rewinds the same recording.
- `Kernel_GetInputMode/FrameCount/Frame/Bytes()` expose mode and progress.
- `Kernel_InputBufferWrite(name)` and `Kernel_InputBufferRead(name)` report disk
  success/failure. Legacy Save/Load/RequestInputLoad entry points remain.

The format remains the old raw **KIP** stream: an initial `sInput`, followed by
byte deltas per task update, or one `0xFF` for an unchanged frame. Only changed
bytes are stored. Allocation capacity, recorded extent and frame count are
tracked separately. A frame is committed completely or recording stops before
it; playback ends with neutral input and returns to LIVE. File reads validate
all delta offsets, payloads and frame boundaries before replacing the recording.
The raw format depends on the `sInput` layout/endian ABI and contains no version,
checksum, initial game state or RNG seed. It is not a portable replay container.

Kernel now includes ordinary joystick directions as well as fire. Its default
keyboard map remains cursor keys/Space/F1/F2/F10. `Input_CombinedUpdate` merges
HELD across sources and derives HIT/UNHIT from the previous combined action:
handing a held action from keyboard to joystick does not create a new HIT, and
releasing one source does not cancel another held source. Rapid re-press directly
after UNHIT also produces HIT. The older two-source `Input_Combine`/
`Input_CombineFire` helpers retain their overwrite semantics.

Kernel init now uses the first task's declared index. Shutdown calls the final
task's deinit; Kernel_DeInit removes its input-monitor VBL callback, frees the
recorder and restores the previous GEMDOS DTA before Platform_DeInit. The old
optional CLI, package task switching, Jaguar pads and mouse-fire overlay are not
the focus of this example.

## Verification

`make check` runs in disposable GEMDOS directories using **STE / 68000 / 8 MHz /
1 MiB / German TOS 1.62**:

- 36 native checks cover combined action edges/overlap, rapid re-press, initial/
  unchanged/all-byte delta frames, byte-exact replay, exact buffer boundaries,
  overflow without partial frames, neutral EOF, rewind, file round trip and
  rejection of short/truncated/invalid-offset/unterminated streams. Failed loads
  preserve the old recording; deinit/reinit checks VBL callback counts and DTA.
- The interactive test sends real Atari keyboard events and configures Hatari
  joystick 1 with host WASD/J. It checks keyboard/joystick handover for movement
  and fire, a recorded route and its full replay hash, unrelated live keys during
  playback, KIP save/load replay, abort and clean TOS exit with exactly one task
  deinit and no remaining monitor callback. It does not inject synthetic packets
  directly into GodLib RAM.

Evidence is in `analysis/verification.json` and the PNG captures. These are
functional emulator checks, not physical joystick tests or CPU measurements.
