CC = m68k-atari-mintelf-gcc
CMINI_DIR = ../../libcmini
GODLIB_DIR = ../../godlib
CFLAGS = -Wall -Os -mshort -mfastcall -m68000 -fpack-struct=2 -I../.. -I$(CMINI_DIR)/include
LDFLAGS = -nostdlib -nostartfiles -nodefaultlibs -static -mshort -mfastcall -m68000 -Wl,--gc-sections -Wl,--relax -L$(CMINI_DIR)/lib/mshort/mfastcall -L$(GODLIB_DIR)
CRT = $(CMINI_DIR)/lib/mshort/mfastcall/crt0.o
TOS ?= /Users/kriss/Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img
all: LCKWIPE.PRG
LCKWIPE.PRG: lckwipe.o lckwipe_s.o $(GODLIB_DIR)/libgod.a
	$(CC) $(LDFLAGS) -s -o $@ $(CRT) lckwipe.o lckwipe_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
lckwipe.o: lckwipe.c lckwipe.h
	$(CC) $(CFLAGS) -c $< -o $@
lckwipe_s.o: lckwipe_s.s assets/IMAGE0.BIN assets/IMAGE1.BIN assets/PALETTE0.BIN assets/PALETTE1.BIN assets/tables.inc assets/STAGES0.BIN assets/STAGES1.BIN
	vasmm68k_mot -Felf -devpac $< -o $@
debug: all
	$(CC) $(CFLAGS) -DLW_BENCH $(LDFLAGS) -Wl,-Map,/tmp/LWDBG.map -o /tmp/LWDBG.PRG $(CRT) lckwipe.c lckwipe_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
debug-release: all
	$(CC) $(LDFLAGS) -o /tmp/LWREL.PRG $(CRT) lckwipe.o lckwipe_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
assets:
	python3 tools/assets.py
check: debug
	python3 tools/check.py
profile: debug
	python3 tools/profile.py
run: all
	hatari --tos "$(TOS)" --machine ste --memsize 1 --monitor rgb --confirm-quit false LCKWIPE.PRG
clean:
	rm -f lckwipe.o lckwipe_s.o LCKWIPE.PRG
.PHONY: all debug debug-release assets check profile run clean
