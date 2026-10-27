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
static void flush_pending_values(void);
static void invalidate_lookup(void *program);
static void lookup_compilation_begin(void);
static void lookup_compilation_end(void *program);
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
 flush_pending_values();lookup_compilation_begin();
 void *program=create(context,kind,source,profile,entry,args);
 lookup_compilation_end(program);
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
#include "cg_lookup_cache.h"
static unsigned long long braid_cg_epoch=1,braid_sampler_epoch=1,braid_gpu_epoch=1;
static unsigned long long braid_commits_skipped,braid_binds_skipped,braid_uploads_skipped,braid_profiles_skipped;
static int enabled_glsl_profiles[2],braid_cg_bindings_deferred;
static void *last_real_vertex,*last_real_fragment;
static int direct_pair_ready(void);
static int known_cg_stage(void *program);
static unsigned long long braid_draws,braid_uniform_reuses,braid_uniform_reads,braid_uniform_uploads,braid_glsl_binds;
static void dirty_cg_state(void){++braid_cg_epoch;}
#include "cg_value_cache.h"
static void cg_status(const char *action,void *program) {
 static int (*loaded)(void*);static unsigned (*id)(void*);static unsigned reports;
 if(!loaded)loaded=resolve_required("libCgGL.so","cgGLIsProgramLoaded");
 if(!id)id=resolve_required("libCgGL.so","cgGLGetProgramID");
 if(++reports<=32){int ok=loaded(program);fprintf(stderr,"BRAID_CGGL: %s program=%p loaded=%d id=%u\n",action,program,ok,ok?id(program):0);}
}
void cgGLLoadProgram(void *program) {
 static void (*real)(void*);if(!real)real=resolve_required("libCgGL.so","cgGLLoadProgram");
 flush_pending_values();lookup_compilation_begin();real(program);lookup_compilation_end(program);++braid_sampler_epoch;++braid_gpu_epoch;last_real_vertex=last_real_fragment=NULL;enabled_glsl_profiles[0]=enabled_glsl_profiles[1]=0;dirty_cg_state();cg_status("load",program);
}
static void *bound_cg_vertex,*bound_cg_fragment;
/* Restore CgGL bookkeeping before entering an unverified/fallback pair.
 * Ready pairs render through our own linked GL programs. */
static void restore_cg_stage(int stage,void *program){
 void **last=stage?&last_real_fragment:&last_real_vertex;
 if(!braid_cg_bindings_deferred||!program||!enabled_glsl_profiles[stage]||*last==program)return;
 static void(*bind)(void*);if(!bind)bind=resolve_required("libCgGL.so","cgGLBindProgram");
 flush_pending_values();bind(program);*last=program;++braid_gpu_epoch;dirty_cg_state();
}
void cgGLBindProgram(void *program) {
 int p=cgGetProgramProfile(program);
 int changed=p==7007?bound_cg_vertex!=program:p==7008?bound_cg_fragment!=program:0;
 if(p==7007)bound_cg_vertex=program;else if(p==7008)bound_cg_fragment=program;
 static void (*real)(void*);if(!real)real=resolve_required("libCgGL.so","cgGLBindProgram");
 if((p==7007||p==7008)&&known_cg_stage(program)){
  ++braid_binds_skipped;
  if(changed){braid_cg_bindings_deferred=1;dirty_cg_state();}return;
 }
 if(direct_bridge_enabled()){
  if(p==7007)restore_cg_stage(1,bound_cg_fragment);
  else if(p==7008)restore_cg_stage(0,bound_cg_vertex);
 }
 flush_pending_values();real(program);++braid_gpu_epoch;
 if(p==7007)last_real_vertex=program;else if(p==7008)last_real_fragment=program;
 if(last_real_vertex==bound_cg_vertex&&last_real_fragment==bound_cg_fragment)braid_cg_bindings_deferred=0;
 dirty_cg_state();cg_status("bind",program);
}
#include "cg_glsl_pair.h"
#include "cg_uniform_bridge.h"
static int direct_pair_ready(void){
 if(!direct_bridge_enabled())return 0;
 braid_uniform_pair *pair=find_uniform_pair();
 return pair&&pair->ready&&pair->resource_epoch==braid_sampler_epoch&&direct_context(pair->contexts[0])&&direct_context(pair->contexts[1]);
}

