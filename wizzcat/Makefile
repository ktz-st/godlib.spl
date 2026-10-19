CC = m68k-atari-mintelf-gcc
LD = m68k-atari-mintelf-gcc
STRIP = m68k-atari-mintelf-strip

CMINI_DIR = ../../libcmini
GODLIB_DIR = ../../godlib

SOURCES_C = wizzcat.c
OBJECTS_C = wizzcat.o
OBJECTS_S = ../lancemod/visual_s.o ../lancemod/scope_s.o ../lancemod/xy_s.o ../lancemod/stereo_s.o

DEFS = -DdGODLIB_FADE

CFLAGS  = -Wall -Os -mshort -mfastcall -m68000 \
          -I. -I$(CMINI_DIR)/include -I../..

CFLAGS += -fno-jump-tables -fno-tree-switch-conversion \
          -fomit-frame-pointer -fno-unwind-tables -fno-asynchronous-unwind-tables \
          -fmerge-constants -fno-ident \
          -fno-inline-functions -fno-inline-small-functions \
          -fpack-struct=2 \
          $(DEFS)

LDFLAGS = -nostdlib -nostartfiles -nodefaultlibs -static \
          -mshort -mfastcall -m68000 \
          -Wl,--gc-sections -Wl,--relax \
          -L$(CMINI_DIR)/lib/mshort/mfastcall \
          -L$(GODLIB_DIR)

OUT = WIZZCAT.PRG
DEBUG_OUT ?= analysis/WIZDBG.PRG

$(OUT): $(OBJECTS_C) $(OBJECTS_S) $(GODLIB_DIR)/libgod.a
	$(LD) $(LDFLAGS) -s -o $(OUT) $(CMINI_DIR)/lib/mshort/mfastcall/crt0.o \
	$(OBJECTS_C) $(OBJECTS_S) \
	-Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
	$(STRIP) --strip-unneeded $(OUT)

$(OBJECTS_C): wizzcat.c $(GODLIB_DIR)/music/wizzcat.h
	$(CC) -c $(CFLAGS) $< -o $@

clean:
	rm -f $(OBJECTS_C) $(OUT) analysis/*DBG.PRG *.map

run: $(OUT)
	hatari -w --machine ste --memsize 1 --monitor rgb --confirm-quit false --fast-boot true $(OUT)

../lancemod/visual_s.o: ../lancemod/visual_s.s ../lancemod/assets/FRAMES.BIN ../lancemod/assets/SPANS.BIN ../lancemod/assets/PALETTE.BIN
	$(MAKE) -C ../lancemod visual_s.o


debug: $(OUT) $(DEBUG_OUT)
$(DEBUG_OUT): $(OBJECTS_C) $(OBJECTS_S) $(GODLIB_DIR)/libgod.a
	mkdir -p analysis
	$(LD) $(LDFLAGS) -o $@ $(CMINI_DIR)/lib/mshort/mfastcall/crt0.o $(OBJECTS_C) $(OBJECTS_S) -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group

.PHONY: clean run debug

../lancemod/scope_s.o: ../lancemod/scope_s.s
	$(MAKE) -C ../lancemod scope_s.o

$(OBJECTS_C): $(GODLIB_DIR)/music/modscope.h

../lancemod/xy_s.o: ../lancemod/xy_s.s
	$(MAKE) -C ../lancemod xy_s.o

../lancemod/stereo_s.o: ../lancemod/stereo_s.s
	$(MAKE) -C ../lancemod stereo_s.o
