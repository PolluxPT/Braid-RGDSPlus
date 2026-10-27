#include <stdio.h>
#include <stdlib.h>
static unsigned swaps;
void SDL_GetVersion(unsigned char *v){v[0]=2;v[1]=32;v[2]=10;}
void SDL_GL_SwapWindow(void*p){if(p!=(void*)0x12345678)abort();if(++swaps==200)fprintf(stderr,"PASS: 200 native SDL swaps through ARM64 Box32\n");}
unsigned SDL_GetTicks(void){return swaps*34;}
