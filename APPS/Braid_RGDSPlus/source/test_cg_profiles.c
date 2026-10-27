#include <stdio.h>
#include <string.h>
extern void* cgCreateContext(void);
extern void cgDestroyContext(void*);
extern int cgGetProfile(const char*);
extern int cgGLGetLatestProfile(int);
extern void* cgCreateProgram(void*,int,const char*,int,const char*,const char**);
extern const char* cgGetProgramString(void*,int);
extern const char* cgGetLastListing(void*);
extern void cgDestroyProgram(void*);
int main(void){void*c=cgCreateContext();if(!c)return 1;
 const char*names[]={"arbvp1","arbfp1"};
 const char*src[]={"float4 main(float4 p : POSITION) : POSITION { return p; }","float4 main(float4 c : COLOR) : COLOR { return c; }"};
 const char*headers[]={"!!ARBvp1.0","!!ARBfp1.0"};
 for(int i=0;i<2;i++){int p=cgGLGetLatestProfile(8+i);printf("Selected %s profile=%d\n",names[i],p);if(p!=cgGetProfile(names[i]))return 2;
 void*s=cgCreateProgram(c,4112,src[i],p,"main",0);if(!s){printf("FAIL compile %s\n",cgGetLastListing(c));return 3;}
 const char*code=cgGetProgramString(s,4106);if(!code||!strstr(code,headers[i])){puts("FAIL assembly header");return 4;}
 printf("PASS: actual Cg compiler emits %s\n",headers[i]);cgDestroyProgram(s);}
 cgDestroyContext(c);return 0;}
