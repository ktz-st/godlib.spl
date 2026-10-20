CC = m68k-atari-mintelf-gcc
AS = vasmm68k_mot
CMINI_DIR = ../../libcmini
GODLIB_DIR = ../../godlib
CFLAGS = -Wall -Os -mshort -mfastcall -m68000 -fpack-struct=2 -I../.. -I$(CMINI_DIR)/include -DdGODLIB_FADE -fno-jump-tables -fno-tree-switch-conversion
LDFLAGS = -nostdlib -nostartfiles -nodefaultlibs -static -mshort -mfastcall -m68000 -Wl,--gc-sections -Wl,--relax -L$(CMINI_DIR)/lib/mshort/mfastcall -L$(GODLIB_DIR)
LIBS = -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
START = $(CMINI_DIR)/lib/mshort/mfastcall/crt0.o
all: RJP1.PRG
RJP1.PRG: rjp1.o $(GODLIB_DIR)/libgod.a
	$(CC) $(LDFLAGS) -s -o $@ $(START) rjp1.o $(LIBS)
rjp1.o: rjp1.c $(GODLIB_DIR)/music/rjp1.h
	$(CC) $(CFLAGS) -c $< -o $@
analysis/RJPDBG.PRG: rjp1.o $(GODLIB_DIR)/libgod.a
	$(CC) $(LDFLAGS) -o $@ $(START) rjp1.o $(LIBS)
debug: RJP1.PRG analysis/RJPDBG.PRG
clean:
	rm -f *.o RJP1.PRG analysis/*.PRG analysis/*.o
.PHONY: all debug clean

# Read-only reference from cfintro.rjp; never modified or linked into RJP1.PRG.
analysis/RJPCHECK.PRG: analysis/core-check.c analysis/reference.o analysis/arm-check.o $(GODLIB_DIR)/libgod.a
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $(START) $< analysis/reference.o analysis/translate.o analysis/arm-check.o $(LIBS)
analysis/translate.o: ../../cfintro.rjp/vd_translate.c
	$(CC) $(CFLAGS) -c $< -o $@
analysis/reference.o: analysis/reference.s ../../cfintro.rjp/vectordean.s
	$(AS) -Felf -devpac $< -o $@
analysis/RJPCHECK.PRG: analysis/translate.o
analysis/RJPBENCH.PRG: analysis/bench.c analysis/reference.o analysis/translate.o $(GODLIB_DIR)/libgod.a
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $(START) $< analysis/reference.o analysis/translate.o $(LIBS)

analysis/arm-check.o: analysis/arm-check.s
	$(AS) -Felf -devpac $< -o $@

check: debug analysis/RJPCHECK.PRG
	python3 analysis/check.py
	python3 analysis/verify.py

profile: debug analysis/RJPBENCH.PRG
	python3 analysis/profile.py
.PHONY: check profile

TOS ?= /Users/kriss/Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img
run: RJP1.PRG
	hatari --tos "$(TOS)" -w --machine ste --memsize 1 --monitor rgb --confirm-quit false --fast-boot true RJP1.PRG
.PHONY: run

analysis/WARTIME.PRG: analysis/war-timing.c rjp1.c $(GODLIB_DIR)/libgod.a
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $(START) $< $(LIBS)

check-war: debug analysis/WARTIME.PRG
	python3 analysis/war-timing.py
	python3 analysis/war-audio.py
.PHONY: check-war

analysis/mixer-check.o: analysis/mixer-check.s
	$(AS) -Felf -devpac $< -o $@
analysis/RJPMCHECK.PRG: analysis/mixer-check.c analysis/mixer-check.o $(GODLIB_DIR)/libgod.a
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $(START) $< analysis/mixer-check.o $(LIBS)

check-mixers: debug analysis/RJPMCHECK.PRG
	python3 analysis/check-mixers.py
	python3 analysis/verify-mixers.py
profile-mixers: debug
	python3 analysis/profile-mixers.py
.PHONY: check-mixers profile-mixers
