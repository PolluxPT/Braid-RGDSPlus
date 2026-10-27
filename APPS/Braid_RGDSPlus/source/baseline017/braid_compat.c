/* SPDX-License-Identifier: MIT; port code, see ../LICENSE.
 * SDL-related declarations/data remain under SDL zlib terms; ../licenses/sdl2.txt. */
/* GLEW GLX queries on a Wayland/EGL context.
   All rendering entrypoints come from GL4ES via Box32's wrapped libGL.
   SDL's native EGL resolver can expose raw GLES functions and MUST NOT be
   mixed with the desktop GL4ES functions imported by the game executable. */
extern void *dlopen(const char *,int);
extern void *dlsym(void *,const char *);
extern int fprintf(void *,const char *,...);
extern void *stderr;
extern void _exit(int) __attribute__((noreturn));
static unsigned char display_cookie;
static int same(const char *a,const char *b) {while(*a && *a==*b){++a;++b;}return *a==*b;}
void *glXGetCurrentContext(void) {
 static void *(*current)(void);
 if(!current) { void *s=dlopen("libSDL2-2.0.so.0",2); if(s)current=dlsym(s,"SDL_GL_GetCurrentContext"); }
 return current?current():(void *)0;
}
void *glXGetCurrentDisplay(void) {return &display_cookie;}
int glXQueryVersion(void *d,int *major,int *minor) {
 (void)d;if(major)*major=1;if(minor)*minor=4;return 1;
}
const char *glXGetClientString(void *d,int name) {
 (void)d;return name==1?"RGDS GL4ES":name==2?"1.4":name==3?"GLX_ARB_get_proc_address":"";
}
const char *glXQueryServerString(void *d,int screen,int name) {(void)screen;return glXGetClientString(d,name);}
const char *glXQueryExtensionsString(void *d,int screen) {(void)d;(void)screen;return "GLX_ARB_get_proc_address";}
void *glXGetProcAddressARB(const unsigned char *symbol) {
 static void *(*getproc)(const unsigned char *);
 static void *gl;
 static int attempted;
 const char *name=(const char *)symbol;
 void *result;
 if(!name)return (void *)0;
#define OWN(fn) if(same(name,#fn))return (void *)fn
 OWN(glXGetCurrentContext);OWN(glXGetCurrentDisplay);OWN(glXQueryVersion);OWN(glXGetClientString);
 OWN(glXQueryServerString);OWN(glXQueryExtensionsString);OWN(glXGetProcAddressARB);
#undef OWN
 if(!attempted) {
  attempted=1;gl=dlopen("libGL.so.1",2);
  if(gl)getproc=dlsym(gl,"glXGetProcAddressARB");
  if((void *)getproc==(void *)glXGetProcAddressARB)getproc=(void *)0;
  if(!getproc)getproc=dlsym((void *)-1,"glXGetProcAddressARB");
  if((void *)getproc==(void *)glXGetProcAddressARB)getproc=(void *)0;
  fprintf(stderr,"BRAID_GLX v0.1: GL4ES resolver %s\n",getproc?"available":"MISSING");
  if(!getproc)_exit(78);
 }
 result=getproc(symbol);
 if(!result && gl)result=dlsym(gl,name);
 if(same(name,"glGetTexLevelParameteriv") || same(name,"glShaderSource") ||
    same(name,"glCreateShader") || same(name,"glBindFramebuffer"))
  fprintf(stderr,"BRAID_GLX: GL4ES %s -> %p\n",name,result);
 return result;
}
void *glXGetProcAddress(const unsigned char *name) {return glXGetProcAddressARB(name);}

/* i386 glibc FILE identity for Cg; Box32 maps this exported object's address
 * to the host stdout stream through its existing FILE wrapper. */
unsigned char _IO_2_1_stdout_[152];

/* Cg programs stay emulated i386. Log compiler selection/results without
 * consuming cgGetError, so the game's own error handling is preserved. */
void *cgCreateProgram(void *context,int kind,const char *source,int profile,const char *entry,const char **args) {
 static void *(*create)(void*,int,const char*,int,const char*,const char**);
 static const char *(*profile_name)(int);
 static const char *(*listing)(void*);
 static unsigned calls;
 if(!create) {
  void *cg=dlopen("libCg.so",2);
  if(cg){create=dlsym(cg,"cgCreateProgram");profile_name=dlsym(cg,"cgGetProfileString");listing=dlsym(cg,"cgGetLastListing");}
  if(!create || (void*)create==(void*)cgCreateProgram){fprintf(stderr,"BRAID_CG: compiler resolver failed\n");_exit(78);}
 }
 void *program=create(context,kind,source,profile,entry,args);
 ++calls;
 if(calls<=12 || !program) fprintf(stderr,"BRAID_CG: compile %u profile=%s(%d) entry=%s result=%p\n",calls,profile_name?profile_name(profile):"unknown",profile,entry?entry:"main",program);
 if(!program && listing){const char *s=listing(context);if(s)fprintf(stderr,"BRAID_CG: compiler listing: %s\n",s);}
 return program;
}

