from pathlib import Path
# Cg sees an opaque SDL/EGL identity, never an Xlib Display structure.
for name in ['wrappedlibgl_private.h','wrappedlibglx_private.h','wrappedlibglxnvidia_private.h']:
 p=Path('braid-build/box64/src/wrapped32')/name
 s=p.read_text();s=s.replace('GO(glXGetCurrentDisplay, XFv)','GO(glXGetCurrentDisplay, pFv)');p.write_text(s)
