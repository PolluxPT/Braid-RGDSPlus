/* SPDX-License-Identifier: MIT
 * The shipped game uses immutable, named Cg program parameters. Cache only
 * successful queries and plain-identifier misses in validated GLSL programs.
 * Invalid handles and aggregate-name misses still go to Cg.
 * Renderer-thread cache, matching the ownership of the existing GLSL bridge. */
#include <stdlib.h>
#include <string.h>
typedef struct lookup_entry {void *program,*parameter;struct lookup_entry *next;char name[];} lookup_entry;
typedef struct profile_entry {void *program;int profile;struct profile_entry *next;} profile_entry;
typedef struct {const char *input;lookup_entry *entry;} lookup_fast_entry;
static lookup_fast_entry lookup_fast[256];
static unsigned long long braid_name_fast_hits;
static lookup_entry *lookup_buckets[256];static profile_entry *profile_buckets[256];
static unsigned lookup_entries,profile_entries,lookup_compilation_depth;
static unsigned long long braid_lookup_hits,braid_lookup_reads,braid_profile_hits,braid_profile_reads,braid_negative_hits;
static int lookup_cache_enabled(void){
 static int enabled=-1;if(enabled<0){const char*s=getenv("BRAID_LOOKUP_CACHE");enabled=!(s&&s[0]=='0');}return enabled&&!lookup_compilation_depth;
}
static int missing_cache_enabled(void){
 static int enabled=-1;if(enabled<0){const char*s=getenv("BRAID_MISSING_CACHE");enabled=!(s&&s[0]=='0');}return enabled;
}
static void invalidate_lookup(void *program){
 memset(lookup_fast,0,sizeof(lookup_fast));
 for(int i=0;i<256;i++){
  lookup_entry **link=&lookup_buckets[i];while(*link){lookup_entry*q=*link;if(!program||q->program==program){*link=q->next;free(q);--lookup_entries;}else link=&q->next;}
  profile_entry **p=&profile_buckets[i];while(*p){profile_entry*q=*p;if(!program||q->program==program){*p=q->next;free(q);--profile_entries;}else p=&q->next;}
 }
}
static void lookup_compilation_begin(void){++lookup_compilation_depth;}
static void lookup_compilation_end(void *program){
 if(program)invalidate_lookup(program);
 if(lookup_compilation_depth)--lookup_compilation_depth;
}
int cgGetProgramProfile(void *program);
static int simple_lookup_name(const char *name,size_t n){
 if(!n)return 0;
 for(size_t i=0;i<n;i++){unsigned char c=name[i];if(!((c>='a'&&c<='z')||(c>='A'&&c<='Z')||c=='_'||(i&&c>='0'&&c<='9')))return 0;}
 return 1;
}
void *cgGetNamedParameter(void *program,const char *name){
 static void *(*real)(void*,const char*);if(!real)real=resolve_required("libCg.so","cgGetNamedParameter");
 if(!program||!name||!lookup_cache_enabled()){++braid_lookup_reads;return real(program,name);}
 /* A repeated caller-owned name still requires a content comparison: inputs
  * may be mutable. This memo avoids hashing the same name a second time, and
  * points into the bounded owned-name table; teardown clears it before free. */
 unsigned fast_bucket=(((unsigned long)program>>2)^((unsigned long)name>>2))&255;
 lookup_fast_entry *fast=&lookup_fast[fast_bucket];lookup_entry *memo=fast->entry;
 if(memo&&fast->input==name&&memo->program==program&&!strcmp(memo->name,name)){
  ++braid_lookup_hits;++braid_name_fast_hits;if(!memo->parameter)++braid_negative_hits;return memo->parameter;
 }
 unsigned hash=(unsigned)((unsigned long)program>>2);size_t n=0;
 while(name[n]&&n<256){hash=(hash*33)^(unsigned char)name[n];++n;}
 if(n>=256){++braid_lookup_reads;return real(program,name);}
 unsigned bucket=hash&255;
 for(lookup_entry*q=lookup_buckets[bucket];q;q=q->next)if(q->program==program&&!strcmp(q->name,name)){fast->input=name;fast->entry=q;++braid_lookup_hits;if(!q->parameter)++braid_negative_hits;return q->parameter;}
 ++braid_lookup_reads;void *parameter=real(program,name);
 int cacheable=parameter!=NULL;
 if(!cacheable&&missing_cache_enabled()&&simple_lookup_name(name,n)){
  /* Do not probe Cg again on a failed query: that could duplicate an error
   * callback for an invalid handle. Only trust an already validated profile. */
  unsigned b=((unsigned long)program>>2)&255;
  for(profile_entry*q=profile_buckets[b];q;q=q->next)if(q->program==program){cacheable=1;break;}
 }
 if(cacheable&&lookup_entries<4096){lookup_entry*q=malloc(sizeof(*q)+n+1);if(q){q->program=program;q->parameter=parameter;memcpy(q->name,name,n+1);q->next=lookup_buckets[bucket];lookup_buckets[bucket]=q;++lookup_entries;fast->input=name;fast->entry=q;}}
 return parameter;
}
int cgGetProgramProfile(void *program){
 static int(*real)(void*);if(!real)real=resolve_required("libCg.so","cgGetProgramProfile");
 unsigned bucket=((unsigned long)program>>2)&255;
 if(program&&lookup_cache_enabled())for(profile_entry*q=profile_buckets[bucket];q;q=q->next)if(q->program==program){++braid_profile_hits;return q->profile;}
 ++braid_profile_reads;int profile=real(program);
 if(program&&lookup_cache_enabled()&&(profile==7007||profile==7008)&&profile_entries<1024){profile_entry*q=malloc(sizeof(*q));if(q){q->program=program;q->profile=profile;q->next=profile_buckets[bucket];profile_buckets[bucket]=q;++profile_entries;}}
 return profile;
}
