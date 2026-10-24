CC = m68k-atari-mintelf-gcc
CMINI_DIR = ../../libcmini
GODLIB_DIR = ../../godlib
CFLAGS = -Wall -Os -mshort -mfastcall -m68000 -fpack-struct=2 -I../.. -I$(CMINI_DIR)/include
LDFLAGS = -nostdlib -nostartfiles -nodefaultlibs -static -mshort -mfastcall -m68000 -Wl,--gc-sections -Wl,--relax -L$(CMINI_DIR)/lib/mshort/mfastcall -L$(GODLIB_DIR)
CRT = $(CMINI_DIR)/lib/mshort/mfastcall/crt0.o
TOS ?= /Users/kriss/Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img
all: DCKTAPIS.PRG
DCKTAPIS.PRG: dcktapis.o dcktapis_s.o $(GODLIB_DIR)/libgod.a
	$(CC) $(LDFLAGS) -s -o $@ $(CRT) dcktapis.o dcktapis_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
dcktapis.o: dcktapis.c dcktapis.h
	$(CC) $(CFLAGS) -c $< -o $@
dcktapis_s.o: dcktapis_s.s assets/PICTURE.BIN assets/PALETTES.BIN
	vasmm68k_mot -Felf -devpac $< -o $@
debug: all
	$(CC) $(CFLAGS) -DTP_BENCH $(LDFLAGS) -Wl,-Map,/tmp/TPDBG.map -o /tmp/TPDBG.PRG $(CRT) dcktapis.c dcktapis_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
debug-release: all
	$(CC) $(LDFLAGS) -o /tmp/TPREL.PRG $(CRT) dcktapis.o dcktapis_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
assets:
	python3 tools/assets.py
check: debug
	python3 tools/check.py
profile: debug-release
	TP_DEBUG=$(CURDIR)/DCKTAPIS.PRG TP_SYMBOLS=/tmp/TPREL.PRG python3 tools/profile.py
run: all
	hatari --tos "$(TOS)" --machine ste --memsize 1 --monitor rgb --confirm-quit false DCKTAPIS.PRG
clean:
	rm -f dcktapis.o dcktapis_s.o DCKTAPIS.PRG
.PHONY: all debug debug-release assets check profile run clean
