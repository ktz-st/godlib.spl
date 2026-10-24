CC = m68k-atari-mintelf-gcc
CMINI_DIR = ../../libcmini
GODLIB_DIR = ../../godlib
CFLAGS = -Wall -Os -mshort -mfastcall -m68000 -fpack-struct=2 -I../.. -I$(CMINI_DIR)/include
LDFLAGS = -nostdlib -nostartfiles -nodefaultlibs -static -mshort -mfastcall -m68000 -Wl,--gc-sections -Wl,--relax -L$(CMINI_DIR)/lib/mshort/mfastcall -L$(GODLIB_DIR)
CRT = $(CMINI_DIR)/lib/mshort/mfastcall/crt0.o
TOS ?= /Users/kriss/Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img
all: DCKVERT.PRG
DCKVERT.PRG: dckvert.o dckvert_s.o $(GODLIB_DIR)/libgod.a
	$(CC) $(LDFLAGS) -s -o $@ $(CRT) dckvert.o dckvert_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
dckvert.o: dckvert.c
	$(CC) $(CFLAGS) -c $< -o $@
dckvert_s.o: dckvert_s.s assets/FONT.BIN assets/PALETTE.BIN assets/text.inc
	vasmm68k_mot -Felf -devpac $< -o $@
debug: DCKVERT.PRG
	$(CC) $(CFLAGS) -DVERT_BENCH $(LDFLAGS) -Wl,-Map,/tmp/DCKVDBG.map -o /tmp/DCKVDBG.PRG $(CRT) dckvert.c dckvert_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
assets:
	python3 tools/assets.py
run: all
	hatari --tos "$(TOS)" --machine ste --memsize 4 --monitor rgb --confirm-quit false DCKVERT.PRG
clean:
	rm -f *.o DCKVERT.PRG
.PHONY: all debug assets run clean
