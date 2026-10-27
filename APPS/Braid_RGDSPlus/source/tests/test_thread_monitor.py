import importlib.util,tempfile
from pathlib import Path
script=Path(__file__).resolve().parents[2]/'runtime/hardware-perf.py'
spec=importlib.util.spec_from_file_location('monitor',script);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
with tempfile.TemporaryDirectory() as d:
 root=Path(d)
 def stat(path,tid,name,ticks,birth=100,cpu=0):
  path.parent.mkdir(parents=True,exist_ok=True);f=['S']+['0']*36
  f[11]=str(ticks);f[19]=str(birth);f[36]=str(cpu)
  path.write_text(str(tid)+' ('+name+') '+' '.join(f))
 main=root/'proc/42/stat';render=root/'proc/42/task/42/stat';audio=root/'proc/42/task/43/stat'
 stat(main,42,'game',100);stat(render,42,'render (main)',100,cpu=1);stat(audio,43,'audio',50,cpu=3)
 sampler=m.Sampler(42,root);hz=sampler.tick_hz;a=sampler.sample(10)
 assert all(t['cpu_percent'] is None for t in a['threads'])
 stat(main,42,'game',100+6*hz);stat(render,42,'render (main)',100+5*hz,cpu=1);stat(audio,43,'audio',50+hz,cpu=3)
 b=sampler.sample(15);threads={t['tid']:t for t in b['threads']}
 assert threads[42]['cpu_percent']==100 and threads[43]['cpu_percent']==20,b
 assert threads[42]['name']=='render (main)' and threads[43]['last_cpu']==3
 audio.unlink();assert len(sampler.sample(20)['threads'])==1
 stat(audio,43,'new worker',0,birth=999,cpu=2)
 assert next(t for t in sampler.sample(25)['threads'] if t['tid']==43)['cpu_percent'] is None
 main.unlink();assert sampler.sample(30) is None
print('PASS thread CPU percentages, names, CPU number, disappearance, TID reuse and process exit')
