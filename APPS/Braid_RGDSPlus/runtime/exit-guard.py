#!/usr/bin/env python3
"""Hold joystick buttons 6+7 for 1.5 seconds; axes never trigger exit."""
import array
import glob
import os
import select
import signal
import struct
import sys
import time
import fcntl

parent = int(sys.argv[1])
devices = {}
held = {}
since = {}
for path in glob.glob('/dev/input/js*'):
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
        name = array.array('B', [0] * 128)
        fcntl.ioctl(fd, 0x80806a13, name, True)
        label = name.tobytes().split(b'\0')[0].decode(errors='replace')
        if not any(token in label.lower() for token in ('anbernic', 'rk3568')):
            os.close(fd)
            continue
        devices[fd] = path
        held[fd] = set()
        since[fd] = None
        print('Exit guard:', path, label, flush=True)
    except OSError as exc:
        print('Exit guard:', path, exc, flush=True)
if not devices:
    print('Exit guard: no matching joystick; use the game Quit menu.', flush=True)
while devices:
    try:
        os.kill(parent, 0)
    except ProcessLookupError:
        break
    ready, _, _ = select.select(list(devices), [], [], 0.1)
    for fd in ready:
        try:
            data = os.read(fd, 8 * 64)
        except BlockingIOError:
            continue
        except OSError:
            data = b''
        if not data:
            os.close(fd)
            del devices[fd]
            continue
        for offset in range(0, len(data) - 7, 8):
            _, value, kind, button = struct.unpack_from('<IhBB', data, offset)
            if kind & 1:
                if value:
                    held[fd].add(button)
                else:
                    held[fd].discard(button)
    for fd in devices:
        if {6, 7} <= held[fd]:
            if since[fd] is None:
                since[fd] = time.monotonic()
            elif time.monotonic() - since[fd] >= 1.5:
                print('Exit guard: START+SELECT held; requesting shutdown.', flush=True)
                os.kill(parent, signal.SIGTERM)
                sys.exit(0)
        else:
            since[fd] = None
