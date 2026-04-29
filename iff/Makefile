CC = m68k-atari-mintelf-gcc
LD = m68k-atari-mintelf-gcc
STRIP = m68k-atari-mintelf-strip

CMINI_DIR = ../../libcmini
GODLIB_DIR = ../../godlib

SOURCES_C = iff.c
OBJECTS_C = $(SOURCES_C:.c=.o)

DEFS = -DdGODLIB_FADE

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

OUT = IFFSHOW.TOS

$(OUT): $(OBJECTS_C)
	$(LD) $(LDFLAGS) -o $(OUT) $(CMINI_DIR)/lib/crt0.o \
	$(OBJECTS_C) \
	-Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
	$(STRIP) --strip-unneeded $(OUT)

$(OBJECTS_C): %.o: %.c
	$(CC) -c $(CFLAGS) $< -o $@

clean:
	rm -f $(OBJECTS_C) $(OUT) *.map

run: $(OUT)
	hatari -w --monitor rgb --fastfdc true $(OUT) &
