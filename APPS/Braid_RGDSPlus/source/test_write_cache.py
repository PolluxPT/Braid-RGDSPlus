"""Verified CPU write buffering: preserve every draw and exact GPU values.
SDK state is checked independently, including flushes before fallback/readback.
"""
import ast,ctypes as C,json,os,pathlib,subprocess,sys,tempfile
here=pathlib.Path(__file__).resolve().parent
if len(sys.argv)==1:
 tree=ast.parse((here/'test_direct_bridge.py').read_text());mock=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='mock' for t in n.targets))
 mock=mock.replace('static int gpu_s=-1,texture_unit;', 'static int gpu_s=-1,texture_unit;\nstatic float expected_m[16]={1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1},expected_t[4]={1,.5,.25,1};')
 mock=mock.replace('memcmp(matrix,gpu_m,sizeof(matrix))||memcmp(tint,gpu_t,sizeof(tint))', 'memcmp(expected_m,gpu_m,sizeof(expected_m))||memcmp(expected_t,gpu_t,sizeof(expected_t))')
 mock+='''
 int cgGetParameterVariability(void*p){return getenv("MOCK_VARYING")?4101:4102;}
 void cgDestroyContext(void*p){clobber();}
 const char* cgGetProfileString(int profile){return "glslv";}
 const char* cgGetLastListing(void*p){return "";}
 int sdk_current(void);
 void* cgCreateProgram(void*c,int kind,const char*text,int profile,const char*entry,const char**args){if(!sdk_current())abort();return (void*)53;}

 void expect_t(const float*v){memcpy(expected_t,v,sizeof(expected_t));}
 void expect_m(const float*v){memcpy(expected_m,v,sizeof(expected_m));}
 int sdk_current(void){return !memcmp(expected_m,matrix,sizeof(matrix))&&!memcmp(expected_t,tint,sizeof(tint));}
 '''
 with tempfile.TemporaryDirectory() as tmp:
  p=pathlib.Path(tmp);(p/'mock.c').write_text(mock);subprocess.run(['gcc','-shared','-fPIC',str(p/'mock.c'),'-o',str(p/'libGL.so.1')],check=True)
  for f in ['libCg.so','libCgGL.so','libSDL2-2.0.so.0']:(p/f).symlink_to('libGL.so.1')
  (p/'new.c').write_text((here/'braid_compat.c').read_text()+'''\nunsigned long long test_queued(void){return braid_writes_deferred;}
unsigned long long test_flushed(void){return braid_writes_flushed;}
''')
  subprocess.run(['gcc','-shared','-fPIC','-O2','-fno-builtin','-I'+str(here),str(p/'new.c'),'-ldl','-o',str(p/'new.so')],check=True)
  for mode in ['off','on','unmapped','varying','value_off','direct_off']:
   env={**os.environ,'LD_LIBRARY_PATH':str(p),'BRAID_WRITE_CACHE':'0' if mode=='off' else '1','BRAID_VALUE_CACHE':'0' if mode=='value_off' else '1','BRAID_DIRECT_BRIDGE':'0' if mode=='direct_off' else '1','BRAID_REVISION_CACHE':'1'}
   env.pop('MOCK_UNMAPPED',None);env.pop('MOCK_VARYING',None)
   if mode=='unmapped':env['MOCK_UNMAPPED']='1'
   if mode=='varying':env['MOCK_VARYING']='1'
   r=subprocess.run([sys.executable,__file__,str(p),mode],env=env,capture_output=True,text=True)
   assert r.returncode==0,(mode,r.stderr)
   print(r.stdout.strip())
else:
 p=pathlib.Path(sys.argv[1]);mode=sys.argv[2];enabled=mode=='on';g=C.CDLL(str(p/'libGL.so.1'));s=C.CDLL(str(p/'new.so'))
 s.test_queued.restype=s.test_flushed.restype=C.c_ulonglong
 def bind(v=21,f=36):s.cgGLEnableProfile(7007);s.cgGLBindProgram(C.c_void_p(v));s.cgGLEnableProfile(7008);s.cgGLBindProgram(C.c_void_p(f))
 def draw():s.glDrawArrays(4,0,6)
 def color(i):
  v=(C.c_float*4)(i/1234,.3,.4,.5);g.expect_t(v);s.cgSetParameter4fv(C.c_void_p(101),v)
 def matrix(i):
  v=(C.c_float*16)(i,0,0,0,0,i,0,0,0,0,i,0,0,0,0,1);g.expect_m(v);s.cgSetMatrixParameterfr(C.c_void_p(100),v)
 def changed(i):color(i);matrix(i+1)
 def context(mode=4133,managed=0):s.cgSetParameterSettingMode(C.c_void_p(1),mode);s.cgGLSetManageTextureParameters(C.c_void_p(1),managed)
 context();bind();draw();draw();before=g.metric(4);q=s.test_queued()
 for i in range(1000):
  bind();changed(i+1);s.cgUpdateProgramParameters(C.c_void_p(21));s.cgUpdateProgramParameters(C.c_void_p(36));draw()
 delta=g.metric(4)-before;queued=s.test_queued()-q
 assert delta==(0 if enabled else 2000),(mode,delta)
 assert queued==(2000 if enabled else 0),(mode,queued)
 # Verify that SDK values are flushed at a public readback boundary. Every
 # buffered change must already have reached the mock GPU on each prior draw.
 v=(C.c_float*64)();assert s.cgGetParameterValuefr(C.c_void_p(101),64,v)==4
 assert g.sdk_current()==1
 print(mode,':1000 changing frames, draws1000, original numeric setters',delta,'buffered writes',queued)
 # Multiple changed writes to one parameter before a readback coalesce.
 before=g.metric(4)
 for i in range(50):color(2000+i)
 s.cgGetParameterValuefr(C.c_void_p(101),64,v)
 assert g.metric(4)-before==(1 if enabled else 50),(mode,g.metric(4)-before)
 assert g.sdk_current()==1;draw()
 # Each original operation below may need Cg's own current values. Queue
 # changes first and assert SDK coherence immediately after the boundary.
 boundaries=[lambda:s.cgCreateProgram(C.c_void_p(1),4112,b'void main(){}',7007,b'main',None),lambda:s.cgSetParameterSettingMode(C.c_void_p(1),4132),lambda:s.cgGLSetManageTextureParameters(C.c_void_p(1),1),lambda:s.cgGLLoadProgram(C.c_void_p(21)),lambda:s.cgGLDisableProfile(7007),lambda:s.cgDestroyProgram(C.c_void_p(21)),lambda:s.cgDestroyContext(C.c_void_p(1))]
 for i,fn in enumerate(boundaries):
  context();bind();draw();changed(3000+i);draw();fn();assert g.sdk_current()==1,(mode,i)
  context();bind(37,52);draw();bind();draw()
 # Force a previously unseen pair: fallback original Cg binds must flush first.
 changed(4000);bind(37,36);draw();assert g.sdk_current()==1
 context(4132);before=g.metric(4);color(4001);color(4001);draw();assert g.metric(4)-before==2
 context();bind();draw();before=g.metric(4)
 s.cgSetParameter2fv(C.c_void_p(103),(C.c_float*2)(4,5));assert g.metric(4)==before+1;draw()
 print('PASS readback, coalescing, immediate/managed modes, varying/unmapped guards, GPU clobbers, loads, fallback binds and program/context lifecycle')
