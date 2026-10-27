#include <stdint.h>
#include <stdio.h>
extern const uint8_t* SDL_GetKeyboardState(int*);
int main(void){
 int n=-1;const uint8_t* a=SDL_GetKeyboardState(&n);
 if(!a||n!=512||a[4]!=1||a[511]!=7){puts("FAIL first snapshot");return 1;}
 const uint8_t* b=SDL_GetKeyboardState(&n);
 if(b!=a||n!=512||b[4]!=0||b[511]!=7){puts("FAIL release or stable pointer");return 2;}
 b=SDL_GetKeyboardState(0);
 if(b!=a||b[4]!=1){puts("FAIL optional count");return 3;}
 puts("PASS: high native pointer mirrored below 4GB; press/release, stable pointer, optional count");return 0;
}
