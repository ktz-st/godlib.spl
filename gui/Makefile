CC = m68k-atari-mintelf-gcc
CMINI_DIR = ../../libcmini
GODLIB_DIR = ../../godlib
CFLAGS = -Wall -Os -mshort -mfastcall -m68000 -fpack-struct=2 -I../.. -I$(CMINI_DIR)/include
LDFLAGS = -nostdlib -nostartfiles -nodefaultlibs -static -mshort -mfastcall -m68000 -Wl,--gc-sections -Wl,--relax -L$(CMINI_DIR)/lib/mshort/mfastcall -L$(GODLIB_DIR)
CRT = $(CMINI_DIR)/lib/mshort/mfastcall/crt0.o
TOS ?= /Users/kriss/Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img
OBJECTS = gui.o assets.o
all: GUI.PRG
GUI.PRG: $(OBJECTS) $(GODLIB_DIR)/libgod.a
	$(CC) $(LDFLAGS) -s -o $@ $(CRT) $(OBJECTS) -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
gui.o: gui.c
	$(CC) $(CFLAGS) -c $< -o $@
debug: GUI.PRG
	$(CC) $(LDFLAGS) -o analysis/GUIDBG.PRG $(CRT) $(OBJECTS) -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
run: GUI.PRG
	hatari --tos "$(TOS)" --machine ste --memsize 1 --monitor rgb --confirm-quit false --fast-boot true GUI.PRG
clean:
	rm -f $(OBJECTS) GUI.PRG analysis/GUIDBG.PRG
.PHONY: all debug run clean

check: debug
	python3 analysis/verify.py
.PHONY: check

assets.o: assets.s assets/FONT.BIN assets/CURSOR.BIN
	vasmm68k_mot -Felf -devpac $< -o $@

assets:
	python3 prepare.py
.PHONY: assets
