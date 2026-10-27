import os
os.environ["BRAID_WRITE_CACHE"]="0"
import ctypes as C, os, pathlib, subprocess, tempfile, sys
source=pathlib.Path(os.environ.get('BRAID_TEST_SOURCE', str(pathlib.Path(__file__).with_name('braid_compat.c')))).resolve()
if len(sys.argv)==1:
 with tempfile.TemporaryDirectory() as t:
  p=pathlib.Path(t)
  (p/'mock.c').write_text(r'''
static int draws,loads,binds;
int cgGetProgramProfile(void *p){return 6150;}
void glGetIntegerv(unsigned n,int *v){if(n==0xba2||n==0xc10){v[0]=v[1]=0;v[2]=640;v[3]=480;}else if(n==0xc23){v[0]=v[1]=v[2]=v[3]=1;}else *v=0;}
unsigned char glIsEnabled(unsigned n){return n==0x8620||n==0x8804;}
void glGetProgramivARB(unsigned t,unsigned n,int *v){*v=n==0x8627?128:7;}
void glDrawArrays(unsigned m,int f,int c){if(m==4&&f==2&&c==6)draws++;}
void glDrawElements(unsigned m,int c,unsigned t,const void *p){if(m==4&&c==6&&t==0x1403&&p==(void*)32)draws++;}
void glBegin(unsigned m){if(m==7)draws++;}
void cgGLLoadProgram(void *p){if(p==(void*)21)loads++;}
void cgGLBindProgram(void *p){if(p==(void*)21)binds++;}
int cgGLIsProgramLoaded(void *p){return p==(void*)21;}
unsigned cgGLGetProgramID(void *p){return p==(void*)21?7:0;}
int totals(void){return draws==130&&loads==1&&binds==1;}
''')
  subprocess.run(['gcc','-shared','-fPIC',str(p/'mock.c'),'-o',str(p/'libGL.so.1')],check=True)
  (p/'libCgGL.so').symlink_to('libGL.so.1')
  (p/'libCg.so').symlink_to('libGL.so.1')
  subprocess.run(['gcc','-shared','-fPIC','-fno-builtin',str(source),'-ldl','-o',str(p/'trace.so')],check=True)
  r=subprocess.run([sys.executable,__file__,str(p)],env={**os.environ,'LD_LIBRARY_PATH':t,'BRAID_TRACE_RENDER':'1'},capture_output=True,text=True)
  assert r.returncode==0,r.stderr
  assert r.stderr.count('BRAID_DRAW:')==13,r.stderr
  assert 'loaded=1 id=7' in r.stderr
  assert 'vertex=1:7/128 fragment=1:7/128' in r.stderr
  print('PASS: native shim forwards CgGL and 130 draw calls, logs valid states, bounds output; no error-consumption calls')
else:
 p=pathlib.Path(sys.argv[1]); g=C.CDLL(str(p/'libGL.so.1'));s=C.CDLL(str(p/'trace.so'))
 s.cgGLLoadProgram(C.c_void_p(21));s.cgGLBindProgram(C.c_void_p(21))
 for i in range(128):s.glDrawArrays(4,2,6)
 s.glDrawElements(4,6,0x1403,C.c_void_p(32));s.glBegin(7)
 assert g.totals()==1
