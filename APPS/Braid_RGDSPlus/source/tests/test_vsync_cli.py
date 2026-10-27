from pathlib import Path
import struct,sys
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_EIP
b=Path(sys.argv[1]).read_bytes()
for argument,expected in [(b'-no_vsync',0),(b'-vsync',1)]:
 u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(0x8040000,0x900000);u.mem_map(0x9000000,0x2000);u.mem_map(0xf000000,0x10000)
 offset=struct.unpack_from('<I',b,28)[0];size,count=struct.unpack_from('<HH',b,42)
 for i in range(count):
  kind,off,va,pa,filesz,memsz,flags,align=struct.unpack_from('<8I',b,offset+i*size)
  if kind==1:u.mem_write(va,b[off:off+filesz])
 u.mem_write(0x833b762,b'\x01' if expected==0 else b'\x00')
 u.mem_write(0x9001000,b'Braid\0');u.mem_write(0x9001100,argument+b'\0')
 u.mem_write(0x9000200,struct.pack('<3I',0x9001000,0x9001100,0))
 sp=0xf008000;end=0xf000000;u.mem_write(sp,struct.pack('<3I',end,2,0x9000200));u.reg_write(UC_X86_REG_ESP,sp)
 u.emu_start(0x80e9ab0,end,count=100000)
 assert u.reg_read(UC_X86_REG_EIP)==end
 assert u.mem_read(0x833b762,1)[0]==expected
 print('PASS: real command-line parser',argument.decode(),'sets startup_vsync=',expected)
