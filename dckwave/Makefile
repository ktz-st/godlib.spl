CC = m68k-atari-mintelf-gcc
CMINI_DIR = ../../libcmini
GODLIB_DIR = ../../godlib
CFLAGS = -Wall -Os -mshort -mfastcall -m68000 -fpack-struct=2 -I../.. -I$(CMINI_DIR)/include
LDFLAGS = -nostdlib -nostartfiles -nodefaultlibs -static -mshort -mfastcall -m68000 -Wl,--gc-sections -Wl,--relax -L$(CMINI_DIR)/lib/mshort/mfastcall -L$(GODLIB_DIR)
CRT = $(CMINI_DIR)/lib/mshort/mfastcall/crt0.o
TOS ?= /Users/kriss/Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img
all: DCKWAVE.PRG
DCKWAVE.PRG: dckwave.o dckwave_s.o $(GODLIB_DIR)/libgod.a
	$(CC) $(LDFLAGS) -s -o $@ $(CRT) dckwave.o dckwave_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
dckwave.o: dckwave.c dckwave.h
	$(CC) $(CFLAGS) -c $< -o $@
dckwave_s.o: dckwave_s.s assets/PICTURE.BIN assets/PALETTE.BIN assets/SHIFTS.BIN
	vasmm68k_mot -Felf -devpac $< -o $@
debug: all
	$(CC) $(CFLAGS) -DDW_BENCH $(LDFLAGS) -Wl,-Map,/tmp/DWDBG.map -o /tmp/DWDBG.PRG $(CRT) dckwave.c dckwave_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
debug-release: all
	$(CC) $(LDFLAGS) -o /tmp/DWREL.PRG $(CRT) dckwave.o dckwave_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
assets:
	python3 tools/assets.py
check: debug
	python3 tools/check.py
profile: debug
	python3 tools/profile.py
run: all
	hatari --tos "$(TOS)" --machine ste --memsize 1 --monitor rgb --confirm-quit false DCKWAVE.PRG
clean:
	rm -f dckwave.o dckwave_s.o DCKWAVE.PRG
.PHONY: all debug debug-release assets check profile run clean
