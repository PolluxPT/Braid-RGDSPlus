import ctypes as C, os, sys
from pathlib import Path
b=Path('build').resolve()
os.environ.update(EGL_PLATFORM='surfaceless',LIBGL_EGL='/lib/x86_64-linux-gnu/libEGL.so.1',LIBGL_GLES=str(b/'host/usr/lib/x86_64-linux-gnu/libGLESv2.so.2'),LIBGL_ES='2',LIBGL_GL='21',LIBGL_FB='0',LIBGL_LOGSHADERERROR='1')
e=C.CDLL('/lib/x86_64-linux-gnu/libEGL.so.1')
def api(lib,name,ret,args):f=getattr(lib,name);f.restype=ret;f.argtypes=args;return f
P=C.c_void_p;I=C.c_int;U=C.c_uint;F=C.c_float
getd=api(e,'eglGetDisplay',P,[P]);init=api(e,'eglInitialize',U,[P,P,P]);bind=api(e,'eglBindAPI',U,[U]);choose=api(e,'eglChooseConfig',U,[P,P,P,I,P]);surf=api(e,'eglCreatePbufferSurface',P,[P,P,P]);ctx=api(e,'eglCreateContext',P,[P,P,P,P]);make=api(e,'eglMakeCurrent',U,[P,P,P,P])
g=C.CDLL(str(b/'host-gl/libGL.so.1'))
d=getd(None);assert init(d,None,None);assert bind(0x30a0)
attrs=(I*13)(0x3024,8,0x3023,8,0x3022,8,0x3033,1,0x3040,4,0x3021,8,0x3038);config=P();num=I();assert choose(d,attrs,C.byref(config),1,C.byref(num)) and num.value
sa=(I*5)(0x3057,64,0x3056,64,0x3038);surface=surf(d,config,sa);ca=(I*3)(0x3098,2,0x3038);context=ctx(d,config,None,ca);assert surface and context
# GL4ES is loaded before an application context is current, as on RGDS+.
get=api(g,'glGetIntegerv',None,[U,P]);vp=(I*4)();get(0xba2,vp);before=list(vp)
assert make(d,surface,surface,context)
baseline='--baseline' in sys.argv
if not baseline:api(g,'gl4es_rgds_attach_context',None,[])()
get(0xba2,vp);after=list(vp);print('VIEWPORT before attach',before,'after attach',after,flush=True);assert after==([0,0,0,0] if baseline else [0,0,64,64])
get(0xc10,vp);assert list(vp)==([0,0,0,0] if baseline else [0,0,64,64])
if not baseline:
 api(g,'gl4es_rgds_resize_default',None,[I,I])(128,128);get(0xc10,vp);assert list(vp)==[0,0,128,128]
# Render through GL4ES ARB-program conversion into a real Mesa GLES2 context.
gen=api(g,'glGenProgramsARB',None,[I,P]);bindp=api(g,'glBindProgramARB',None,[U,U]);prog=api(g,'glProgramStringARB',None,[U,U,I,P]);enable=api(g,'glEnable',None,[U]);err=api(g,'glGetError',U,[])
create=api(g,'glCreateShader',U,[U]);setsource=api(g,'glShaderSource',None,[U,I,P,P]);compile_shader=api(g,'glCompileShader',None,[U]);getshader=api(g,'glGetShaderiv',None,[U,U,P]);getlog=api(g,'glGetShaderInfoLog',None,[U,I,P,P])
program=api(g,'glCreateProgram',U,[])();attach=api(g,'glAttachShader',None,[U,U])
for kind,path in [(0x8b31,'build/glsl.vp'),(0x8b30,'build/glsl.fp')]:
 sh=create(kind);source=C.c_char_p(Path(path).read_bytes());setsource(sh,1,C.byref(source),None);compile_shader(sh);status=I();getshader(sh,0x8b81,C.byref(status));log=C.create_string_buffer(8192);getlog(sh,8192,None,log);assert status.value,log.value;attach(program,sh)
api(g,'glLinkProgram',None,[U])(program);status=I();api(g,'glGetProgramiv',None,[U,U,P])(program,0x8b82,C.byref(status));assert status.value
api(g,'glUseProgram',None,[U])(program)
location=api(g,'glGetUniformLocation',I,[U,C.c_char_p]);setfv=api(g,'glUniform4fv',None,[I,I,P])
matrix=(F*16)(1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1);setfv(location(program,b'_object_to_proj_matrix[0]'),4,matrix)
zero=(F*4)(0,0,0,0);setfv(location(program,b'_global_color_add'),1,zero);api(g,'glUniform1i',None,[I,I])(location(program,b'_diffuse_texture'),0)
tex=U();api(g,'glGenTextures',None,[I,P])(1,C.byref(tex));api(g,'glBindTexture',None,[U,U])(0xde1,tex.value)
api(g,'glTexParameteri',None,[U,U,I])(0xde1,0x2801,0x2600);api(g,'glTexParameteri',None,[U,U,I])(0xde1,0x2800,0x2600)
white=(C.c_ubyte*4)(255,255,255,255);api(g,'glTexImage2D',None,[U,I,I,I,I,I,U,U,P])(0xde1,0,0x1908,1,1,0,0x1908,0x1401,white)
assert err()==0
api(g,'glViewport',None,[I,I,I,I])(0,0,64,64);api(g,'glPushAttrib',None,[U])(0x80000);api(g,'glScissor',None,[I,I,I,I])(0,0,64,64);api(g,'glPopAttrib',None,[])();enable(0xc11)
api(g,'glClearColor',None,[F,F,F,F])(0,0,0,1);api(g,'glClear',None,[U])(0x4000)
api(g,'glColor4f',None,[F,F,F,F])(1,0,0,1);api(g,'glBegin',None,[U])(7);vertex=api(g,'glVertex3f',None,[F,F,F])
for x,y in [(-1,-1),(1,-1),(1,1),(-1,1)]:vertex(x,y,0)
api(g,'glEnd',None,[])();api(g,'glFinish',None,[])()
pixel=(C.c_ubyte*4)();api(g,'glReadPixels',None,[I,I,I,I,U,U,P])(32,32,1,1,0x1908,0x1401,pixel);print('REAL GLES2 ARB pixel',list(pixel),'error',hex(err()),flush=True);assert (pixel[0]==pixel[1]==pixel[2]==0) if baseline else (pixel[0]>200 and pixel[1]<10 and pixel[2]<10)
print('PASS: reproduced black output without context attach' if baseline else 'PASS: actual supplied Cg-generated GLSL Braid shader renders red through GL4ES/GLES2',flush=True)

# Test process owns intentionally mismatched baseline state; omit library destructors.
os._exit(0)
