from pathlib import Path
p=Path('braid-build/box64/src/wrapped32/wrappedsdl2_private.h');p.write_text(p.read_text().replace('GO(SDL_GL_SwapWindow, vFp)','GOM(SDL_GL_SwapWindow, vFEp)'))
p=Path('braid-build/box64/src/wrapped32/wrappedsdl2.c');s=p.read_text().replace('GO(SDL_GL_CreateContext, pFp_t)','GO(SDL_GL_CreateContext, pFp_t) \\\n    GO(SDL_GL_SwapWindow, vFp_t)');s=s.replace('typedef int (*iFui_t)', 'typedef void (*vFp_t)(void*);\ntypedef int (*iFui_t)',1)
s+='''
EXPORT void my32_2_SDL_GL_SwapWindow(x64emu_t* emu, void* win)
{
    static void (*flush)(void);
    static const unsigned char* (*getstring)(unsigned);
    static unsigned frames;
    if(getenv("BRAID_RGDS_GLES")) {
        if(!flush) {
            const char* path=getenv("BOX64_LIBGL");
            void* gl=dlopen(path?path:"libGL.so.1", RTLD_LAZY|RTLD_GLOBAL);
            if(gl) { flush=dlsym(gl,"glFlush"); getstring=dlsym(gl,"glGetString"); }
        }
        if(flush) flush();
        if(!frames && getstring) fprintf(stderr,"BRAID_RENDER: GL=%s renderer=%s\\n",getstring(0x1f02),getstring(0x1f01));
        ++frames;
        if(frames<=3 || frames==120 || frames%1800==0) fprintf(stderr,"BRAID_RENDER: presented frame %u\\n",frames);
    }
    my->SDL_GL_SwapWindow(win);
}
''';p.write_text(s)
