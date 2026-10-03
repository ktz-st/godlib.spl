CC = m68k-atari-mintelf-gcc
STRIP = m68k-atari-mintelf-strip
CMINI_DIR = ../../libcmini
GODLIB_DIR = ../../godlib
CFLAGS = -fno-strict-aliasing -Wall -Os -mshort -mfastcall -m68000 -fpack-struct=2 -I../.. -I$(CMINI_DIR)/include
LDFLAGS = -s -nostdlib -nostartfiles -nodefaultlibs -static -mshort -mfastcall -m68000 -Wl,--gc-sections -Wl,--relax -L$(CMINI_DIR)/lib/mshort/mfastcall -L$(GODLIB_DIR)

all: DESERTMX.TOS VOICE.RAW

DESERTMX.TOS: desertmix.o verify.o $(GODLIB_DIR)/libgod.a
	$(CC) $(LDFLAGS) -o $@ $(CMINI_DIR)/lib/crt0.o desertmix.o verify.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
	$(STRIP) --strip-unneeded $@

desertmix.o: desertmix.c $(GODLIB_DIR)/audio/desertmix.h
	$(CC) $(CFLAGS) -c $< -o $@

verify.o: verify.c
	$(CC) $(CFLAGS) -c $< -o $@

VOICE.RAW: ../mixer/voice.raw prepare_sample.py
	python3 prepare_sample.py $< $@

run: all
	hatari -w --machine ste --memsize 4 --monitor rgb --fast-boot true DESERTMX.TOS

clean:
	rm -f desertmix.o verify.o DESERTMX.TOS
.PHONY: all run clean

# Unstripped target for Hatari symbol-based validation.
debug: all analysis/DESERTDBG.TOS
analysis/DESERTDBG.TOS: desertmix.o verify.o $(GODLIB_DIR)/libgod.a
	mkdir -p analysis
	$(CC) $(filter-out -s,$(LDFLAGS)) -Wl,-Map=analysis/desertmix.map -o $@ $(CMINI_DIR)/lib/crt0.o desertmix.o verify.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
.PHONY: debug
