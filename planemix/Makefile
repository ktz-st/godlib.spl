CC = m68k-atari-mintelf-gcc
STRIP = m68k-atari-mintelf-strip
CMINI_DIR = ../../libcmini
GODLIB_DIR = ../../godlib
CFLAGS = -fno-strict-aliasing -Wall -Os -mshort -mfastcall -m68000 -fpack-struct=2 -I../.. -I$(CMINI_DIR)/include
LDFLAGS = -nostdlib -nostartfiles -nodefaultlibs -static -mshort -mfastcall -m68000 -Wl,--gc-sections -Wl,--relax -L$(CMINI_DIR)/lib/mshort/mfastcall -L$(GODLIB_DIR)
CRT = $(CMINI_DIR)/lib/mshort/mfastcall/crt0.o

all: LAYFX.PRG
LAYFX.PRG: planemix.o planemix_s.o $(GODLIB_DIR)/libgod.a
	$(CC) $(LDFLAGS) -s -o $@ $(CRT) planemix.o planemix_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
	$(STRIP) --strip-unneeded $@
planemix.o: planemix.c $(GODLIB_DIR)/screen/screen.h $(GODLIB_DIR)/video/video.h
	$(CC) $(CFLAGS) -c $< -o $@
run: all
	hatari -w --spec512 1 --machine st --memsize 4 --monitor rgb --confirm-quit false --fast-boot true LAYFX.PRG
debug: all analysis/LAYDB.PRG
analysis/LAYDB.PRG: planemix.o planemix_s.o $(GODLIB_DIR)/libgod.a
	mkdir -p analysis
	$(CC) $(LDFLAGS) -o $@ $(CRT) planemix.o planemix_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
planemix_s.o: planemix_s.s
	vasmm68k_mot -Felf -devpac $< -o $@
clean:
	rm -f *.o LAYFX.PRG analysis/LAYDB.PRG
.PHONY: all run debug clean
