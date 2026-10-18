CC = m68k-atari-mintelf-gcc
CMINI_DIR = ../../libcmini
GODLIB_DIR = ../../godlib
CFLAGS = -Wall -Os -mshort -mfastcall -m68000 -fpack-struct=2 -I../.. -I$(CMINI_DIR)/include
LDFLAGS = -nostdlib -nostartfiles -nodefaultlibs -static -mshort -mfastcall -m68000 -Wl,--gc-sections -Wl,--relax -L$(CMINI_DIR)/lib/mshort/mfastcall -L$(GODLIB_DIR)
CRT = $(CMINI_DIR)/lib/mshort/mfastcall/crt0.o
TOS ?= /Users/kriss/Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img
OBJECTS = iris.o geometry.o iris_s.o scan_s.o live_s.o
all: IRIS.PRG
IRIS.PRG: $(OBJECTS) $(GODLIB_DIR)/libgod.a
	$(CC) $(LDFLAGS) -s -o $@ $(CRT) $(OBJECTS) -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
	m68k-atari-mintelf-strip --strip-unneeded $@
iris.o geometry.o: %.o: %.c iris.h
	$(CC) $(CFLAGS) -c $< -o $@
scan_s.o: scan_s.s
	vasmm68k_mot -Felf -devpac $< -o $@
live_s.o: live_s.s
	vasmm68k_mot -Felf -devpac $< -o $@
iris_s.o: iris_s.s assets/IMAGE.BIN assets/IMAGE2.BIN assets/PALETTE.BIN assets/PALETTE2.BIN assets/SINE.S
	vasmm68k_mot -Felf -devpac $< -o $@
debug: IRIS.PRG
	mkdir -p analysis
	$(CC) $(LDFLAGS) -o analysis/IRISDBG.PRG $(CRT) $(OBJECTS) -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
assets:
	python3 prepare.py
run: IRIS.PRG
	hatari --tos "$(TOS)" --machine ste --memsize 1 --monitor rgb --confirm-quit false --fast-boot true IRIS.PRG
clean:
	rm -f $(OBJECTS) IRIS.PRG analysis/IRISDBG.PRG
.PHONY: all debug assets run clean
