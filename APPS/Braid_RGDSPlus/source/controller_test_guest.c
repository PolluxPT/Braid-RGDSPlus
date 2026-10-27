#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
typedef struct { int32_t type; int32_t value[2]; } Bind;
typedef struct { unsigned char bytes[16]; } Guid;
extern Bind SDL_GameControllerGetBindForAxis(void*,int);
extern Bind SDL_GameControllerGetBindForButton(void*,int);
extern Guid SDL_JoystickGetDeviceGUID(int);
extern Guid SDL_JoystickGetGUIDFromString(const char*);
extern void SDL_LogError(int,const char*,...);
extern void SDL_MinimizeWindow(void*);
static void check(Bind b,int type,int a,int c){if(b.type!=type||b.value[0]!=a||b.value[1]!=c)abort();}
int main(void){
 void* c=(void*)0x12345678;
 for(int j=0;j<10000;j++){
  check(SDL_GameControllerGetBindForAxis(c,1),2,3,0);
  check(SDL_GameControllerGetBindForAxis(c,2),3,1,8);
  check(SDL_GameControllerGetBindForAxis(c,3),1,9,0);
  check(SDL_GameControllerGetBindForAxis(c,-1),0,0,0);
  check(SDL_GameControllerGetBindForButton(c,0),1,2,0);
  check(SDL_GameControllerGetBindForButton(c,1),3,0,4);
 }
 Guid g=SDL_JoystickGetDeviceGUID(3);for(int i=0;i<16;i++)if(g.bytes[i]!=51+i)abort();
 g=SDL_JoystickGetGUIDFromString("a");for(int i=0;i<16;i++)if(g.bytes[i]!=97+i)abort();
 SDL_LogError(7,"binding=%d label=%s",42,"ok");SDL_MinimizeWindow(c);
 puts("PASS: 60000 i386 binding struct returns, axis/button/hat/none values, GUID struct returns and stack discipline");return 0;
}
