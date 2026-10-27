#include <stdint.h>
#include <stdio.h>
#include <sys/mman.h>
#include <stdlib.h>
static uint8_t* keys;
static unsigned calls;
const uint8_t* SDL_GetKeyboardState(int* n){
 if(!keys){
  keys=mmap((void*)0x100800000ULL,4096,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED,-1,0);
  if(keys==MAP_FAILED)abort();
  fprintf(stderr,"KEYBOARD_TEST native state=%p above32=%d\n",keys,(uintptr_t)keys>UINT32_MAX);
 }
 keys[4]=(++calls)&1;keys[511]=7;if(n)*n=512;return keys;
}
