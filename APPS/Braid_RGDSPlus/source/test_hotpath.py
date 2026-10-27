import os
os.environ["BRAID_WRITE_CACHE"]="0"
"""CPU-only renderer fixture: verify actual draw values across indexed collisions.
Counts describe avoided Cg snapshot copies, not real device FPS.
"""
import ast, ctypes as C, json, os, pathlib, subprocess, sys, tempfile
here=pathlib.Path(__file__).resolve().parent
if len(sys.argv)==1:
    tree=ast.parse((here/'test_direct_bridge.py').read_text())
    mock=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='mock' for t in n.targets))
    mock=mock.replace('return p==(void*)21||p==(void*)37?7007:7008;', 'return ((unsigned long)p&1)?7007:7008;')
    mock+='\nvoid cgDestroyContext(void*p){clobber();}\n'
    with tempfile.TemporaryDirectory() as tmp:
        p=pathlib.Path(tmp);(p/'mock.c').write_text(mock)
        subprocess.run(['gcc','-O2','-shared','-fPIC',str(p/'mock.c'),'-o',str(p/'libGL.so.1')],check=True)
        for lib in ['libCg.so','libCgGL.so','libSDL2-2.0.so.0']:(p/lib).symlink_to('libGL.so.1')
        src=(here/'braid_compat.c').read_text()+'''\nunsigned long long test_revision_hits(void){return braid_revision_hits;}
unsigned long long test_value_hits(void){return braid_value_hits;}
'''
        (p/'test.c').write_text(src)
        subprocess.run(['gcc','-shared','-fPIC','-O2','-fno-builtin','-I'+str(here),str(p/'test.c'),'-ldl','-o',str(p/'new.so')],check=True)
        results=[]
        for revision in ['0','1']:
            r=subprocess.run([sys.executable,__file__,str(p)],env={**os.environ,'LD_LIBRARY_PATH':str(p),'BRAID_REVISION_CACHE':revision,'BRAID_DIRECT_BRIDGE':'1','BRAID_VALUE_CACHE':'1'},capture_output=True,text=True)
            assert r.returncode==0,r.stderr
            results.append(json.loads(r.stdout))
        assert results[0]['draws']==results[1]['draws']==10000
        assert results[0]['uploads']==results[1]['uploads']
        assert results[0]['copies']==20000,results
        assert results[1]['copies']==0 and results[1]['revision_hits']==20000,results
        print('PASS 10000 draws across32 shader pairs (including hash collisions):',results)
        print('PASS changing values, GPU clobbers, mode transitions, managed textures, resource reload, program/context destruction and reused handles')
else:
    p=pathlib.Path(sys.argv[1]);g=C.CDLL(str(p/'libGL.so.1'));s=C.CDLL(str(p/'new.so'))
    s.test_revision_hits.restype=s.test_value_hits.restype=C.c_ulonglong
    def bind(i):
        # Eight collisions per index, including stage-index collisions.
        v,f=21+1024*i,36+1024*i
        s.cgGLEnableProfile(7007);s.cgGLBindProgram(C.c_void_p(v));s.cgGLEnableProfile(7008);s.cgGLBindProgram(C.c_void_p(f))
    def draw():s.glDrawArrays(4,0,6)
    def context(mode=4133,managed=0):
        s.cgSetParameterSettingMode(C.c_void_p(1),mode);s.cgGLSetManageTextureParameters(C.c_void_p(1),managed)
    context()
    for i in range(64):bind(i%32);draw()
    before=[g.metric(i) for i in range(7)];copies=s.test_value_hits();hits=s.test_revision_hits()
    for i in range(10000):
        bind(i%32)
        # A setter for an unreflected parameter dirties the global Cg epoch.
        s.cgSetParameter2fv(C.c_void_p(103),(C.c_float*2)(i,i+1));draw()
    after=[g.metric(i) for i in range(7)]
    result=dict(draws=after[0]-before[0],uploads=after[2]-before[2],copies=s.test_value_hits()-copies,revision_hits=s.test_revision_hits()-hits)
    # Draw validation in the mock aborts on any stale matrix/tint/sampler.
    for i in range(64):
        bind(i%32);s.cgSetParameter4fv(C.c_void_p(101),(C.c_float*4)(i/100,.3,.4,.5));draw()
    context(4132);bind(0);draw()
    s.cgSetParameter4fv(C.c_void_p(101),(C.c_float*4)(.1,.2,.3,.4));draw()
    context(4133,1);bind(4);draw();s.cgUpdateProgramParameters(C.c_void_p(21+1024*4));draw()
    context();bind(0);draw();s.cgGLLoadProgram(C.c_void_p(21));draw()
    s.cgDestroyProgram(C.c_void_p(21));bind(0);draw()
    # All parameter/program identities reused in a fresh context. It starts in
    # immediate mode: old deferred/managed metadata must not survive teardown.
    s.cgDestroyContext(C.c_void_p(1));bind(0);draw()
    s.cgSetParameter4fv(C.c_void_p(101),(C.c_float*4)(.9,.8,.7,.6));draw()
    context();bind(1);draw()
    print(json.dumps(result))
