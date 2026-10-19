CC = m68k-atari-mintelf-gcc
LD = m68k-atari-mintelf-gcc
STRIP = m68k-atari-mintelf-strip

CMINI_DIR = ../../libcmini
GODLIB_DIR = ../../godlib

SOURCES_C = lancemod.c
OBJECTS_C = $(SOURCES_C:.c=.o)
OBJECTS_S = visual_s.o scope_s.o xy_s.o stereo_s.o

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

OUT = LANCEMOD.PRG

$(OUT): $(OBJECTS_C) $(OBJECTS_S) $(GODLIB_DIR)/libgod.a
	$(LD) $(LDFLAGS) -s -o $(OUT) $(CMINI_DIR)/lib/mshort/mfastcall/crt0.o \
	$(OBJECTS_C) $(OBJECTS_S) \
	-Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
	$(STRIP) --strip-unneeded $(OUT)

$(OBJECTS_C): %.o: %.c
	$(CC) -c $(CFLAGS) $< -o $@

clean:
	rm -f $(OBJECTS_C) $(OBJECTS_S) $(OUT) analysis/LMDBG.PRG *.map

run: $(OUT)
	hatari -w --machine ste --memsize 1 --monitor rgb --confirm-quit false --fast-boot true $(OUT)

visual_s.o: visual_s.s assets/FRAMES.BIN assets/SPANS.BIN assets/PALETTE.BIN
	vasmm68k_mot -Felf -devpac $< -o $@

$(OBJECTS_C): $(GODLIB_DIR)/music/lancemod.h

assets/FRAMES.BIN: prepare.py assets/STF_VU.DAT
	python3 prepare.py
assets/SPANS.BIN assets/PALETTE.BIN: assets/FRAMES.BIN
	@test -f $@ || python3 prepare.py

debug: $(OUT) analysis/LMDBG.PRG
analysis/LMDBG.PRG: $(OBJECTS_C) $(OBJECTS_S) $(GODLIB_DIR)/libgod.a
	mkdir -p analysis
	$(LD) $(LDFLAGS) -o $@ $(CMINI_DIR)/lib/mshort/mfastcall/crt0.o $(OBJECTS_C) $(OBJECTS_S) -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group

.PHONY: clean run debug

scope_s.o: scope_s.s
	vasmm68k_mot -Felf $< -o $@

$(OBJECTS_C): $(GODLIB_DIR)/music/modscope.h

xy_s.o: xy_s.s
	vasmm68k_mot -Felf $< -o $@

stereo_s.o: stereo_s.s
	vasmm68k_mot -Felf $< -o $@
