# Troubleshooting

- **Unsupported game file:** compare with `tools/supported_game.json`. This version is pinned to one Linux i386 build. Do not rename a Windows executable or bypass checksum checks.
- **Preparation asks for runtime packages:** add `--download-runtime`, supply the exact offline packages with `--runtime-packages`, or use a supported private complete package as input.
- **Download unavailable:** retry later or use the exact Debian packages offline. Do not substitute another architecture/version without testing and updating the recorded hashes.
- **Output already exists:** choose a new output folder. Keep previous saves when copying the prepared APPS contents to the card.
- **Launch reports missing files:** run the preparation step first. The public port ZIP intentionally does not contain a ready-to-play commercial game installation.
- **Blank picture or unexpected graphics after updating:** verify all matching port files were replaced together. Keep the native GL4ES/Box32 binaries supplied with this version. Collect the logs below.
- **Regression with v1.6 buffered writes:** change `runtime/write-cache.txt` from `1` to `0`, then relaunch. This restores v1.5's original changed-value setter path while retaining the other optimizations.
- **Performance:** 30 FPS is a target. Use the same scene/actions for comparisons. Lowering output size is not required for this release; the known internal cap and full-size presentation are already configured.

Configuration files accept `0` or `1`: `write-cache.txt`, `revision-cache.txt`, `missing-cache.txt`, `lookup-cache.txt`, `value-cache.txt`, `direct-bridge.txt`. Supplied defaults are `1` for all six. Change one at a time and relaunch.

Logs in `Roms/APPS/Braid_RGDSPlus/logs`:

- `Arranque_Braid.txt`: version, configuration, lower-screen state, exit and cleanup.
- `Braid_Game.txt`: shader diagnostics, FPS windows and cache counters including `writes_deferred`/`writes_flushed`.
- `Hardware_Perf.txt`: read-only clocks, temperatures and process/thread CPU data.

Review logs for personal paths before attaching to a public issue. Do not upload saved games, complete private packages or game assets.
