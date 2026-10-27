from pathlib import Path
p=Path('braid-build/box64/src/wrapped32/wrappedsdl2_private.h');s=p.read_text().replace('//%S J SDL2_GUID_t uuuu','//%S J SDL2_GUID_t uuuu\n//%S z SDL2_Bind_t iii')
s=s.replace('//GO(SDL_GameControllerGetBindForAxis, HFpi)','GOS(SDL_GameControllerGetBindForAxis, zFEpi)').replace('//GO(SDL_GameControllerGetBindForButton, HFpi)','GOS(SDL_GameControllerGetBindForButton, zFEpi)').replace('//GOM(SDL_LogError, vFEipV)','GOM(SDL_LogError, vFEipV)').replace('//GO(SDL_MinimizeWindow, vFp)','GO(SDL_MinimizeWindow, vFp)');p.write_text(s)
p=Path('braid-build/box64/src/wrapped32/wrappedsdl2.c');s=p.read_text().replace('typedef struct {\n    uint8_t data[16];','typedef struct { int32_t type; int32_t value[2]; } SDL2_Bind_t;\n\ntypedef struct {\n    uint8_t data[16];',1)
s=s.replace('my32_2_SDL_JoystickGetDeviceGUID(void* ret, int index)','my32_2_SDL_JoystickGetDeviceGUID(x64emu_t* emu, void* ret, int index)').replace('my32_2_SDL_JoystickGetGUIDFromString(void* ret, void* s)','my32_2_SDL_JoystickGetGUIDFromString(x64emu_t* emu, void* ret, void* s)')
s+='''
/* SDL binding structs are twelve bytes on both ARM64 and i386. Native ARM64
 * returns them in registers; i386 uses a caller buffer and callee pops its
 * hidden pointer. GOS registers that four-byte stack adjustment. */
EXPORT void* my32_2_SDL_GameControllerGetBindForAxis(x64emu_t* emu, void* ret, void* controller, int axis)
{
    *(SDL2_Bind_t*)ret=my->SDL_GameControllerGetBindForAxis(controller,axis);
    return ret;
}
EXPORT void* my32_2_SDL_GameControllerGetBindForButton(x64emu_t* emu, void* ret, void* controller, int button)
{
    *(SDL2_Bind_t*)ret=my->SDL_GameControllerGetBindForButton(controller,button);
    return ret;
}
EXPORT void my32_2_SDL_LogError(x64emu_t* emu, int category, void* fmt, void* b)
{
    myStackAlign32((const char*)fmt,(uint32_t*)b,emu->scratch);
    PREPARE_VALIST_32;
    my->SDL_LogMessageV(category,5,fmt,VARARGS_32);
}
''';p.write_text(s)
