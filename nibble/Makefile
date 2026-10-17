CC = m68k-atari-mintelf-gcc
STRIP = m68k-atari-mintelf-strip
CMINI_DIR = ../../libcmini
GODLIB_DIR = ../../godlib
CFLAGS = -fno-strict-aliasing -Wall -Os -mshort -mfastcall -m68000 -fpack-struct=2 -I../.. -I$(CMINI_DIR)/include
LDFLAGS = -nostdlib -nostartfiles -nodefaultlibs -static -mshort -mfastcall -m68000 -Wl,--gc-sections -Wl,--relax -L$(CMINI_DIR)/lib/mshort/mfastcall -L$(GODLIB_DIR)
CRT = $(CMINI_DIR)/lib/mshort/mfastcall/crt0.o

all: NIBBLE.PRG
NIBBLE.PRG: nibble.o nibble_s.o $(GODLIB_DIR)/libgod.a
	$(CC) $(LDFLAGS) -s -o $@ $(CRT) nibble.o nibble_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
	$(STRIP) --strip-unneeded $@
nibble.o: nibble.c $(GODLIB_DIR)/screen/screen.h $(GODLIB_DIR)/video/video.h
	$(CC) $(CFLAGS) -c $< -o $@
run: all
	hatari -w --machine st --memsize 4 --monitor rgb --confirm-quit false --fast-boot true NIBBLE.PRG
debug: all analysis/NDBG.PRG
analysis/NDBG.PRG: nibble.o nibble_s.o $(GODLIB_DIR)/libgod.a
	mkdir -p analysis
	$(CC) $(LDFLAGS) -o $@ $(CRT) nibble.o nibble_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
nibble_s.o: nibble_s.s assets/LOST16.FON assets/NIBBLE.DAT assets/NIBBLE1.DAT
	vasmm68k_mot -Felf -devpac $< -o $@
clean:
	rm -f *.o NIBBLE.PRG analysis/NDBG.PRG
.PHONY: all run debug clean
