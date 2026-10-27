#!/usr/bin/env python3
"""Prepare a PRIVATE RGDS+ install from an owned, supported Linux Braid copy.
Python 3.10+, standard library only. Run on Windows, macOS or Linux.
"""
import argparse,hashlib,io,json,os,pathlib,shutil,sys,tarfile,tempfile,urllib.request
ROOT=pathlib.Path(__file__).resolve().parents[1]

def digest(data):return hashlib.sha256(data).hexdigest()

def deb_member(blob,basename):
    """Read an exact regular-library member; never extract arbitrary paths."""
    if not blob.startswith(b'!<arch>\n'):raise ValueError('Invalid Debian archive')
    off=8
    while off+60<=len(blob):
        h=blob[off:off+60]
        if h[58:60]!=b'`\n':raise ValueError('Invalid ar member header')
        name=h[:16].decode('ascii').strip().rstrip('/');size=int(h[48:58]);start=off+60
        payload=blob[start:start+size]
        if len(payload)!=size:raise ValueError('Truncated Debian archive')
        if name.startswith('data.tar.'):
            with tarfile.open(fileobj=io.BytesIO(payload),mode='r:*') as tar:
                matches=[m for m in tar.getmembers() if m.isfile() and pathlib.PurePosixPath(m.name).name==basename]
                if len(matches)!=1:raise ValueError('Missing or ambiguous runtime member: '+basename)
                return tar.extractfile(matches[0]).read()
        off=start+size+(size%2)
    raise ValueError('Debian data archive missing')

def prepare(game_dir,output,download=False,package_dir=None):
    game_dir=pathlib.Path(game_dir).resolve();output=pathlib.Path(output).resolve()
    rules=json.loads((ROOT/'tools/supported_game.json').read_text())
    if output.exists():raise ValueError('Output already exists. Choose a new folder; existing saves are never overwritten.')
    if game_dir==output or game_dir in output.parents or output in game_dir.parents:raise ValueError('Keep the output separate from your original game folder.')
    for name,expected in rules['required_files'].items():
        p=game_dir/name
        if not p.is_file():raise ValueError('Missing owned game file: '+name)
        if digest(p.read_bytes())!=expected:raise ValueError('Unsupported game file: '+name+'. This port requires the pinned Linux i386 edition; see docs/INSTALL.md.')
    syslibs={}
    packages=json.loads((ROOT/'tools/runtime-packages.json').read_text())
    for package,member,target in [('libstdc++6','libstdc++.so.6.0.30','libstdc++.so.6'),('libgcc-s1','libgcc_s.so.1','libgcc_s.so.1')]:
        record=packages[package];filename=pathlib.PurePosixPath(record['Filename']).name
        # A user's existing private standalone install is also a supported source.
        private=game_dir.parent/'runtime/libs.x86'/target
        if private.is_file() and digest(private.read_bytes())==rules['runtime_outputs'][target]:
            syslibs[target]=private.read_bytes();continue
        local=pathlib.Path(package_dir)/filename if package_dir else None
        if local and local.is_file():blob=local.read_bytes()
        elif download:
            url='https://deb.debian.org/debian/'+record['Filename']
            print('Downloading pinned runtime:',filename)
            with urllib.request.urlopen(url,timeout=60) as response:blob=response.read(10*1024*1024)
        else:raise ValueError('Runtime package required: '+filename+'. Add --download-runtime or --runtime-packages DIR.')
        if digest(blob)!=record['SHA256']:raise ValueError('Runtime package checksum mismatch: '+filename)
        data=deb_member(blob,member)
        if digest(data)!=rules['runtime_outputs'][target]:raise ValueError('Extracted runtime checksum mismatch: '+target)
        syslibs[target]=data
    sys.path.insert(0,str(ROOT/'APPS/Braid_RGDSPlus/source'))
    from patch_render_limit import patch
    original=(game_dir/'Braid.bin.x86').read_bytes();adapted=patch(original)
    if digest(adapted)!=rules['adapted_game_sha256']:raise ValueError('Adapted executable checksum mismatch')
    output.parent.mkdir(parents=True,exist_ok=True)
    # Build in a separate staging directory and install only after validation.
    with tempfile.TemporaryDirectory(prefix='braid-prepare-',dir=output.parent) as temp:
        staged=pathlib.Path(temp)/'install';staged.mkdir()
        shutil.copytree(ROOT/'APPS',staged/'APPS',ignore=shutil.ignore_patterns('source','__pycache__'))
        target=staged/'APPS/Braid_RGDSPlus';owned=target/'game'
        shutil.copytree(game_dir/'data',owned/'data')
        (owned/'lib').mkdir(exist_ok=True)
        for name in ['libCg.so','libCgGL.so']:shutil.copy2(game_dir/'lib'/name,owned/'lib'/name)
        (owned/'Braid.bin.x86').write_bytes(original);(owned/'Braid.rgds.x86').write_bytes(adapted)
        if (game_dir/'licenses').is_dir():shutil.copytree(game_dir/'licenses',owned/'licenses')
        if (game_dir/'Icon.png').is_file():
            (staged/'APPS/Imgs').mkdir(exist_ok=True);shutil.copy2(game_dir/'Icon.png',staged/'APPS/Imgs/Braid.png')
        for name,data in syslibs.items():(target/'runtime/libs.x86'/name).write_bytes(data)
        shutil.copy2(ROOT/'LICENSE',target/'LICENSE')
        for p in [staged/'APPS/Braid.sh',target/'runtime/box64-box32',owned/'Braid.rgds.x86']:p.chmod(p.stat().st_mode|0o111)
        (staged/'PRIVATE_INSTALL.txt').write_text('Prepared from your owned game. Keep private. Copy APPS contents into Roms/APPS. Preserve savedata when updating.\n')
        staged.rename(output)
    print('Ready:',output/'APPS')
    print('Copy the contents of APPS into TF2/Roms/APPS. Keep existing savedata.')
    return output

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--game-dir',required=True);p.add_argument('--output',required=True);p.add_argument('--download-runtime',action='store_true');p.add_argument('--runtime-packages')
    a=p.parse_args()
    try:prepare(a.game_dir,a.output,a.download_runtime,a.runtime_packages)
    except (ValueError,OSError,tarfile.TarError) as e:p.exit(1,'Preparation failed: '+str(e)+'\n')
if __name__=='__main__':main()
