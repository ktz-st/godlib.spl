CC = m68k-atari-mintelf-gcc
STRIP = m68k-atari-mintelf-strip
CMINI_DIR = ../../libcmini
GODLIB_DIR = ../../godlib
CFLAGS = -fno-strict-aliasing -Wall -Os -mshort -mfastcall -m68000 -fpack-struct=2 -I../.. -I$(CMINI_DIR)/include
LDFLAGS = -nostdlib -nostartfiles -nodefaultlibs -static -mshort -mfastcall -m68000 -Wl,--gc-sections -Wl,--relax -L$(CMINI_DIR)/lib/mshort/mfastcall -L$(GODLIB_DIR)
CRT = $(CMINI_DIR)/lib/mshort/mfastcall/crt0.o

all: SPRCHUNK.PRG
SPRCHUNK.PRG: spritechunk.o $(GODLIB_DIR)/libgod.a
	$(CC) $(LDFLAGS) -s -o $@ $(CRT) spritechunk.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
	$(STRIP) --strip-unneeded $@
spritechunk.o: spritechunk.c $(GODLIB_DIR)/graphic/graphic.h
	$(CC) $(CFLAGS) -c $< -o $@
run: all
	hatari -w --machine st --memsize 4 --monitor rgb --fast-boot true SPRCHUNK.PRG
debug: all analysis/SPRCHDBG.PRG
analysis/SPRCHDBG.PRG: spritechunk.o $(GODLIB_DIR)/libgod.a
	mkdir -p analysis
	$(CC) $(LDFLAGS) -Wl,-Map=analysis/spritechunk.map -o $@ $(CRT) spritechunk.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
clean:
	rm -f spritechunk.o SPRCHUNK.PRG analysis/SPRCHDBG.PRG analysis/spritechunk.map
.PHONY: all run debug clean
