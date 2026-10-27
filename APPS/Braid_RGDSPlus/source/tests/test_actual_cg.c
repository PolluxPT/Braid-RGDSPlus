#include <stdio.h>
#include <string.h>
extern void *cgCreateContext(void),*cgCreateParameter(void*,int);
extern int cgGetType(const char*),cgGetParameterRows(void*),cgGetParameterColumns(void*),cgGetParameterValuefr(void*,int,float*);
extern void *cgGetParameterContext(void*);
extern void cgSetParameterSettingMode(void*,int),cgSetParameter4fv(void*,const float*),cgSetMatrixParameterfr(void*,const float*);
extern int cgGetError(void);
int main(){
 void*c=cgCreateContext();cgSetParameterSettingMode(c,4133);
 const char*types[]={"float4","float4x4"};
 for(int t=0;t<2;t++){
  void*p=cgCreateParameter(c,cgGetType(types[t]));if(!p||cgGetParameterContext(p)!=c)return 1;
  int rows=cgGetParameterRows(p),cols=cgGetParameterColumns(p);printf("%s rows=%d cols=%d\n",types[t],rows,cols);
  if(rows!=(t?4:1)||cols!=4)return 2;
  for(int j=0;j<100;j++){
   float input[16],output[64];for(int i=0;i<16;i++)input[i]=(float)(j*13+i)/17;
   if(t)cgSetMatrixParameterfr(p,input);else cgSetParameter4fv(p,input);
   int n=cgGetParameterValuefr(p,64,output);
   if(n!=(t?16:4)||memcmp(input,output,n*sizeof(float))||cgGetError())return 3;
  }
 }
 puts("PASS actual supplied Cg: deferred setters/getters match byte-for-byte, matrix row-major order and vector dimensions verified");return 0;
}
