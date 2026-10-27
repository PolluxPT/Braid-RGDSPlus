#!/bin/sh
BASE="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
GAME="$BASE/Braid_RGDSPlus"
RT="$GAME/runtime"
mkdir -p "$GAME/logs" "$GAME/savedata/home" || exit 1
LOCK="$GAME/savedata/.running"
if ! mkdir "$LOCK" 2>/dev/null; then
 old=$(cat "$LOCK/pid" 2>/dev/null)
 case "$old" in ''|*[!0-9]*) old='';; esac
 if [ -n "$old" ] && kill -0 "$old" 2>/dev/null; then exit 1; fi
 rm -f "$LOCK/pid"; rmdir "$LOCK" 2>/dev/null || exit 1
 mkdir "$LOCK" || exit 1
fi
echo "$$" > "$LOCK/pid"
LOG="$GAME/logs/Arranque_Braid.txt"
[ ! -f "$LOG" ] || cp "$LOG" "$GAME/logs/Previous_Launch.txt"
exec > "$LOG" 2>&1
export LANG=C LC_ALL=C
printf 'Braid RGDS+ standalone v1.6 Final / Linux Box32 GLSL GLES2\n'
date; uname -a; id
LOWER=/sys/class/backlight/backlight/brightness
game_pid='' audio_pid='' guard_pid='' perf_pid='' lower_saved='' session_tmp=''
cleanup() {
 trap - EXIT INT TERM HUP
 [ -z "$guard_pid" ] || { kill "$guard_pid" 2>/dev/null || :; wait "$guard_pid" 2>/dev/null || :; }
 if [ -n "$game_pid" ]; then
  kill -TERM "$game_pid" 2>/dev/null || :
  n=0
  while kill -0 "$game_pid" 2>/dev/null && [ "$n" -lt 5 ]; do sleep 1; n=$((n+1)); done
  kill -KILL "$game_pid" 2>/dev/null || :; wait "$game_pid" 2>/dev/null || :
 fi
 [ -z "$perf_pid" ] || { kill -TERM "$perf_pid" 2>/dev/null || :; wait "$perf_pid" 2>/dev/null || :; }
 [ -z "$audio_pid" ] || { kill -TERM "$audio_pid" 2>/dev/null || :; wait "$audio_pid" 2>/dev/null || :; }
 [ -z "$lower_saved" ] || printf '%s\n' "$lower_saved" > "$LOWER" 2>/dev/null || :
 case "$session_tmp" in /tmp/braid-rgds.*) rm -rf -- "$session_tmp";; esac
 cat /proc/meminfo > "$GAME/logs/Memory_After.txt" 2>/dev/null || :
 rm -f "$LOCK/pid"; rmdir "$LOCK" 2>/dev/null || :
 echo 'Launcher cleanup complete.'
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM HUP
case "$(uname -m)" in aarch64|arm64) :;; *) echo 'ERROR: ARM64 Linux required.'; exit 2;; esac
for f in game/Braid.rgds.x86 game/data/package.braid game/data/package0.braid game/lib/libCg.so game/lib/libCgGL.so runtime/box64-box32 runtime/gl4es/libGL.so.1 runtime/libs.x86/libbraid_compat.so runtime/libs.x86/libstdc++.so.6 runtime/libs.x86/libgcc_s.so.1; do
 [ -s "$GAME/$f" ] || { echo "ERROR: missing $f"; exit 3; }
done
command -v python3 >/dev/null 2>&1 || { echo 'ERROR: python3 required for hardware controls.'; exit 7; }
command -v amixer >/dev/null 2>&1 || { echo 'ERROR: amixer required for safe initial volume.'; exit 7; }
chmod +x "$RT/box64-box32" "$GAME/game/Braid.rgds.x86" 2>/dev/null || :
if [ -z "${XDG_RUNTIME_DIR:-}" ]; then
 for d in /var/run "/run/user/$(id -u)" /run/user/0 /tmp; do
  for s in "$d"/wayland-*; do
   [ -S "$s" ] || continue
   export XDG_RUNTIME_DIR="$d" WAYLAND_DISPLAY="${s##*/}"; break 2
  done
 done
fi
if [ -z "${WAYLAND_DISPLAY:-}" ] && [ -n "${XDG_RUNTIME_DIR:-}" ]; then
 for s in "$XDG_RUNTIME_DIR"/wayland-*; do
  [ -S "$s" ] || continue
  export WAYLAND_DISPLAY="${s##*/}"; break
 done
