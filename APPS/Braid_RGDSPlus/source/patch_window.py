from pathlib import Path
p=Path('braid-build/box64/src/wrapped32/wrappedsdl2_private.h');p.write_text(p.read_text().replace('GO(SDL_CreateWindow, pFpiiiiu)','GOM(SDL_CreateWindow, pFEpiiiiu)'))
p=Path('braid-build/box64/src/wrapped32/wrappedsdl2.c');s=p.read_text();s+='''
EXPORT void* my32_2_SDL_CreateWindow(x64emu_t* emu, void* title, int x, int y, int w, int h, unsigned flags)
{
    if(getenv("BRAID_RGDS_GLES")) {
        my->SDL_GL_SetAttribute(17,2);
        my->SDL_GL_SetAttribute(18,0);
        my->SDL_GL_SetAttribute(21,4);
    }
    void* win=my->SDL_CreateWindow(title,x,y,w,h,flags);
    if(getenv("BRAID_RGDS_GLES")) fprintf(stderr,"BRAID_VIDEO: window %dx%d flags=%x result=%p\\n",w,h,flags,win);
    return win;
}
''';p.write_text(s)
