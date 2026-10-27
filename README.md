# Braid for RGDS+

Standalone Linux Braid integration for the Anbernic RGDS+ stock OS, maintained by [PolluxPT](https://github.com/PolluxPT).

**Version 1.6.0. Bring your own supported Linux i386 game copy.** Download `Braid_RGDSPlus_v1.6_PortOnly.zip` from this repository's Releases page. The public package includes the launcher, port runtime, source and tools. Commercial game files and NVIDIA Cg libraries are supplied locally by the player.

## Install

1. Extract the port-only ZIP into a new folder on your computer. Install Python 3.10 or newer if needed.
2. Find your Linux game's folder containing `Braid.bin.x86`, `data` and `lib`.
3. Open a terminal in the extracted port folder. On Windows run:

   ```powershell
   py -3 tools/prepare_game.py --game-dir "C:\Games\Braid\game" --output "C:\Braid_RGDSPlus_Install" --download-runtime
   ```

   On Linux/macOS use `python3` instead of `py -3` and your own paths. The script verifies the supported game, patches a separate executable, and downloads two small pinned Debian i386 runtime packages over HTTPS. Package and extracted-library SHA-256 hashes are checked. An existing private standalone install can supply those runtime libraries instead. Offline packages are also supported.
4. Copy the **contents** of the generated `APPS` folder into `TF2/Roms/APPS`. Replace matching port files when updating, and **keep `Braid_RGDSPlus/savedata`**.
5. Launch **Braid** from APPS. Keep the game folder named `Braid_RGDSPlus`; the launcher must remain beside it.

See [detailed installation](docs/INSTALL.md), [troubleshooting](docs/TROUBLESHOOTING.md) and [build information](docs/BUILD.md).

## Features

- Full-size top-screen presentation with 16:9 letterboxing and 640×360 internal rendering.
- 30 FPS target; demanding scrolling and animated scenery can still drop frames.
- Paired GLSL renderer with guarded shader/value/query caches and buffered numeric uniform updates.
- Physical volume buttons, remembered game volume and system volume restoration.
- Lower-screen backlight off during play, restored on exit.
- Hold **START + SELECT for 1.5 seconds** to exit.
- Native Linux i386 game through Box32 and ARM64 GL4ES; firmware SDL, EGL and Mali drivers.

The graphics/controls foundation has been tested by the maintainer on hardware in earlier revisions. The new v1.6 buffered-write optimization passes local renderer fixtures and tests against the supplied Cg library; its hardware FPS gain is unmeasured. Startup still includes Cg compilation. There is no locked-30-FPS guarantee.

## Supported files

This build supports the pinned Linux i386 executable with SHA-256:

```text
8428ff57c83ed227be67b7a90caa8483b5983e6cca4a896471f60e9a5d497448
```

Required asset and Cg hashes are in `tools/supported_game.json`. Windows executables, other editions and Braid Anniversary Edition are not interchangeable with this build. Preparation refuses unsupported files and leaves the original game untouched.

## Reporting issues

Give the port version, stock OS details and steps to reproduce. Attach `Braid_Game.txt`, `Hardware_Perf.txt` and `Arranque_Braid.txt` from `Braid_RGDSPlus/logs` after checking them for personal paths. Compare performance in the same scene with the same actions.

## License and credits

Port code: MIT; see [LICENSE](LICENSE). Box64/Box32 by ptitSeb and contributors; GL4ES by Sebastien Chevalier, Ryan Hileman and contributors. RGDS+ integration follows the maintainer's SteamWorld work. Third-party notices are retained under `APPS/Braid_RGDSPlus/licenses` and in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

Braid, its executable, artwork, resources, fonts, audio and NVIDIA Cg libraries retain their owners' terms. They are excluded from this public repository/release. Locally prepared installs contain your own game files and should remain private.
