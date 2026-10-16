CC = m68k-atari-mintelf-gcc
STRIP = m68k-atari-mintelf-strip
CMINI_DIR = ../../libcmini
GODLIB_DIR = ../../godlib
CFLAGS = -Wall -Os -mshort -mfastcall -m68000 -fpack-struct=2 -I../.. -I$(CMINI_DIR)/include
LDFLAGS = -s -nostdlib -nostartfiles -nodefaultlibs -static -mshort -mfastcall -m68000 -Wl,--gc-sections -Wl,--relax -L$(CMINI_DIR)/lib/mshort/mfastcall -L$(GODLIB_DIR)

all: PCMFRAME.TOS VOICE.RAW

PCMFRAME.TOS: pcmframe.o $(GODLIB_DIR)/libgod.a
	$(CC) $(LDFLAGS) -o $@ $(CMINI_DIR)/lib/crt0.o pcmframe.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
	$(STRIP) --strip-unneeded $@

pcmframe.o: pcmframe.c $(GODLIB_DIR)/audio/pcmframe.h
	$(CC) $(CFLAGS) -c $< -o $@

VOICE.RAW: ../mixer/voice.raw prepare_sample.py
	python3 prepare_sample.py $< $@

run: all
	hatari -w --machine ste --memsize 4 --monitor rgb --fast-boot true PCMFRAME.TOS

clean:
	rm -f pcmframe.o PCMFRAME.TOS
.PHONY: all run clean

# Unstripped target for Hatari symbol-based validation.
debug: all analysis/PCMFRDBG.TOS
analysis/PCMFRDBG.TOS: pcmframe.o $(GODLIB_DIR)/libgod.a
	mkdir -p analysis
	$(CC) $(filter-out -s,$(LDFLAGS)) -Wl,-Map=analysis/pcmframe.map -o $@ $(CMINI_DIR)/lib/crt0.o pcmframe.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
.PHONY: debug
