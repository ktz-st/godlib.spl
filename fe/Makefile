CC = m68k-atari-mintelf-gcc
CMINI_DIR = ../../libcmini
GODLIB_DIR = ../../godlib
CFLAGS = -Wall -Os -mshort -mfastcall -m68000 -fpack-struct=2 -I../.. -I$(CMINI_DIR)/include
LDFLAGS = -nostdlib -nostartfiles -nodefaultlibs -static -mshort -mfastcall -m68000 -Wl,--gc-sections -Wl,--relax -L$(CMINI_DIR)/lib/mshort/mfastcall -L$(GODLIB_DIR)
CRT = $(CMINI_DIR)/lib/mshort/mfastcall/crt0.o
TOS ?= /Users/kriss/Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img
OBJECTS = fe.o assets.o
all: FE.PRG
FE.PRG: $(OBJECTS) $(GODLIB_DIR)/libgod.a
	$(CC) $(LDFLAGS) -s -o $@ $(CRT) $(OBJECTS) -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
fe.o: fe.c
	$(CC) $(CFLAGS) -c $< -o $@
debug: FE.PRG
	$(CC) $(LDFLAGS) -o analysis/FEDBG.PRG $(CRT) $(OBJECTS) -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
run: FE.PRG
	hatari --tos "$(TOS)" --machine ste --memsize 1 --monitor rgb --confirm-quit false --fast-boot true FE.PRG
clean:
	rm -f $(OBJECTS) FE.PRG analysis/FEDBG.PRG
.PHONY: all debug run clean

check: debug
	python3 analysis/verify.py
.PHONY: check

assets.o: assets.s assets/MENU.FED assets/NORMAL.BFB assets/ACTIVE.BFB assets/TITLE.BFB assets/MAIN.PI1 assets/OPTIONS.PI1 assets/CURSOR.BSB assets/CHIME.RAW
	vasmm68k_mot -Felf -devpac $< -o $@

assets: assets/MENU.FED
	python3 prepare.py
.PHONY: assets

assets/MENU.FED: menu.txt $(GODLIB_DIR)/tools/febuild/febuild.py $(GODLIB_DIR)/tools/febuild/schema.json
	python3 $(GODLIB_DIR)/tools/febuild/febuild.py $< $@
