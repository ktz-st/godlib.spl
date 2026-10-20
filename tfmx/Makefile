CC = m68k-atari-mintelf-gcc
AS = vasmm68k_mot
CMINI_DIR = ../../libcmini
GODLIB_DIR = ../../godlib
CFLAGS = -Wall -Os -mshort -mfastcall -m68000 -fpack-struct=2 -I../.. -I$(CMINI_DIR)/include -DdGODLIB_FADE -fno-jump-tables -fno-tree-switch-conversion
LDFLAGS = -nostdlib -nostartfiles -nodefaultlibs -static -mshort -mfastcall -m68000 -Wl,--gc-sections -Wl,--relax -L$(CMINI_DIR)/lib/mshort/mfastcall -L$(GODLIB_DIR)
LIBS = -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
START = $(CMINI_DIR)/lib/mshort/mfastcall/crt0.o
all: TFMX.PRG
TFMX.PRG: tfmx.o $(GODLIB_DIR)/libgod.a
	$(CC) $(LDFLAGS) -s -o $@ $(START) tfmx.o $(LIBS)
tfmx.o: tfmx.c $(GODLIB_DIR)/music/tfmx.h
	$(CC) $(CFLAGS) -c $< -o $@
analysis/TFMXDBG.PRG: tfmx.o $(GODLIB_DIR)/libgod.a
	$(CC) $(LDFLAGS) -o $@ $(START) tfmx.o $(LIBS)
debug: TFMX.PRG analysis/TFMXDBG.PRG
clean:
	rm -f *.o TFMX.PRG analysis/*.PRG analysis/*.o
.PHONY: all debug clean

analysis/TFMCHECK.PRG: analysis/core-check.c $(GODLIB_DIR)/libgod.a
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $(START) $< $(LIBS)
check: debug analysis/TFMCHECK.PRG analysis/TFMSEQ.PRG analysis/TFMWIN.PRG analysis/TFMCAD.PRG
	python3 analysis/check-sequence.py
	python3 analysis/check.py
	python3 analysis/check-window.py
	python3 analysis/verify.py
	python3 analysis/dma-timing.py
	python3 analysis/check-cadence.py
profile: debug
	python3 analysis/profile.py
.PHONY: check profile
analysis/reference.o: analysis/reference.s analysis/reference-core.s
	$(AS) -Felf -devpac $< -o $@
analysis/TFMSEQ.PRG: analysis/sequence-check.c analysis/reference.o $(GODLIB_DIR)/libgod.a
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $(START) $< analysis/reference.o $(LIBS)
analysis/reference-core.s: analysis/prepare-reference.py ../../ugh.agt/src/atari/tfmx_engine.asm
	python3 analysis/prepare-reference.py
analysis/TFMWIN.PRG: analysis/window-check.c $(GODLIB_DIR)/libgod.a
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $(START) $< $(LIBS)
analysis/TFMCAD.PRG: analysis/cadence-check.c $(GODLIB_DIR)/libgod.a
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $(START) $< $(LIBS)