/* v0.1.5: bounded diagnostics at the game's actual CgGL and draw calls.
 * Never consume glGetError/cgGetError or override the game's render state. */
static void *resolve_required(const char *library,const char *name) {
 void *h=dlopen(library,2); void *p=h?dlsym(h,name):(void*)0;
 if(!p){fprintf(stderr,"BRAID_TRACE: missing %s in %s\n",name,library);_exit(78);}
 return p;
}
static void cg_status(const char *action,void *program) {
 static int (*loaded)(void*);static unsigned (*id)(void*);static unsigned reports;
 if(!loaded)loaded=resolve_required("libCgGL.so","cgGLIsProgramLoaded");
 if(!id)id=resolve_required("libCgGL.so","cgGLGetProgramID");
 if(++reports<=32){int ok=loaded(program);fprintf(stderr,"BRAID_CGGL: %s program=%p loaded=%d id=%u\n",action,program,ok,ok?id(program):0);}
}
void cgGLLoadProgram(void *program) {
 static void (*real)(void*);if(!real)real=resolve_required("libCgGL.so","cgGLLoadProgram");
 real(program);cg_status("load",program);
}
static void *bound_cg_vertex,*bound_cg_fragment;
void cgGLBindProgram(void *program) {
 static int (*profile)(void*);
 if(!profile)profile=resolve_required("libCg.so","cgGetProgramProfile");
 int p=profile(program);if(p==7007)bound_cg_vertex=program;else if(p==7008)bound_cg_fragment=program;
 static void (*real)(void*);if(!real)real=resolve_required("libCgGL.so","cgGLBindProgram");
 real(program);cg_status("bind",program);
}
#include "cg_glsl_pair.h"
#include "cg_uniform_bridge.h"
static unsigned draw_calls;
static void draw_state(const char *kind,int count) {
 static void (*get)(unsigned,int*);static unsigned char (*enabled)(unsigned);
 static void (*getprogram)(unsigned,unsigned,int*);
 unsigned n=++draw_calls;
 if(n>12 && n!=120 && n!=600 && n%10000)return;
 if(!get)get=resolve_required("libGL.so.1","glGetIntegerv");
 if(!enabled)enabled=resolve_required("libGL.so.1","glIsEnabled");
 if(!getprogram)getprogram=resolve_required("libGL.so.1","glGetProgramivARB");
 int vp[4]={0},clip[4]={0},mask[4]={0},fbo=0,texture=0,vlen=0,flen=0,vbind=0,fbind=0,glsl=0;
 get(0x0ba2,vp);get(0x0c10,clip);get(0x0c23,mask);get(0x8ca6,&fbo);get(0x8069,&texture);
 get(0x8b8d,&glsl);
 if(!glsl){getprogram(0x8620,0x8627,&vlen);getprogram(0x8804,0x8627,&flen);
 getprogram(0x8620,0x8677,&vbind);getprogram(0x8804,0x8677,&fbind);}
 fprintf(stderr,"BRAID_DRAW: n=%u kind=%s count=%d viewport=%d,%d,%d,%d scissor=%d:%d,%d,%d,%d mask=%d%d%d%d depth=%d blend=%d fbo=%d texture=%d glsl=%d vertex=%d:%d/%d fragment=%d:%d/%d\n",
 n,kind,count,vp[0],vp[1],vp[2],vp[3],enabled(0x0c11),clip[0],clip[1],clip[2],clip[3],mask[0],mask[1],mask[2],mask[3],enabled(0x0b71),enabled(0x0be2),fbo,texture,glsl,enabled(0x8620),vbind,vlen,enabled(0x8804),fbind,flen);
}
void glDrawArrays(unsigned mode,int first,int count) {
 static void (*real)(unsigned,int,int);if(!real)real=resolve_required("libGL.so.1","glDrawArrays");
 sync_cg_uniforms();draw_state("arrays",count);real(mode,first,count);
}
void glDrawElements(unsigned mode,int count,unsigned type,const void *indices) {
 static void (*real)(unsigned,int,unsigned,const void*);if(!real)real=resolve_required("libGL.so.1","glDrawElements");
 sync_cg_uniforms();draw_state("elements",count);real(mode,count,type,indices);
}
void glBegin(unsigned mode) {
 static void (*real)(unsigned);if(!real)real=resolve_required("libGL.so.1","glBegin");
 sync_cg_uniforms();draw_state("immediate",-1);real(mode);
}
