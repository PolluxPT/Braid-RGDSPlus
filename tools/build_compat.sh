#!/bin/sh
set -eu
braid_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
braid_zig=${BRAID_ZIG:-zig}
"$braid_zig" cc -target x86-linux-gnu.2.28 -shared -fPIC -O2 -fno-builtin \
 "$braid_root/APPS/Braid_RGDSPlus/source/braid_compat.c" -ldl \
 -o "$braid_root/APPS/Braid_RGDSPlus/runtime/libs.x86/libbraid_compat.so"
printf '%s\n' 'Built i386 compatibility library. Regenerate public_manifest.json before a new release.'
