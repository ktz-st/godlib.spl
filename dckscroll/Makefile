CC = m68k-atari-mintelf-gcc
CMINI_DIR = ../../libcmini
GODLIB_DIR = ../../godlib
CFLAGS = -Wall -Os -mshort -mfastcall -m68000 -fpack-struct=2 -I../.. -I$(CMINI_DIR)/include
LDFLAGS = -nostdlib -nostartfiles -nodefaultlibs -static -mshort -mfastcall -m68000 -Wl,--gc-sections -Wl,--relax -L$(CMINI_DIR)/lib/mshort/mfastcall -L$(GODLIB_DIR)
CRT = $(CMINI_DIR)/lib/mshort/mfastcall/crt0.o
TOS ?= /Users/kriss/Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img
all: DCKSCRL.PRG
DCKSCRL.PRG: dckscroll.o dckscroll_s.o $(GODLIB_DIR)/libgod.a
	$(CC) $(LDFLAGS) -s -o $@ $(CRT) dckscroll.o dckscroll_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
dckscroll.o: dckscroll.c
	$(CC) $(CFLAGS) -c $< -o $@
dckscroll_s.o: dckscroll_s.s assets/FONT.BIN assets/PATHS.BIN assets/PALETTE.BIN assets/text.inc
	vasmm68k_mot -Felf -devpac $< -o $@
debug: DCKSCRL.PRG
	$(CC) $(CFLAGS) -DDCK_BENCH $(LDFLAGS) -Wl,-Map,/tmp/DCKDBG.map -o /tmp/DCKDBG.PRG $(CRT) dckscroll.c dckscroll_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
assets:
	python3 tools/assets.py
run: all
	hatari --tos "$(TOS)" --machine ste --memsize 4 --monitor rgb --confirm-quit false DCKSCRL.PRG
clean:
	rm -f *.o DCKSCRL.PRG
.PHONY: all debug assets run clean
