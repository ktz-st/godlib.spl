CC = m68k-atari-mintelf-gcc
STRIP = m68k-atari-mintelf-strip
CMINI_DIR = ../../libcmini
GODLIB_DIR = ../../godlib
CFLAGS = -fno-strict-aliasing -Wall -Os -mshort -mfastcall -m68000 -fpack-struct=2 -I../.. -I$(CMINI_DIR)/include
LDFLAGS = -nostdlib -nostartfiles -nodefaultlibs -static -mshort -mfastcall -m68000 -Wl,--gc-sections -L$(CMINI_DIR)/lib/mshort/mfastcall -L$(GODLIB_DIR)
CRT = $(CMINI_DIR)/lib/mshort/mfastcall/crt0.o

all: SPEC.PRG SPEC4K.PRG
SPEC.PRG: spectrum.o spectrum_s.o $(GODLIB_DIR)/libgod.a
	$(CC) $(LDFLAGS) -s -o $@ $(CRT) spectrum.o spectrum_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
	$(STRIP) --strip-unneeded $@
spectrum.o: spectrum.c $(GODLIB_DIR)/screen/screen.h $(GODLIB_DIR)/video/video.h
	$(CC) $(CFLAGS) -c $< -o $@
run: all
	hatari -w --machine ste --memsize 4 --monitor rgb --confirm-quit false --fast-boot true SPEC.PRG
debug: all analysis/PDBG.PRG
analysis/PDBG.PRG: spectrum.o spectrum_s.o $(GODLIB_DIR)/libgod.a
	mkdir -p analysis
	$(CC) $(LDFLAGS) -o $@ $(CRT) spectrum.o spectrum_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
spectrum_s.o: spectrum_s.s assets/PIXELS.BIN assets/PALST.BIN assets/PALSTE.BIN
	vasmm68k_mot -Felf -devpac $< -o $@
clean:
	rm -f *.o SPEC.PRG SPEC4K.PRG analysis/PDBG.PRG
.PHONY: all run debug clean assets

assets: assets/PIXELS.BIN assets/PALST.BIN assets/PALSTE.BIN assets/CHARTPIX.BIN assets/CHARTST.BIN assets/CHARTSTE.BIN
assets/PIXELS.BIN assets/PALST.BIN assets/PALSTE.BIN: assets/PICTURE.SPU tools/prepare.py
	python3 tools/prepare.py

SPEC4K.PRG: spectrum.o spectrum_chart_s.o $(GODLIB_DIR)/libgod.a
	$(CC) $(LDFLAGS) -s -o $@ $(CRT) spectrum.o spectrum_chart_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
	$(STRIP) --strip-unneeded $@
spectrum_chart_s.o: spectrum_s.s assets/CHARTPIX.BIN assets/CHARTST.BIN assets/CHARTSTE.BIN
	vasmm68k_mot -DSPECTRUM_CHART=1 -Felf -devpac $< -o $@
assets/CHARTPIX.BIN assets/CHARTST.BIN assets/CHARTSTE.BIN: tools/chart.py
	python3 tools/chart.py
