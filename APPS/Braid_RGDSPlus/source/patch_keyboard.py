from pathlib import Path
p=Path('braid-build/box64/src/wrapped32/wrappedsdl2_private.h');s=p.read_text();assert 'GO(SDL_GetKeyboardState, pFp)' in s;s=s.replace('GO(SDL_GetKeyboardState, pFp)','GOM(SDL_GetKeyboardState, pFEp)');p.write_text(s)
p=Path('braid-build/box64/src/wrapped32/wrappedsdl2.c');s=p.read_text();s+='''
/* The firmware SDL keyboard array can reside above 4GB. The non-PIE Box32
 * executable owns a stable low-address mirror for the i386 caller. Braid
 * requests this state on every input frame. Never truncate the native pointer. */
EXPORT void* my32_2_SDL_GetKeyboardState(x64emu_t* emu, int* numkeys)
{
    static unsigned char state[512];
    static int reported;
    int n=0;
    const unsigned char* native=my->SDL_GetKeyboardState(&n);
    if(!native || n<0) n=0;
    if(n>(int)sizeof(state)) n=sizeof(state);
    memset(state,0,sizeof(state));
    if(n) memcpy(state,native,n);
    if(numkeys) *numkeys=n;
    if(!reported && getenv("BRAID_RGDS_GLES")) {
        fprintf(stderr,"BRAID_INPUT: keyboard mirror=%p native=%p keys=%d\\n",state,native,n);
        reported=1;
    }
    return native?state:NULL;
}
''';p.write_text(s)
