import importlib.util
from pathlib import Path
import tempfile
base=Path(__file__).resolve().parent
script=base/'runtime/hardware-perf.py'
if not script.exists():script=base.parents[1]/'runtime/hardware-perf.py'
spec=importlib.util.spec_from_file_location('monitor',script)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
with tempfile.TemporaryDirectory() as directory:
    root=Path(directory)
    for name,value in {'sys/class/thermal/thermal_zone0/type':'soc-thermal','sys/class/thermal/thermal_zone0/temp':'55000','sys/devices/system/cpu/cpufreq/policy0/scaling_cur_freq':'1800000','sys/class/devfreq/gpu/cur_freq':'800000000'}.items():
        p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(value)
    p=root/'proc/42/stat';p.parent.mkdir(parents=True)
    def state(ticks):
        fields=['S']+['0']*19;fields[11]=str(ticks);fields[12]='0'
        p.write_text('42 (Braid game) '+' '.join(fields))
    sampler=m.Sampler(42,root);state(100);a=sampler.sample(10)
    state(100+5*sampler.tick_hz);b=sampler.sample(15)
    assert a['process_cpu_percent'] is None and b['process_cpu_percent']==100
    assert b['sensors']['sys/class/thermal/thermal_zone0/temp']=='55000'
    (root/'sys/class/thermal/thermal_zone0/temp').unlink()
    assert 'sys/class/thermal/thermal_zone0/temp' not in sampler.sample(20)['sensors']
    p.unlink();assert sampler.sample(25) is None
print('PASS: CPU utilization, sensor reads, disappearing nodes and process exit')
