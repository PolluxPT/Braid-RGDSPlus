extern void SDL_GL_SwapWindow(void*);
__attribute__((noreturn)) void _start(void){for(int i=0;i<200;i++)SDL_GL_SwapWindow((void*)0x12345678);__asm__ volatile("int $0x80"::"a"(1),"b"(0):"memory");__builtin_unreachable();}
