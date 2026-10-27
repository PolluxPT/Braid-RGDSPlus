from pathlib import Path
p=Path('braid-build/box64/src/wrapped32/wrappedsdl2_private.h');s=p.read_text().replace('GO(SDL_GL_SetAttribute, iFui)','GOM(SDL_GL_SetAttribute, iFEui)').replace('GO(SDL_GL_CreateContext, pFp)','GOM(SDL_GL_CreateContext, pFEp)');p.write_text(s)
p=Path('braid-build/box64/src/wrapped32/wrappedsdl2.c');s=p.read_text().replace('GO(SDL_FreeRW, sdl2_freerw)','GO(SDL_FreeRW, sdl2_freerw) \\\n    GO(SDL_GL_SetAttribute, iFui_t) \\\n    GO(SDL_GL_CreateContext, pFp_t)')
s=s.replace('typedef void (*vFiupV_t)', 'typedef int (*iFui_t)(unsigned, int);\ntypedef void* (*pFp_t)(void*);\ntypedef void (*vFiupV_t)',1)
pos=s.index('EXPORT void* my32_2_SDL_GL_GetProcAddress')
s=s[:pos]+'''/* RGDS+ Braid: SDL owns a native GLES2 Wayland context; GL4ES translates desktop calls. */
EXPORT int my32_2_SDL_GL_SetAttribute(x64emu_t* emu, unsigned attr, int value)
{
    if(getenv("BRAID_RGDS_GLES")) {
        if(attr==17) value=2;
        if(attr==18) value=0;
        if(attr==21) value=4;
    }
    return my->SDL_GL_SetAttribute(attr, value);
}
EXPORT void* my32_2_SDL_GL_CreateContext(x64emu_t* emu, void* win)
{
    if(getenv("BRAID_RGDS_GLES")) {
        my->SDL_GL_SetAttribute(17,2);
        my->SDL_GL_SetAttribute(18,0);
        my->SDL_GL_SetAttribute(21,4);
    }
    return my->SDL_GL_CreateContext(win);
}

'''+s[pos:]
s=s.replace('return getGLProcAddress32(emu, NULL, (glprocaddress_t)my->SDL_GL_GetProcAddress, rname);','''if(getenv("BRAID_RGDS_GLES")) {
        static void* gl;
        static glprocaddress_t proc;
        if(!gl) { const char* path=getenv("BOX64_LIBGL"); gl=dlopen(path?path:"libGL.so.1", RTLD_LAZY|RTLD_GLOBAL); }
        if(gl && !proc) proc=(glprocaddress_t)dlsym(gl,"glXGetProcAddress");
        if(proc) return getGLProcAddress32(emu, NULL, proc, rname);
    }
    return getGLProcAddress32(emu, NULL, (glprocaddress_t)my->SDL_GL_GetProcAddress, rname);''')
p.write_text(s)
