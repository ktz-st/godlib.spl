CC = m68k-atari-mintelf-gcc
STRIP = m68k-atari-mintelf-strip
CMINI_DIR = ../../libcmini
GODLIB_DIR = ../../godlib
CFLAGS = -fno-strict-aliasing -Wall -Os -mshort -mfastcall -m68000 -fpack-struct=2 -I../.. -I$(CMINI_DIR)/include
LDFLAGS = -nostdlib -nostartfiles -nodefaultlibs -static -mshort -mfastcall -m68000 -Wl,--gc-sections -Wl,--relax -L$(CMINI_DIR)/lib/mshort/mfastcall -L$(GODLIB_DIR)
CRT = $(CMINI_DIR)/lib/mshort/mfastcall/crt0.o

all: PHASE.PRG
PHASE.PRG: phasescroll.o phase_s.o split.o split_s.o $(GODLIB_DIR)/libgod.a
	$(CC) $(LDFLAGS) -s -o $@ $(CRT) phasescroll.o phase_s.o split.o split_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
	$(STRIP) --strip-unneeded $@
phasescroll.o: phasescroll.c phase.h $(GODLIB_DIR)/screen/screen.h $(GODLIB_DIR)/video/video.h
	$(CC) $(CFLAGS) -c $< -o $@
run: all
	hatari -w --machine ste --memsize 4 --monitor rgb --confirm-quit false --fast-boot true PHASE.PRG
debug: all analysis/PDBG.PRG
analysis/PDBG.PRG: phasescroll.o phase_s.o split.o split_s.o $(GODLIB_DIR)/libgod.a
	mkdir -p analysis
	$(CC) $(LDFLAGS) -o $@ $(CRT) phasescroll.o phase_s.o split.o split_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
split.o: split.c phase.h
	$(CC) $(CFLAGS) -c $< -o $@
phase_s.o: phase_s.s system.equ assets/TDATA.BIN assets/LMAP.BIN
	vasmm68k_mot -Felf -devpac $< -o $@
split_s.o: split_s.s
	vasmm68k_mot -Felf -devpac $< -o $@
clean:
	rm -f *.o PHASE.PRG analysis/PDBG.PRG
.PHONY: all run debug clean
