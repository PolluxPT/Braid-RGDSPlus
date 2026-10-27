from pathlib import Path
p=Path('braid-build/box64/src/wrapped32/wrappedsdl2.c');s=p.read_text();start=s.index('EXPORT void my32_2_SDL_GL_SwapWindow(');end=s.index('EXPORT void* my32_2_SDL_CreateWindow(',start)
s=s[:start]+'''/* RGDS+ Wayland presentation: map/raise the window explicitly and request
 * compositor fullscreen without requiring a desktop display-mode switch. */
EXPORT void my32_2_SDL_GL_SwapWindow(x64emu_t* emu, void* win)
{
    static void (*flush)(void);
    static const unsigned char* (*getstring)(unsigned);
    static unsigned (*geterror)(void);
    static void (*readpixels)(int,int,int,int,unsigned,unsigned,void*);
    static void (*getinteger)(unsigned,int*);
    static unsigned frames;
    if(getenv("BRAID_RGDS_GLES")) {
        if(!frames) {
            unsigned before=my->SDL_GetWindowFlags(win);
            my->SDL_ShowWindow(win);
            int rc=my->SDL_SetWindowFullscreen(win,0x1001);
            my->SDL_RaiseWindow(win);
            int w=0,h=0;my->SDL_GL_GetDrawableSize(win,&w,&h);
            fprintf(stderr,"BRAID_VIDEO: force-show fullscreen=%d flags=%x->%x display=%d drawable=%dx%d\\n",rc,before,my->SDL_GetWindowFlags(win),my->SDL_GetWindowDisplayIndex(win),w,h);
            const char* path=getenv("BOX64_LIBGL");
            void* gl=dlopen(path?path:"libGL.so.1",RTLD_LAZY|RTLD_GLOBAL);
            if(gl) {
                flush=dlsym(gl,"glFlush");getstring=dlsym(gl,"glGetString");
                geterror=dlsym(gl,"glGetError");readpixels=dlsym(gl,"glReadPixels");
                getinteger=dlsym(gl,"glGetIntegerv");
            }
        }
        if(flush) flush();
        if(!frames && getstring) fprintf(stderr,"BRAID_RENDER: GL=%s renderer=%s\\n",getstring(0x1f02),getstring(0x1f01));
        ++frames;
        if(frames<=3 || frames==120 || frames%1800==0) {
            fprintf(stderr,"BRAID_RENDER: presented frame %u\\n",frames);
            int w=0,h=0;my->SDL_GL_GetDrawableSize(win,&w,&h);
            unsigned error_before=geterror?geterror():0;
            unsigned nonblack=0,maxrgb=0;
            if(readpixels && w>0 && h>0) for(int y=1;y<=3;y++) for(int x=1;x<=3;x++) {
                unsigned char rgba[4]={0,0,0,0};
                readpixels(w*x/4,h*y/4,1,1,0x1908,0x1401,rgba);
                if(rgba[0]||rgba[1]||rgba[2]) ++nonblack;
                for(int i=0;i<3;i++) if(rgba[i]>maxrgb) maxrgb=rgba[i];
            }
            int viewport[4]={0},fbo=0,program=0;
            if(getinteger) {getinteger(0x0ba2,viewport);getinteger(0x8ca6,&fbo);getinteger(0x8b8d,&program);}
            fprintf(stderr,"BRAID_PIXELS: frame=%u flags=%x drawable=%dx%d viewport=%d,%d,%d,%d fbo=%d program=%d nonblack=%u/9 maxrgb=%u gl_error=%x/%x\\n",frames,my->SDL_GetWindowFlags(win),w,h,viewport[0],viewport[1],viewport[2],viewport[3],fbo,program,nonblack,maxrgb,error_before,geterror?geterror():0);
        }
    }
    my->SDL_GL_SwapWindow(win);
}

'''+s[end:]
old='''        my->SDL_GL_SetAttribute(21,4);
    }
    void* win=my->SDL_CreateWindow(title,x,y,w,h,flags);'''
new='''        my->SDL_GL_SetAttribute(21,4);
        flags=(flags&~8u)|4u; /* SDL_WINDOW_HIDDEN -> SDL_WINDOW_SHOWN */
    }
    void* win=my->SDL_CreateWindow(title,x,y,w,h,flags);'''
assert old in s;s=s.replace(old,new,1);p.write_text(s)
