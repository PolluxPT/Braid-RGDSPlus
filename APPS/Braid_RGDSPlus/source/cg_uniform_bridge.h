/* SPDX-License-Identifier: MIT
 * Braid's Cg parameters are set through the generic deferred Cg API. Mirror
 * numeric values into the current GLSL pair before drawing. Sampler assignment
 * and texture binding remain owned by CgGL and the game. */
#include <stdlib.h>
#include <string.h>
typedef struct {
 void *parameter;int location,width,count,valid,sampler;
 braid_value *cached_value;unsigned long long value_revision;float last[64];char name[128];unsigned sampler_unit,last_gpu_unit;int sampler_valid;unsigned long long sampler_epoch;
} braid_uniform;
typedef struct braid_uniform_pair {
 unsigned program;void *vertex,*fragment;int count,ready,complete;void *contexts[2];unsigned long long epoch,gpu_epoch,resource_epoch,write_epoch;
 braid_uniform *uniforms;struct braid_uniform_pair *next;
} braid_uniform_pair;
static braid_uniform_pair *uniform_pairs,*last_uniform_pair;
static braid_uniform_pair *uniform_pair_index[256],*stage_index[256];
/* Indexes contain pointers to existing records, never independent readiness.
 * Recheck identities after collisions; readiness/context/resource guards remain
 * at each use. Records live until process exit. Destruction clears indexes. */
static braid_uniform_pair *find_uniform_pair(void){
 braid_uniform_pair *pair=last_uniform_pair;
 if(!pair||pair->vertex!=bound_cg_vertex||pair->fragment!=bound_cg_fragment)pair=uniform_pair_index[pair_bucket(bound_cg_vertex,bound_cg_fragment)];
 if(!pair||pair->vertex!=bound_cg_vertex||pair->fragment!=bound_cg_fragment)pair=uniform_pairs;
 while(pair&&(pair->vertex!=bound_cg_vertex||pair->fragment!=bound_cg_fragment))pair=pair->next;
 if(pair)uniform_pair_index[pair_bucket(bound_cg_vertex,bound_cg_fragment)]=pair;
 return pair;
}
static void clear_pair_indexes(void){
 memset(glsl_pair_index,0,sizeof(glsl_pair_index));
 memset(uniform_pair_index,0,sizeof(uniform_pair_index));
 memset(stage_index,0,sizeof(stage_index));
}
static void sync_cg_uniforms(void) {
 static void (*get)(unsigned,int*);
 static void (*active)(unsigned,unsigned,int,int*,int*,unsigned*,char*);
 static void (*program_info)(unsigned,unsigned,int*);
 static int (*location)(unsigned,const char*),(*value)(void*,int,float*);
 static int (*referenced)(void*);static unsigned (*texture_enum)(void*);static void (*sampler)(int,int);
 static void *(*named)(void*,const char*);
 static void (*upload[4])(int,int,const float*);
 static unsigned reports;
 ++braid_draws;
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
 braid_uniform_pair *pair=find_uniform_pair();
 if(pair&&pair->program!=(unsigned)program)return;
 if(!pair){
  int total=0;program_info(program,0x8b86,&total);if(total<0||total>256)return;
  pair=calloc(1,sizeof(*pair));if(!pair)return;
  pair->uniforms=calloc(total?total:1,sizeof(*pair->uniforms));if(!pair->uniforms){free(pair);return;}
  pair->program=program;pair->vertex=bound_cg_vertex;pair->fragment=bound_cg_fragment;
  if(direct_bridge_enabled()){
   void *(*context)(void*)=resolve_required("libCg.so","cgGetProgramContext");
   pair->contexts[0]=context(pair->vertex);pair->contexts[1]=context(pair->fragment);
  }
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
  pair->complete=pair->count==total;pair->next=uniform_pairs;uniform_pairs=pair;
  fprintf(stderr,"BRAID_UNIFORMS: GLSL=%u mapped=%d active=%d vertex=%p fragment=%p\n",pair->program,pair->count,total,pair->vertex,pair->fragment);
 }
 last_uniform_pair=pair;uniform_pair_index[pair_bucket(bound_cg_vertex,bound_cg_fragment)]=pair;
 if(pair->epoch==braid_cg_epoch){++braid_uniform_reuses;return;}
 int complete=pair->complete;
 int preserve=pair->complete&&direct_bridge_enabled()&&pair->gpu_epoch==braid_gpu_epoch&&direct_context(pair->contexts[0])&&direct_context(pair->contexts[1]);
 for(int i=0;i<pair->count;i++){
  braid_uniform *u=&pair->uniforms[i];
  if(u->sampler){
   unsigned unit;
   if(value_cache_enabled()&&u->sampler_epoch==braid_sampler_epoch){unit=u->sampler_unit;++braid_sampler_hits;}
   else {unit=texture_enum(u->parameter);++braid_sampler_reads;if(unit>=0x84c0&&unit<0x84e0){u->sampler_unit=unit;u->sampler_epoch=braid_sampler_epoch;}}
   if(unit>=0x84c0&&unit<0x84e0){
    if(preserve&&u->sampler_valid&&u->last_gpu_unit==unit)++braid_uploads_skipped;
    else {sampler(u->location,unit-0x84c0);++braid_uniform_uploads;u->last_gpu_unit=unit;u->sampler_valid=1;}
   }else complete=0;
   continue;
  }
  braid_value *v=u->cached_value;
  /* A revision identifies the exact CPU snapshot previously sent to this GL
   * program. Only bypass the copy when the existing GPU-preservation guard and
   * deferred-context/value-cache guards also pass. GPU clobbers always upload. */
  if(revision_cache_enabled()&&preserve&&u->valid&&value_cache_enabled()&&v&&v->valid&&deferred_value(v)&&v->n==u->width*u->count&&u->value_revision==v->revision){++braid_revision_hits;++braid_uploads_skipped;continue;}
  float values[64];int n=cached_parameter(u->parameter,64,values,value);
  if(value_cache_enabled()){u->cached_value=find_value(u->parameter,0);if(u->cached_value)u->value_revision=u->cached_value->revision;}
  if(n!=u->width*u->count){complete=0;continue;}
  if(preserve&&u->valid&&!memcmp(u->last,values,n*sizeof(float))){++braid_uploads_skipped;continue;}
  upload[u->width-1](u->location,u->count,values);++braid_uniform_uploads;
  memcpy(u->last,values,n*sizeof(float));u->valid=1;
  if(reports++<16)fprintf(stderr,"BRAID_UNIFORMS: %s count=%d first=%g,%g\n",u->name,n,(double)values[0],(double)(n>1?values[1]:0));
 }
 pair->epoch=braid_cg_epoch;pair->gpu_epoch=braid_gpu_epoch;pair->resource_epoch=braid_sampler_epoch;pair->ready=complete;
 if(complete&&pair->write_epoch!=braid_sampler_epoch&&write_cache_enabled()&&direct_bridge_enabled()&&direct_context(pair->contexts[0])&&direct_context(pair->contexts[1])){
  for(int i=0;i<pair->count;i++){braid_value*v=pair->uniforms[i].cached_value;if(v&&v->valid&&v->uniform)v->write_verified_epoch=braid_sampler_epoch;}
  pair->write_epoch=braid_sampler_epoch;
 }
}
