Braid RGDS+ v0.1.2 integration

Reference: https://github.com/PolluxPT/SteamWorldHeist-RGDSPlus
Reuses the RGDS+ controller mapping and existing physical-volume/exit approach.
Box64 upstream: https://github.com/ptitSeb/box64
GL4ES upstream: https://github.com/ptitSeb/gl4es
Exact source revisions are recorded in BUILD_INFO.json.

Box64 is built with BOX32=ON, ARM64=ON, Release, cross-target aarch64-linux-gnu
with glibc 2.28 minimum via Zig 0.17.0. The source adaptation scripts expect the
upstream checkout at braid-build/box64 relative to their working directory.
Apply patch_box.py, patch_swap.py, then patch_window.py, patch_display.py, patch_keyboard.py and patch_controller.py before configuring.
They force SDL's 32-bit wrapped graphics path to request a native GLES2 context,
resolve SDL GL function queries from GL4ES, flush GL4ES before each swap,
and log rendering/window activity, only when BRAID_RGDS_GLES is enabled.
The compiler wrapper normalizes Zig's assembly CPU spelling to cortex_a55.
Box64 is linked with -Wl,-s to reduce the executable size.

GL4ES: Release, NOX11=ON, NO_GBM=ON and GLX_STUBS=ON, same ARM64/glibc target.
Firmware SDL creates the Wayland EGL context. Explicit LIBGL_EGL and LIBGL_GLES
paths select /lib/libEGL.so.1 and /lib/libGLESv2.so.2.

braid_compat.c builds as an i386 shared library using:
zig cc -target x86-linux-gnu.2.28 -shared -fPIC -O2 -fno-builtin
  braid_compat.c -ldl -o libbraid_compat.so
It provides Wayland-friendly GLX metadata/resolution and an i386 stdout identity
object. Box32's FILE conversion handles the latter. Cg context initialization
was tested through the actual built ARM64 Box32 under QEMU.

The supplied original game binary is preserved. Braid.rgds.x86 is a same-size
copy with its single HOME-NUL string changed to BRHM-NUL. The launcher exports
BRHM to private savedata/home and XDG_DATA_HOME to savedata. No gameplay code,
Cg library, resource package, or audio/music bytes are modified.
GNU libstdc++ and libgcc are i386 Debian bookworm runtime packages. Their package
metadata and hashes are in runtime-packages.json. These are private bundled
runtime copies; the listed packages' corresponding sources are on Debian.

No physical RGDS+ is attached to the build environment. Test results do not
establish real-hardware gameplay or performance.

Replace GL4ES src/glx/glx_stubs.c with glx_stubs_rgds.c before building. It adapts glXGetCurrentContext to native SDL and supplies a display identity for Cg. Other unused GLX operations remain stubs.

The dedicated Box32 build treats glXGetCurrentDisplay as an opaque pointer, avoiding Xlib Display structure conversion on the synthetic Wayland identity.

0.1.1: SDL_GetKeyboardState copies native SDL's 512-scancode state into a static
array in the non-PIE Box32 executable, whose address is below 4GB. Braid invokes
this API on every keyboard input frame. The native SDL state is never truncated
or exposed directly to i386. The optional count is copied as a 32-bit int.
Regression fixture: keyboard_test_native.c maps its state at 0x100800000 in an
isolated test process. keyboard_test_guest.c is the i386 caller. Under QEMU
ARM64, original runtime exits 134 (same error as hardware); patched runtime
passes press/release, stable pointer and NULL-count cases with exit 0.

0.1.2: Adds GOS struct-return wrappers for SDL_GameControllerGetBindForAxis and
SDL_GameControllerGetBindForButton (12-byte native/i386 binding structure, hidden
i386 result buffer and four-byte callee stack adjustment). Corrects emulator
argument placement in the existing GUID-return adapters. Adds variadic LogError
forwarding and MinimizeWindow. All 85 direct SDL imports in this supplied Braid
ELF are present in the wrapper table. Regression fixture verifies 60,000 axis,
button, hat and none binding returns, GUID returns, log varargs and window call.
The old runtime fails resolution; the patched runtime passes under ARM64 QEMU.
The earlier keyboard high-pointer regression is retained. Graphics, game files
and audio settings are unchanged from the hardware-tested v0.1.1 configuration.

