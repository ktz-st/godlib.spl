CC = m68k-atari-mintelf-gcc
STRIP = m68k-atari-mintelf-strip
CMINI_DIR = ../../libcmini
GODLIB_DIR = ../../godlib
CFLAGS = -fno-strict-aliasing -Wall -Os -mshort -mfastcall -m68000 -fpack-struct=2 -I../.. -I$(CMINI_DIR)/include
LDFLAGS = -nostdlib -nostartfiles -nodefaultlibs -static -mshort -mfastcall -m68000 -Wl,--gc-sections -Wl,--relax -L$(CMINI_DIR)/lib/mshort/mfastcall -L$(GODLIB_DIR)
CRT = $(CMINI_DIR)/lib/mshort/mfastcall/crt0.o

all: WIPE.PRG COAST.PI1 SPACE.PI1 FOREST.PI1
WIPE.PRG: wipe.o $(GODLIB_DIR)/libgod.a
	$(CC) $(LDFLAGS) -s -o $@ $(CRT) wipe.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
	$(STRIP) --strip-unneeded $@
wipe.o: wipe.c $(GODLIB_DIR)/wipe/wipe.h
	$(CC) $(CFLAGS) -c $< -o $@
run: all
	hatari -w --machine st --memsize 4 --monitor rgb --fast-boot true WIPE.PRG
debug: all analysis/WIPEDBG.PRG
analysis/WIPEDBG.PRG: wipe.o $(GODLIB_DIR)/libgod.a
	mkdir -p analysis
	$(CC) $(LDFLAGS) -Wl,-Map=analysis/wipe.map -o $@ $(CRT) wipe.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
assets: COAST.PI1 SPACE.PI1 FOREST.PI1
COAST.PI1: assets/coast.png prepare_assets.py ../tools/abc2_assets.py
	python3 prepare_assets.py coast
SPACE.PI1: assets/space.png prepare_assets.py ../tools/abc2_assets.py
	python3 prepare_assets.py space
FOREST.PI1: assets/forest.png prepare_assets.py ../tools/abc2_assets.py
	python3 prepare_assets.py forest
clean:
	rm -f wipe.o WIPE.PRG analysis/WIPEDBG.PRG analysis/wipe.map
.PHONY: all run debug clean assets
