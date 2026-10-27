#include <stdio.h>
extern void* SDL_CreateWindow(const char*,int,int,int,int,unsigned);
extern void* SDL_GL_CreateContext(void*);
extern void SDL_GL_SwapWindow(void*);
int main(void){void*w=SDL_CreateWindow("Braid test",0,0,640,480,0xa);if(!w||!SDL_GL_CreateContext(w))return 1;for(int i=0;i<120;i++)SDL_GL_SwapWindow(w);puts("PASS: i386 presentation fixture");return 0;}
