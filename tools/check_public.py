#!/usr/bin/env python3
"""Audit exact public inventory, content hashes and excluded commercial files."""
import hashlib,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
IGNORED={'.git','dist','__pycache__','.cache','local_install','private_input'}
def audit():
    manifest=json.loads((ROOT/'public_manifest.json').read_text());files=manifest['files']
    actual={str(p.relative_to(ROOT)).replace('\\','/') for p in ROOT.rglob('*') if p.is_file() and not any(x in IGNORED for x in p.relative_to(ROOT).parts)}
    expected=set(files)|{'public_manifest.json'}
    if actual!=expected:raise ValueError('Inventory mismatch: extra='+str(sorted(actual-expected))+' missing='+str(sorted(expected-actual)))
    for name,sha in files.items():
        p=ROOT/name
        if hashlib.sha256(p.read_bytes()).hexdigest()!=sha:raise ValueError('Changed public file: '+name)
        if p.name in {'libCg.so','libCgGL.so','libstdc++.so.6','libgcc_s.so.1','package.braid','package0.braid','Braid.bin.x86','Braid.rgds.x86','Braid.rgds.fullres.x86'}:raise ValueError('Excluded binary/data in public inventory: '+name)
        if '/game/' in name and p.name!='README.txt':raise ValueError('Game content in public inventory: '+name)
        if '/savedata/' in name or '/logs/' in name:raise ValueError('Private runtime state in public inventory: '+name)
    return files
if __name__=='__main__':print('PASS public inventory:',len(audit()),'files, exact hashes; game/SDK/GNU binaries and runtime state excluded')
