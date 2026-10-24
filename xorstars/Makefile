CC = m68k-atari-mintelf-gcc
CMINI_DIR = ../../libcmini
GODLIB_DIR = ../../godlib
CFLAGS = -Wall -Os -mshort -mfastcall -m68000 -fpack-struct=2 -I../.. -I$(CMINI_DIR)/include
LDFLAGS = -nostdlib -nostartfiles -nodefaultlibs -static -mshort -mfastcall -m68000 -Wl,--gc-sections -Wl,--relax -L$(CMINI_DIR)/lib/mshort/mfastcall -L$(GODLIB_DIR)
CRT = $(CMINI_DIR)/lib/mshort/mfastcall/crt0.o
TOS ?= /Users/kriss/Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img
all: XORSTARS.PRG
XORSTARS.PRG: xorstars.o xorstars_s.o $(GODLIB_DIR)/libgod.a
	$(CC) $(LDFLAGS) -s -o $@ $(CRT) xorstars.o xorstars_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
xorstars.o: xorstars.c
	$(CC) $(CFLAGS) -c $< -o $@
xorstars_s.o: xorstars_s.s
	vasmm68k_mot -Felf -devpac $< -o $@
debug: XORSTARS.PRG
	$(CC) $(CFLAGS) -DXOR_BENCH $(LDFLAGS) -Wl,-Map,/tmp/XORDBG.map -o /tmp/XORDBG.PRG $(CRT) xorstars.c xorstars_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
run: all
	hatari --tos "$(TOS)" --machine ste --memsize 4 --monitor rgb --confirm-quit false XORSTARS.PRG
clean:
	rm -f *.o XORSTARS.PRG
.PHONY: all debug run clean