0.1.3: After patch_controller.py, apply patch_video.py and patch_video_members.py.
This removes SDL_WINDOW_HIDDEN and adds SDL_WINDOW_SHOWN at creation for the
RGDS-specific path. First swap explicitly shows the window, requests compositor
fullscreen desktop (0x1001), then raises the window. It logs actual window
flags/display/drawable and samples nine RGB points at frames 1/2/3/120 and every
1800 frames, plus viewport/FBO/program/errors. This is not a claim that Braid
rendered correctly: the fixture supplies native SDL stubs and a known GL color
pattern, checking the bridge's presentation calls and diagnostics only.
Prior keyboard/controller fixes and game resources remain unchanged.

0.1.4 canonical snapshots: replace Box64 src/wrapped32/wrappedsdl2.c with
wrappedsdl2_rgds.c and src/wrapped32/wrappedsdl2_private.h with
wrappedsdl2_private_rgds.h. Replace GL4ES src/gl/glstate.c with glstate_rgds.c.
These snapshots include all earlier SDL adaptations. Keep the prior
glx_stubs_rgds.c adaptation and the same build configuration.
The new gl4es_rgds_attach_context creates/activates GL4ES state after the native
SDL context is current, mirroring GLX's NewGLState/ActivateGLState lifecycle.
The default drawable resize hook preserves explicit game clips/letterboxing.
The dedicated runtime assumes Braid's existing single-context rendering path;
these adaptations are not a general SDL multicontext implementation.
Cg profile overrides are NVIDIA's documented CGGL_LATEST_VERTEX_PROFILE=arbvp1
and CGGL_LATEST_FRAGMENT_PROFILE=arbfp1. Shader diagnostics do not consume
cgGetError, preserving the game's handling.
Test_real_renderer.py uses a native host GL4ES build and a real surfaceless
Mesa EGL/GLES2 pbuffer. Baseline state reproduces black pixels after scissor
push/pop; attaching state gives correct dimensions and a red ARB-program quad.
This proves the initialization issue in the isolated renderer path, not a
Braid playthrough or physical RGDS+ rendering.

0.1.5 diagnostic: rebuild braid_compat.c using the same i386 command.
Box32/GL4ES unchanged. test_trace.py is a native host forwarding fixture;
run from package root, adjusting its source path to APPS/Braid_RGDSPlus/source.
No hardware fix claimed. CgGL loaded status and draw states are now logged.

0.1.6 private RGDS+ build (AI-assisted port changes; no upstream PR):
In addition to v0.1.4 snapshots, copy enable_rgds.c to src/gl/enable.c and
getter_rgds.c to src/gl/getter.c in the pinned GL4ES checkout. Changes add
GL_FRAGMENT_PROGRAM_ARB to glIsEnabled and return four GLint components for
GL_COLOR_WRITEMASK, instead of copying four Boolean bytes into one GLint.
The v0.1.5 fragment-disabled trace was a query defect, not proof of disablement.
Rebuild GL4ES with the existing flags and -Wno-error=date-time for Zig.
Box32 binary unchanged. Rebuild braid_compat.c with the same i386 command.
Launcher selects Cg glslv/glslf rather than arbvp1/arbfp1. No backlight writes.
Native Python ctypes display-check.py uses firmware SDL/GLES, fullscreen on
SDL display 0, for five seconds before game launch. Logs backlight node values
read-only and six framebuffer color samples. This is a visibility test; local
readback cannot prove physical panel routing on a remote RGDS+.

