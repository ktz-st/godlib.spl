CC = m68k-atari-mintelf-gcc
LD = m68k-atari-mintelf-gcc
STRIP = m68k-atari-mintelf-strip

CMINI_DIR = ../../libcmini
GODLIB_DIR = ../../godlib

SOURCES_C = mixer.c
OBJECTS_C = $(SOURCES_C:.c=.o)

DEFS = -DdGODLIB_FADE -DdGODLIB_AUDIO_MIXER

CFLAGS  = -Wall -Os -mshort -mfastcall -m68000 \
          -I. -I$(CMINI_DIR)/include -I../..

CFLAGS += -fno-jump-tables -fno-tree-switch-conversion \
          -fomit-frame-pointer -fno-unwind-tables -fno-asynchronous-unwind-tables \
          -fmerge-constants -fno-ident \
          -fno-inline-functions -fno-inline-small-functions \
          -fpack-struct=2 \
          $(DEFS)

LDFLAGS = -s -nostdlib -nostartfiles -nodefaultlibs -static \
          -mshort -mfastcall -m68000 \
          -Wl,--gc-sections -Wl,--relax \
          -L$(CMINI_DIR)/lib/mshort/mfastcall \
          -L$(GODLIB_DIR)

OUT = MIXER.PRG

all: $(OUT)

$(OUT): $(OBJECTS_C) $(GODLIB_DIR)/libgod.a
	$(LD) $(LDFLAGS) -o $(OUT) $(CMINI_DIR)/lib/mshort/mfastcall/crt0.o \
	$(OBJECTS_C) \
	-Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
	$(STRIP) --strip-unneeded $(OUT)

$(OBJECTS_C): %.o: %.c
	$(CC) -c $(CFLAGS) $< -o $@

clean:
	rm -rf $(OBJECTS_C) $(OUT) *.map

TOS ?= /Users/kriss/Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img
run: $(OUT)
	hatari --tos "$(TOS)" --machine ste --memsize 1 --monitor rgb --confirm-quit false $(OUT)

analysis/AMIXDBG.PRG: analysis/check.c $(GODLIB_DIR)/audio/amixer.c $(GODLIB_DIR)/audio/amixer.h $(GODLIB_DIR)/libgod.a
	$(CC) $(CFLAGS) $(filter-out -s,$(LDFLAGS)) -o $@ $(CMINI_DIR)/lib/mshort/mfastcall/crt0.o $< -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
analysis/AMIXUI.PRG: $(OBJECTS_C) $(GODLIB_DIR)/libgod.a
	$(CC) $(filter-out -s,$(LDFLAGS)) -o $@ $(CMINI_DIR)/lib/mshort/mfastcall/crt0.o $(OBJECTS_C) -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
check: $(OUT) analysis/AMIXDBG.PRG analysis/AMIXUI.PRG
	python3 analysis/verify.py
	python3 analysis/verify-ui.py
.PHONY: all run check

bench: $(GODLIB_DIR)/libgod.a
	bash analysis/build-bench.sh
profile: bench
	python3 analysis/profile.py
.PHONY: bench profile
