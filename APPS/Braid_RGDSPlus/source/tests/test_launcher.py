from pathlib import Path
import os,subprocess,tempfile

with tempfile.TemporaryDirectory() as directory:
    root=Path(directory);apps=root/'APPS';game=apps/'Braid_RGDSPlus';runtime=game/'runtime';bin=root/'bin'
    runtime.mkdir(parents=True);bin.mkdir();brightness=root/'brightness';brightness.write_text('70\n')
    launcher=Path(__file__).resolve().parent/'launcher.sh'
    if not launcher.exists():launcher=Path(__file__).resolve().parent.parents[2]/'Braid.sh'
    (apps/'Braid.sh').write_text(launcher.read_text().replace('/sys/class/backlight/backlight/brightness',str(brightness)))
    for name in ('game/Braid.rgds.x86','game/data/package.braid','game/data/package0.braid','game/lib/libCg.so','game/lib/libCgGL.so','runtime/gl4es/libGL.so.1','runtime/libs.x86/libbraid_compat.so','runtime/libs.x86/libstdc++.so.6','runtime/libs.x86/libgcc_s.so.1','runtime/rgds-controller.txt'):
        p=game/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('fixture')
    scripts={
      'uname':'#!/bin/sh\necho aarch64\n',
      'amixer':'#!/bin/sh\nexit 0\n',
      'python3':'''#!/bin/sh
case "$2" in
 */rgds-audio-keys.py) echo ready > "$5"; exec sleep 30;;
 */exit-guard.py) exec sleep 30;;
 */hardware-perf.py) echo "MONITOR PID $3"; exec sleep 30;;
 *) exit 99;;
esac
'''}
    for name,body in scripts.items():p=bin/name;p.write_text(body);p.chmod(0o755)
    p=runtime/'box64-box32';p.write_text('''#!/bin/sh
if [ "$1" = --version ]; then exit 0; fi
[ "$(cat "$TEST_BRIGHTNESS")" = 0 ] || exit 91
[ "$BRAID_VALUE_CACHE" = "$TEST_CACHE" ] || exit 92
[ "$BRAID_DIRECT_BRIDGE" = "$TEST_DIRECT" ] || exit 93
[ "$BRAID_LOOKUP_CACHE" = "$TEST_LOOKUP" ] || exit 94
[ "$BRAID_MISSING_CACHE" = "$TEST_MISSING" ] || exit 97
[ "$BRAID_REVISION_CACHE" = "$TEST_REVISION" ] || exit 98
[ "$BRAID_WRITE_CACHE" = "$TEST_WRITE" ] || exit 99
[ -d "$LIBGL_PSA_FOLDER" ] || exit 95
case "$LIBGL_PSA_FOLDER" in */savedata/cache/gl4es) :;; *) exit 96;; esac
printf 'ARGS %s\n' "$*"
sleep 0.3
''');p.chmod(0o755)
    env={**os.environ,'PATH':str(bin)+':'+os.environ['PATH'],'WAYLAND_DISPLAY':'wayland-fixture','XDG_RUNTIME_DIR':str(root),'TEST_BRIGHTNESS':str(brightness)}
    for cache,direct,lookup,missing,revision,write in ((v,d,l,m,r,w) for v in ('1','0') for d in ('1','0') for l in ('1','0') for m in ('1','0') for r in ('1','0') for w in ('1','0')):
        (runtime/'value-cache.txt').write_text(cache+'\n')
        (runtime/'direct-bridge.txt').write_text(direct+'\n')
        (runtime/'lookup-cache.txt').write_text(lookup+'\n')
        (runtime/'missing-cache.txt').write_text(missing+'\n')
        (runtime/'revision-cache.txt').write_text(revision+'\n')
        (runtime/'write-cache.txt').write_text(write+'\n')
        result=subprocess.run(['/bin/sh',str(apps/'Braid.sh')],env={**env,"TEST_CACHE":cache,"TEST_DIRECT":direct,"TEST_LOOKUP":lookup,"TEST_MISSING":missing,"TEST_REVISION":revision,"TEST_WRITE":write},timeout=15)
        assert result.returncode==0,(game/'logs/Arranque_Braid.txt').read_text()
        log=(game/'logs/Braid_Game.txt').read_text()
        assert '-no_vsync -no_vsync_test -width 640 -height 360' in log
        assert (game/'logs/Hardware_Perf.txt').read_text().startswith('MONITOR PID ')
        assert brightness.read_text().strip()=='70'
        assert not (game/'savedata/.running').exists()
        assert 'Launcher cleanup complete' in (game/'logs/Arranque_Braid.txt').read_text()
print('PASS: all64 cache combinations, persistent shader path, performance arguments, monitor startup, lower-screen off/restore and launcher cleanup')
