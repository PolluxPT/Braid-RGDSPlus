from pathlib import Path
p=Path('braid-build/box64/src/wrapped32/wrappedsdl2.c');s=p.read_text();s=s.replace('typedef void (*vFp_t)(void*);','''typedef uint32_t (*rgds_uFp_t)(void*);
typedef int (*rgds_iFp_t)(void*);
typedef int (*rgds_iFpu_t)(void*,uint32_t);
typedef void (*rgds_vFppp_t)(void*,void*,void*);
typedef void (*vFp_t)(void*);''',1)
s=s.replace('GO(SDL_FreeRW, sdl2_freerw)','''GO(SDL_FreeRW, sdl2_freerw) \\
    GO(SDL_GetWindowFlags, rgds_uFp_t) \\
    GO(SDL_GetWindowDisplayIndex, rgds_iFp_t) \\
    GO(SDL_GL_GetDrawableSize, rgds_vFppp_t) \\
    GO(SDL_ShowWindow, vFp_t) \\
    GO(SDL_RaiseWindow, vFp_t) \\
    GO(SDL_SetWindowFullscreen, rgds_iFpu_t)''',1);p.write_text(s)
