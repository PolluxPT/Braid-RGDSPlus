"""Execute actual final-quad instructions and check presentation coordinates."""
import sys,struct
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from test_resolution import execute
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_FPCW

def quad(data):
 u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(0x08040000,0x900000);u.mem_map(0xf000000,0x10000)
 phoff=struct.unpack_from('<I',data,28)[0];size,num=struct.unpack_from('<HH',data,42)
 for i in range(num):
  kind,off,va,pa,fs,ms,flags,align=struct.unpack_from('<8I',data,phoff+i*size)
  if kind==1:u.mem_write(va,data[off:off+fs])
 u.mem_write(0x833b420,struct.pack('<II',1280,720));u.reg_write(UC_X86_REG_ESP,0xf008000);u.reg_write(UC_X86_REG_FPCW,0x37f)
 u.emu_start(0x8194d94,0x8194db7,count=30)
 return struct.unpack('<4f',u.mem_read(0xf008000,16))
old=Path(sys.argv[1]).read_bytes();new=Path(sys.argv[2]).read_bytes()
assert quad(old)==(0,0,640,360)
assert quad(new)==(0,0,1280,720)
assert execute(new,1024,768)==(640,360,1024,768)
print('PASS actual final quad: 640x360 -> 1280x720 virtual; scene remains 640x360, physical 1024x768')
