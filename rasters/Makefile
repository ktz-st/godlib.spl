CC = m68k-atari-mintelf-gcc
STRIP = m68k-atari-mintelf-strip
CMINI_DIR = ../../libcmini
GODLIB_DIR = ../../godlib
CFLAGS = -fno-strict-aliasing -Wall -Os -mshort -mfastcall -m68000 -fpack-struct=2 -I../.. -I$(CMINI_DIR)/include
LDFLAGS = -nostdlib -nostartfiles -nodefaultlibs -static -mshort -mfastcall -m68000 -Wl,--gc-sections -Wl,--relax -L$(CMINI_DIR)/lib/mshort/mfastcall -L$(GODLIB_DIR)
CRT = $(CMINI_DIR)/lib/mshort/mfastcall/crt0.o

all: RASTR.PRG
RASTR.PRG: rasters.o raster.o raster_s.o $(GODLIB_DIR)/libgod.a
	$(CC) $(LDFLAGS) -s -o $@ $(CRT) rasters.o raster.o raster_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
	$(STRIP) --strip-unneeded $@
rasters.o: rasters.c rasters.h $(GODLIB_DIR)/screen/screen.h $(GODLIB_DIR)/video/video.h
	$(CC) $(CFLAGS) -c $< -o $@
run: all
	hatari -w --machine ste --memsize 4 --monitor rgb --confirm-quit false --fast-boot true RASTR.PRG
debug: all analysis/RDBG.PRG
analysis/RDBG.PRG: rasters.o raster.o raster_s.o $(GODLIB_DIR)/libgod.a
	mkdir -p analysis
	$(CC) $(LDFLAGS) -o $@ $(CRT) rasters.o raster.o raster_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
raster.o: raster.c rasters.h
	$(CC) $(CFLAGS) -c $< -o $@
raster_s.o: raster_s.s
	vasmm68k_mot -Felf -devpac $< -o $@
clean:
	rm -f *.o RASTR.PRG analysis/RDBG.PRG
.PHONY: all run debug clean
