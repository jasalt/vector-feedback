
# Picture Plane

An interactive **Jolt + [Slipstream](https://github.com/jlt-commons/slipstream)** vector-feedback instrument. A rectangular picture plane and crosshair are injected into a feedback loop; previous frames are repeatedly reprojected through a movable pinhole camera, faded, and colored by age.

Pan, dolly, roll, yaw, and pitch produce spirals, tunnels, and keystone distortion. Camera changes propagate through existing feedback rather than replacing it with a newly generated static stack.

https://github.com/user-attachments/assets/95a155ef-22c5-4353-a9a2-a4f93ed8ab40

## Build and run

Requires Jolt **0.8.23+**, Git, CMake, a C++20 compiler, Python 3 (GLAD generation), pkg-config, FreeType development headers, and OpenGL. Linux also needs GLFW's X11/Wayland development dependencies. CMake fetches GLFW, GLAD, and msdfgen; the setup script fetches pinned Slughorn sources and its JSON submodule. First build requires network access.

```sh
bash scripts/setup.sh
jolt -M:run
```

For a source checkout of Jolt, set `JOLT=/absolute/path/to/jolt/bin/jolt` when running setup, then use that executable in place of `jolt`. Set `SLUGHORN_HOME` to reuse an existing complete Slughorn checkout; otherwise setup uses `.cache/slughorn`.

The program detects common Linux/macOS fonts. If necessary:

```sh
jolt -M:run --font /absolute/path/to/font.ttf
```

Or set `SLIPSTREAM_TEST_FONT`.

## Controls

| Input | Camera adjustment |
|---|---|
| Left drag | Horizontal / vertical translation |
| Right drag | Yaw / pitch (perspective tilt) |
| Middle drag | Roll |
| Mouse wheel | Dolly / magnification |
| Space | Pause / resume feedback |
| R | Reset camera and clear feedback |
| Close window | Quit |

Drag adjustments are relative and remain set after release. The initial camera has a gentle shrink, roll, and tilt, so feedback starts without interaction. A mouse with three buttons is recommended. Camera parameters remain editable while paused; feedback resumes with the new settings.

## Verification

Pure math, temporal-history, input, and shader-uniform tests need no graphics libraries or native build:

```sh
jolt -M:test
```

Deterministic rendering smoke test (65 render frames, then quit):

```sh
jolt -M:run --frames 65 --capture frame.ppm
# On headless Linux with Mesa and Xvfb installed:
xvfb-run -a jolt -M:run --frames 65 --capture frame.ppm
```

Capture is a top-down RGB PPM. Timed runs advance one feedback tick per rendered frame; normal interactive runs use elapsed time with bounded catch-up.

## Implementation

- `src/feedback/model.clj`: pure camera homographies, input, and bounded 30 Hz temporal simulation.
- `src/feedback/visuals.clj`: Slipstream scene, projective vector coverage shader, and control readout.
- `src/feedback/main.clj`: native window/input lifecycle and optional capture.

The loop retains 48 vector-frame homographies. Each tick applies the current camera to all surviving frames and injects a new rectangle. Slipstream renders a single immutable vector quad; typed `mat3` uniforms inverse-project each pixel into each retained frame, where rectangle/crosshair coverage is analytically antialiased. Geometry/atlases are not rebuilt every frame, and the normal loop performs no framebuffer readback.

This is **vector feedback**, not a webcam feed or recursive framebuffer texture effect: vectors remain crisp under reprojection, history is finite (1.6 seconds), and there is no raster blur or external video input. The camera controls describe the per-pass feedback transform, as in a camera pointed at its own monitor.
