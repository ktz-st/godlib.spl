CC = m68k-atari-mintelf-gcc
STRIP = m68k-atari-mintelf-strip
CMINI_DIR = ../../libcmini
GODLIB_DIR = ../../godlib
CFLAGS = -fno-strict-aliasing -Wall -Os -mshort -mfastcall -m68000 -fpack-struct=2 -I../.. -I$(CMINI_DIR)/include
LDFLAGS = -s -nostdlib -nostartfiles -nodefaultlibs -static -mshort -mfastcall -m68000 -Wl,--gc-sections -Wl,--relax -L$(CMINI_DIR)/lib/mshort/mfastcall -L$(GODLIB_DIR)

all: PACMADMX.TOS

PACMADMX.TOS: pacmadmix.o verify.o $(GODLIB_DIR)/libgod.a
	$(CC) $(LDFLAGS) -o $@ $(CMINI_DIR)/lib/mshort/mfastcall/crt0.o pacmadmix.o verify.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
	$(STRIP) --strip-unneeded $@

pacmadmix.o: pacmadmix.c $(GODLIB_DIR)/audio/pacmadmix.h
	$(CC) $(CFLAGS) -c $< -o $@

verify.o: verify.c
	$(CC) $(CFLAGS) -c $< -o $@

run: all
	hatari -w --machine ste --memsize 4 --monitor rgb --fast-boot true PACMADMX.TOS

clean:
	rm -f pacmadmix.o verify.o PACMADMX.TOS
.PHONY: all run clean

# Unstripped target for Hatari symbol-based validation.
debug: all analysis/PACMADDBG.TOS
analysis/PACMADDBG.TOS: pacmadmix.o verify.o $(GODLIB_DIR)/libgod.a
	mkdir -p analysis
	$(CC) $(filter-out -s,$(LDFLAGS)) -Wl,-Map=analysis/pacmadmix.map -o $@ $(CMINI_DIR)/lib/mshort/mfastcall/crt0.o pacmadmix.o verify.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
.PHONY: debug
