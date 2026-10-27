#include <stdio.h>
#include <stdlib.h>
extern void *cgCreateContext(void);
extern void *cgCreateProgramFromFile(void *,int,const char *,int,const char *,const char **);
extern const char *cgGetProgramString(void *,int);
extern const char *cgGetLastListing(void *);
extern int cgGetProfile(const char *);
int main(int argc,char **argv){
 if(argc<3)return 2;
 void *ctx=cgCreateContext();
 const char *args[]={"-I.",NULL,NULL};if(argc>3)args[1]=argv[3];
 for(int i=0;i<2;i++){
  int profile=argc>4?cgGetProfile(i?"glslf":"glslv"):(i?7000:6150);
  fprintf(stderr,"profile=%d\n",profile);
  void *p=cgCreateProgramFromFile(ctx,4112,argv[1],profile,i?"pixel_shader":"vertex_shader",args);
  if(!p){fprintf(stderr,"compile failed %s\n",cgGetLastListing(ctx));return 3;}
  const char *s=cgGetProgramString(p,4106);char path[1024];snprintf(path,sizeof(path),"%s.%s",argv[2],i?"fp":"vp");
  FILE *f=fopen(path,"w");if(!f)return 4;fputs(s,f);fclose(f);
 }
 return 0;
}
