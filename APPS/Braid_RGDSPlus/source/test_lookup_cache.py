import ctypes as C,os,pathlib,subprocess,sys,tempfile
here=pathlib.Path(__file__).resolve().parent
mock=r'''
#include <stdint.h>
#include <string.h>
static int names,profiles,generation=1;
void *cgGetNamedParameter(void*p,const char*n){names++;if(p==(void*)999||!n||(!strcmp(n,"late")&&generation==1)||!strcmp(n,"missing")||!strcmp(n,"missing[0]"))return 0;return (void*)(uintptr_t)(generation*100+(unsigned char)n[0]);}
int cgGetProgramProfile(void*p){profiles++;if(p==(void*)999)return 6145;return generation%2?7007:7008;}
void cgDestroyProgram(void*p){generation++;}
void cgDestroyContext(void*p){generation++;}
int counter(int kind){return kind?profiles:names;}
'''
if len(sys.argv)==1:
 with tempfile.TemporaryDirectory() as d:
  p=pathlib.Path(d);(p/'mock.c').write_text(mock)
  subprocess.run(['gcc','-shared','-fPIC',str(p/'mock.c'),'-o',str(p/'libCg.so')],check=True)
  (p/'shim.c').write_text((here/'braid_compat.c').read_text()+'\nunsigned long long test_name_fast_hits(void){return braid_name_fast_hits;}\n')
  subprocess.run(['gcc','-shared','-fPIC','-O2','-fno-builtin','-I'+str(here),str(p/'shim.c'),'-ldl','-o',str(p/'shim.so')],check=True)
  for mode in ['0','1','2']:
   r=subprocess.run([sys.executable,__file__,str(p),mode],env={**os.environ,'LD_LIBRARY_PATH':str(p),'BRAID_LOOKUP_CACHE':'0' if mode=='0' else '1','BRAID_MISSING_CACHE':'0' if mode=='2' else '1'},capture_output=True,text=True)
   assert r.returncode==0,r.stderr;print(r.stdout.strip())
else:
 p=pathlib.Path(sys.argv[1]);enabled=sys.argv[2]!='0';missing_enabled=sys.argv[2]=='1';real=C.CDLL(str(p/'libCg.so'));shim=C.CDLL(str(p/'shim.so'))
 shim.cgGetNamedParameter.argtypes=[C.c_void_p,C.c_char_p];shim.cgGetNamedParameter.restype=C.c_void_p
 shim.cgGetProgramProfile.argtypes=[C.c_void_p];shim.cgGetProgramProfile.restype=C.c_int
 for i in range(1000):
  assert shim.cgGetNamedParameter(21,b'alpha')==197
  assert shim.cgGetProgramProfile(21)==7007
 assert real.counter(0)==(1 if enabled else 1000)
 assert real.counter(1)==(1 if enabled else 1000)
 print(('cached' if enabled else 'fallback'),'1000 repeated queries: name/profile Cg calls',real.counter(0),real.counter(1))
 mutable=C.create_string_buffer(b'alpha');assert shim.cgGetNamedParameter(21,mutable)==197
 before_fast=shim.test_name_fast_hits()
 for i in range(100):assert shim.cgGetNamedParameter(21,mutable)==197
 assert shim.test_name_fast_hits()-before_fast==(100 if enabled else 0)
 mutable.value=b'beta';assert shim.cgGetNamedParameter(21,mutable)==198
 mutable.value=b'alpha';assert shim.cgGetNamedParameter(21,mutable)==197
 assert shim.cgGetNamedParameter(21,b'alpha')==197
 before=real.counter(0)
 for i in range(2):assert shim.cgGetNamedParameter(21,b'missing') is None
 assert real.counter(0)==before+(1 if missing_enabled else 2)
 before=real.counter(0)
 for i in range(2):assert shim.cgGetNamedParameter(21,b'x'*300)==220
 assert real.counter(0)==before+2
 # Complex name misses must remain uncached.
 before=real.counter(0)
 for i in range(2):shim.cgGetNamedParameter(21,b'missing[0]')
 assert real.counter(0)==before+2
 before=real.counter(0);old_profiles=real.counter(1)
 for i in range(2):assert shim.cgGetNamedParameter(999,b'missing') is None
 assert real.counter(0)==before+2 and real.counter(1)==old_profiles
 assert shim.cgGetNamedParameter(21,b'late') is None
 assert shim.cgGetNamedParameter(21,b'late') is None
 shim.cgDestroyProgram(C.c_void_p(21))
 # A previously missing parameter may exist after the program handle is reused.
 assert shim.cgGetNamedParameter(21,b'late')==308
 assert shim.cgGetNamedParameter(21,b'alpha')==297
 assert shim.cgGetProgramProfile(21)==7008
 shim.cgDestroyContext(C.c_void_p(1))
 assert shim.cgGetNamedParameter(21,b'alpha')==397
 assert shim.cgGetProgramProfile(21)==7007
 print('PASS positive/negative results, repeated caller pointers, mutated/restored names, uncached aggregate/long misses and destruction/reused handles')
