"""Execute the supplied game's real decide_resolution function in Unicorn."""
import struct,sys
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_EIP,UC_X86_REG_EAX,UC_X86_REG_FPCW

def execute(data,width,height):
    u=Uc(UC_ARCH_X86,UC_MODE_32)
    u.mem_map(0x08040000,0x00900000)
    phoff=struct.unpack_from('<I',data,28)[0]
    phentsize,phnum=struct.unpack_from('<HH',data,42)
    for i in range(phnum):
        kind,offset,va,pa,filesz,memsz,flags,align=struct.unpack_from('<8I',data,phoff+i*phentsize)
        if kind==1:u.mem_write(va,data[offset:offset+filesz])
    u.mem_map(0x09000000,0x2000);u.mem_map(0x0f000000,0x10000)
    u.mem_write(0x08812aa4,struct.pack('<I',0x09000000))
    u.mem_write(0x09000004,struct.pack('<I',0x09001000))
    # InitOGL selects desktop fullscreen at 0x08196e6c on the RGDS+ path.
    u.mem_write(0x082ef000,struct.pack('<I',0x1001))
    stack=0x0f008000;end=0x0f000000
    u.mem_write(stack,struct.pack('<II',end,0));u.reg_write(UC_X86_REG_ESP,stack)
    u.reg_write(UC_X86_REG_FPCW,0x037f)
    def hook(cpu,address,size,unused):
        if address==0x0808d72c: # SDL_GetCurrentDisplayMode@plt
            sp=cpu.reg_read(UC_X86_REG_ESP)
            ret,display,output=struct.unpack('<III',cpu.mem_read(sp,12))
            assert display==0
            cpu.mem_write(output,struct.pack('<5I',0,width,height,60,0))
            cpu.reg_write(UC_X86_REG_EAX,0);cpu.reg_write(UC_X86_REG_ESP,sp+4);cpu.reg_write(UC_X86_REG_EIP,ret)
    u.hook_add(UC_HOOK_CODE,hook)
    u.emu_start(0x08194f40,end,count=1000)
    assert u.reg_read(UC_X86_REG_EIP)==end
    return struct.unpack('<4I',u.mem_read(0x09001004,16))

if __name__=='__main__':
    old=Path(sys.argv[1]).read_bytes();new=Path(sys.argv[2]).read_bytes()
    for size,expected_old,expected_new in [((1024,768),(1024,576,1024,768),(640,360,1024,768)),((800,600),(800,450,800,600),(640,360,800,600)),((320,240),(320,180,320,240),(320,180,320,240))]:
        a=execute(old,*size);b=execute(new,*size)
        assert a==expected_old,(size,a);assert b==expected_new,(size,b)
        print('PASS real resolution function:',size,a,'->',b)
