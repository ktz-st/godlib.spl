CC = m68k-atari-mintelf-gcc
LD = m68k-atari-mintelf-gcc
STRIP = m68k-atari-mintelf-strip

CMINI_DIR = ../../libcmini
GODLIB_DIR = ../../godlib

SOURCES_C = sndh.c
OBJECTS_C = $(SOURCES_C:.c=.o)
OBJECTS_S = bars_s.o psg_s.o spectrum_s.o extra_s.o organ_s.o

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

OUT = SNDH.TOS
TOS ?= /Users/kriss/Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img

$(OUT): $(OBJECTS_C) $(OBJECTS_S) $(GODLIB_DIR)/libgod.a
	$(LD) $(LDFLAGS) -s -o $(OUT) $(CMINI_DIR)/lib/mshort/mfastcall/crt0.o \
	$(OBJECTS_C) $(OBJECTS_S) \
	-Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
	$(STRIP) --strip-unneeded $(OUT)

$(OBJECTS_C): %.o: %.c
	$(CC) -c $(CFLAGS) $< -o $@

clean:
	rm -f $(OBJECTS_C) $(OBJECTS_S) $(OUT) build/SNDBG.PRG *.map

run: $(OUT)
	hatari --tos "$(TOS)" -w --machine ste --memsize 1 --monitor rgb --confirm-quit false --fast-boot true $(OUT)

%.o: %.s
	vasmm68k_mot -Felf -devpac $< -o $@

psg_s.o: assets/NOTES.BIN
bars_s.o: assets/FRAMES8.BIN assets/SPANS.BIN assets/PALETTE.BIN
$(OBJECTS_C): visual.h
assets:
	python3 prepare.py
	python3 prepare_extra.py
debug: $(OUT)
	mkdir -p build
	$(LD) $(LDFLAGS) -o build/SNDBG.PRG $(CMINI_DIR)/lib/mshort/mfastcall/crt0.o $(OBJECTS_C) $(OBJECTS_S) -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
.PHONY: clean run debug assets

extra_s.o: assets/PIANO.BIN assets/KEYOFF.BIN assets/KEYS.BIN assets/SCOPESTEP.BIN assets/RINGS.S

organ_s.o: assets/ORGAN.BIN assets/ORGANPAL.BIN
