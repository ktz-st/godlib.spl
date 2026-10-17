CC = m68k-atari-mintelf-gcc
STRIP = m68k-atari-mintelf-strip
CMINI_DIR = ../../libcmini
GODLIB_DIR = ../../godlib
CFLAGS = -fno-strict-aliasing -Wall -Os -mshort -mfastcall -m68000 -fpack-struct=2 -I../.. -I$(CMINI_DIR)/include
LDFLAGS = -nostdlib -nostartfiles -nodefaultlibs -static -mshort -mfastcall -m68000 -Wl,--gc-sections -Wl,--relax -L$(CMINI_DIR)/lib/mshort/mfastcall -L$(GODLIB_DIR)
CRT = $(CMINI_DIR)/lib/mshort/mfastcall/crt0.o

all: FSCRL.PRG
assets/BUGSY.BIN: assets/BUGSY.MBK tools/prepare.py
	python3 tools/prepare.py
FSCRL.PRG: fastscroll.o scroll_s.o $(GODLIB_DIR)/libgod.a
	$(CC) $(LDFLAGS) -s -o $@ $(CRT) fastscroll.o scroll_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
	$(STRIP) --strip-unneeded $@
fastscroll.o: fastscroll.c $(GODLIB_DIR)/screen/screen.h $(GODLIB_DIR)/video/video.h
	$(CC) $(CFLAGS) -c $< -o $@
run: all
	hatari -w --machine ste --memsize 4 --monitor rgb --confirm-quit false --fast-boot true FSCRL.PRG
debug: all analysis/FDBG.PRG
analysis/FDBG.PRG: fastscroll.o scroll_s.o $(GODLIB_DIR)/libgod.a
	mkdir -p analysis
	$(CC) $(LDFLAGS) -o $@ $(CRT) fastscroll.o scroll_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
scroll_s.o: scroll_s.s assets/BUGSY.BIN
	vasmm68k_mot -Felf -devpac $< -o $@
clean:
	rm -f *.o FSCRL.PRG analysis/FDBG.PRG
.PHONY: all run debug clean
