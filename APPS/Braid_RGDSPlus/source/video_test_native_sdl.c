#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
static unsigned flags,shows,fullscreen,raises,swaps;
static int major,minor,profile,current;
static void check(void* p){if(p!=(void*)0x12345678)abort();}
int SDL_GL_SetAttribute(unsigned a,int v){if(a==17)major=v;if(a==18)minor=v;if(a==21)profile=v;return 0;}
void* SDL_CreateWindow(const char* title,int x,int y,int w,int h,unsigned f){if((f&8)||!(f&4)||major!=2||minor!=0||profile!=4)abort();flags=f;return (void*)0x12345678;}
void* SDL_GL_CreateContext(void* w){check(w);current=1;return (void*)0x23456789;}
unsigned SDL_GetWindowFlags(void* w){check(w);return flags;}
void SDL_ShowWindow(void* w){check(w);shows++;flags=(flags&~8)|4;}
int SDL_SetWindowFullscreen(void* w,unsigned f){check(w);if(f!=0x1001)abort();fullscreen++;flags|=f;return 0;}
void SDL_RaiseWindow(void* w){check(w);raises++;}
void SDL_GL_GetDrawableSize(void* w,int* x,int* y){check(w);*x=640;*y=480;}
int SDL_GetWindowDisplayIndex(void* w){check(w);return 0;}
void SDL_GL_SwapWindow(void* w){check(w);if(shows!=1||fullscreen!=1||raises!=1||!(flags&4)||(flags&8))abort();if(++swaps==120)fprintf(stderr,"PASS: shown GLES2 window, explicit fullscreen/show/raise before swap, 120 swaps\n");}

void* SDL_GL_GetCurrentContext(void){return current?(void*)0x23456789:0;}