Validation: supplied Cg library under qemu-i386 selects GLSL profiles 7007/7008
with documented overrides (GL capability stub), emits GLSL for the actual
premultiplied_alpha.cgfx source extracted locally from the supplied package.
That GLSL was compiled/linked by a native GL4ES build and real Mesa GLES2;
identity matrix, red vertex color and white texture produce RGBA 255,0,0,255.
This isolated shader test does not reproduce the complete CgGL/Box32 game path.
The native firmware-API display checker passed on host SDL offscreen/EGL with
six matching color samples. Launcher fixture verifies probe invocation, GLSL
environment and cleanup. Actual RGDS+ Braid picture remains unverified.
Test scripts reference build paths and privately extracted shaders; these
commercial derived shader files are not added as public source snapshots.

0.1.7 private port change (AI-assisted, no upstream contribution):
Compile braid_compat.c with cg_glsl_pair.h and cg_uniform_bridge.h in its source
include directory. Same i386/glibc2.28 target and original build command.
The shader-pair cache links the real Cg compiled sources using the core GLSL API,
bypassing the proprietary CgGL/GL4ES stage-pairing issue. Uniform reflection maps
compiled _names to referenced Cg source parameters. cgGetParameterValuefr returns
row-major matrix values; the generated vec4 uniform arrays receive those values.
Sampler assignment uses the original cgGLGetTextureEnum result. Generic Cg CPU
updates remain unchanged. Float/vector uniforms and vec4 matrix arrays used by
this supplied Braid are supported; this is not a general replacement Cg runtime.
Caches are process-owned in Braid's single-context lifetime. It intentionally
uploads parameters on each draw to avoid stale values after original CgGL calls.
Box32 and GL4ES ARM64 binaries remain from v0.1.6. Only the i386 compatibility shim
and launcher behavior change. Full game remains private. Hardware test needed.
Local actual-game run reached 125frames and exited0; image evidence at30/120.
Host offscreen capture cropped. A separate full-size QEMU variant crashed,
so the host tests do not establish full-game stability or hardware behavior.

0.1.8 performance cache:
The original Cg setters/update/profile/mode/load/bind calls are forwarded, then
invalidate a monotonically increasing state epoch. A pair may reuse its uniform
values only within the same epoch. Frame presentation also invalidates the epoch.
Original Cg GPU side effects are never assumed absent: after an epoch changes,
the real paired program is rebound and its numeric/sampler values reuploaded.
Repeated unchanged draws skip Cg value reads, sampler lookups, uploads and
redundant program binds. Last-pair pointers avoid repeated linked-list searches.
No game render quality or resolution option changes are made in this revision.

Source build command remains: zig cc -target x86-linux-gnu.2.28 -shared -fPIC
-O2 -fno-builtin braid_compat.c -ldl -o libbraid_compat.so (headers alongside it).
Run test_cache.py with Python/gcc on the host for the old/new forwarding,
coherency and work-count test. baseline017/ contains the previous bridge source.
Set BRAID_TRACE_RENDER=1 for the older per-draw diagnostics; default is off.
SDL_GetTicks measures actual presented-frame intervals, logging every5seconds.
Cumulative counters show reuse; initial loading lowers the first FPS sample.
Tested the timing hook through actual ARM64 Box32/QEMU and a native SDL stub
using test_swap_start.c/native_sdl_stub.c; its fake ticks do not benchmark FPS.
Whole-game host QEMU/Mesa attempts were unstable or too slow to benchmark.
The cache has controlled correctness/ABI validation, not RGDS+ FPS validation.

0.1.9 render-load and frame-pacing trial:
The supplied ELF exports ideal_width/ideal_height data at VAs0x082ef004/008,
file offsets0x2a7004/008. InitOGL enables desktop fullscreen style0x1001.
Its resolution selection independently clamps internal rendering to these ideal
limits while recording the native physical dimensions. The640x480 command-line
window request did not override those ideal limits in this mode. Patch only the
640x360 ideal data values, retaining1280x720 virtual gameplay coordinates and
the original executable. patch_render_limit.py pins source hashes, performs the
existing HOME->BRHM adaptation, and writes a separate output file.

