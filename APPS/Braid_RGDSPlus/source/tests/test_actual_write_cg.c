/* CPU-only test of the exact cache header against the supplied i386 Cg SDK.
 * Complete linked-pair eligibility is modeled here and tested with GL mocks
 * separately. This is not a Box32/GLES hardware rendering test. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dlfcn.h>
#include <assert.h>
static unsigned long long braid_uniform_reads,braid_sampler_epoch=1;
static void *resolve_required(const char *lib,const char *symbol){
 void*h=dlopen(lib,RTLD_NOW);void*p=h?dlsym(h,symbol):NULL;
 if(!p){fprintf(stderr,"missing %s: %s\n",symbol,dlerror());exit(1);}return p;
}
#include "cg_value_cache.h"
int main(void){
 void*(*create_context)(void)=resolve_required("libCg.so","cgCreateContext");
 void*(*create_parameter)(void*,int)=resolve_required("libCg.so","cgCreateParameter");
 int(*type)(const char*)=resolve_required("libCg.so","cgGetType");
 int(*get)(void*,int,float*)=resolve_required("libCg.so","cgGetParameterValuefr");
 void(*mode)(void*,int)=resolve_required("libCg.so","cgSetParameterSettingMode");
 int(*error)(void)=resolve_required("libCg.so","cgGetError");
 void*context=create_context();assert(context);mode(context,4133);value_mode(context,4133);value_manage_textures(context,0);
 const char*types[]={"float2","float4","float4x4"};const int sizes[]={2,4,16};
 for(int t=0;t<3;t++){
  void*p=create_parameter(context,type(types[t]));assert(p);
  void(*set)(void*,const float*)=resolve_required("libCg.so",t==2?"cgSetMatrixParameterfr":t==1?"cgSetParameter4fv":"cgSetParameter2fv");
  float initial[16]={0},input[16],output[64],raw[64];set(p,initial);
  int n=sizes[t];assert(cached_parameter(p,64,output,get)==n);
  braid_value*v=setter_value(p,n,t==2);assert(v&&v->uniform);
  v->write_verified_epoch=braid_sampler_epoch;
  for(int j=1;j<=1000;j++){
   for(int k=0;k<n;k++)input[k]=(float)(j*13+k)/17;
   assert(defer_value(v,input));assert(cached_parameter(p,64,output,get)==n);assert(!memcmp(input,output,n*sizeof(float)));
   assert(get(p,64,raw)==n&&!memcmp(raw,initial,n*sizeof(float)));assert(!error());
  }
  unsigned long long before=braid_writes_flushed;flush_pending_values();
  assert(braid_writes_flushed==before+1);assert(get(p,64,raw)==n&&!memcmp(input,raw,n*sizeof(float)));assert(!error());
  printf("PASS supplied Cg %s:1000 CPU updates, exact mirrored values, one final SDK write\n",types[t]);
 }
 assert(braid_writes_deferred==3000&&braid_writes_flushed==3);
 assert(!defer_value(NULL,NULL));return 0;
}