fi
[ -n "${WAYLAND_DISPLAY:-}" ] || { echo 'ERROR: no Wayland session.'; exit 4; }
unset LD_PRELOAD SDL_DYNAMIC_API SDL_VIDEO_EGL_DRIVER SDL_VIDEO_DRIVER SDL_AUDIO_DRIVER
unset BOX64_EMULATED_LIBS BOX64_PREFER_EMULATED BOX64_NORCFILES
export LD_LIBRARY_PATH="$RT/gl4es:/lib:/usr/lib:/lib/aarch64-linux-gnu:/usr/lib/aarch64-linux-gnu"
export SDL_VIDEODRIVER=wayland SDL_AUDIODRIVER=alsa
# Native SDL creates GLES2/EGL; desktop GL symbols are handled by GL4ES.
export SDL_OPENGL_ES_DRIVER=1 SDL_VIDEO_GL_DRIVER=/lib/libGLESv2.so.2
export LIBGL_EGL=/lib/libEGL.so.1 LIBGL_GLES=/lib/libGLESv2.so.2
export LIBGL_ES=2 LIBGL_GL=21 LIBGL_FB=0
# Preserve the existing native shader archive in a writable, persistent folder.
mkdir -p "$GAME/savedata/cache/gl4es" || exit 8
export LIBGL_PSA_FOLDER="$GAME/savedata/cache/gl4es"
# Compile Cg directly to GLSL, bypassing ARB assembly conversion.
export CGGL_LATEST_VERTEX_PROFILE=glslv CGGL_LATEST_FRAGMENT_PROFILE=glslf
export LIBGL_NOARBPROGRAM=0 LIBGL_LOGSHADERERROR=1
export SDL_GAMECONTROLLERCONFIG="$(cat "$RT/rgds-controller.txt")"
export SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS=1
export BRHM="$GAME/savedata/home"
export XDG_DATA_HOME="$GAME/savedata" XDG_CONFIG_HOME="$GAME/savedata/config" XDG_CACHE_HOME="$GAME/savedata/cache"
export BOX64_DYNAREC=1 BOX64_LOG=0 BOX64_SHOWSEGV=1 BOX64_BOX32=1
export BOX64_NOPERSONA32BITS=1 BOX64_DYNACACHE=0 BOX64_RCFILE="$RT/box64-braid.rc"
export BOX64_LD_LIBRARY_PATH="$RT/libs.x86:$GAME/game/lib"
export BOX64_LIBGL="$RT/gl4es/libGL.so.1"
export BOX64_LD_PRELOAD="$RT/libs.x86/libbraid_compat.so"
export BRAID_RGDS_GLES=1
# Read one numeric setting without executing configuration text.
case "$(cat "$RT/value-cache.txt" 2>/dev/null)" in
 0) export BRAID_VALUE_CACHE=0;;
 *) export BRAID_VALUE_CACHE=1;;
esac
echo "Shader CPU value cache: $BRAID_VALUE_CACHE"
case "$(cat "$RT/lookup-cache.txt" 2>/dev/null)" in
 0) export BRAID_LOOKUP_CACHE=0;;
 *) export BRAID_LOOKUP_CACHE=1;;
esac
echo "Cg query cache: $BRAID_LOOKUP_CACHE"
case "$(cat "$RT/missing-cache.txt" 2>/dev/null)" in
 0) export BRAID_MISSING_CACHE=0;;
 *) export BRAID_MISSING_CACHE=1;;
esac
echo "Cg optional-parameter cache: $BRAID_MISSING_CACHE"
case "$(cat "$RT/direct-bridge.txt" 2>/dev/null)" in
 0) export BRAID_DIRECT_BRIDGE=0;;
 *) export BRAID_DIRECT_BRIDGE=1;;
esac
echo "Direct shader bridge: $BRAID_DIRECT_BRIDGE"
case "$(cat "$RT/revision-cache.txt" 2>/dev/null)" in
 0) export BRAID_REVISION_CACHE=0;;
 *) export BRAID_REVISION_CACHE=1;;
esac
echo "Uniform revision cache: $BRAID_REVISION_CACHE"
case "$(cat "$RT/write-cache.txt" 2>/dev/null)" in
 0) export BRAID_WRITE_CACHE=0;;
 *) export BRAID_WRITE_CACHE=1;;
esac
echo "Verified shader write cache: $BRAID_WRITE_CACHE"
session_tmp=$(mktemp -d /tmp/braid-rgds.XXXXXX) || exit 6
export TMPDIR="$session_tmp"
printf 'WAYLAND_DISPLAY=%s XDG_RUNTIME_DIR=%s\n' "$WAYLAND_DISPLAY" "${XDG_RUNTIME_DIR:-}"
cat /proc/meminfo > "$GAME/logs/Memory_Before.txt" 2>/dev/null || :
"$RT/box64-box32" --version
python3 -u "$RT/rgds-audio-keys.py" /sys/class/anbernic_misc/openbor_volume "$GAME/savedata/volume-level.txt" "$session_tmp/audio-ready" > "$GAME/logs/Audio_Keys.txt" 2>&1 & audio_pid=$!
n=0
while [ ! -f "$session_tmp/audio-ready" ] && kill -0 "$audio_pid" 2>/dev/null && [ "$n" -lt 10 ]; do sleep 1; n=$((n+1)); done
if [ ! -f "$session_tmp/audio-ready" ] || [ "$(cat "$session_tmp/audio-ready")" != ready ]; then
 echo 'ERROR: mixer setup failed. See logs/Audio_Keys.txt.'; exit 7
fi
python3 -u "$RT/exit-guard.py" "$$" > "$GAME/logs/Exit_Guard.txt" 2>&1 & guard_pid=$!
# Lower-panel control used in the previously hardware-tested releases.
if [ -r "$LOWER" ] && [ -w "$LOWER" ]; then
 lower_saved=$(cat "$LOWER" 2>/dev/null)
 case "$lower_saved" in ''|*[!0-9]*) lower_saved='';; *) printf '0\n' > "$LOWER" 2>/dev/null || :; echo "Lower screen disabled (saved brightness=$lower_saved).";; esac
fi
cd "$GAME/game" || exit 5
echo 'Starting Braid: 640x360 internal scene limit, fullscreen output, 30fps target, game VSync disabled, postprocessing disabled.'
"$RT/box64-box32" "$GAME/game/Braid.rgds.x86" -no_launcher -30fps -no_post -no_vsync -no_vsync_test -width 640 -height 360 > "$GAME/logs/Braid_Game.txt" 2>&1 & game_pid=$!
python3 -u "$RT/hardware-perf.py" "$game_pid" > "$GAME/logs/Hardware_Perf.txt" 2>&1 & perf_pid=$!
wait "$game_pid"; rc=$?; game_pid=''
echo "Braid exit code: $rc"
exit "$rc"
