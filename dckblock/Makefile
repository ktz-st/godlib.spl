CC = m68k-atari-mintelf-gcc
CMINI_DIR = ../../libcmini
GODLIB_DIR = ../../godlib
CFLAGS = -Wall -Os -mshort -mfastcall -m68000 -fpack-struct=2 -I../.. -I$(CMINI_DIR)/include
LDFLAGS = -nostdlib -nostartfiles -nodefaultlibs -static -mshort -mfastcall -m68000 -Wl,--gc-sections -Wl,--relax -L$(CMINI_DIR)/lib/mshort/mfastcall -L$(GODLIB_DIR)
CRT = $(CMINI_DIR)/lib/mshort/mfastcall/crt0.o
TOS ?= /Users/kriss/Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img
all: DCKBLOCK.PRG
DCKBLOCK.PRG: dckblock.o dckblock_s.o $(GODLIB_DIR)/libgod.a
	$(CC) $(LDFLAGS) -s -o $@ $(CRT) dckblock.o dckblock_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
dckblock.o: dckblock.c
	$(CC) $(CFLAGS) -c $< -o $@
dckblock_s.o: dckblock_s.s assets/PICTURE.BIN assets/PALETTE.BIN assets/MOVE.BIN assets/rows.inc
	vasmm68k_mot -Felf -devpac $< -o $@
debug: all
	$(CC) $(CFLAGS) -DDB_BENCH $(LDFLAGS) -Wl,-Map,/tmp/DBDBG.map -o /tmp/DBDBG.PRG $(CRT) dckblock.c dckblock_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
debug-release: all
	$(CC) $(LDFLAGS) -o /tmp/DBREL.PRG $(CRT) dckblock.o dckblock_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
assets:
	python3 tools/assets.py
check: debug
	python3 tools/check.py
profile: debug
	python3 tools/profile.py
	python3 tools/profile_spikes.py
run: all
	hatari --tos "$(TOS)" --machine ste --memsize 1 --monitor rgb --confirm-quit false DCKBLOCK.PRG
clean:
	rm -f dckblock.o dckblock_s.o DCKBLOCK.PRG
.PHONY: all debug debug-release assets check profile run clean
