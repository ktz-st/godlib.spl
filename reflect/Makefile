CC = m68k-atari-mintelf-gcc
STRIP = m68k-atari-mintelf-strip
CMINI_DIR = ../../libcmini
GODLIB_DIR = ../../godlib
CFLAGS = -fno-strict-aliasing -Wall -Os -mshort -mfastcall -m68000 -fpack-struct=2 -I../.. -I$(CMINI_DIR)/include
LDFLAGS = -nostdlib -nostartfiles -nodefaultlibs -static -mshort -mfastcall -m68000 -Wl,--gc-sections -Wl,--relax -L$(CMINI_DIR)/lib/mshort/mfastcall -L$(GODLIB_DIR)
CRT = $(CMINI_DIR)/lib/mshort/mfastcall/crt0.o

all: REFL.PRG
REFL.PRG: reflect.o reflect_s.o $(GODLIB_DIR)/libgod.a
	$(CC) $(LDFLAGS) -s -o $@ $(CRT) reflect.o reflect_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
	$(STRIP) --strip-unneeded $@
reflect.o: reflect.c $(GODLIB_DIR)/graphic/reflection.h $(GODLIB_DIR)/screen/screen.h $(GODLIB_DIR)/video/video.h
	$(CC) $(CFLAGS) -c $< -o $@
run: all
	hatari -w --machine ste --memsize 4 --monitor rgb --confirm-quit false --fast-boot true REFL.PRG
debug: all analysis/RDBG.PRG
analysis/RDBG.PRG: reflect.o reflect_s.o $(GODLIB_DIR)/libgod.a
	mkdir -p analysis
	$(CC) $(LDFLAGS) -o $@ $(CRT) reflect.o reflect_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
reflect_s.o: reflect_s.s assets/TOP.PI1 assets/SOURCE.BIN
	vasmm68k_mot -Felf -devpac $< -o $@
clean:
	rm -f *.o REFL.PRG analysis/RDBG.PRG analysis/*.o analysis/ORACLE.PRG analysis/original-core.bin
.PHONY: all run debug clean

assets/TOP.PI1: assets/CASTLE.PI1 tools/prepare.py
	python3 tools/prepare.py
assets/SOURCE.BIN: assets/TOP.PI1
	@test -f $@ || python3 tools/prepare.py

oracle: analysis/ORACLE.PRG
analysis/original-core.bin: analysis/inspect-missing-link.py ../../stos/mislink/mislink/STOS/LINK2.EXR
	python3 analysis/inspect-missing-link.py
analysis/original_s.o: analysis/original_s.s analysis/original-core.bin
	vasmm68k_mot -Felf -devpac $< -o $@
analysis/oracle.o: analysis/oracle.c $(GODLIB_DIR)/graphic/reflection.h
	$(CC) $(CFLAGS) -c $< -o $@
analysis/ORACLE.PRG: analysis/oracle.o analysis/original_s.o $(GODLIB_DIR)/libgod.a
	$(CC) $(LDFLAGS) -o $@ $(CRT) analysis/oracle.o analysis/original_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
.PHONY: oracle

# Refresh this embedded copy from its original-RGB ABC2 asset pipeline.
assets/CASTLE.PI1: ../water/assets/CASTLE.PI1
	cp $< $@
../water/assets/CASTLE.PI1: ../water/assets/castle-source.png ../water/tools/prepare.py ../tools/abc2_assets.py
	$(MAKE) -C ../water assets/CASTLE.PI1
