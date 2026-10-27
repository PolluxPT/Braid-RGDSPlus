#include <dlfcn.h>
const unsigned char *glGetString(unsigned n){return (const unsigned char*)(n==0x1f02?"2.1":n==0x8b8c?"1.20":n==0x1f03?"GL_ARB_shader_objects GL_ARB_vertex_shader GL_ARB_fragment_shader GL_ARB_vertex_program GL_ARB_fragment_program":"test");}
void glGetIntegerv(unsigned n,int *p){*p=16;}
unsigned glGetError(void){return 0;}
void *glXGetCurrentContext(void){return (void*)1;}
void *glXGetCurrentDisplay(void){return (void*)1;}
int glXQueryVersion(void*d,int*a,int*b){*a=1;*b=4;return 1;}
const char *glXQueryExtensionsString(void*d,int s){return "GLX_ARB_get_proc_address";}
void *glXGetProcAddressARB(const char *name){return dlsym(dlopen("libGL.so.1",2),name);}
void *glXGetProcAddress(const char *name){return glXGetProcAddressARB(name);}