The real decide_resolution function at0x08194f40 was executed in Unicorn with
SDL_GetCurrentDisplayMode stubbed only for display dimensions. Borderless state
matches InitOGL and recorded hardware flags. Results: 1024x576 scene ->640x360,
physical1024x768 unchanged. Smaller display clamp cases pass. The actual command
parser at0x080e9ab0 confirms supported VSync flags. The -30fps cap remains enabled;
-no_vsync/-no_vsync_test are a frame-pacing experiment, not a confirmed cause/fix.
No texture assets, gameplay instruction bytes or timing/physics constants change.

The i386 shim retains the v0.1.8 shader/cache logic. Additional glViewport and
glBindFramebufferEXT forwarding records the largest observed offscreen viewport.
FPS output adds mean time between swaps, mean/max time inside swap, and observed
scene size. Between-swap time includes game frame-cap sleeps; swap duration is
presentation/flush waiting, not an exclusive GPU timer. scene_max=0x0 means no
observed offscreen viewport in that sample, not proof of zero-sized rendering.

hardware-perf.py uses only Python stdlib and reads /proc and selected sysfs
sensor/frequency nodes every5seconds. CPU utilization100% means one busy core;
clock and temperature readings retain raw sysfs units (CPU usuallykHz, devfreq
usuallyHz, thermal usuallymillidegreesC). Availability varies by firmware.
It neither changes governors nor raises frequencies or thermal limits.

The old full-resolution adapted executable is included asBraid.rgds.fullres.x86
for reversible image-quality comparison. For a comparison under the samev0.1.9
pacing/settings, copy it overBraid.rgds.x86. Reapply the new release to restore
640x360. OriginalBraid.bin.x86 remains intact. No new hardware FPS claim is made.


v0.1.10: final quad fild instructions at0x8194da3 and0x8194dad now read
virtual_height/width at0x833b424/420, matching rendering_2d_right_handed.
The640x360 ideal dimensions remain for render target allocation.
Unicorn instruction test verifies full virtual quad and unchanged low-res scene.


v0.1.11 CPU parameter cache
-------------------------
The supplied0.1.10 logs show steady gameplay near30FPS with demanding windows
around25-28FPS and one19.92FPS interval. During most active play, total process
CPU is roughly100-113% (100%=one core), CPU clock1992MHz, GPU load roughly30-50%
at800MHz, and SoC temperature peaks around47.2C. This suggests CPU-side overhead;
it is not an exclusive CPU profiler measurement or proof of one root cause.

cg_value_cache.h snapshots Cg's own row-major getter values. Only game-imported
float2/float4/float4x4 setters with confirmed types/shapes may update snapshots.
Identical setters are omitted only when the context was explicitly observed
inCG_DEFERRED_PARAMETER_SETTING(4133). Immediate/unknown modes still read Cg
and forward setters. Other types/shapes fall back to Cg reads after a setter.
Mode transitions and program destruction invalidate snapshots. All changed
setters and every original CgGL bind/load/commit are forwarded, and existing
state epochs still force GPU refreshes. No GPU-value equality assumptions are
introduced. Sampler enums are cached per reflected uniform until any program
load/destruction. Invalid texture enums are never cached.

BRAID_VALUE_CACHE=0 bypasses these optimizations. The launcher selects this
from runtime/value-cache.txt (1 default,0 fallback); it reads a number without
executing file content. BRAID_PERF appends cumulative value_hits,
setters_skipped,sampler_reads,sampler_hits. parameter_reads now counts actual
Cg getter calls. It does not count CPU snapshot hits.

Run python3 source/test_cache.py for controlled cache/fallback correctness.
Both modes execute3001 draws and3003 GPU uniform uploads in1000 changing
frames. Actual Cg value reads2002->2; original setter calls3000->1001. Tests
also overwrite GPU state, change shader pairs/modes, invalidate on destruction,
and reassign sampler units on load. The launcher fixture tests both config
values, lower-screen0/restore70, monitoring and cleanup.

The i386 shim was rebuilt with the documented Zig target. ARM64 Box32/GL4ES,
firmware SDL path, game executable and assets are unchanged from0.1.10.
No actual Cg/Box32/GPU end-to-end0.1.11 playthrough or device FPS measurement
was performed here; this release requires hardware testing.


