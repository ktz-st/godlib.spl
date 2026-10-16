CC = m68k-atari-mintelf-gcc
STRIP = m68k-atari-mintelf-strip
CMINI_DIR = ../../libcmini
GODLIB_DIR = ../../godlib
CFLAGS = -fno-strict-aliasing -Wall -Os -mshort -mfastcall -m68000 -fpack-struct=2 -I../.. -I$(CMINI_DIR)/include
LDFLAGS = -s -nostdlib -nostartfiles -nodefaultlibs -static -mshort -mfastcall -m68000 -Wl,--gc-sections -Wl,--relax -L$(CMINI_DIR)/lib/mshort/mfastcall -L$(GODLIB_DIR)

all: PCMVOICE.TOS

PCMVOICE.TOS: pcmvoice.o verify.o $(GODLIB_DIR)/libgod.a
	$(CC) $(LDFLAGS) -o $@ $(CMINI_DIR)/lib/mshort/mfastcall/crt0.o pcmvoice.o verify.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
	$(STRIP) --strip-unneeded $@

pcmvoice.o: pcmvoice.c $(GODLIB_DIR)/audio/pcmvoice.h
	$(CC) $(CFLAGS) -c $< -o $@

verify.o: verify.c
	$(CC) $(CFLAGS) -c $< -o $@

run: all
	hatari -w --machine ste --memsize 4 --monitor rgb --fast-boot true PCMVOICE.TOS

clean:
	rm -f pcmvoice.o verify.o PCMVOICE.TOS
.PHONY: all run clean

# Unstripped target for Hatari symbol-based validation.
debug: all analysis/PCMVODBG.TOS
analysis/PCMVODBG.TOS: pcmvoice.o verify.o $(GODLIB_DIR)/libgod.a
	mkdir -p analysis
	$(CC) $(filter-out -s,$(LDFLAGS)) -Wl,-Map=analysis/pcmvoice.map -o $@ $(CMINI_DIR)/lib/mshort/mfastcall/crt0.o pcmvoice.o verify.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
.PHONY: debug
