CC = m68k-atari-mintelf-gcc
STRIP = m68k-atari-mintelf-strip
CMINI_DIR = ../../libcmini
GODLIB_DIR = ../../godlib
CFLAGS = -fno-strict-aliasing -Wall -Os -mshort -mfastcall -m68000 -fpack-struct=2 -I../.. -I$(CMINI_DIR)/include
LDFLAGS = -nostdlib -nostartfiles -nodefaultlibs -static -mshort -mfastcall -m68000 -Wl,--gc-sections -Wl,--relax -L$(CMINI_DIR)/lib/mshort/mfastcall -L$(GODLIB_DIR)
CRT = $(CMINI_DIR)/lib/mshort/mfastcall/crt0.o

all: MOON.PRG
assets/IMAGE.BIN: prepare.py assets/source.png ../tools/abc2_assets.py
	python3 prepare.py
assets/PALETTE.BIN assets/FORE.BIN assets/PHASES.BIN assets/PATH.BIN assets/MOON.BIN assets/STARS.BIN assets/STARPOS.BIN assets/FORE_REF.BIN: assets/IMAGE.BIN
	@test -f $@ || python3 prepare.py
MOON.PRG: moon.o moon_s.o $(GODLIB_DIR)/libgod.a
	$(CC) $(LDFLAGS) -s -o $@ $(CRT) moon.o moon_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
	$(STRIP) --strip-unneeded $@
moon.o: moon.c $(GODLIB_DIR)/screen/screen.h $(GODLIB_DIR)/video/video.h
	$(CC) $(CFLAGS) -c $< -o $@
run: all
	hatari -w --spec512 1 --machine st --memsize 1 --monitor rgb --confirm-quit false --fast-boot true MOON.PRG
debug: all analysis/MNDBG.PRG
analysis/MNDBG.PRG: moon.o moon_s.o $(GODLIB_DIR)/libgod.a
	mkdir -p analysis
	$(CC) $(LDFLAGS) -o $@ $(CRT) moon.o moon_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
moon_s.o: moon_s.s assets/IMAGE.BIN assets/PALETTE.BIN assets/FORE.BIN assets/PHASES.BIN assets/PATH.BIN assets/MOON.BIN assets/STARS.BIN assets/STARPOS.BIN assets/FORE_REF.BIN
	vasmm68k_mot -Felf -devpac $< -o $@
clean:
	rm -f *.o MOON.PRG analysis/MNDBG.PRG
.PHONY: all run debug clean