v0.1.12 guarded direct shader bridge
----------------------------------
0.1.11 hardware logs show that CPU value caching works (only20 cumulative Cg
reads) but demanding gameplay still drops17-20FPS. The direct path targets
remaining duplicate CgGL backend work, without changing game or display sizes.

Eligibility requires: both GLSL stages present, successful custom link, every
active uniform mapped, successful numeric reads with expected counts, valid
sampler units, both contexts observed in deferred mode, and texture management
explicitly disabled. Unverified pairs retain original behavior. Initial
CgGLLoadProgram and changed-program binds remain original calls. A ready pair
can bypass cgUpdateProgramParameters: its complete parameter set is uploaded
to the actual paired program by our bridge instead. Redundant GLSL profile enables may be skipped after a verified ready pair;
disables clear the tracked enable state. Redundant identical stage
binds may be skipped when CgGL's last actual stage binding still matches.

A separate GPU generation advances for original bind/load/profile/commit calls,
non-deferred setters, mode/texture-management changes and destruction. After
any such event, uniforms are refreshed conservatively. Otherwise, per-program
uniform snapshots can skip identical uploads. Original deferred numeric
setters remain CPU-side and are tracked by the value cache. A swap forces a
fresh program bind on the next draw; uniform objects retain their GL values.
Program destruction also retires paired-program lookup entries to prevent
reuse of stale Cg handles. Entries are reclaimed by process exit.

NVIDIA's Cg3.1 reference describes cgUpdateProgramParameters as applying deferred
parameters to3D API resources and clearing their deferred state; it assumes
that the correct API program has been bound. This port's custom linked pair
already owns actual rendering, so the guarded path uploads its values directly.
Reference: https://developer.download.nvidia.com/cg/Cg_3.1/Cg-3.1_April2012_ReferenceManual.pdf

Tests: source/test_direct_bridge.py compares compatibility/direct modes and an
incomplete-mapping case.1000 changing frames retain3001 draws; original commits
2000->0, original Cg binds2002->3, GPU uploads3003->1005. A separate1000 changing
passes within one frame reduces GPU uploads3000->1000 and custom GL program
binds1000->1. Forced original GPU clobbers, managed textures, immediate mode,
load-time sampler reassignment, pair changes and destruction pass. These are
synthetic counts, not hardware performance predictions. The existing CPU cache
fixture runs with direct mode disabled to preserve its separate comparison.

source/tests/test_actual_cg.c was built fori386 and executed viaqemu-i386 using
the supplied libCg.so:100 changes each of float4 and float4x4 return byte-exact
values from cgGetParameterValuefr. Matrix rows/columns4x4 and vector1x4 match
cache assumptions. This validates Cg value semantics, not GL rendering.

The launcher fixture tests all four combinations of the direct/value switches,
monitor startup, lower-screen off/restoration and cleanup. i386 shim compiled
with the documented Zig target; Box32/GL4ES/game/assets unchanged. No actual
0.1.12 Box32/GLES gameplay or hardware FPS benchmark was performed here.

runtime/direct-bridge.txt1 enables the guarded path;0 retains0.1.11 behavior.
BRAID_PERF appends commits_skipped,binds_skipped,uploads_skipped,profiles_skipped.


v1.0 Final: extend the existing sampler-resource cache to game-imported
cgGLGetTextureEnum queries. Only valid GL_TEXTURE0..31 values are cached;
loads and destruction invalidate through braid_sampler_epoch. value-cache0
bypasses this addition. The direct-bridge fixture verifies query reassignment
after load. The original game executable and all assets/runtime binaries other
than the i386 shim are unchanged. Final addition has no hardware FPS result.


v1.1 performance: known_cg_stage permits deferring backend binds of any
verified stage, including switches to a different ready pair. Logical changes
still dirty the Cg epoch. CgGL bookkeeping is restored before unverified pairs
or forwarded commits, and before initial custom-pair creation if necessary.
Redundant profile enables use verified-stage eligibility rather than transient
intermediate-pair eligibility. This matters between the vertex and fragment
bind calls: the intermediate combination often is never drawn or mapped.
GPU generations remain stable for entirely verified switches; per-GL-program
uniform snapshots and glUseProgram then preserve the intended shader state.
Destroyed Cg handles are also removed from the tracked bound stages.

