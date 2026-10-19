CC = m68k-atari-mintelf-gcc
CMINI_DIR = ../../libcmini
GODLIB_DIR = ../../godlib
CFLAGS = -Wall -Os -mshort -mfastcall -m68000 -fpack-struct=2 -I../.. -I$(CMINI_DIR)/include
LDFLAGS = -nostdlib -nostartfiles -nodefaultlibs -static -mshort -mfastcall -m68000 -Wl,--gc-sections -Wl,--relax -L$(CMINI_DIR)/lib/mshort/mfastcall -L$(GODLIB_DIR)
CRT = $(CMINI_DIR)/lib/mshort/mfastcall/crt0.o
TOS ?= /Users/kriss/Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img
OBJECTS = cutscene.o assets_s.o
all: CUTSCENE.PRG
CUTSCENE.PRG: $(OBJECTS) $(GODLIB_DIR)/libgod.a
	$(CC) $(LDFLAGS) -s -o $@ $(CRT) $(OBJECTS) -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
	m68k-atari-mintelf-strip --strip-unneeded $@
cutscene.o: cutscene.c
	$(CC) $(CFLAGS) -c $< -o $@
assets_s.o: assets_s.s scene.txt assets/CASTLE.PI1 assets/FOREST.PI1 assets/FONT.BIN assets/STAR.BIN assets/ARRIVAL.RAW assets/PATH.RAW assets/FOREST.RAW assets/JOURNEY.RAW
	vasmm68k_mot -Felf -devpac $< -o $@
debug: CUTSCENE.PRG
	mkdir -p analysis
	$(CC) $(LDFLAGS) -o analysis/CUTDBG.PRG $(CRT) $(OBJECTS) -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
assets:
	python3 prepare.py
run: CUTSCENE.PRG
	hatari --tos "$(TOS)" --machine ste --memsize 1 --monitor rgb --confirm-quit false --fast-boot true CUTSCENE.PRG
clean:
	rm -f $(OBJECTS) CUTSCENE.PRG analysis/CUTDBG.PRG analysis/CUTTEST.PRG
.PHONY: all debug assets run clean

voices:
	python3 voices.py
.PHONY: voices

analysis/CUTTEST.PRG: analysis/runtime-check.c cutscene.c assets_s.o $(GODLIB_DIR)/libgod.a
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $(CRT) $< assets_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group

check: debug analysis/CUTTEST.PRG
	python3 analysis/verify-runtime.py
	python3 analysis/verify.py
.PHONY: check
