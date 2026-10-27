# Build and verification

The distributed MIT native runtime binaries are the v1.6 port's tested foundation. The compatibility library is compiled from the exact source included here. Upstream Box64/GL4ES revisions and binary hashes are recorded in `APPS/Braid_RGDSPlus/BUILD_INFO.json`.

## Compatibility library

On Linux/macOS with Zig 0.17.0 in PATH:

```sh
sh tools/build_compat.sh
```

The target is `x86-linux-gnu.2.28`, shared PIC, `-O2 -fno-builtin`, linked with `libdl`. This builds `APPS/Braid_RGDSPlus/runtime/libs.x86/libbraid_compat.so`. The shipped library requires GLIBC 2.0/2.1 symbols; it runs as i386 code through Box32.

## Native runtime adaptations

Box64/Box32: upstream commit `1a49e470758276d49b2d09a78e199e12951c6dc3`.
GL4ES: upstream commit `2037865590d410bcd7b8d1f22b841472ed6d39ac`.

The `source` directory contains the adaptation scripts and modified source snapshots for the SDL/GLX/context fixes. `source/BUILD.md` preserves the detailed historical build settings and validation notes. Its paths refer to the original build workspace; it is reference material, not a turnkey native-runtime build command for a fresh machine. Rebuilding the full ARM64 stack requires upstream source, an ARM64 cross toolchain and the documented source replacements. There is no claim of a bit-for-bit reproducible native build from a single command.

Upstream sources:

- https://github.com/ptitSeb/box64
- https://github.com/ptitSeb/gl4es

## Host-only checks

Python 3 and GCC on Linux:

```sh
python3 tools/check_public.py
sh -n APPS/Braid.sh
python3 APPS/Braid_RGDSPlus/source/test_lookup_cache.py
python3 APPS/Braid_RGDSPlus/source/test_cache.py
python3 APPS/Braid_RGDSPlus/source/test_direct_bridge.py
python3 APPS/Braid_RGDSPlus/source/test_hotpath.py
python3 APPS/Braid_RGDSPlus/source/test_write_cache.py
python3 APPS/Braid_RGDSPlus/source/test_trace.py
python3 APPS/Braid_RGDSPlus/source/tests/test_monitor.py
python3 APPS/Braid_RGDSPlus/source/tests/test_thread_monitor.py
python3 APPS/Braid_RGDSPlus/source/tests/test_launcher.py
```

The write-cache fixture exercises the new default and fallback guards; older exact-count fixtures explicitly select `BRAID_WRITE_CACHE=0`. Game-binary/SDK/QEMU/Mesa fixtures also retained in `source` require additional local dependencies and owned game files, and are not run by this workflow. Host fixtures do not measure device FPS.

## Release inventory

`public_manifest.json` records every public file's SHA-256. `tools/check_public.py` rejects inventory changes, excluded game/SDK/GNU binaries and private runtime state. `tools/make_release.py` packages only audited entries into `dist/Braid_RGDSPlus_v1.6_PortOnly.zip` and writes `SHA256SUMS.txt`.

When changing the port, review the intended public file list and regenerate its hashes before packaging; never add local prepared game files. Update the version and release filenames for a new release. These commands are pinned for v1.6.0.
