CC = m68k-atari-mintelf-gcc
CMINI_DIR = ../../libcmini
GODLIB_DIR = ../../godlib
CFLAGS = -Wall -Os -mshort -mfastcall -m68000 -fpack-struct=2 -I../.. -I$(CMINI_DIR)/include
LDFLAGS = -nostdlib -nostartfiles -nodefaultlibs -static -mshort -mfastcall -m68000 -Wl,--gc-sections -Wl,--relax -L$(CMINI_DIR)/lib/mshort/mfastcall -L$(GODLIB_DIR)
CRT = $(CMINI_DIR)/lib/mshort/mfastcall/crt0.o
TOS ?= /Users/kriss/Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img
OBJECTS = achieve.o assets.o
all: ACHIEVE.PRG
ACHIEVE.PRG: $(OBJECTS) $(GODLIB_DIR)/libgod.a
	$(CC) $(LDFLAGS) -s -o $@ $(CRT) $(OBJECTS) -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
achieve.o: achieve.c
	$(CC) $(CFLAGS) -c $< -o $@
debug: ACHIEVE.PRG
	$(CC) $(LDFLAGS) -o analysis/ACHDBG.PRG $(CRT) $(OBJECTS) -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
run: ACHIEVE.PRG
	hatari --tos "$(TOS)" --machine ste --memsize 1 --monitor rgb --confirm-quit false --fast-boot true ACHIEVE.PRG
clean:
	rm -f $(OBJECTS) ACHIEVE.PRG analysis/ACHDBG.PRG
.PHONY: all debug run clean

check: debug analysis/ACHTEST.PRG
	python3 analysis/verify.py
.PHONY: check

assets.o: assets.s assets/NORMAL.BFB assets/ACTIVE.BFB
	vasmm68k_mot -Felf -devpac $< -o $@

analysis/ACHTEST.PRG: analysis/runtime-check.c $(GODLIB_DIR)/libgod.a
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $(CRT) $< -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
check-native: debug analysis/ACHTEST.PRG
	python3 analysis/verify.py
.PHONY: check-native

assets:
	python3 prepare.py
.PHONY: assets
