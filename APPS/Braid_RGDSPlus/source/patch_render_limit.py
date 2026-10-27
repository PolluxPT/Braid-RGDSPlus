"""Create the RGDS+ adapted executable from the pinned supplied original."""
from pathlib import Path
import hashlib
import struct
import sys

ORIGINAL='8428ff57c83ed227be67b7a90caa8483b5983e6cca4a896471f60e9a5d497448'
ADAPTED018='484c5e80164e9d5ab7874d83ee70584baa9b877be8d2ec33e60fac87e955f468'

def patch(data):
    digest=hashlib.sha256(data).hexdigest()
    if digest not in (ORIGINAL,ADAPTED018):raise ValueError('Unsupported executable hash')
    if digest==ORIGINAL:
        if data.count(b'HOME\0')!=1:raise ValueError('Unexpected save-path string layout')
        data=data.replace(b'HOME\0',b'BRHM\0',1)
    if struct.unpack_from('<II',data,0x2a7004)!=(1280,720):raise ValueError('Unexpected ideal_width/ideal_height data')
    out=bytearray(data);struct.pack_into('<II',out,0x2a7004,640,360)
    # Present in the same virtual coordinate system as rendering_2d_right_handed.
    # Keep the internal render cap independent from final quad dimensions.
    for va,old,new in [(0x8194da3,0x82ef008,0x833b424),(0x8194dad,0x82ef004,0x833b420)]:
        offset=va-0x8048000
        if out[offset:offset+6]!=b'\xdb\x05'+struct.pack('<I',old):raise ValueError('Unexpected final quad instruction')
        struct.pack_into('<I',out,offset+2,new)
    return bytes(out)

if __name__=='__main__':
    source=Path(sys.argv[1]);destination=Path(sys.argv[2])
    if source.resolve()==destination.resolve():raise SystemExit('Use a separate output file; keep the original')
    output=patch(source.read_bytes());destination.write_bytes(output)
    print('Adapted executable SHA-256:',hashlib.sha256(output).hexdigest())
