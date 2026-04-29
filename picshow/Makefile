CC = m68k-atari-mintelf-gcc
CXX = m68k-atari-mintelf-g++
LD = m68k-atari-mintelf-gcc
AS = vasmm68k_mot
AR = m68k-atari-mintelf-ar
STRIP = m68k-atari-mintelf-strip

CMINI_DIR = ../../libcmini
GODLIB_DIR = ../../godlib

SOURCES_C = picshow.c
SOURCES_CPP =
SOURCES_S =

OBJECTS_C   = $(SOURCES_C:.c=.o)
OBJECTS_CPP = $(SOURCES_CPP:.cpp=.o)
OBJECTS_S = $(SOURCES_S:.s=.o)

DEFS = -DdGODLIB_FADE

CFLAGS  = -Wall -Os -mshort -mfastcall -m68000 \
          -I. -I$(CMINI_DIR)/include -I../..

CFLAGS += -fno-jump-tables -fno-tree-switch-conversion \
          -fomit-frame-pointer -fno-unwind-tables -fno-asynchronous-unwind-tables \
          -fmerge-constants -fno-ident \
          -fno-inline-functions -fno-inline-small-functions \
		  -fpack-struct=2 \
		  $(DEFS)

CXXFLAGS = $(CFLAGS) -std=gnu++17 \
           -fno-exceptions -fno-rtti -fno-threadsafe-statics -fno-use-cxa-atexit \
           -ffreestanding -fno-builtin \
		   $(DEFS)

LDFLAGS = -s -nostdlib -nostartfiles -nodefaultlibs -static \
          -mshort -mfastcall -m68000 \
          -Wl,--gc-sections -Wl,--relax \
          -L$(CMINI_DIR)/lib/mshort/mfastcall \
		  -L$(GODLIB_DIR)

OUT = PICSHOW.PRG

$(OUT): $(OBJECTS_C) $(OBJECTS_S) $(OBJECTS_CPP)
	$(LD) $(LDFLAGS) -o $(OUT) $(CMINI_DIR)/lib/crt0.o \
	$(OBJECTS_S) $(OBJECTS_C) $(OBJECTS_CPP) \
	-Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
	$(STRIP) --strip-unneeded $(OUT)

$(OBJECTS_C): %.o: %.c
	$(CC) -c $(CFLAGS) $< -o $@

$(OBJECTS_CPP): %.o: %.cpp
	 $(CXX) -c $(CXXFLAGS) $< -o $@

$(OBJECTS_S): %.o: %.s
	$(AS) -nosym -devpac -Felf $< -o $@

clean:
	rm -rf $(OBJECTS_S) $(OBJECTS_C) $(OBJECTS_CPP) $(OUT) *.map

map:
	$(LD) $(LDFLAGS) -Wl,-Map=link.map -o $(OUT) $(CMINI_DIR)/lib/minicrt0.o \
	$(OBJECTS_S) $(OBJECTS_C) $(OBJECTS_CPP) \
	-lgcc -lcmini -lgod  -lgcc

run: $(OUT)
	hatari  -w --monitor rgb --fastfdc true --fastfdc true $(OUT) &

