CC = m68k-atari-mintelf-gcc
LD = m68k-atari-mintelf-gcc
STRIP = m68k-atari-mintelf-strip

CMINI_DIR = ../../libcmini
GODLIB_DIR = ../../godlib

SOURCES_C = leonard.c
OBJECTS_C = leonard$(RATE).o
OBJECTS_S = ../lancemod/visual_s.o ../lancemod/scope_s.o ../lancemod/xy_s.o ../lancemod/stereo_s.o

RATE ?= 25
ifeq ($(RATE),12)
RATE_ENUM = 1
else ifeq ($(RATE),25)
RATE_ENUM = 2
else
$(error RATE must be 12 or 25)
endif
DEFS = -DdGODLIB_FADE -DLEONARD_RATE=$(RATE_ENUM)

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

OUT = $(if $(filter 12,$(RATE)),LEO12.PRG,LEONARD.PRG)
DEBUG_OUT ?= $(if $(filter 12,$(RATE)),analysis/LEO12DBG.PRG,analysis/LEODBG.PRG)

$(OUT): $(OBJECTS_C) $(OBJECTS_S) $(GODLIB_DIR)/libgod.a | LOSTPARO.MOD
	$(LD) $(LDFLAGS) -s -o $(OUT) $(CMINI_DIR)/lib/mshort/mfastcall/crt0.o \
	$(OBJECTS_C) $(OBJECTS_S) \
	-Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
	$(STRIP) --strip-unneeded $(OUT)

$(OBJECTS_C): leonard.c $(GODLIB_DIR)/music/leonardmod.h
	$(CC) -c $(CFLAGS) $< -o $@

clean:
	rm -f leonard.o leonard12.o leonard25.o leonard_s.o $(OUT) analysis/*DBG.PRG LEONARD.PRG LEO12.PRG .rate-* *.map

TOS ?= /Users/kriss/Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img

run: $(OUT)
	hatari --tos "$(TOS)" -w --machine ste --memsize 1 --monitor rgb --confirm-quit false --fast-boot true $(OUT)

../lancemod/visual_s.o: ../lancemod/visual_s.s ../lancemod/assets/FRAMES.BIN ../lancemod/assets/SPANS.BIN ../lancemod/assets/PALETTE.BIN
	$(MAKE) -C ../lancemod visual_s.o

LOSTPARO.MOD: ../lancemod/LOSTPARO.MOD
	cp $< $@

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

analysis/LEOCHECK.PRG: analysis/vbl-check.c $(GODLIB_DIR)/libgod.a
	mkdir -p analysis
	$(LD) $(CFLAGS) $(LDFLAGS) -o $@ $(CMINI_DIR)/lib/mshort/mfastcall/crt0.o $< -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group

check:
	$(MAKE) RATE=25 debug
	$(MAKE) RATE=12 debug
	$(MAKE) analysis/LEOCHECK.PRG
	python3 analysis/verify-vbl.py
.PHONY: check
