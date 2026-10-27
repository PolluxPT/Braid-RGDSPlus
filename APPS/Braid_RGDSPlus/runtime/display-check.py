#!/usr/bin/env python3
"""Native firmware SDL/GLES display check. Never writes backlight controls."""
import ctypes as C
import os
import time
from pathlib import Path

def backlights():
    for node in sorted(Path('/sys/class/backlight').glob('*')):
        values = {}
        for name in ('brightness', 'actual_brightness', 'max_brightness', 'bl_power'):
            try: values[name] = (node / name).read_text().strip()
            except OSError: pass
        print('BACKLIGHT:', node.name, values, flush=True)

def main():
    backlights()
    s = C.CDLL('libSDL2-2.0.so.0')
    def api(lib, name, ret, args):
        f = getattr(lib, name); f.restype = ret; f.argtypes = args; return f
    P=C.c_void_p; I=C.c_int; U=C.c_uint; F=C.c_float
    error = api(s,'SDL_GetError',C.c_char_p,[])
    init = api(s,'SDL_Init',I,[U]); quit_sdl = api(s,'SDL_Quit',None,[])
    assert init(0x20)==0, error()
    window=context=None
    try:
        count=api(s,'SDL_GetNumVideoDisplays',I,[])()
        name=api(s,'SDL_GetDisplayName',C.c_char_p,[I])
        print('NATIVE_DISPLAY: displays=',count,flush=True)
        for n in range(count): print('NATIVE_DISPLAY:',n,name(n),flush=True)
        attr=api(s,'SDL_GL_SetAttribute',I,[I,I])
        for key,value in ((17,2),(18,0),(21,4),(5,1)): assert attr(key,value)==0,error()
        window=api(s,'SDL_CreateWindow',P,[C.c_char_p,I,I,I,I,U])(b'Braid RGDS+ display check',0x2fff0000,0x2fff0000,640,480,0x1007)
        assert window,error()
        context=api(s,'SDL_GL_CreateContext',P,[P])(window)
        assert context,error()
        assert api(s,'SDL_GL_MakeCurrent',I,[P,P])(window,context)==0,error()
        api(s,'SDL_ShowWindow',None,[P])(window)
        api(s,'SDL_RaiseWindow',None,[P])(window)
        api(s,'SDL_GL_SetSwapInterval',I,[I])(1)
        size=api(s,'SDL_GL_GetDrawableSize',None,[P,P,P])
        swap=api(s,'SDL_GL_SwapWindow',None,[P])
        pump=api(s,'SDL_PumpEvents',None,[])
        w=I();h=I();size(window,C.byref(w),C.byref(h))
        assert w.value>0 and h.value>0
        print('NATIVE_DISPLAY: display=0 drawable=%dx%d colors=red,green,blue,white,magenta,cyan duration=5s'%(w.value,h.value),flush=True)
        g=C.CDLL(os.environ.get('LIBGL_GLES','/lib/libGLESv2.so.2'))
        enable=api(g,'glEnable',None,[U]);scissor=api(g,'glScissor',None,[I,I,I,I])
        color=api(g,'glClearColor',None,[F,F,F,F]);clear=api(g,'glClear',None,[U])
        read=api(g,'glReadPixels',None,[I,I,I,I,U,U,P])
        colors=((1,0,0),(0,1,0),(0,0,1),(1,1,1),(1,0,1),(0,1,1))
        enable(0x0c11)
        until=time.monotonic()+5;frames=0
        while time.monotonic()<until:
            pump();size(window,C.byref(w),C.byref(h))
            for n,rgb in enumerate(colors):
                x0=n*w.value//6;x1=(n+1)*w.value//6
                scissor(x0,0,x1-x0,h.value);color(*rgb,1);clear(0x4000)
            if frames==0:
                samples=[]
                for n in range(6):
                    pixel=(C.c_ubyte*4)();read((2*n+1)*w.value//12,h.value//2,1,1,0x1908,0x1401,pixel);samples.append(list(pixel))
                print('NATIVE_DISPLAY: framebuffer samples=',samples,flush=True)
            swap(window);frames+=1;time.sleep(0.01)
        print('NATIVE_DISPLAY: completed frames=',frames,flush=True)
    finally:
        if context: api(s,'SDL_GL_DeleteContext',None,[P])(context)
        if window: api(s,'SDL_DestroyWindow',None,[P])(window)
        quit_sdl();backlights()

if __name__=='__main__':
    try: main()
    except Exception as exc:
        print('NATIVE_DISPLAY: FAILED',repr(exc),flush=True)
        raise SystemExit(1)
