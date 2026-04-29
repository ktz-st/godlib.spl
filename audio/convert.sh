#!/usr/bin/env sh
set -eu

cd "$(dirname "$0")"

convert_sample() {
	if [ ! -f "$1" ]; then
		echo "missing input: $1"
		return
	fi
	ffmpeg -i "$1" -ar "$2" -y -f s8 -c:a pcm_s8 $3 "$4"
}

convert_sample DRAGON.WAV 25033 '-af pan=mono|c0=c1' loop.raw
convert_sample OH_YES.WAV 12517 '-af pan=mono|c0=c1' voice.raw
convert_sample ARCHERY.WAV 12517 '' stereo.raw
