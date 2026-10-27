#!/usr/bin/env python3
import hashlib,pathlib,zipfile
from check_public import ROOT,audit
files=audit();out=ROOT/'dist';out.mkdir(exist_ok=True)
asset=out/'Braid_RGDSPlus_v1.6_PortOnly.zip'
with zipfile.ZipFile(asset,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for name in sorted(set(files)|{'public_manifest.json'}):
  z.write(ROOT/name,name)
sha=hashlib.sha256(asset.read_bytes()).hexdigest()
(out/'SHA256SUMS.txt').write_text(sha+'  '+asset.name+'\n')
print(asset);print(sha)
