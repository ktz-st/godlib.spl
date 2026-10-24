CC = m68k-atari-mintelf-gcc
CMINI_DIR = ../../libcmini
GODLIB_DIR = ../../godlib
CFLAGS = -Wall -Os -mshort -mfastcall -m68000 -fpack-struct=2 -I../.. -I$(CMINI_DIR)/include
LDFLAGS = -nostdlib -nostartfiles -nodefaultlibs -static -mshort -mfastcall -m68000 -Wl,--gc-sections -Wl,--relax -L$(CMINI_DIR)/lib/mshort/mfastcall -L$(GODLIB_DIR)
CRT = $(CMINI_DIR)/lib/mshort/mfastcall/crt0.o
TOS ?= /Users/kriss/Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img
all: DCKMULTI.PRG
DCKMULTI.PRG: dckmulti.o dckmulti_s.o $(GODLIB_DIR)/libgod.a
	$(CC) $(LDFLAGS) -s -o $@ $(CRT) dckmulti.o dckmulti_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
dckmulti.o: dckmulti.c
	$(CC) $(CFLAGS) -c $< -o $@
dckmulti_s.o: dckmulti_s.s assets/FONT.BIN assets/PALETTE.BIN assets/text.inc assets/tables.inc assets/config.inc
	vasmm68k_mot -Felf -devpac $< -o $@
debug: DCKMULTI.PRG
	$(CC) $(CFLAGS) -DHS_BENCH $(LDFLAGS) -Wl,-Map,/tmp/DCKMDBG.map -o /tmp/DCKMDBG.PRG $(CRT) dckmulti.c dckmulti_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
assets:
	python3 tools/assets.py
run: all
	hatari --tos "$(TOS)" --machine ste --memsize 4 --monitor rgb --confirm-quit false DCKMULTI.PRG
clean:
	rm -f *.o DCKMULTI.PRG
.PHONY: all debug assets run clean
