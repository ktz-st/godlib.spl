CC = m68k-atari-mintelf-gcc
STRIP = m68k-atari-mintelf-strip
CMINI_DIR = ../../libcmini
GODLIB_DIR = ../../godlib
CFLAGS = -fno-strict-aliasing -Wall -Os -mshort -mfastcall -m68000 -fpack-struct=2 -I../.. -I$(CMINI_DIR)/include
LDFLAGS = -nostdlib -nostartfiles -nodefaultlibs -static -mshort -mfastcall -m68000 -Wl,--gc-sections -Wl,--relax -L$(CMINI_DIR)/lib/mshort/mfastcall -L$(GODLIB_DIR)
CRT = $(CMINI_DIR)/lib/mshort/mfastcall/crt0.o

all: WOBBLE.PRG
assets/PRESHIFT.BIN: assets/COAST.PI1 tools/prepare.py
	python3 tools/prepare.py
assets/PALETTE.BIN assets/LOOKUP.BIN: assets/PRESHIFT.BIN
	@test -f $@ || python3 tools/prepare.py
WOBBLE.PRG: wobble.o wobble_s.o $(GODLIB_DIR)/libgod.a
	$(CC) $(LDFLAGS) -s -o $@ $(CRT) wobble.o wobble_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
	$(STRIP) --strip-unneeded $@
wobble.o: wobble.c $(GODLIB_DIR)/screen/screen.h $(GODLIB_DIR)/video/video.h
	$(CC) $(CFLAGS) -c $< -o $@
run: all
	hatari -w --machine ste --memsize 4 --monitor rgb --confirm-quit false --fast-boot true WOBBLE.PRG
debug: all analysis/WDBG.PRG
analysis/WDBG.PRG: wobble.o wobble_s.o $(GODLIB_DIR)/libgod.a
	mkdir -p analysis
	$(CC) $(LDFLAGS) -o $@ $(CRT) wobble.o wobble_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
wobble_s.o: wobble_s.s assets/PRESHIFT.BIN assets/PALETTE.BIN assets/LOOKUP.BIN
	vasmm68k_mot -Felf -devpac $< -o $@
clean:
	rm -f *.o WOBBLE.PRG analysis/WDBG.PRG
.PHONY: all run debug clean

# Refresh this embedded copy from its original-RGB ABC2 asset pipeline.
assets/COAST.PI1: ../wipe/COAST.PI1
	cp $< $@
../wipe/COAST.PI1: ../wipe/assets/coast.png ../wipe/prepare_assets.py ../tools/abc2_assets.py
	$(MAKE) -C ../wipe COAST.PI1
