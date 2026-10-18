CC = m68k-atari-mintelf-gcc
CMINI_DIR = ../../libcmini
GODLIB_DIR = ../../godlib
CFLAGS = -Wall -Os -mshort -mfastcall -m68000 -fpack-struct=2 -I../.. -I$(CMINI_DIR)/include
LDFLAGS = -nostdlib -nostartfiles -nodefaultlibs -static -mshort -mfastcall -m68000 -Wl,--gc-sections -Wl,--relax -L$(CMINI_DIR)/lib/mshort/mfastcall -L$(GODLIB_DIR)
CRT = $(CMINI_DIR)/lib/mshort/mfastcall/crt0.o
TOS ?= /Users/kriss/Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img
all: CRT.PRG
CRT.PRG: crt.o crt_s.o crt_tv.o $(GODLIB_DIR)/libgod.a
	$(CC) $(LDFLAGS) -s -o $@ $(CRT) crt.o crt_s.o crt_tv.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
	m68k-atari-mintelf-strip --strip-unneeded $@
crt.o: crt.c crt.h
	$(CC) $(CFLAGS) -c $< -o $@
crt_s.o: crt_s.s assets/IMAGE.BIN assets/SOURCE.BIN assets/PALETTE.BIN assets/IMAGE2.BIN assets/SOURCE2.BIN assets/PALETTE2.BIN
	vasmm68k_mot -Felf -devpac $< -o $@
crt_tv.o: crt_tv.s assets/TVSTEPS.S
	vasmm68k_mot -Felf -devpac $< -o $@
assets:
	python3 prepare.py
debug: CRT.PRG
	$(CC) $(LDFLAGS) -o analysis/CRTDBG.PRG $(CRT) crt.o crt_s.o crt_tv.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
run: CRT.PRG
	hatari --tos "$(TOS)" --machine ste --memsize 1 --monitor rgb --confirm-quit false --fast-boot true CRT.PRG
clean:
	rm -f *.o CRT.PRG analysis/CRTDBG.PRG
.PHONY: all assets debug run clean
