CC = m68k-atari-mintelf-gcc
STRIP = m68k-atari-mintelf-strip
CMINI_DIR = ../../libcmini
GODLIB_DIR = ../../godlib
CFLAGS = -fno-strict-aliasing -Wall -Os -mshort -mfastcall -m68000 -fpack-struct=2 -I../.. -I$(CMINI_DIR)/include
LDFLAGS = -nostdlib -nostartfiles -nodefaultlibs -static -mshort -mfastcall -m68000 -Wl,--gc-sections -Wl,--relax -L$(CMINI_DIR)/lib/mshort/mfastcall -L$(GODLIB_DIR)
CRT = $(CMINI_DIR)/lib/mshort/mfastcall/crt0.o

all: SCROLL8.PRG
SCROLL8.PRG: scroll8.o scroll8_s.o $(GODLIB_DIR)/libgod.a
	$(CC) $(LDFLAGS) -s -o $@ $(CRT) scroll8.o scroll8_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
	$(STRIP) --strip-unneeded $@
scroll8.o: scroll8.c text.h $(GODLIB_DIR)/screen/screen.h $(GODLIB_DIR)/video/video.h
	$(CC) $(CFLAGS) -c $< -o $@
run: all
	hatari -w --spec512 1 --machine st --memsize 4 --monitor rgb --confirm-quit false --fast-boot true SCROLL8.PRG
debug: all analysis/S8DBG.PRG
analysis/S8DBG.PRG: scroll8.o scroll8_s.o $(GODLIB_DIR)/libgod.a
	mkdir -p analysis
	$(CC) $(LDFLAGS) -o $@ $(CRT) scroll8.o scroll8_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
scroll8_s.o: scroll8_s.s
	vasmm68k_mot -Felf -devpac $< -o $@
clean:
	rm -f *.o SCROLL8.PRG analysis/S8DBG.PRG
.PHONY: all run debug clean
