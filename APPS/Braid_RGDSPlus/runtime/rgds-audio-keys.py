#!/usr/bin/env python3
"""RGDS+ evdev volume keys -> ALSA mixer, adapted from the supplied Heist port."""
import glob
import os
import re
import select
import signal
import struct
import subprocess
import sys
import time
from pathlib import Path

CURVE = (0, 8, 15, 23, 32, 42, 53, 64, 76, 88, 100)
MIXERS = ('Master', 'PCM', 'Speaker', 'Playback', 'Headphone', 'Headphones')
UP, DOWN, EV_KEY = 115, 114, 1

def command(*args):
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=1)
    except (OSError, subprocess.TimeoutExpired):
        return None

def mixer_snapshot(text):
    channels = []
    for line in text.splitlines():
        if 'Playback' not in line:
            continue
        pct = re.search(r'\[(\d+)%\]', line)
        if pct:
            switch = re.findall(r'\[(on|off)\]', line)
            channels.append((pct.group(1), switch[-1] if switch else None))
    return channels

def main():
    node = Path(sys.argv[1])
    state = Path(sys.argv[2])
    ready = Path(sys.argv[3])
    stopped = False
    def stop(*_):
        nonlocal stopped
        stopped = True
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    saved_sysfs = None
    try:
        saved_sysfs = node.read_text().strip()
        if not saved_sysfs.isdigit(): saved_sysfs = None
    except OSError:
        pass
    mixer, before = None, []
    for candidate in MIXERS:
        result = command('amixer', 'sget', candidate)
        if result is not None and result.returncode == 0:
            snap = mixer_snapshot(result.stdout)
            if snap:
                mixer, before = candidate, snap
                break
    level = 3  # 23% on first launch, lower than Heist's 53% default.
    try:
        requested = int(state.read_text().strip())
        if 0 <= requested <= 10: level = requested
    except (OSError, ValueError):
        pass
    fds, buffers = [], {}
    def apply(n):
        nonlocal level
        level = max(0, min(10, n))
        try: node.write_text(str(level) + '\n')
        except OSError: pass
        if mixer:
            result = command('amixer', '-q', 'sset', mixer, str(CURVE[level]) + '%')
            status = 'ok' if result is not None and result.returncode == 0 else 'failed'
            print('[AUDIO] level=%d/10 mixer=%s percent=%d result=%s' % (level, mixer, CURVE[level], status), flush=True)
        else:
            print('[AUDIO] no usable ALSA mixer; sysfs-only level=%d/10' % level, flush=True)
        try: state.write_text(str(level) + '\n')
        except OSError: pass
    try:
        for path in sorted(glob.glob('/dev/input/event*')):
            try:
                fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
                fds.append(fd); buffers[fd] = b''
            except OSError:
                pass
        print('[AUDIO] event devices=%d selected mixer=%s' % (len(fds), mixer), flush=True)
        apply(level)
        ready.write_text('ready\n' if mixer else 'no-mixer\n')
        fmt = 'llHHi'; size = struct.calcsize(fmt)
        while not stopped:
            if not fds:
                time.sleep(0.2); continue
            readable, _, _ = select.select(fds, [], [], 0.2)
            for fd in readable:
                try: data = os.read(fd, 4096)
                except BlockingIOError: continue
                except OSError: data = b''
                if not data:
                    fds.remove(fd); os.close(fd); continue
                buffers[fd] += data
                while len(buffers[fd]) >= size:
                    item, buffers[fd] = buffers[fd][:size], buffers[fd][size:]
                    _, _, kind, code, value = struct.unpack(fmt, item)
                    if kind == EV_KEY and value in (1, 2) and code in (UP, DOWN):
                        apply(level + (1 if code == UP else -1))
    finally:
        for fd in fds: os.close(fd)
        if mixer and before:
            levels = ','.join(pct + '%' for pct, _ in before)
            args = ['amixer', '-q', 'sset', mixer, levels]
            switches = {s for _, s in before if s is not None}
            if len(switches) == 1: args.append('unmute' if switches == {'on'} else 'mute')
            restored = command(*args)
            print('[AUDIO] mixer restore=%s' % ('ok' if restored is not None and restored.returncode == 0 else 'failed'), flush=True)
        if saved_sysfs is not None:
            try: node.write_text(saved_sysfs + '\n')
            except OSError: pass
        ready.unlink(missing_ok=True)
        print('[AUDIO] stopped; app volume saved, previous system level restored.', flush=True)

if __name__ == '__main__':
    main()
