/* SPDX-License-Identifier: MIT
 * Braid's Cg parameters are set through the generic deferred Cg API. Mirror
 * numeric values into the current GLSL pair before drawing. Sampler assignment
 * and texture binding remain owned by CgGL and the game. */
#include <stdlib.h>
#include <string.h>
typedef struct {
 void *parameter;int location,width,count,valid,sampler;
 float last[64];char name[128];
} braid_uniform;
typedef struct braid_uniform_pair {
 unsigned program;void *vertex,*fragment;int count;
 braid_uniform *uniforms;struct braid_uniform_pair *next;
} braid_uniform_pair;
static braid_uniform_pair *uniform_pairs;
static void sync_cg_uniforms(void) {
 static void (*get)(unsigned,int*);
 static void (*active)(unsigned,unsigned,int,int*,int*,unsigned*,char*);
 static void (*program_info)(unsigned,unsigned,int*);
 static int (*location)(unsigned,const char*),(*value)(void*,int,float*);
 static int (*referenced)(void*);static unsigned (*texture_enum)(void*);static void (*sampler)(int,int);
 static void *(*named)(void*,const char*);
 static void (*upload[4])(int,int,const float*);
 static unsigned reports;
 if(!bound_cg_vertex&&!bound_cg_fragment)return;
 if(!get){
  get=resolve_required("libGL.so.1","glGetIntegerv");
  active=resolve_required("libGL.so.1","glGetActiveUniform");
  program_info=resolve_required("libGL.so.1","glGetProgramiv");
  location=resolve_required("libGL.so.1","glGetUniformLocation");
  named=resolve_required("libCg.so","cgGetNamedParameter");
  referenced=resolve_required("libCg.so","cgIsParameterReferenced");
  texture_enum=resolve_required("libCgGL.so","cgGLGetTextureEnum");sampler=resolve_required("libGL.so.1","glUniform1i");
  value=resolve_required("libCg.so","cgGetParameterValuefr");
  upload[0]=resolve_required("libGL.so.1","glUniform1fv");
  upload[1]=resolve_required("libGL.so.1","glUniform2fv");
  upload[2]=resolve_required("libGL.so.1","glUniform3fv");
  upload[3]=resolve_required("libGL.so.1","glUniform4fv");
 }
 int program=bind_braid_glsl_pair();if(!program)return;
 braid_uniform_pair *pair=uniform_pairs;
 while(pair&&(pair->program!=(unsigned)program||pair->vertex!=bound_cg_vertex||pair->fragment!=bound_cg_fragment))pair=pair->next;
 if(!pair){
  int total=0;program_info(program,0x8b86,&total);if(total<0||total>256)return;
  pair=calloc(1,sizeof(*pair));if(!pair)return;
  pair->uniforms=calloc(total?total:1,sizeof(*pair->uniforms));if(!pair->uniforms){free(pair);return;}
  pair->program=program;pair->vertex=bound_cg_vertex;pair->fragment=bound_cg_fragment;
  for(int i=0;i<total;i++){
   char name[128]={0};int length=0,count=0;unsigned type=0;
   active(program,i,sizeof(name),&length,&count,&type,name);
   int width=type==0x1406?1:type==0x8b50?2:type==0x8b51?3:type==0x8b52?4:0;
   int is_sampler=type==0x8b5e;
   if((!width&&!is_sampler)||count<1||(!is_sampler&&count>64/width)||name[0]!='_')continue;
   int loc=location(program,name);if(loc<0)continue;
   char source[128];memcpy(source,name+1,sizeof(source)-1);source[127]=0;
   char *index=strchr(source,'[');if(index)*index=0;
   void *p=bound_cg_vertex?named(bound_cg_vertex,source):NULL;
   if(p&&!referenced(p))p=NULL;
   if(!p&&bound_cg_fragment)p=named(bound_cg_fragment,source);
   if(!p)continue;
   braid_uniform *u=&pair->uniforms[pair->count++];u->parameter=p;u->location=loc;u->width=width;u->count=count;u->sampler=is_sampler;memcpy(u->name,name,sizeof(name));
  }
  pair->next=uniform_pairs;uniform_pairs=pair;
  fprintf(stderr,"BRAID_UNIFORMS: GLSL=%u mapped=%d active=%d vertex=%p fragment=%p\n",pair->program,pair->count,total,pair->vertex,pair->fragment);
 }
 for(int i=0;i<pair->count;i++){
  braid_uniform *u=&pair->uniforms[i];
  if(u->sampler){unsigned unit=texture_enum(u->parameter);if(unit>=0x84c0&&unit<0x84e0)sampler(u->location,unit-0x84c0);continue;}
  float values[64];int n=value(u->parameter,64,values);
  if(n!=u->width*u->count)continue;
  upload[u->width-1](u->location,u->count,values);
  memcpy(u->last,values,n*sizeof(float));u->valid=1;
  if(reports++<16)fprintf(stderr,"BRAID_UNIFORMS: %s count=%d first=%g,%g\n",u->name,n,(double)values[0],(double)(n>1?values[1]:0));
 }
}
