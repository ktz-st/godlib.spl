#!/bin/bash
set -e
cd "$(dirname "$0")/../../.."
cc=m68k-atari-mintelf-gcc
common=(-Wall -Os -mshort -mfastcall -m68000 -fpack-struct=2 -I. -Ilibcmini/include -Igodlib/audio)
link=(-nostdlib -nostartfiles -nodefaultlibs -static -mshort -mfastcall -m68000 -Wl,--gc-sections -Wl,--relax -Llibcmini/lib/mshort/mfastcall -Lgodlib)
$cc "${common[@]}" -c godlib.spl/mixer/analysis/bench.c -o godlib.spl/mixer/analysis/bench.o
if [[ ${1:-} == baseline ]]; then
 $cc "${common[@]}" -c godlib.spl/mixer/analysis/baseline/amixer.c -o godlib.spl/mixer/analysis/baseline/amixer.o
 vasmm68k_mot -nosym -devpac -Felf godlib.spl/mixer/analysis/baseline/amixer_s.s -o godlib.spl/mixer/analysis/baseline/amixer_s.o
 $cc "${link[@]}" -o godlib.spl/mixer/analysis/BASE.PRG libcmini/lib/mshort/mfastcall/crt0.o godlib.spl/mixer/analysis/bench.o godlib.spl/mixer/analysis/baseline/amixer.o godlib.spl/mixer/analysis/baseline/amixer_s.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
else
 $cc "${link[@]}" -o godlib.spl/mixer/analysis/BENCH.PRG libcmini/lib/mshort/mfastcall/crt0.o godlib.spl/mixer/analysis/bench.o -Wl,--start-group -lgod -lcmini -lgcc -Wl,--end-group
fi