static int known_cg_stage(void *program){
 if(!direct_bridge_enabled())return 0;
 unsigned bucket=((unsigned long)program>>2)&255;
 braid_uniform_pair *q=stage_index[bucket];
 if(q&&q->ready&&q->resource_epoch==braid_sampler_epoch&&(q->vertex==program||q->fragment==program)&&direct_context(q->contexts[0])&&direct_context(q->contexts[1]))return 1;
 for(q=uniform_pairs;q;q=q->next)
  if(q->ready&&q->resource_epoch==braid_sampler_epoch&&(q->vertex==program||q->fragment==program)&&direct_context(q->contexts[0])&&direct_context(q->contexts[1])){stage_index[bucket]=q;return 1;}
 return 0;
}

static unsigned draw_calls;
static void draw_state(const char *kind,int count) {
 static int trace=-1;if(trace<0){const char *v=getenv("BRAID_TRACE_RENDER");trace=v&&v[0]=='1';}if(!trace)return;
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

/* Changing setters dirty the CPU snapshot. Verified deferred uniforms may use
 * the write buffer; original SDK calls remain the fallback and are preceded
 * by a flush wherever CgGL or an explicit readback needs current values. */
void cgSetMatrixParameterfr(void *p,const float *v){
 static void(*real)(void*,const float*);if(!real)real=resolve_required("libCg.so","cgSetMatrixParameterfr");
 braid_value *cached=setter_value(p,16,1);if(redundant_value(cached,v))return;
 if(defer_value(cached,v)){dirty_cg_state();return;}
 flush_conflicting_value(p);
 if(!deferred_parameter(p))++braid_gpu_epoch;
 real(p,v);changed_value(p,cached,v);dirty_cg_state();
}
void cgSetParameter2fv(void *p,const float *v){
 static void(*real)(void*,const float*);if(!real)real=resolve_required("libCg.so","cgSetParameter2fv");
 braid_value *cached=setter_value(p,2,0);if(redundant_value(cached,v))return;
 if(defer_value(cached,v)){dirty_cg_state();return;}
 flush_conflicting_value(p);
 if(!deferred_parameter(p))++braid_gpu_epoch;
 real(p,v);changed_value(p,cached,v);dirty_cg_state();
}
void cgSetParameter4fv(void *p,const float *v){
 static void(*real)(void*,const float*);if(!real)real=resolve_required("libCg.so","cgSetParameter4fv");
 braid_value *cached=setter_value(p,4,0);if(redundant_value(cached,v))return;
 if(defer_value(cached,v)){dirty_cg_state();return;}
 flush_conflicting_value(p);
 if(!deferred_parameter(p))++braid_gpu_epoch;
 real(p,v);changed_value(p,cached,v);dirty_cg_state();
}
void cgUpdateProgramParameters(void *p){
 static void(*real)(void*);if(!real)real=resolve_required("libCg.so","cgUpdateProgramParameters");
 if((p==bound_cg_vertex||p==bound_cg_fragment)&&direct_pair_ready()){++braid_commits_skipped;return;}
 if(direct_bridge_enabled()){restore_cg_stage(0,bound_cg_vertex);restore_cg_stage(1,bound_cg_fragment);}
 flush_pending_values();real(p);++braid_gpu_epoch;dirty_cg_state();
}
void cgSetParameterSettingMode(void *p,int mode){
 static void(*real)(void*,int);if(!real)real=resolve_required("libCg.so","cgSetParameterSettingMode");flush_pending_values();real(p,mode);++braid_gpu_epoch;value_mode(p,mode);dirty_cg_state();
}
void cgGLEnableProfile(int profile){
 static void(*real)(int);if(!real)real=resolve_required("libCgGL.so","cgGLEnableProfile");int stage=profile==7007?0:profile==7008?1:-1;
 if(stage>=0&&enabled_glsl_profiles[stage]&&known_cg_stage(bound_cg_vertex)&&known_cg_stage(bound_cg_fragment)){++braid_profiles_skipped;return;}
 flush_pending_values();real(profile);if(stage>=0)enabled_glsl_profiles[stage]=1;
 ++braid_gpu_epoch;last_real_vertex=last_real_fragment=NULL;dirty_cg_state();
}
static unsigned braid_draw_fbo,braid_scene_w,braid_scene_h;
void glBindFramebufferEXT(unsigned target,unsigned framebuffer){
 static void(*real)(unsigned,unsigned);if(!real)real=resolve_required("libGL.so.1","glBindFramebufferEXT");
 real(target,framebuffer);if(target==0x8d40||target==0x8ca9)braid_draw_fbo=framebuffer;
}
void glViewport(int x,int y,int w,int h){
 static void(*real)(int,int,int,int);if(!real)real=resolve_required("libGL.so.1","glViewport");
 real(x,y,w,h);
 if(braid_draw_fbo&&w>0&&h>0&&(unsigned long long)w*h>(unsigned long long)braid_scene_w*braid_scene_h){braid_scene_w=w;braid_scene_h=h;}
}
void SDL_GL_SwapWindow(void *window){
 static void(*swap)(void*);static unsigned(*ticks)(void);
 static unsigned start,frames,last_end;static int started;
 static unsigned long long between_ms,swap_ms;static unsigned max_swap_ms;
 if(!swap){swap=resolve_required("libSDL2-2.0.so.0","SDL_GL_SwapWindow");ticks=resolve_required("libSDL2-2.0.so.0","SDL_GetTicks");}
 unsigned entered=ticks();
 if(!started){start=entered;last_end=entered;started=1;}
 between_ms+=(unsigned)(entered-last_end);
 swap(window);last_glsl_program=0;++frames;dirty_cg_state();
 unsigned now=ticks(),wait=(unsigned)(now-entered),elapsed=(unsigned)(now-start);
 swap_ms+=wait;if(wait>max_swap_ms)max_swap_ms=wait;last_end=now;
 if(elapsed>=5000){
  fprintf(stderr,"BRAID_PERF: fps=%.2f frames=%u elapsed_ms=%u draws=%llu cached_draws=%llu parameter_reads=%llu uniform_uploads=%llu shader_binds=%llu between_avg_ms=%.2f swap_avg_ms=%.2f swap_max_ms=%u scene_max=%ux%u value_hits=%llu setters_skipped=%llu sampler_reads=%llu sampler_hits=%llu commits_skipped=%llu binds_skipped=%llu uploads_skipped=%llu profiles_skipped=%llu lookup_hits=%llu lookup_reads=%llu profile_hits=%llu profile_reads=%llu negative_hits=%llu revision_hits=%llu name_fast_hits=%llu writes_deferred=%llu writes_flushed=%llu\n",1000.0*frames/elapsed,frames,elapsed,braid_draws,braid_uniform_reuses,braid_uniform_reads,braid_uniform_uploads,braid_glsl_binds,(double)between_ms/frames,(double)swap_ms/frames,max_swap_ms,braid_scene_w,braid_scene_h,braid_value_hits,braid_setters_skipped,braid_sampler_reads,braid_sampler_hits,braid_commits_skipped,braid_binds_skipped,braid_uploads_skipped,braid_profiles_skipped,braid_lookup_hits,braid_lookup_reads,braid_profile_hits,braid_profile_reads,braid_negative_hits,braid_revision_hits,braid_name_fast_hits,braid_writes_deferred,braid_writes_flushed);
  start=now;frames=0;between_ms=swap_ms=0;max_swap_ms=0;braid_scene_w=braid_scene_h=0;
 }
}

/* Parameter handles can be reused after program destruction. */
void cgDestroyProgram(void *p){
 static void(*real)(void*);if(!real)real=resolve_required("libCg.so","cgDestroyProgram");
 flush_pending_values();lookup_compilation_begin();real(p);lookup_compilation_end(p);
 for(braid_uniform_pair*q=uniform_pairs;q;q=q->next)if(q->vertex==p||q->fragment==p){q->vertex=q->fragment=NULL;q->ready=0;}
 for(braid_glsl_pair*q=glsl_pairs;q;q=q->next)if(q->vertex==p||q->fragment==p)q->vertex=q->fragment=NULL;
 clear_pair_indexes();last_uniform_pair=NULL;last_glsl_pair=NULL;last_glsl_program=0;
 if(bound_cg_vertex==p)bound_cg_vertex=NULL;
 if(bound_cg_fragment==p)bound_cg_fragment=NULL;
 invalidate_values();++braid_sampler_epoch;++braid_gpu_epoch;last_real_vertex=last_real_fragment=NULL;dirty_cg_state();
}

void cgGLSetManageTextureParameters(void *context,int managed){
 static void(*real)(void*,int);if(!real)real=resolve_required("libCgGL.so","cgGLSetManageTextureParameters");
 flush_pending_values();real(context,managed);value_manage_textures(context,managed);++braid_gpu_epoch;dirty_cg_state();
}

void cgGLDisableProfile(int profile){
 static void(*real)(int);if(!real)real=resolve_required("libCgGL.so","cgGLDisableProfile");
 flush_pending_values();real(profile);if(profile==7007)enabled_glsl_profiles[0]=0;else if(profile==7008)enabled_glsl_profiles[1]=0;
 ++braid_gpu_epoch;last_real_vertex=last_real_fragment=NULL;dirty_cg_state();
}

/* Cache the game's texture-unit queries as well as the bridge's queries.
 * Resource assignments are invalidated by every CgGL load/destruction. */
unsigned cgGLGetTextureEnum(void *parameter){
 typedef struct texture_query {void *parameter;unsigned unit;unsigned long long epoch;struct texture_query *next;} texture_query;
 static texture_query *buckets[256];static unsigned(*real)(void*);
 if(!real)real=resolve_required("libCgGL.so","cgGLGetTextureEnum");
 if(!value_cache_enabled())return real(parameter);
 unsigned bucket=((unsigned long)parameter>>2)&255;
 texture_query *q=buckets[bucket];while(q&&q->parameter!=parameter)q=q->next;
 if(q&&q->epoch==braid_sampler_epoch)return q->unit;
 unsigned unit=real(parameter);
 if(unit>=0x84c0&&unit<0x84e0){
  if(!q){q=calloc(1,sizeof(*q));if(q){q->parameter=parameter;q->next=buckets[bucket];buckets[bucket]=q;}}
  if(q){q->unit=unit;q->epoch=braid_sampler_epoch;}
 }
 return unit;
}

void cgDestroyContext(void *context){
 static void(*real)(void*);if(!real)real=resolve_required("libCg.so","cgDestroyContext");
 flush_pending_values();lookup_compilation_begin();real(context);lookup_compilation_end(NULL);invalidate_lookup(NULL);
 for(braid_uniform_pair*q=uniform_pairs;q;q=q->next){q->vertex=q->fragment=NULL;q->ready=0;}
 for(braid_glsl_pair*q=glsl_pairs;q;q=q->next)q->vertex=q->fragment=NULL;
 clear_pair_indexes();last_uniform_pair=NULL;last_glsl_pair=NULL;last_glsl_program=0;
 bound_cg_vertex=bound_cg_fragment=NULL;last_real_vertex=last_real_fragment=NULL;
 memset(value_contexts,0,sizeof(value_contexts));invalidate_values();
 enabled_glsl_profiles[0]=enabled_glsl_profiles[1]=0;braid_cg_bindings_deferred=0;
 ++braid_sampler_epoch;++braid_gpu_epoch;dirty_cg_state();
}

/* Preserve SDK readback semantics if called outside our mirrored getter path. */
int cgGetParameterValuefr(void *p,int n,float *values){
 static int(*real)(void*,int,float*);if(!real)real=resolve_required("libCg.so","cgGetParameterValuefr");
 flush_pending_values();return real(p,n,values);
}
