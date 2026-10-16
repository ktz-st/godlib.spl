CC = m68k-atari-mintelf-gcc
STRIP = m68k-atari-mintelf-strip
CMINI_DIR = ../../libcmini
GODLIB_DIR = ../../godlib
CFLAGS = -fno-strict-aliasing -Wall -Os -mshort -mfastcall -m68000 -fpack-struct=2 -I../.. -I$(CMINI_DIR)/include
LDFLAGS = -nostdlib -nostartfiles -nodefaultlibs -static -mshort -mfastcall -m68000 -Wl,--gc-sections -Wl,--relax -L$(CMINI_DIR)/lib/mshort/mfastcall -L$(GODLIB_DIR)
CRT = $(CMINI_DIR)/lib/mshort/mfastcall/crt0.o

all: PALFX.PRG
PALFX.PRG: palsplit.o raster.o raster_s.o $(GODLIB_DIR)/libgod.a
	$(CC) $(LDFLAGS) -s -o $@ $(CRT) palsplit.o raster.o raster_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
	$(STRIP) --strip-unneeded $@
palsplit.o: palsplit.c palsplit.h $(GODLIB_DIR)/screen/screen.h $(GODLIB_DIR)/video/video.h
	$(CC) $(CFLAGS) -c $< -o $@
run: all
	hatari -w --machine ste --memsize 4 --monitor rgb --confirm-quit false --fast-boot true PALFX.PRG
debug: all analysis/PALDBG.PRG
analysis/PALDBG.PRG: palsplit.o raster.o raster_s.o $(GODLIB_DIR)/libgod.a
	mkdir -p analysis
	$(CC) $(LDFLAGS) -o $@ $(CRT) palsplit.o raster.o raster_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
raster.o: raster.c palsplit.h
	$(CC) $(CFLAGS) -c $< -o $@
raster_s.o: raster_s.s COAST.PI1
	vasmm68k_mot -Felf -devpac $< -o $@
clean:
	rm -f *.o PALFX.PRG PALSPLIT.PRG analysis/PALDBG.PRG
.PHONY: all run debug clean
