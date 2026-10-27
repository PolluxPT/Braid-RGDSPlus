/* SPDX-License-Identifier: MIT
 * CPU-side Cg values for the three numeric setters imported by this game.
 * Verified uniform writes may be buffered while the paired bridge owns drawing.
 * Flush latest values before original CgGL fallback calls or SDK readback.
 * Identical setters may be elided only in an observed DEFERRED context.
 */
#include <stdlib.h>
#include <string.h>
typedef struct braid_value {
 void *parameter,*context;int n,valid,rows,columns,metadata,kind,uniform,pending;
 unsigned long long write_verified_epoch;struct braid_value *pending_next;
 unsigned long long revision;float values[64];struct braid_value *next;
} braid_value;
static braid_value *value_buckets[256],*pending_values;
static unsigned long long braid_writes_deferred,braid_writes_flushed;
static int write_cache_enabled(void){
 static int enabled=-1;if(enabled<0){const char*s=getenv("BRAID_WRITE_CACHE");enabled=!(s&&s[0]=='0');}return enabled;
}
static void flush_pending_values(void);
typedef struct {void *context;int mode,managed,managed_known;} braid_context_mode;
static braid_context_mode value_contexts[32];
static unsigned long long braid_value_hits,braid_setters_skipped,braid_sampler_reads,braid_sampler_hits;
static unsigned long long braid_revision_hits;
static int revision_cache_enabled(void){
 static int enabled=-1;if(enabled<0){const char*s=getenv("BRAID_REVISION_CACHE");enabled=!(s&&s[0]=='0');}return enabled;
}
static int value_cache_enabled(void){
 static int enabled=-1;if(enabled<0){const char *s=getenv("BRAID_VALUE_CACHE");enabled=!(s&&s[0]=='0');}return enabled;
}
static braid_value *find_value(void *p,int create){
 unsigned bucket=((unsigned long)p>>2)&255;
 braid_value *v=value_buckets[bucket];while(v&&v->parameter!=p)v=v->next;
 if(!v&&create){v=calloc(1,sizeof(*v));if(v){v->parameter=p;v->next=value_buckets[bucket];value_buckets[bucket]=v;}}
 return v;
}
static void value_metadata(braid_value *v){
 static void *(*context)(void*);static int (*rows)(void*),(*columns)(void*),(*type)(void*);static const char *(*type_name)(int);
 if(v->metadata)return;
 if(!context){context=resolve_required("libCg.so","cgGetParameterContext");rows=resolve_required("libCg.so","cgGetParameterRows");columns=resolve_required("libCg.so","cgGetParameterColumns");type=resolve_required("libCg.so","cgGetParameterType");type_name=resolve_required("libCg.so","cgGetTypeString");}
 v->context=context(v->parameter);v->rows=rows(v->parameter);v->columns=columns(v->parameter);const char *name=type_name(type(v->parameter));
 if(write_cache_enabled()){int(*variability)(void*)=resolve_required("libCg.so","cgGetParameterVariability");v->uniform=variability(v->parameter)==4102;}
 v->kind=name&&!strcmp(name,"float4x4")?16:name&&!strcmp(name,"float4")?4:name&&!strcmp(name,"float2")?2:0;v->metadata=1;
}
static int deferred_value(braid_value *v){
 for(int i=0;i<32;i++)if(value_contexts[i].context==v->context)return value_contexts[i].mode==4133;
 return 0;
}
static void value_mode(void *context,int mode){
 for(int i=0;i<32;i++)if(value_contexts[i].context==context||!value_contexts[i].context){value_contexts[i].context=context;value_contexts[i].mode=mode;break;}
 /* A mode transition flushes Cg values; refresh from Cg before caching again. */
 for(int i=0;i<256;i++)for(braid_value*v=value_buckets[i];v;v=v->next)if(v->context==context)v->valid=0;
}
static void invalidate_values(void){
 for(int i=0;i<256;i++)for(braid_value*v=value_buckets[i];v;v=v->next){v->valid=0;v->metadata=0;v->kind=0;v->uniform=0;v->write_verified_epoch=0;}
}
static int cached_parameter(void *p,int capacity,float *output,int (*read)(void*,int,float*)){
 if(!value_cache_enabled()){++braid_uniform_reads;return read(p,capacity,output);}
 braid_value*v=find_value(p,1);
 if(v&&v->valid&&deferred_value(v)&&v->n<=capacity){memcpy(output,v->values,v->n*sizeof(float));++braid_value_hits;return v->n;}
 ++braid_uniform_reads;int n=read(p,capacity,output);
 if(v&&n>0&&n<=64&&n<=capacity){v->n=n;memcpy(v->values,output,n*sizeof(float));value_metadata(v);v->valid=1;++v->revision;}
 return n;
}
/* Only records first observed through Cg's own getter are eligible.
 * Matrix setters are cached only for confirmed 4x4 parameters. */