Test mock now stores GPU uniform values per program. It checks original stage
bindings on every forwarded Cg commit and alternates two verified pairs1000
times. Compatibility:2000 Cg binds/3000 GPU uploads. Direct:0 binds/2 uploads
after warm-up with constant per-pair values. Changes and invalidations still
refresh correctly; incomplete mapping retains compatibility. Synthetic counts
are not hardware performance results. CPU cache fixtures also pass.

Game binary/source symbols confirm loading/JPEG/audio threads; set_processor
is a no-op in this executable. No game main-thread parallelization is claimed.
No startup cache is enabled. Latest logs show roughly35seconds before steady
rendering; translation/compilation/loading are not separately timed.


v1.2: deferred_parameter now independently creates/queries context metadata
for a numeric parameter even when no active paired-program uniform references
it. This prevents deferred CPU-only setters from falsely advancing the GPU
generation. Values are not invented or cached by this metadata-only lookup;
original setters still execute and snapshot validity rules stay intact.
GPU-value preservation additionally requires complete uniform mapping.
The fixture includes an optimized-out float2 parameter:100 setters cause
300 uploads in compatibility and0 in direct mode. Immediate-mode mutations,
GPU clobbers and incomplete mapping retain conservative refresh behavior.
The new test supplements existing alternating-pair and lifecycle tests.
Compiled i386 shim and controlled tests pass; no hardware v1.2 FPS measurement.


v1.3 RC1
--------
New cg_lookup_cache.h memoizes successful Cg parameter-name lookups by live
program and owned name string, and GLSL program profiles. Failed/overlong-name
queries still go to Cg. Bounded4096 name/1024 profile entries; create/destroy
program and destroy-context hooks retire cached identities. The cache shares
the renderer-thread ownership assumptions of the existing paired GLSL bridge.
The pinned game does not mutate shader parameter declarations or array sizes.
No generic cross-thread Cg cache or multicore renderer is claimed.

Binding uses the profile memoizer. Actual SDK calls and hits are logged as
lookup_reads,lookup_hits,profile_reads,profile_hits in BRAID_PERF. Internal CgGL
callbacks that bypass the exported API are not included in those counts.
lookup-cache.txt0 disables this optimization. Fixture1000 repeated successful
queries:1000->1 underlying Cg calls for each query type. Mutable names, missing
queries, long names, destruction and reused identities pass. These are API call
counts, not measured hardware FPS. The draw/parameter fixtures remain intact.

The native library contains LIBGL_PSA_FOLDER support. The launcher redirects
its existing shader archive to savedata/cache/gl4es without changing HOME or
forcing unsupported GPU capabilities. This does not cache Cg compiler work.
No measured startup gain or guaranteed binary-cache support is asserted.
Reference: https://ptitseb.github.io/gl4es/USAGE.html

Read-only hardware monitoring adds per-thread ticks/CPU percentages, names and
last CPU from /proc/PID/task/TID/stat every5seconds. Starttime guards TID reuse;
missing threads are skipped. Existing process/sensor readings are retained.
All8 cache-switch combinations and shader-directory creation pass the launcher
fixture, including lower0/restore70, audio/helper cleanup and monitor startup.

Built with Zig0.17.0 target x86-linux-gnu.2.28 -shared -fPIC -O2 -fno-builtin,
linked libdl. Imported version requirements remain GLIBC2.0/2.1. Original game,
Box32 and ARM64 GL4ES binaries unchanged. No end-to-end RC1 hardware playthrough.


v1.4 Final
----------
RC1 hardware logs:27.7714FPS average across246 windows after startup, min16.58,
max30.07.20,020,675 query hits and5,630,352 underlying name queries; main
thread reaches approximatelyone core. Remaining missing optional queries are
targeted without changing drawing/game logic. No controlled hardware gain
is asserted for this version.

