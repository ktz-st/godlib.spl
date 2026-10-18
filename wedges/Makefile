CC = m68k-atari-mintelf-gcc
CMINI_DIR = ../../libcmini
GODLIB_DIR = ../../godlib
CFLAGS = -Wall -Os -mshort -mfastcall -m68000 -fpack-struct=2 -I../.. -I$(CMINI_DIR)/include
LDFLAGS = -nostdlib -nostartfiles -nodefaultlibs -static -mshort -mfastcall -m68000 -Wl,--gc-sections -Wl,--relax -L$(CMINI_DIR)/lib/mshort/mfastcall -L$(GODLIB_DIR)
CRT = $(CMINI_DIR)/lib/mshort/mfastcall/crt0.o
TOS ?= /Users/kriss/Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img
OBJECTS = wedges.o cache.o wedges_s.o
all: WEDGES.PRG WEDGERT.PRG
WEDGES.PRG: $(OBJECTS) $(GODLIB_DIR)/libgod.a
	$(CC) $(LDFLAGS) -s -o $@ $(CRT) $(OBJECTS) -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
	m68k-atari-mintelf-strip --strip-unneeded $@
wedges.o cache.o: %.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@
wedges_s.o: wedges_s.s assets/SINE.S
	vasmm68k_mot -Felf -devpac $< -o $@
debug: WEDGES.PRG WEDGERT.PRG
	mkdir -p analysis
	$(CC) $(LDFLAGS) -o analysis/WEDGESDBG.PRG $(CRT) $(OBJECTS) -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
	$(CC) $(LDFLAGS) -o analysis/RTDBG.PRG $(CRT) wedges_rt.o live_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
WEDGERT.PRG: wedges_rt.o live_s.o $(GODLIB_DIR)/libgod.a
	$(CC) $(LDFLAGS) -s -o $@ $(CRT) wedges_rt.o live_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
	m68k-atari-mintelf-strip --strip-unneeded $@
wedges_rt.o: wedges.c
	$(CC) $(CFLAGS) -DWEDGES_REALTIME -c $< -o $@
live_s.o: live_s.s assets/COTS.S assets/XMASKS.S
	vasmm68k_mot -Felf -devpac $< -o $@
assets:
	python3 prepare.py
run: WEDGES.PRG
	hatari --tos "$(TOS)" --machine ste --memsize 1 --monitor rgb --confirm-quit false --fast-boot true WEDGES.PRG
clean:
	rm -f $(OBJECTS) wedges_rt.o live_s.o WEDGES.PRG WEDGERT.PRG analysis/WEDGESDBG.PRG analysis/RTDBG.PRG
.PHONY: all debug assets run clean

run-live: WEDGERT.PRG
	hatari --tos "$(TOS)" --machine ste --memsize 1 --monitor rgb --confirm-quit false --fast-boot true WEDGERT.PRG
.PHONY: run-live
