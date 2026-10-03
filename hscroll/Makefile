CC = m68k-atari-mintelf-gcc
STRIP = m68k-atari-mintelf-strip
CMINI_DIR = ../../libcmini
GODLIB_DIR = ../../godlib
CFLAGS = -fno-strict-aliasing -Wall -Os -mshort -mfastcall -m68000 -fpack-struct=2 -I../.. -I$(CMINI_DIR)/include
LDFLAGS = -nostdlib -nostartfiles -nodefaultlibs -static -mshort -mfastcall -m68000 -Wl,--gc-sections -Wl,--relax -L$(CMINI_DIR)/lib/mshort/mfastcall -L$(GODLIB_DIR)
CRT = $(CMINI_DIR)/lib/mshort/mfastcall/crt0.o

all: HSCROLL.PRG PANORAMA.BIN
HSCROLL.PRG: hscroll.o verify.o $(GODLIB_DIR)/libgod.a
	$(CC) $(LDFLAGS) -s -o $@ $(CRT) hscroll.o verify.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
	$(STRIP) --strip-unneeded $@
hscroll.o: hscroll.c $(GODLIB_DIR)/screen/screen.h $(GODLIB_DIR)/video/video.h
	$(CC) $(CFLAGS) -c $< -o $@
run: all
	hatari -w --machine ste --memsize 4 --monitor rgb --fast-boot true HSCROLL.PRG
debug: all analysis/HSCRDBG.PRG analysis/PANDBG.PRG
analysis/HSCRDBG.PRG: analysis/hscroll-grid.o verify.o $(GODLIB_DIR)/libgod.a
	mkdir -p analysis
	$(CC) $(LDFLAGS) -Wl,-Map=analysis/hscroll.map -o $@ $(CRT) analysis/hscroll-grid.o verify.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
verify.o: verify.c
	$(CC) $(CFLAGS) -c $< -o $@
clean:
	rm -f hscroll.o verify.o HSCROLL.PRG analysis/HSCRDBG.PRG analysis/PANDBG.PRG analysis/hscroll-grid.o analysis/hscroll.map analysis/MODES.PRG
.PHONY: all run debug clean

# Legacy NONE/V/H/H+V allocation and clamp checks on STE.
analysis/MODES.PRG: analysis/verify-modes.c $(GODLIB_DIR)/libgod.a
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $(CRT) $< -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group

analysis/hscroll-grid.o: hscroll.c $(GODLIB_DIR)/screen/screen.h
	mkdir -p analysis
	$(CC) $(CFLAGS) -DHSCROLL_VERIFY_PATTERN -c $< -o $@
analysis/PANDBG.PRG: hscroll.o verify.o $(GODLIB_DIR)/libgod.a
	$(CC) $(LDFLAGS) -o $@ $(CRT) hscroll.o verify.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
PANORAMA.BIN: assets/panorama-original.png prepare_assets.py
	python3 prepare_assets.py
assets: PANORAMA.BIN
.PHONY: assets
