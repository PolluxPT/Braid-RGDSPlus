import os
os.environ["BRAID_WRITE_CACHE"]="0"
import ctypes as C, pathlib, subprocess, os, sys, tempfile
here=pathlib.Path(__file__).resolve().parent
mock='\n#include <string.h>\n#include <stdlib.h>\n#include <stdio.h>\nstatic unsigned nextid=10,current=999,ticks;\nstatic int draws,reads,uploads,binds,setters,mode,commits,cgbinds;static void *real_v,*real_f;\nstatic float matrix[16]={1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1},tint[4]={1,0.5,0.25,1},gpu_m[16],gpu_t[4];\nstatic int gpu_s=-1,texture_unit;\nstatic float saved_m[2048][16],saved_t[2048][4];static int saved_s[2048];\nstatic void clobber(void){current=999;memset(gpu_m,0,sizeof(gpu_m));memset(gpu_t,0,sizeof(gpu_t));gpu_s=-1;memset(saved_m,0,sizeof(saved_m));memset(saved_t,0,sizeof(saved_t));memset(saved_s,0xff,sizeof(saved_s));}\nint cgGetProgramProfile(void*p){return p==(void*)21||p==(void*)37?7007:7008;}\nconst char*cgGetProgramString(void*p,int kind){return "#version 110\\nvoid main(){}\\n";}\nvoid cgGLBindProgram(void*p){if(cgGetProgramProfile(p)==7007)real_v=p;else real_f=p;cgbinds++;clobber();}\nvoid cgGLLoadProgram(void*p){texture_unit=1-texture_unit;clobber();}\nint cgGLIsProgramLoaded(void*p){return 1;}\nunsigned cgGLGetProgramID(void*p){return 7;}\nvoid cgGLEnableProfile(int p){clobber();}\nvoid cgGLDisableProfile(int p){clobber();}\nvoid *cgGetNamedParameter(void*p,const char*n){\n if(cgGetProgramProfile(p)==7007&&!strcmp(n,"m"))return (void*)100;\n if(cgGetProgramProfile(p)==7008&&!strcmp(n,"tint"))return (void*)101;\n if(cgGetProgramProfile(p)==7008&&!strcmp(n,"diffuse_texture"))return (void*)102;\n return 0;\n}\nint cgIsParameterReferenced(void*p){return 1;}\nunsigned cgGLGetTextureEnum(void*p){return 0x84c0+texture_unit;}\nint cgGetParameterValuefr(void*p,int n,float*v){reads++;if(p==(void*)100){memcpy(v,matrix,sizeof(matrix));return 16;}if(p==(void*)101){memcpy(v,tint,sizeof(tint));return 4;}abort();}\nvoid cgSetMatrixParameterfr(void*p,const float*v){setters++;memcpy(matrix,v,sizeof(matrix));if(mode!=4133)clobber();}\nvoid cgSetParameter4fv(void*p,const float*v){setters++;memcpy(tint,v,sizeof(tint));if(mode!=4133)clobber();}\nvoid cgSetParameter2fv(void*p,const float*v){setters++;if(mode!=4133)clobber();}\nvoid cgUpdateProgramParameters(void*p){if((cgGetProgramProfile(p)==7007?real_v:real_f)!=p)abort();commits++;clobber();}\nvoid cgSetParameterSettingMode(void*p,int m){mode=m;clobber();}\nunsigned glCreateShader(unsigned t){return nextid++;}\nunsigned glCreateProgram(void){return nextid++;}\nvoid glShaderSource(unsigned s,int c,const char**p,const int*l){if(c!=1||!strstr(*p,"#version"))abort();}\nvoid glCompileShader(unsigned s){}\nvoid glGetShaderiv(unsigned s,unsigned n,int*p){*p=1;}\nvoid glGetShaderInfoLog(unsigned s,int n,int*l,char*p){if(n)*p=0;}\nvoid glGetProgramInfoLog(unsigned s,int n,int*l,char*p){if(n)*p=0;}\nvoid glAttachShader(unsigned p,unsigned s){}\nvoid glLinkProgram(unsigned p){}\nvoid glGetProgramiv(unsigned p,unsigned n,int*v){*v=n==0x8b86?(getenv("MOCK_UNMAPPED")?4:3):1;}\nvoid glUseProgram(unsigned p){current=p;binds++;memcpy(gpu_m,saved_m[p],sizeof(gpu_m));memcpy(gpu_t,saved_t[p],sizeof(gpu_t));gpu_s=saved_s[p];}\nvoid glGetIntegerv(unsigned n,int*p){if(n==0x8b8d)*p=current;else *p=0;}\nvoid glGetActiveUniform(unsigned p,unsigned i,int max,int*l,int*size,unsigned*type,char*name){\n const char*n=i==3?"_unknown":i==0?"_m[0]":i==1?"_tint":"_diffuse_texture";\n strcpy(name,n);*l=strlen(n);*size=i==0?4:1;*type=i==2?0x8b5e:0x8b52;\n}\nint glGetUniformLocation(unsigned p,const char*n){return !strcmp(n,"_m[0]")?0:!strcmp(n,"_tint")?16:20;}\nvoid glUniform1fv(int l,int n,const float*v){abort();}\nvoid glUniform2fv(int l,int n,const float*v){abort();}\nvoid glUniform3fv(int l,int n,const float*v){abort();}\nvoid glUniform4fv(int l,int n,const float*v){uploads++;if(l==0&&n==4){memcpy(gpu_m,v,sizeof(gpu_m));memcpy(saved_m[current],v,sizeof(gpu_m));}else if(l==16&&n==1){memcpy(gpu_t,v,sizeof(gpu_t));memcpy(saved_t[current],v,sizeof(gpu_t));}else abort();}\nvoid glUniform1i(int l,int v){uploads++;gpu_s=v;saved_s[current]=v;}\nvoid glBindFramebufferEXT(unsigned target,unsigned fbo){}\nvoid glViewport(int x,int y,int w,int h){}\nvoid glDrawArrays(unsigned m,int first,int n){if(current==999||memcmp(matrix,gpu_m,sizeof(matrix))||memcmp(tint,gpu_t,sizeof(tint))||gpu_s!=texture_unit)abort();draws++;}\nvoid glDrawElements(unsigned m,int n,unsigned t,const void*p){glDrawArrays(m,0,n);}\nvoid glBegin(unsigned m){glDrawArrays(m,0,0);}\nvoid glGetProgramivARB(unsigned t,unsigned n,int*p){*p=0;}\nunsigned char glIsEnabled(unsigned c){return 0;}\nvoid SDL_GL_SwapWindow(void*w){ticks+=34;}\nunsigned SDL_GetTicks(void){return ticks;}\nint metric(int n){return n==0?draws:n==1?reads:n==2?uploads:n==3?binds:n==4?setters:n==5?commits:cgbinds;}\n\nvoid* cgGetParameterContext(void*p){return (void*)1;}\nvoid* cgGetProgramContext(void*p){return (void*)1;}\nvoid cgGLSetManageTextureParameters(void*p,int m){clobber();}\nint cgGetParameterRows(void*p){return p==(void*)100?4:1;}\nint cgGetParameterColumns(void*p){return p==(void*)103?2:4;}\nint cgGetParameterType(void*p){return p==(void*)100?16:p==(void*)103?2:4;}\nconst char *cgGetTypeString(int t){return t==16?"float4x4":t==2?"float2":"float4";}\nvoid cgDestroyProgram(void*p){clobber();}\n'
if len(sys.argv)==1:
 with tempfile.TemporaryDirectory() as tmp:
  p=pathlib.Path(tmp);(p/'mock.c').write_text(mock)
  subprocess.run(['gcc','-shared','-fPIC',str(p/'mock.c'),'-o',str(p/'libGL.so.1')],check=True)
  for lib in ['libCg.so','libCgGL.so','libSDL2-2.0.so.0']:(p/lib).symlink_to('libGL.so.1')
  subprocess.run(['gcc','-shared','-fPIC','-O2','-fno-builtin','-I'+str(here),str(here/'braid_compat.c'),'-ldl','-o',str(p/'new.so')],check=True)
  for enabled in ['0','1','2']:
   r=subprocess.run([sys.executable,__file__,str(p),enabled],env={**os.environ,'LD_LIBRARY_PATH':str(p),'BRAID_VALUE_CACHE':'1','BRAID_DIRECT_BRIDGE':'0' if enabled=='0' else '1',**({'MOCK_UNMAPPED':'1'} if enabled=='2' else {})},capture_output=True,text=True)
   assert r.returncode==0,r.stderr
   assert 'scene_max=640x360' in r.stderr and 'swap_avg_ms=34.00' in r.stderr,r.stderr
   print(r.stdout.strip())
