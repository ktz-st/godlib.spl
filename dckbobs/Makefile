CC = m68k-atari-mintelf-gcc
CMINI_DIR = ../../libcmini
GODLIB_DIR = ../../godlib
CFLAGS = -Wall -Os -mshort -mfastcall -m68000 -fpack-struct=2 -I../.. -I$(CMINI_DIR)/include
LDFLAGS = -nostdlib -nostartfiles -nodefaultlibs -static -mshort -mfastcall -m68000 -Wl,--gc-sections -Wl,--relax -L$(CMINI_DIR)/lib/mshort/mfastcall -L$(GODLIB_DIR)
CRT = $(CMINI_DIR)/lib/mshort/mfastcall/crt0.o
TOS ?= /Users/kriss/Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img
all: DCKBOBS.PRG
DCKBOBS.PRG: dckbobs.o dckbobs_s.o $(GODLIB_DIR)/libgod.a
	$(CC) $(LDFLAGS) -s -o $@ $(CRT) dckbobs.o dckbobs_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
dckbobs.o: dckbobs.c dckbobs.h
	$(CC) $(CFLAGS) -c $< -o $@
dckbobs_s.o: dckbobs_s.s assets/SPRITES.BIN assets/PALETTE.BIN assets/PATHS.BIN assets/paths.inc
	vasmm68k_mot -Felf -devpac $< -o $@
debug: all
	$(CC) $(CFLAGS) -DBOBS_BENCH $(LDFLAGS) -Wl,-Map,/tmp/BOBSDBG.map -o /tmp/BOBSDBG.PRG $(CRT) dckbobs.c dckbobs_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
debug-release: all
	$(CC) $(LDFLAGS) -o /tmp/BOBSREL.PRG $(CRT) dckbobs.o dckbobs_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
assets:
	python3 tools/assets.py
check: debug
	python3 tools/check.py
profile: debug
	python3 tools/profile.py
run: all
	hatari --tos "$(TOS)" --machine ste --memsize 4 --monitor rgb --confirm-quit false DCKBOBS.PRG
clean:
	rm -f dckbobs.o dckbobs_s.o DCKBOBS.PRG
.PHONY: all debug debug-release assets check profile run clean
