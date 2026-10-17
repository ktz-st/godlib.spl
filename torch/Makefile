CC = m68k-atari-mintelf-gcc
STRIP = m68k-atari-mintelf-strip
CMINI_DIR = ../../libcmini
GODLIB_DIR = ../../godlib
CFLAGS = -fno-strict-aliasing -Wall -Os -mshort -mfastcall -m68000 -fpack-struct=2 -I../.. -I$(CMINI_DIR)/include
LDFLAGS = -nostdlib -nostartfiles -nodefaultlibs -static -mshort -mfastcall -m68000 -Wl,--gc-sections -Wl,--relax -L$(CMINI_DIR)/lib/mshort/mfastcall -L$(GODLIB_DIR)
CRT = $(CMINI_DIR)/lib/mshort/mfastcall/crt0.o

all: TORCH.PRG
assets/IMAGE.BIN: prepare.py ../water/assets/castle-source.png ../tools/abc2_assets.py
	python3 prepare.py
assets/PALETTE.BIN assets/HALF.BIN assets/SINE.BIN: assets/IMAGE.BIN
	@test -f $@ || python3 prepare.py
TORCH.PRG: torch.o torch_s.o $(GODLIB_DIR)/libgod.a
	$(CC) $(LDFLAGS) -s -o $@ $(CRT) torch.o torch_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
	$(STRIP) --strip-unneeded $@
torch.o: torch.c $(GODLIB_DIR)/screen/screen.h $(GODLIB_DIR)/video/video.h
	$(CC) $(CFLAGS) -c $< -o $@
run: all
	hatari -w --spec512 1 --machine st --memsize 4 --monitor rgb --confirm-quit false --fast-boot true TORCH.PRG
debug: all analysis/TCHDB.PRG
analysis/TCHDB.PRG: torch.o torch_s.o $(GODLIB_DIR)/libgod.a
	mkdir -p analysis
	$(CC) $(LDFLAGS) -o $@ $(CRT) torch.o torch_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
torch_s.o: torch_s.s assets/IMAGE.BIN assets/PALETTE.BIN assets/HALF.BIN assets/SINE.BIN
	vasmm68k_mot -Felf -devpac $< -o $@
clean:
	rm -f *.o TORCH.PRG analysis/TCHDB.PRG
.PHONY: all run debug clean