else:
 p=pathlib.Path(sys.argv[1]);enabled=sys.argv[2]=='1';g=C.CDLL(str(p/'libGL.so.1'));s=C.CDLL(str(p/'new.so'))
 def bind(v=21,f=36):s.cgGLEnableProfile(7007);s.cgGLBindProgram(C.c_void_p(v));s.cgGLEnableProfile(7008);s.cgGLBindProgram(C.c_void_p(f))
 def draw(n=1):
  for i in range(n):s.glDrawArrays(4,0,6)
 def metrics():return tuple(g.metric(i) for i in range(7))
 def tint(a):return (C.c_float*4)(a,.3,.4,.5)
 matrix=(C.c_float*16)(2,0,0,0,0,2,0,0,0,0,2,0,0,0,0,1)
 s.cgSetParameterSettingMode(C.c_void_p(1),4133);s.cgGLSetManageTextureParameters(C.c_void_p(1),0);bind();s.glBindFramebufferEXT(0x8d40,2);s.glViewport(0,0,640,360);draw()
 for i in range(1000):
  bind()
  # Each frame has changed values, repeated identical deferred setters,
  # original CgGL commits that clobber GPU values, and fresh frame epochs.
  s.cgSetMatrixParameterfr(C.c_void_p(100),matrix)
  color=tint((i%7)/10)
  s.cgSetParameter4fv(C.c_void_p(101),color)
  s.cgSetParameter4fv(C.c_void_p(101),color)
  s.cgUpdateProgramParameters(C.c_void_p(21));s.cgUpdateProgramParameters(C.c_void_p(36));draw(3)
  s.SDL_GL_SwapWindow(None)
 m=metrics()
 assert m[0]==3001,m
 assert m[1]==2,m
 assert m[4]==1001,m
 assert m[2]==(1004 if enabled else 3003),m
 assert m[5]==(0 if enabled else 2000),m
 assert m[6]==(2 if enabled else 2002),m
 print(('direct' if enabled else 'compatible'),'1000 changing frames: draws, Cg reads, uploads, binds, original setters, commits, Cg binds =',m)
 before=metrics()
 for i in range(1000):
  bind();s.cgSetParameter4fv(C.c_void_p(101),tint(.11 if i%2 else .22))
  s.cgUpdateProgramParameters(C.c_void_p(21));s.cgUpdateProgramParameters(C.c_void_p(36));draw()
 after=metrics()
 assert after[2]-before[2]==(1000 if enabled else 3000),(before,after)
 assert after[3]-before[3]==(1 if enabled else 1000),(before,after)
 color=tint(.11)
 print('PASS1000 changing passes within one frame: GPU uploads',after[2]-before[2],'GLSL binds',after[3]-before[3])
 # Parameter103 is optimized out of every active GLSL uniform list.
 before=metrics()
 for i in range(100):
  s.cgSetParameter2fv(C.c_void_p(103),(C.c_float*2)(i,i+1));draw()
 after=metrics()
 assert after[2]-before[2]==(0 if enabled else 300),(before,after)
 print('PASS100 unreferenced deferred setters: GPU uploads',after[2]-before[2])
 # Alternating shader pairs reproduces scrolling's repeated program changes.
 bind(37,52);draw();bind(21,36);draw()
 before=metrics()
 for i in range(1000):
  v,f=(37,52) if i%2 else (21,36)
  bind(v,f);s.cgSetParameter4fv(C.c_void_p(101),tint(.4 if i%2 else .7))
  s.cgUpdateProgramParameters(C.c_void_p(v));s.cgUpdateProgramParameters(C.c_void_p(f));draw()
 after=metrics()
 if enabled:
  assert after[6]==before[6],(before,after)
  assert after[5]==before[5],(before,after)
  assert after[2]-before[2]<1100,(before,after)
 print('PASS1000 alternating pairs: original Cg binds',after[6]-before[6],'GPU uploads',after[2]-before[2])
 color=tint(.4);bind(21,36);draw()
 s.cgGLSetManageTextureParameters(C.c_void_p(1),1);draw();before=metrics();s.cgUpdateProgramParameters(C.c_void_p(21));draw();assert metrics()[5]==before[5]+1
 s.cgGLSetManageTextureParameters(C.c_void_p(1),0);draw()
 old_unit=s.cgGLGetTextureEnum(C.c_void_p(102));assert s.cgGLGetTextureEnum(C.c_void_p(102))==old_unit
 s.cgGLLoadProgram(C.c_void_p(21));assert s.cgGLGetTextureEnum(C.c_void_p(102))!=old_unit;before=metrics();s.cgUpdateProgramParameters(C.c_void_p(21));draw();assert metrics()[5]==before[5]+1
 # Mode transition invalidates cached values and immediate mode retains even
 # duplicate setters. Both must restore the intentionally clobbered GPU state.
 s.cgSetParameterSettingMode(C.c_void_p(1),4132);draw();before=metrics();s.cgUpdateProgramParameters(C.c_void_p(21));draw();assert metrics()[5]==before[5]+1
 before=metrics();s.cgSetParameter4fv(C.c_void_p(101),color);s.cgSetParameter4fv(C.c_void_p(101),color);draw();after=metrics();assert after[4]-before[4]==2
 s.cgGLDisableProfile(7007);s.cgGLEnableProfile(7007);draw()
 # Program destruction invalidates CPU snapshots; original Cg remains source.
 s.cgDestroyProgram(C.c_void_p(21));bind(37,52);draw();before=metrics();assert before[1]>m[1]
 for change in [lambda:bind(37,52),lambda:bind(21,36),lambda:s.cgGLLoadProgram(C.c_void_p(21)),lambda:s.cgGLEnableProfile(7007)]:change();draw()
 print('PASS changed values, redundant deferred setters, immediate mode, GPU clobbers, pair switches, frame boundaries and destruction')