Cache NULL results only for plain identifiers on a program whose GLSL profile
has already been positively validated in profile_buckets. Do not query the
profile after an invalid query: that could duplicate an SDK error callback.
Complex names, invalid/unvalidated programs and disabled modes keep SDK calls.
Program declarations are immutable in the pinned game's API usage. All entries
are bounded and lifecycle-invalidated. Bypass name/profile caching while Cg
creates/loads/destroys programs and destroys contexts to avoid transient metadata.
BRAID_PERF adds cumulative negative_hits. missing-cache.txt0 independently
restores RC1 missing-query behavior. Existing successful-query caches remain.

NVIDIA documents NULL for an absent parameter and an invalid-program error
for an invalid handle. Reference: https://developer.nvidia.com/w/cg/cgGetNamedParameter.html

Actual SDK test: source/tests/test_actual_missing_cg.c includes the exact
lookup header and resolves the supplied libCg.so. It creates a real GLSL
program, verifies a live uniform,1000 absent-name queries with999 cached hits,
compiler bypass and exactlyone error callback for each invalid/destroyed-handle
query. Executed underqemu-i386 with private Debian glibc. This tests Cg query
semantics, not the full Box32/OpenGL rendering stack. No GPU driver replacement,
resolution change, gameplay patch, Box32 rebuild or ARM64 GL4ES change.

Local fixtures: positive/negative lookup, mutable names, missing array names,
invalid handles without extra profile queries, handle reuse and compiler
lifecycle; existing value/draw/direct-path fixtures; monitor fixtures; all16
launcher switch combinations. Build: Zig0.17.0, x86-linux-gnu.2.28, shared PIC
O2 fno-builtin, libdl. Hardware gains and warm startup times remain unmeasured.


v1.5 Performance
----------------
Input hardware evidence: v1.4 session303 windows after two startup samples,
mean27.5864FPS,min18.16,max30.09.11 complete GLSL pairs,5,099,925 draws,
26,324,543 name-cache hits (5,463,430 absent names),104 underlying name reads.
Exit0 and launcher cleanup. Main thread remains CPU-heavy; no controlled
cross-session speedup inferred.

Three CPU bookkeeping changes, no draw/game/scene-resolution change:
1. Direct-mapped256-slot indexes for linked pairs, uniform pairs and verified
   stages. Each hit still compares identities and rechecks readiness, resource
   epoch and context eligibility. Collision/miss falls back to existing list.
   Indexes point into existing process-lifetime records, not copied eligibility.
   Program destruction clears all indexes before identities may be reused.
2. A revision per CPU numeric snapshot and a last-upload revision per uniform.
   Shortcut requires value cache enabled, valid deferred snapshot, correct
   element count, valid uploaded value and the existing complete-pair/GPU-epoch/
   deferred/unmanaged-context preservation guards. Changed setters/readbacks
   increment revisions. Mode/lifecycle changes invalidate snapshots. No cached
   pointer is freed. Falls back to previous copy/memcmp/upload logic otherwise.
   revision-cache.txt0 disables only this shortcut. New BRAID_PERF revision_hits.
3. A256-slot caller-name-pointer memo into the existing bounded owned-name
   table. Pointer equality alone is insufficient: compare the owned name text
   on every hit. Input pointer is never dereferenced later without being passed
   as a current valid query. Changed text, collision or program mismatch takes
   original hash path. Clear memo before lookup entries are freed. Compilation
   bypass, missing-query restrictions and error behavior are retained.
   New BRAID_PERF name_fast_hits; lookup-cache0 disables the entire name cache.

Context destruction now conservatively retires all renderer pair identities,
value/context metadata and indexes, including reused handles in a fresh context.
This is outside the gameplay hot path; it cannot reuse old deferred eligibility.

