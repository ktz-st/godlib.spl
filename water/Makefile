CC = m68k-atari-mintelf-gcc
STRIP = m68k-atari-mintelf-strip
CMINI_DIR = ../../libcmini
GODLIB_DIR = ../../godlib
CFLAGS = -fno-strict-aliasing -Wall -Os -mshort -mfastcall -m68000 -fpack-struct=2 -I../.. -I$(CMINI_DIR)/include
LDFLAGS = -nostdlib -nostartfiles -nodefaultlibs -static -mshort -mfastcall -m68000 -Wl,--gc-sections -Wl,--relax -L$(CMINI_DIR)/lib/mshort/mfastcall -L$(GODLIB_DIR)
CRT = $(CMINI_DIR)/lib/mshort/mfastcall/crt0.o

all: WATER.PRG
WATER.PRG: water.o water_s.o $(GODLIB_DIR)/libgod.a
	$(CC) $(LDFLAGS) -s -o $@ $(CRT) water.o water_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
	$(STRIP) --strip-unneeded $@
water.o: water.c assets/config.h $(GODLIB_DIR)/screen/screen.h $(GODLIB_DIR)/video/video.h
	$(CC) $(CFLAGS) -c $< -o $@
run: all
	hatari -w --machine ste --memsize 4 --monitor rgb --confirm-quit false --fast-boot true WATER.PRG
debug: all analysis/WDBG.PRG
analysis/WDBG.PRG: water.o water_s.o $(GODLIB_DIR)/libgod.a
	mkdir -p analysis
	$(CC) $(LDFLAGS) -o $@ $(CRT) water.o water_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
water_s.o: water_s.s assets/CASTLE.PI1 assets/ROWS.BIN assets/SURFACE.BIN
	vasmm68k_mot -Felf -devpac $< -o $@
clean:
	rm -f *.o WATER.PRG analysis/WDBG.PRG
.PHONY: all run debug clean

assets/CASTLE.PI1: assets/castle-source.png tools/prepare.py ../tools/abc2_assets.py
	python3 tools/prepare.py
assets/ROWS.BIN assets/SURFACE.BIN assets/config.h: assets/CASTLE.PI1
	@test -f $@ || python3 tools/prepare.py
