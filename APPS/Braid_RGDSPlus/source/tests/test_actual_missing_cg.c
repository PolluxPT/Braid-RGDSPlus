#include <stdio.h>
#include <stdlib.h>
#include <dlfcn.h>
#include <stdint.h>
static void *sdk;
static void *resolve_required(const char *lib,const char *name){
 (void)lib;if(!sdk)sdk=dlopen("libCg.so",RTLD_NOW|RTLD_LOCAL);
 void*p=sdk?dlsym(sdk,name):NULL;if(!p){fprintf(stderr,"missing %s: %s\n",name,dlerror());exit(2);}return p;
}
#include "cg_lookup_cache.h"
static int errors;
static void error_callback(void){++errors;}
int main(){
 void*(*context)(void)=resolve_required("libCg.so","cgCreateContext");
 void*(*create)(void*,int,const char*,int,const char*,const char**)=resolve_required("libCg.so","cgCreateProgram");
 int(*error)(void)=resolve_required("libCg.so","cgGetError");
 void(*callback)(void(*)(void))=resolve_required("libCg.so","cgSetErrorCallback");
 void(*destroy)(void*)=resolve_required("libCg.so","cgDestroyProgram");
 void(*destroy_context)(void*)=resolve_required("libCg.so","cgDestroyContext");
 void *c=context();void*p=create(c,4112,"float4 main(uniform float4 tint):COLOR {return tint;}",7008,"main",NULL);
 if(!p||error())return 3;
 if(cgGetProgramProfile(p)!=7008)return 4;
 void *tint=cgGetNamedParameter(p,"tint");if(!tint||error())return 5;
 for(int i=0;i<1000;i++)if(cgGetNamedParameter(p,"optional")||error()||cgGetNamedParameter(p,"tint")!=tint)return 6;
 if(braid_negative_hits!=999)return 7;
 unsigned long long before=braid_lookup_reads;
 lookup_compilation_begin();
 for(int i=0;i<2;i++)if(cgGetNamedParameter(p,"optional")||error())return 10;
 lookup_compilation_end(NULL);
 if(braid_lookup_reads!=before+2)return 11;
 if(cgGetNamedParameter(p,"optional")||braid_negative_hits!=1000)return 12;
 callback(error_callback);error();errors=0;
 if(cgGetNamedParameter(NULL,"optional")||!error()||errors!=1)return 8;
 destroy(p);invalidate_lookup(p);error();errors=0;
 if(cgGetNamedParameter(p,"optional")||!error()||errors!=1)return 9;
 callback(NULL);destroy_context(c);invalidate_lookup(NULL);
 puts("PASS supplied Cg: missing parameter returns NULL without error,cached misses, compiler bypass, live parameter stable, invalid/destroyed handles preserve one error callback each");return 0;
}