New test_hotpath.py validates10000 draws through32 pairs with deliberate index
collisions. With revisions off/on: snapshot copies20000->0; GPU uploads0->0
(after warmup); draws10000->10000. Mock draw validates exact matrix/tint/sampler.
Also tests changes, clobbers, context modes, managed textures, resource loads,
program/context destruction and reused handles. These counts are not hardware
FPS. Existing fixtures pass; lookup fixture adds same-pointer mutation/reversion.
Launcher all32 switch combinations pass. Build remains Zig0.17.0,
x86-linux-gnu.2.28 shared PIC O2 fno-builtin linked libdl; imports GLIBC2.0/2.1.
Main loop remains single-threaded. No v1.5 device FPS or startup speed claim.


v1.6 Final
----------
v1.5 supplied hardware session:217 five-second windows after startup;
mean27.607235,min14.42,max30.08FPS.3007271 draws;1866198 revision hits;
14909545 name-pointer fast hits;16965021 query hits,122 underlying name reads.
Exit0, lower-panel disabled and cleanup logged. These are not controlled
cross-session comparisons or evidence of a v1.6 hardware gain.

Buffer changed numeric uniform values only after an original Cg getter and
complete, ready linked-pair mapping have established the exact type/shape.
The SDK must report variability CG_UNIFORM(4102). Supported setters are exactly
the pinned executable's float2,float4,row-major float4x4 APIs. Existing deferred
mode, unmanaged-texture and resource-epoch eligibility guards remain required.
A per-value pending bit/list coalesces repeated writes. The renderer consumes
the same CPU snapshots and revisions, and actual GPU uploads are unchanged.
No draw calls, gameplay updates, scene resolution or frame-pacing code changed.

Flush the latest pending values before each original CgGL bind/commit/profile
operation, any unverified/incomplete-pair draw path, load/create/destroy program,
context destruction, mode/texture-management transition and exported numeric
readback. Conflicting setter shapes flush first. Mode/lifecycle invalidation
happens after the flush. The SDK therefore sees current values at its required
boundaries. Generic Cg parameter connections, effect APIs, declaration mutation,
other setter/readback APIs and multithreaded use are outside this pinned-game
optimization. None are imported by the supplied executable. The numerical
eligibility rules do not authorize skipping SDK work for varying parameters.

runtime/write-cache.txt1 defaults on;0 retains v1.5 changed-setter behavior.
BRAID_PERF logs cumulative writes_deferred,writes_flushed. Existing options,
volume helpers, backlight restoration and save locations are retained.

Integration test_write_cache.py keeps an independent expected-value model and
validates every draw's GPU matrix,tint and sampler.1000 changing frames:
original numeric setters2000->0 while all1000 draws remain; explicit readback
flushes final values.50 queued changes coalesce to1 SDK setter. Checks off/on,
unmapped/varying guards, disabled value/direct paths, immediate/managed modes,
GPU clobbers, creation/load, fallbacks, program/context destruction and reused
handles. Existing exact-count fixtures explicitly exercise write-cache0; new
fixture exercises the new default and its fallbacks.

source/tests/test_actual_write_cg.c includes the exact cache header and resolves
the supplied i386 Cg library. Underqemu-i386,1000 float2 changes,1000 float4
changes and1000 row-major float4x4 changes match CPU snapshots byte-for-byte;
original SDK values remain old until flushing, then match final values exactly.
Each parameter requires one final SDK write; SDK reports no errors. This test
models complete-pair eligibility; GL mocks separately test real eligibility and
GPU data. Neither test is a full hardware rendering benchmark.

All64 launcher combinations pass; previous renderer/query/revision and monitor
fixtures pass. Build:Zig0.17.0,target x86-linux-gnu.2.28,shared PIC O2 fno-builtin,
libdl,GLIBC2.0/2.1 requirements. Native Box32/GL4ES and game binaries unchanged.
No CPU/GPU governor writes, overclock, gameplay skipping or multicore renderer.

Cg reference used to check deferred setting/getter semantics:
https://developer.nvidia.com/w/cg/cgSetParameterSettingMode.html
https://developer.nvidia.com/w/cg/cgSetParameter4fv.html
https://developer.nvidia.com/w/cg/cgGetParameterValuefr.html
