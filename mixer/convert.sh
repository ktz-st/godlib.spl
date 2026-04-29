#!/usr/bin/env sh
set -eu

cd "$(dirname "$0")"

if [ ! -f OH_YES.WAV ]; then
	echo "missing input: OH_YES.WAV"
	exit 0
fi

ffmpeg -i OH_YES.WAV -ar 12517 -y -f s8 -c:a pcm_s8 -af "pan=mono|c0=c1" voice.raw