static braid_value *setter_value(void *p,int n,int matrix){
 if(!value_cache_enabled())return NULL;
 braid_value*v=find_value(p,0);if(!v||!v->valid||v->n!=n)return NULL;
 if(v->kind!=n)return NULL;
 if(matrix&&(v->rows!=4||v->columns!=4))return NULL;
 if(!matrix&&(v->rows!=1||v->columns!=n))return NULL;
 return v;
}
static int redundant_value(braid_value*v,const float*values){
 if(v&&deferred_value(v)&&!memcmp(v->values,values,v->n*sizeof(float))){++braid_setters_skipped;return 1;}return 0;
}
static void changed_value(void *p,braid_value*v,const float*values){
 if(v){memcpy(v->values,values,v->n*sizeof(float));v->valid=1;++v->revision;}
 else {v=find_value(p,0);if(v)v->valid=0;}
}

static int direct_bridge_enabled(void){
 static int enabled=-1;if(enabled<0){const char*s=getenv("BRAID_DIRECT_BRIDGE");enabled=!(s&&s[0]=='0');}return enabled;
}
static int direct_context(void *context){
 for(int i=0;i<32;i++)if(value_contexts[i].context==context)return value_contexts[i].mode==4133&&value_contexts[i].managed_known&&!value_contexts[i].managed;
 return 0;
}
static void value_manage_textures(void *context,int managed){
 for(int i=0;i<32;i++)if(value_contexts[i].context==context||!value_contexts[i].context){value_contexts[i].context=context;value_contexts[i].managed=managed;value_contexts[i].managed_known=1;break;}
}
static int deferred_parameter(void *p){
 if(!p)return 0;
 /* Unreferenced parameters never reach the uniform getter, but their setters
  * still obey the context's deferred mode. Do not treat them as GPU writes. */
 braid_value*v=find_value(p,1);if(!v)return 0;
 value_metadata(v);return deferred_value(v);
}

/* Only immutable numeric uniform records observed through an original getter
 * and a complete ready pair are eligible. No parameter connections/arrays or
 * other setter APIs are imported by the pinned Braid executable. */
static int defer_value(braid_value *v,const float *values){
 if(!write_cache_enabled()||!direct_bridge_enabled()||!v||!v->uniform||v->write_verified_epoch!=braid_sampler_epoch||!direct_context(v->context))return 0;
 changed_value(v->parameter,v,values);
 if(!v->pending){v->pending=1;v->pending_next=pending_values;pending_values=v;}
 ++braid_writes_deferred;return 1;
}
static void flush_pending_values(void){
 static void(*set2)(void*,const float*),(*set4)(void*,const float*),(*setm)(void*,const float*);
 if(!pending_values)return;
 if(!set2){set2=resolve_required("libCg.so","cgSetParameter2fv");set4=resolve_required("libCg.so","cgSetParameter4fv");setm=resolve_required("libCg.so","cgSetMatrixParameterfr");}
 while(pending_values){
  braid_value *v=pending_values;pending_values=v->pending_next;v->pending_next=NULL;v->pending=0;
  if(v->n==16)setm(v->parameter,v->values);else if(v->n==4)set4(v->parameter,v->values);else set2(v->parameter,v->values);
  ++braid_writes_flushed;
 }
}
static void flush_conflicting_value(void *p){braid_value*v=find_value(p,0);if(v&&v->pending)flush_pending_values();}
