#include <stdio.h>
void glFlush(void){}
const unsigned char* glGetString(unsigned n){return (const unsigned char*)(n==0x1f02?"2.1 test":"test renderer");}
unsigned glGetError(void){return 0;}
void glReadPixels(int x,int y,int w,int h,unsigned fmt,unsigned type,void* p){unsigned char* b=p;b[0]=16;b[1]=32;b[2]=48;b[3]=255;}
void glGetIntegerv(unsigned n,int* p){if(n==0x0ba2){p[0]=p[1]=0;p[2]=640;p[3]=480;}else *p=0;}

#include <dlfcn.h>
#include <stdlib.h>
void gl4es_rgds_attach_context(void){void* s=dlopen("libSDL2-2.0.so.0",2);void*(*current)(void)=s?dlsym(s,"SDL_GL_GetCurrentContext"):0;if(!current||!current())abort();fprintf(stderr,"PASS: GL4ES attach called after SDL context is current\n");}
void gl4es_rgds_resize_default(int w,int h){if(w!=640||h!=480)abort();}
