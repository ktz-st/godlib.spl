CC = m68k-atari-mintelf-gcc
STRIP = m68k-atari-mintelf-strip
CMINI_DIR = ../../libcmini
GODLIB_DIR = ../../godlib
CFLAGS = -fno-strict-aliasing -Wall -Os -mshort -mfastcall -m68000 -fpack-struct=2 -I../.. -I$(CMINI_DIR)/include
LDFLAGS = -nostdlib -nostartfiles -nodefaultlibs -static -mshort -mfastcall -m68000 -Wl,--gc-sections -Wl,--relax -L$(CMINI_DIR)/lib/mshort/mfastcall -L$(GODLIB_DIR)
CRT = $(CMINI_DIR)/lib/mshort/mfastcall/crt0.o

all: CHKFX.PRG
assets/SPANS.BIN: prepare.py
	python3 prepare.py
assets/OFFSETS.BIN assets/PARAMS.BIN: assets/SPANS.BIN
	@test -f $@ || python3 prepare.py
CHKFX.PRG: checker.o checker_s.o $(GODLIB_DIR)/libgod.a
	$(CC) $(LDFLAGS) -s -o $@ $(CRT) checker.o checker_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
	$(STRIP) --strip-unneeded $@
checker.o: checker.c $(GODLIB_DIR)/screen/screen.h $(GODLIB_DIR)/video/video.h
	$(CC) $(CFLAGS) -c $< -o $@
run: all
	hatari -w --spec512 1 --machine st --memsize 4 --monitor rgb --confirm-quit false --fast-boot true CHKFX.PRG
debug: all analysis/CHKDBG.PRG assets/PARAMS.BIN
analysis/CHKDBG.PRG: checker.o checker_s.o $(GODLIB_DIR)/libgod.a
	mkdir -p analysis
	$(CC) $(LDFLAGS) -o $@ $(CRT) checker.o checker_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
checker_s.o: checker_s.s assets/SPANS.BIN assets/OFFSETS.BIN
	vasmm68k_mot -Felf -devpac $< -o $@
clean:
	rm -f *.o CHKFX.PRG analysis/CHKDBG.PRG
.PHONY: all run debug clean
