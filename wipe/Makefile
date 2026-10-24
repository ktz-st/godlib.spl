CC = m68k-atari-mintelf-gcc
STRIP = m68k-atari-mintelf-strip
CMINI_DIR = ../../libcmini
GODLIB_DIR = ../../godlib
CFLAGS = -fno-strict-aliasing -Wall -Os -mshort -mfastcall -m68000 -fpack-struct=2 -I../.. -I$(CMINI_DIR)/include
LDFLAGS = -nostdlib -nostartfiles -nodefaultlibs -static -mshort -mfastcall -m68000 -Wl,--gc-sections -Wl,--relax -L$(CMINI_DIR)/lib/mshort/mfastcall -L$(GODLIB_DIR)
TOS ?= /Users/kriss/Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img
CRT = $(CMINI_DIR)/lib/mshort/mfastcall/crt0.o

all: WIPE.PRG COAST.PI1 SPACE.PI1 FOREST.PI1
WIPE.PRG: wipe.o $(GODLIB_DIR)/libgod.a
	$(CC) $(LDFLAGS) -s -o $@ $(CRT) wipe.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
	$(STRIP) --strip-unneeded $@
wipe.o: wipe.c $(GODLIB_DIR)/wipe/wipe.h
	$(CC) $(CFLAGS) -c $< -o $@
run: all
	hatari --machine ste --tos "$(TOS)" --memsize 1 --monitor rgb --confirm-quit false WIPE.PRG
debug: all tools/abi_s.o
	$(CC) $(CFLAGS) -DWIPE_BENCH $(LDFLAGS) -o /tmp/WIPEDBG.PRG $(CRT) wipe.c tools/abi_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
debug-release: all
	$(CC) $(LDFLAGS) -o /tmp/WIPEREL.PRG $(CRT) wipe.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
tools/abi_s.o: tools/abi_s.s
	vasmm68k_mot -Felf -devpac $< -o $@
check: debug
	python3 tools/check.py
	python3 tools/check-dirty.py
profile: debug
	python3 tools/profile.py
assets: COAST.PI1 SPACE.PI1 FOREST.PI1
COAST.PI1: assets/coast.png prepare_assets.py ../tools/abc2_assets.py
	python3 prepare_assets.py coast
SPACE.PI1: assets/space.png prepare_assets.py ../tools/abc2_assets.py
	python3 prepare_assets.py space
FOREST.PI1: assets/forest.png prepare_assets.py ../tools/abc2_assets.py
	python3 prepare_assets.py forest
clean:
	rm -f wipe.o WIPE.PRG tools/abi_s.o
.PHONY: all run debug debug-release check profile clean assets
