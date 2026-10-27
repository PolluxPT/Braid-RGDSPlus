# Third-party notices

- **Port integration:** Copyright (c) 2026 Filipe Baeta (PolluxPT), MIT. Root `LICENSE` applies to the original port code; upstream material retains its own notices.
- **Box64/Box32:** MIT, Copyright (c) 2020 ptitSeb. License retained in `APPS/Braid_RGDSPlus/licenses/box64.txt`; source revision recorded in BUILD_INFO.json. Native binary included.
- **GL4ES:** MIT, Copyright (c) 2016–2018 Sebastien Chevalier and (c) 2013–2016 Ryan Hileman. License retained in `licenses/gl4es.txt`; source revision recorded in BUILD_INFO.json. Native binary included.
- **SDL:** firmware library used from the device. SDL-compatible adaptation material retains SDL's zlib license in `licenses/sdl2.txt`. No firmware SDL or Mali driver library is bundled.
- **RGDS+ reference integration:** maintainer's SteamWorld integration; MIT notice retained in `licenses/RGDS-integration-MIT.txt`.
- **GNU runtimes:** libstdc++ and libgcc binaries are not distributed in this public package. The preparation tool obtains the exact Debian i386 packages locally or uses a player's existing private install. Metadata, package URLs and hashes are in `tools/runtime-packages.json`. Package copyright/license records accompany Debian packages; corresponding gcc-12 source packages are available at https://deb.debian.org/debian/pool/main/g/gcc-12/ .
- **Braid and NVIDIA Cg:** executable, game data, fonts, audio, artwork and Cg/CgGL SDK binaries are excluded. The preparation tool imports them from the player's own supported Linux game copy. Original notices are copied locally when present. This project is an unofficial device integration and is not affiliated with the game's owners or NVIDIA.

A locally prepared game-containing install is for private use. Publish only the audited port-only assets supplied in this kit.
