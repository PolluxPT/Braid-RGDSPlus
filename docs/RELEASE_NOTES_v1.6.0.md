## Braid RGDS+ v1.6.0

Standalone integration for **Anbernic RGDS+ stock Linux**. Requires your own supported **Linux i386 Braid** game files.

### Download and install

Download **Braid_RGDSPlus_v1.6_PortOnly.zip** and follow its README. Prepare a private install with `tools/prepare_game.py`, then copy the generated APPS contents into `TF2/Roms/APPS`. Keep existing `Braid_RGDSPlus/savedata` when updating.

This release asset contains the launcher, port runtime, source, notices and preparation tools. Game data, executable, artwork, fonts, audio and NVIDIA Cg binaries are supplied locally from your own copy. The preparation tool verifies required files and pinned runtime downloads by SHA-256.

### Changes

- Buffered numeric shader updates reduce repeated original Cg setter work during changing camera/scene values.
- Verified pair/type/context guards and SDK flushes preserve fallback and readback behavior.
- New independent `runtime/write-cache.txt` switch; set to `0` to restore v1.5 changed-setter behavior if needed.
- Full-size top-screen output, 640×360 internal resolution, physical volume buttons, lower-screen shutdown and existing save paths retained.

### Validation and limits

Local fixtures retain all draws and exact matrix/colour/sampler values. Tests against the supplied i386 Cg library verify float2, float4 and matrix values. All 64 launcher setting combinations pass.

**The v1.6 hardware FPS gain is unmeasured.** 30 FPS is a target; demanding scrolling and animated scenery can still cause drops. Startup includes shader compilation. This is an unofficial port integration.

If reporting an issue, include the version and relevant `Arranque_Braid.txt`, `Braid_Game.txt` and `Hardware_Perf.txt` logs after checking them for personal paths.
