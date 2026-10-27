#include <stdint.h>
#include <stdio.h>
#include <stdarg.h>
#include <string.h>
#include <stdlib.h>
typedef struct { int32_t type; int32_t value[2]; } Bind;
typedef struct { unsigned char bytes[16]; } Guid;
static void check(void* p){if(p!=(void*)0x12345678)abort();}
Bind SDL_GameControllerGetBindForAxis(void* c,int i){check(c);Bind b={0,{0,0}};switch(i){case 1:b=(Bind){2,{3,0}};break;case 2:b=(Bind){3,{1,8}};break;case 3:b=(Bind){1,{9,0}};break;}return b;}
Bind SDL_GameControllerGetBindForButton(void* c,int i){check(c);return i?(Bind){3,{0,4}}:(Bind){1,{2,0}};}
Guid SDL_JoystickGetDeviceGUID(int i){Guid g;for(int j=0;j<16;j++)g.bytes[j]=i*17+j;return g;}
Guid SDL_JoystickGetGUIDFromString(const char* s){Guid g;for(int j=0;j<16;j++)g.bytes[j]=(unsigned char)s[0]+j;return g;}
void SDL_LogMessageV(int category,int priority,const char* fmt,va_list ap){char buf[128];vsnprintf(buf,sizeof(buf),fmt,ap);if(category!=7||priority!=5||strcmp(buf,"binding=42 label=ok"))abort();fprintf(stderr,"PASS: variadic SDL_LogError category=%d priority=%d %s\n",category,priority,buf);}
void SDL_MinimizeWindow(void* p){check(p);fprintf(stderr,"PASS: SDL_MinimizeWindow forwarded\n");}
