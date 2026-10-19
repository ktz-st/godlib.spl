CC = m68k-atari-mintelf-gcc
STRIP = m68k-atari-mintelf-strip
CMINI_DIR = ../../libcmini
GODLIB_DIR = ../../godlib
CFLAGS = -Wall -Os -mshort -mfastcall -m68000 -fpack-struct=2 -I../.. -I$(CMINI_DIR)/include
LDFLAGS = -s -nostdlib -nostartfiles -nodefaultlibs -static -mshort -mfastcall -m68000 -Wl,--gc-sections -Wl,--relax -L$(CMINI_DIR)/lib/mshort/mfastcall -L$(GODLIB_DIR)

all: PCMBLOCK.PRG VOICE12.RAW VOICE25.RAW

PCMBLOCK.PRG: pcmblock.o verify.o $(GODLIB_DIR)/libgod.a
	$(CC) $(LDFLAGS) -o $@ $(CMINI_DIR)/lib/crt0.o pcmblock.o verify.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
	$(STRIP) --strip-unneeded $@

pcmblock.o: pcmblock.c $(GODLIB_DIR)/audio/pcmblock.h
	$(CC) $(CFLAGS) -c $< -o $@
verify.o: verify.c
	$(CC) $(CFLAGS) -c $< -o $@

VOICE12.RAW: ../mixer/voice.raw prepare_sample.py
	python3 prepare_sample.py ../mixer/voice.raw

VOICE25.RAW: VOICE12.RAW
	test -f $@ || python3 prepare_sample.py ../mixer/voice.raw

run: all
	hatari -w --machine ste --memsize 4 --monitor rgb --fast-boot true PCMBLOCK.PRG
clean:
	rm -f pcmblock.o verify.o PCMBLOCK.PRG
.PHONY: all run clean

# Unstripped target for Hatari symbol-based validation.
debug: all analysis/PCMBLDBG.PRG
analysis/PCMBLDBG.PRG: pcmblock.o verify.o $(GODLIB_DIR)/libgod.a
	mkdir -p analysis
	$(CC) $(filter-out -s,$(LDFLAGS)) -Wl,-Map=analysis/pcmblock.map -o $@ $(CMINI_DIR)/lib/crt0.o pcmblock.o verify.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
.PHONY: debug
