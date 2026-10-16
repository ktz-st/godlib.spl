CC = m68k-atari-mintelf-gcc
STRIP = m68k-atari-mintelf-strip
CMINI_DIR = ../../libcmini
GODLIB_DIR = ../../godlib
CFLAGS = -fno-strict-aliasing -Wall -Os -mshort -mfastcall -m68000 -fpack-struct=2 -I../.. -I$(CMINI_DIR)/include
LDFLAGS = -nostdlib -nostartfiles -nodefaultlibs -static -mshort -mfastcall -m68000 -Wl,--gc-sections -Wl,--relax -L$(CMINI_DIR)/lib/mshort/mfastcall -L$(GODLIB_DIR)
CRT = $(CMINI_DIR)/lib/mshort/mfastcall/crt0.o

all: SPLITH.PRG
SPLITH.PRG: splitscreenh.o split.o split_s.o $(GODLIB_DIR)/libgod.a
	$(CC) $(LDFLAGS) -s -o $@ $(CRT) splitscreenh.o split.o split_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
	$(STRIP) --strip-unneeded $@
splitscreenh.o: splitscreenh.c split.h $(GODLIB_DIR)/screen/screen.h $(GODLIB_DIR)/video/video.h
	$(CC) $(CFLAGS) -c $< -o $@
run: all
	hatari -w --machine ste --memsize 4 --monitor rgb --confirm-quit false --fast-boot true SPLITH.PRG
debug: all analysis/SPLITHDB.PRG
analysis/SPLITHDB.PRG: splitscreenh.o split.o split_s.o $(GODLIB_DIR)/libgod.a
	mkdir -p analysis
	$(CC) $(LDFLAGS) -o $@ $(CRT) splitscreenh.o split.o split_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
split.o: split.c split.h
	$(CC) $(CFLAGS) -c $< -o $@
split_s.o: split_s.s PANORAMA.BIN
	vasmm68k_mot -Felf -devpac $< -o $@
clean:
	rm -f *.o SPLITH.PRG analysis/SPLITHDB.PRG
.PHONY: all run debug clean
