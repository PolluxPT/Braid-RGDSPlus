# Changelog

## 1.6.0

- Buffered changing numeric shader uniforms in the verified paired-GLSL path; flush current SDK values at compatibility, readback and lifecycle boundaries.
- Added an independent `write-cache.txt` fallback setting and `writes_deferred` / `writes_flushed` telemetry.
- Preserved full-size top-screen rendering, 640×360 internal scene cap, physical volume support, lower-screen shutdown and save paths.
- Public port-only packaging, owned-game preparation tool, pinned runtime acquisition, source, license notices and host regression checks.

Local validation: 1,000 changing frames retain all draws and exact GPU values while avoiding 2,000 original numeric Cg setter calls during those frames. Tests against the supplied Cg library preserve exact float2, float4 and matrix values. All 64 launcher setting combinations pass. These are validation results, not a measured hardware FPS gain; 30 FPS remains a target.
