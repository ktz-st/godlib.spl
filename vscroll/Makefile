CC = m68k-atari-mintelf-gcc
STRIP = m68k-atari-mintelf-strip
CMINI_DIR = ../../libcmini
GODLIB_DIR = ../../godlib
CFLAGS = -fno-strict-aliasing -Wall -Os -mshort -mfastcall -m68000 -fpack-struct=2 -I../.. -I$(CMINI_DIR)/include
LDFLAGS = -nostdlib -nostartfiles -nodefaultlibs -static -mshort -mfastcall -m68000 -Wl,--gc-sections -Wl,--relax -L$(CMINI_DIR)/lib/mshort/mfastcall -L$(GODLIB_DIR)
CRT = $(CMINI_DIR)/lib/mshort/mfastcall/crt0.o

all: VSCROLL.PRG TOWER.BIN
VSCROLL.PRG: vscroll.o $(GODLIB_DIR)/libgod.a
	$(CC) $(LDFLAGS) -s -o $@ $(CRT) vscroll.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
	$(STRIP) --strip-unneeded $@
vscroll.o: vscroll.c $(GODLIB_DIR)/screen/screen.h $(GODLIB_DIR)/video/video.h
	$(CC) $(CFLAGS) -c $< -o $@
run: all
	hatari -w --machine ste --memsize 4 --monitor rgb --fast-boot true VSCROLL.PRG
debug: all analysis/VSCDBG.PRG
analysis/VSCDBG.PRG: vscroll.o $(GODLIB_DIR)/libgod.a
	mkdir -p analysis
	$(CC) $(LDFLAGS) -o $@ $(CRT) vscroll.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
TOWER.BIN: assets/tower-original.png prepare_assets.py ../tools/abc2_assets.py
	python3 prepare_assets.py
assets: TOWER.BIN
clean:
	rm -f vscroll.o VSCROLL.PRG analysis/VSCDBG.PRG
.PHONY: all run debug assets clean
