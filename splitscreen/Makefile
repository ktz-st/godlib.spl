CC = m68k-atari-mintelf-gcc
STRIP = m68k-atari-mintelf-strip
CMINI_DIR = ../../libcmini
GODLIB_DIR = ../../godlib
CFLAGS = -fno-strict-aliasing -Wall -Os -mshort -mfastcall -m68000 -fpack-struct=2 -I../.. -I$(CMINI_DIR)/include
LDFLAGS = -nostdlib -nostartfiles -nodefaultlibs -static -mshort -mfastcall -m68000 -Wl,--gc-sections -Wl,--relax -L$(CMINI_DIR)/lib/mshort/mfastcall -L$(GODLIB_DIR)
CRT = $(CMINI_DIR)/lib/mshort/mfastcall/crt0.o

all: SPLIT.PRG
SPLIT.PRG: splitscreen.o split.o split_s.o $(GODLIB_DIR)/libgod.a
	$(CC) $(LDFLAGS) -s -o $@ $(CRT) splitscreen.o split.o split_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
	$(STRIP) --strip-unneeded $@
splitscreen.o: splitscreen.c split.h $(GODLIB_DIR)/screen/screen.h $(GODLIB_DIR)/video/video.h
	$(CC) $(CFLAGS) -c $< -o $@
run: all
	hatari -w --machine ste --memsize 4 --monitor rgb --confirm-quit false --fast-boot true SPLIT.PRG
debug: all analysis/SPLITDBG.PRG
analysis/SPLITDBG.PRG: splitscreen.o split.o split_s.o $(GODLIB_DIR)/libgod.a
	mkdir -p analysis
	$(CC) $(LDFLAGS) -o $@ $(CRT) splitscreen.o split.o split_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
split.o: split.c split.h
	$(CC) $(CFLAGS) -c $< -o $@
split_s.o: split_s.s TOWER.BIN
	vasmm68k_mot -Felf -devpac $< -o $@
clean:
	rm -f *.o SPLIT.PRG analysis/SPLITDBG.PRG
.PHONY: all run debug clean

# Refresh this embedded copy from its original-RGB ABC2 asset pipeline.
TOWER.BIN: ../vscroll/TOWER.BIN
	cp $< $@
../vscroll/TOWER.BIN: ../vscroll/assets/tower-original.png ../vscroll/prepare_assets.py ../tools/abc2_assets.py
	$(MAKE) -C ../vscroll TOWER.BIN
