#!/usr/bin/env python3
"""Read-only CPU, clock and thermal sampling for the Braid process."""
import json
import os
from pathlib import Path
import signal
import sys
import threading
import time

class Sampler:
    def __init__(self,pid,root=Path('/')):
        self.pid=pid;self.root=Path(root);self.previous=None;self.thread_previous={}
        self.tick_hz=os.sysconf('SC_CLK_TCK')
        self.paths=[]
        patterns=('sys/class/thermal/thermal_zone*/type','sys/class/thermal/thermal_zone*/temp',
                  'sys/devices/system/cpu/cpufreq/policy*/scaling_cur_freq',
                  'sys/devices/system/cpu/cpufreq/policy*/scaling_max_freq',
                  'sys/devices/system/cpu/cpufreq/policy*/cpuinfo_max_freq',
                  'sys/devices/system/cpu/cpufreq/policy*/scaling_governor',
                  'sys/class/devfreq/*/cur_freq','sys/class/devfreq/*/min_freq',
                  'sys/class/devfreq/*/max_freq','sys/class/devfreq/*/governor',
                  'sys/class/devfreq/*/load','sys/class/devfreq/*/device/utilization',
                  'sys/class/devfreq/*/device/utilisation')
        for pattern in patterns:self.paths.extend(self.root.glob(pattern))
        self.paths=sorted(set(self.paths))

    def sample(self,now):
        sensors={}
        for p in self.paths:
            try:sensors[str(p.relative_to(self.root))]=p.read_text().strip()[:160]
            except (OSError,UnicodeError):pass
        try:
            text=(self.root/f'proc/{self.pid}/stat').read_text()
            fields=text[text.rfind(')')+2:].split()
            ticks=int(fields[11])+int(fields[12])
        except (OSError,ValueError,IndexError):return None
        usage=None
        if self.previous and now>self.previous[0]:
            usage=round(100*(ticks-self.previous[1])/self.tick_hz/(now-self.previous[0]),1)
        self.previous=(now,ticks)
        threads=[];current={}
        for path in sorted((self.root/f'proc/{self.pid}/task').glob('*/stat')):
            try:
                raw=path.read_text();end=raw.rfind(')');f=raw[end+2:].split()
                tid=int(path.parent.name);ticks=int(f[11])+int(f[12]);birth=f[19]
                old=self.thread_previous.get(tid);percent=None
                if old and old[2]==birth and now>old[0] and ticks>=old[1]:
                    percent=round(100*(ticks-old[1])/self.tick_hz/(now-old[0]),1)
                current[tid]=(now,ticks,birth)
                threads.append(dict(tid=tid,name=raw[raw.find('(')+1:end][:80],cpu_percent=percent,last_cpu=int(f[36]) if len(f)>36 else None))
            except (OSError,ValueError,IndexError):pass
        self.thread_previous=current
        return dict(monotonic_s=round(now,3),process_cpu_percent=usage,sensors=sensors,threads=threads)

def main():
    pid=int(sys.argv[1]);sampler=Sampler(pid);stop=threading.Event();start=time.monotonic()
    for sig in (signal.SIGTERM,signal.SIGINT,signal.SIGHUP):signal.signal(sig,lambda *_:stop.set())
    print(json.dumps(dict(event='start',pid=pid,tick_hz=sampler.tick_hz,wall_time_s=time.time())),flush=True)
    while not stop.is_set():
        now=time.monotonic();record=sampler.sample(now)
        if record is None:break
        record['elapsed_s']=round(now-start,3)
        print(json.dumps(record,sort_keys=True),flush=True)
        stop.wait(5)
    print(json.dumps(dict(event='stop',elapsed_s=round(time.monotonic()-start,3))),flush=True)

if __name__=='__main__':main()
