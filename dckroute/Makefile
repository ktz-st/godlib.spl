CC = m68k-atari-mintelf-gcc
CMINI_DIR = ../../libcmini
GODLIB_DIR = ../../godlib
CFLAGS = -Wall -Os -mshort -mfastcall -m68000 -fpack-struct=2 -I../.. -I$(CMINI_DIR)/include
LDFLAGS = -nostdlib -nostartfiles -nodefaultlibs -static -mshort -mfastcall -m68000 -Wl,--gc-sections -Wl,--relax -L$(CMINI_DIR)/lib/mshort/mfastcall -L$(GODLIB_DIR)
CRT = $(CMINI_DIR)/lib/mshort/mfastcall/crt0.o
TOS ?= /Users/kriss/Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img
all: DCKROUTE.PRG
DCKROUTE.PRG: dckroute.o dckroute_s.o $(GODLIB_DIR)/libgod.a
	$(CC) $(LDFLAGS) -s -o $@ $(CRT) dckroute.o dckroute_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
dckroute.o: dckroute.c
	$(CC) $(CFLAGS) -c $< -o $@
dckroute_s.o: dckroute_s.s assets/COLUMNS.BIN assets/ROWS.BIN assets/PATHS.BIN assets/PALETTE.BIN assets/text.inc
	vasmm68k_mot -Felf -devpac $< -o $@
debug: all
	$(CC) $(CFLAGS) -DROUTE_BENCH $(LDFLAGS) -Wl,-Map,/tmp/DRDBG.map -o /tmp/DRDBG.PRG $(CRT) dckroute.c dckroute_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
debug-release: all
	$(CC) $(LDFLAGS) -o /tmp/DRREL.PRG $(CRT) dckroute.o dckroute_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
assets:
	python3 tools/assets.py
check: debug
	python3 tools/check.py
profile: debug
	python3 tools/profile.py
run: all
	hatari --tos "$(TOS)" --machine ste --memsize 1 --monitor rgb --confirm-quit false DCKROUTE.PRG
clean:
	rm -f dckroute.o dckroute_s.o DCKROUTE.PRG
.PHONY: all debug debug-release assets check profile run clean
