# Installation

## Requirements

- Anbernic RGDS+ running the stock Linux environment used by the maintainer (tested foundation: Linux 6.1.141, ARM64, firmware SDL2 2.32.10).
- Your supported original Linux i386 Braid files. A purchase alone does not make the Windows build compatible; obtain the Linux edition through your legitimate game provider.
- Python 3.10+ on a Windows, macOS or Linux computer for preparation.
- Internet for the two pinned Debian runtime downloads, or their exact `.deb` files supplied offline.

## Prepare on Windows

1. Extract the **port-only release asset** into a fresh folder, for example `C:\BraidPort`.
2. Locate the owned game folder. It must contain `Braid.bin.x86`, `data/package.braid`, `data/package0.braid`, `lib/libCg.so` and `lib/libCgGL.so`.
3. Open PowerShell in `C:\BraidPort`.
4. Run:

   ```powershell
   py -3 tools/prepare_game.py --game-dir "C:\Games\Braid\game" --output "C:\Braid_RGDSPlus_Install" --download-runtime
   ```

   Change the game path to your real folder. Choose an output folder that does not already exist. The script builds a separate install and does not overwrite your owned game or an existing output folder.
5. Wait for `Ready:`. Required game files, downloaded packages and extracted runtime libraries are SHA-256 checked. Unsupported/corrupt files stop preparation.
6. Open `C:\Braid_RGDSPlus_Install\APPS`. Copy its **contents** into `TF2/Roms/APPS` on the device's card.
7. The resulting launcher is `Roms/APPS/Braid.sh` and the game folder is `Roms/APPS/Braid_RGDSPlus`.
8. Start Braid from the device menu. Initial loading can take time while Cg compiles shaders.

On Linux/macOS, use `python3 tools/prepare_game.py ...` and normal local paths. On card filesystems that retain Unix permissions, ensure `Braid.sh`, `runtime/box64-box32` and `game/Braid.rgds.x86` are executable.

## Existing private complete package

Point `--game-dir` at the `APPS/Braid_RGDSPlus/game` directory of your private complete package. Its adjacent `runtime/libs.x86` can supply the exact GNU libraries, so no runtime download is necessary. These game-containing packages are private inputs, not public release assets.

## Offline runtime packages

The exact package URLs and checksums are in `tools/runtime-packages.json`. Download both `.deb` files from Debian on a connected computer and place them in one folder:

- `libstdc++6_12.2.0-14+deb12u1_i386.deb`
- `libgcc-s1_12.2.0-14+deb12u1_i386.deb`

Use `--runtime-packages "C:\BraidRuntimeDebs"` instead of `--download-runtime`. Extraction uses Python's standard library and selects only the required regular library members. No package installation or administrator rights are needed on the preparation computer.

## Updates and saves

Keep a backup of `Braid_RGDSPlus/savedata`. Prepare a new install folder, then replace matching files on the card while preserving the existing `savedata` directory. Game progress and remembered volume remain there. The preparation script never edits an existing output directory.

## Controls and screens

Use the configured game controls; START+SELECT held for 1.5 seconds exits. Physical volume buttons adjust the remembered game volume. The lower backlight is disabled during play and its previous brightness is restored during launcher cleanup. Top-screen presentation stays full size at 16:9; the internal scene resolution is 640×360.
