/* SPDX-License-Identifier: MIT. Explicitly link both Cg-generated GLSL stages. */
#include <stdlib.h>
#include <string.h>
typedef struct braid_glsl_pair {
 void *vertex,*fragment;unsigned program;struct braid_glsl_pair *next;
} braid_glsl_pair;
static braid_glsl_pair *glsl_pairs;
static unsigned bind_braid_glsl_pair(void) {
 static const char *(*source)(void*,int);
 static unsigned (*create_shader)(unsigned),(*create_program)(void);
 static void (*shader_source)(unsigned,int,const char**,const int*),(*compile)(unsigned),(*shader_info)(unsigned,unsigned,int*);
 static void (*shader_log)(unsigned,int,int*,char*),(*program_log)(unsigned,int,int*,char*);
 static void (*attach)(unsigned,unsigned),(*link)(unsigned),(*program_info)(unsigned,unsigned,int*),(*use)(unsigned);
 if(!bound_cg_vertex||!bound_cg_fragment)return 0;
 if(!source){
  source=resolve_required("libCg.so","cgGetProgramString");
  create_shader=resolve_required("libGL.so.1","glCreateShader");create_program=resolve_required("libGL.so.1","glCreateProgram");
  shader_source=resolve_required("libGL.so.1","glShaderSource");compile=resolve_required("libGL.so.1","glCompileShader");
  shader_info=resolve_required("libGL.so.1","glGetShaderiv");shader_log=resolve_required("libGL.so.1","glGetShaderInfoLog");
  attach=resolve_required("libGL.so.1","glAttachShader");link=resolve_required("libGL.so.1","glLinkProgram");
  program_info=resolve_required("libGL.so.1","glGetProgramiv");program_log=resolve_required("libGL.so.1","glGetProgramInfoLog");
  use=resolve_required("libGL.so.1","glUseProgram");
 }
 braid_glsl_pair *pair=glsl_pairs;
 while(pair&&(pair->vertex!=bound_cg_vertex||pair->fragment!=bound_cg_fragment))pair=pair->next;
 if(!pair){
  pair=calloc(1,sizeof(*pair));if(!pair)return 0;
  pair->vertex=bound_cg_vertex;pair->fragment=bound_cg_fragment;pair->next=glsl_pairs;glsl_pairs=pair;
  unsigned shaders[2]={0};void *cg[2]={pair->vertex,pair->fragment};
  for(int i=0;i<2;i++){
   const char *text=source(cg[i],4106);if(!text)return 0;
   shaders[i]=create_shader(i?0x8b30:0x8b31);shader_source(shaders[i],1,&text,NULL);compile(shaders[i]);
   int ok=0;shader_info(shaders[i],0x8b81,&ok);
   if(!ok){char log[2048]={0};shader_log(shaders[i],sizeof(log),NULL,log);fprintf(stderr,"BRAID_GLSL_PAIR: %s compile FAILED: %s\n",i?"fragment":"vertex",log);return 0;}
  }
  unsigned program=create_program();attach(program,shaders[0]);attach(program,shaders[1]);link(program);
  int ok=0;program_info(program,0x8b82,&ok);
  if(!ok){char log[2048]={0};program_log(program,sizeof(log),NULL,log);fprintf(stderr,"BRAID_GLSL_PAIR: link FAILED: %s\n",log);return 0;}
  pair->program=program;fprintf(stderr,"BRAID_GLSL_PAIR: linked vertex=%p fragment=%p GLSL=%u\n",pair->vertex,pair->fragment,program);
 }
 if(pair->program)use(pair->program);
 return pair->program;
}
