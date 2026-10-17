CC = m68k-atari-mintelf-gcc
STRIP = m68k-atari-mintelf-strip
CMINI_DIR = ../../libcmini
GODLIB_DIR = ../../godlib
CFLAGS = -fno-strict-aliasing -Wall -Os -mshort -mfastcall -m68000 -fpack-struct=2 -I../.. -I$(CMINI_DIR)/include
LDFLAGS = -nostdlib -nostartfiles -nodefaultlibs -static -mshort -mfastcall -m68000 -Wl,--gc-sections -Wl,--relax -L$(CMINI_DIR)/lib/mshort/mfastcall -L$(GODLIB_DIR)
CRT = $(CMINI_DIR)/lib/mshort/mfastcall/crt0.o

all: SNOW.PRG
assets/WINTER.BIN: assets/winter-source.png tools/prepare.py ../tools/abc2_assets.py
	python3 tools/prepare.py
assets/palette.h: assets/WINTER.BIN
	@test -f $@ || python3 tools/prepare.py
SNOW.PRG: snowfall.o snow_s.o $(GODLIB_DIR)/libgod.a
	$(CC) $(LDFLAGS) -s -o $@ $(CRT) snowfall.o snow_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
	$(STRIP) --strip-unneeded $@
snowfall.o: snowfall.c assets/palette.h $(GODLIB_DIR)/screen/screen.h $(GODLIB_DIR)/video/video.h
	$(CC) $(CFLAGS) -c $< -o $@
run: all
	hatari -w --machine ste --memsize 4 --monitor rgb --confirm-quit false --fast-boot true SNOW.PRG
debug: all analysis/SDBG.PRG
analysis/SDBG.PRG: snowfall.o snow_s.o $(GODLIB_DIR)/libgod.a
	mkdir -p analysis
	$(CC) $(LDFLAGS) -o $@ $(CRT) snowfall.o snow_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
snow_s.o: snow_s.s assets/WINTER.BIN
	vasmm68k_mot -Felf -devpac $< -o $@
clean:
	rm -f *.o SNOW.PRG analysis/*.o analysis/SDBG.PRG analysis/SVER.PRG analysis/BASE.PRG analysis/BASESY.PRG
.PHONY: all run debug clean verify baseline

verify: analysis/SVER.PRG
analysis/SVER.PRG: analysis/verify.o analysis/reference_s.o snow_s.o $(GODLIB_DIR)/libgod.a
	$(CC) $(LDFLAGS) -o $@ $(CRT) analysis/verify.o analysis/reference_s.o snow_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
analysis/verify.o: snowfall.c assets/palette.h
	$(CC) $(CFLAGS) -DSNOW_VERIFY -c $< -o $@
analysis/reference_s.o: analysis/reference_s.s
	vasmm68k_mot -Felf -devpac $< -o $@

baseline: analysis/BASE.PRG analysis/BASESY.PRG
analysis/BASE.PRG: analysis/BASESY.PRG
	cp $< $@
	$(STRIP) --strip-unneeded $@
analysis/BASESY.PRG: analysis/baseline.o analysis/baseline_s.o $(GODLIB_DIR)/libgod.a
	$(CC) $(LDFLAGS) -o $@ $(CRT) analysis/baseline.o analysis/baseline_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
analysis/baseline.o: analysis/baseline.c assets/palette.h
	$(CC) $(CFLAGS) -I. -c $< -o $@
analysis/baseline_s.o: analysis/baseline_s.s assets/WINTER.BIN
	vasmm68k_mot -Felf -devpac $< -o $@
