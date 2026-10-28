# Resolving Slipstream's FreeType dependency with Nix

## Problem

Running the application on Fedora with Nix-provided Jolt can fail with:

```text
required native library slipstream did not load — ./native/libslipstream.so
is there but did not load: libfreetype.so.6: cannot open shared object file:
No such file or directory
```

The native Slipstream library was built in the Fedora VM against Fedora's FreeType. It declares a dependency on `libfreetype.so.6`, but has no embedded runtime search path for it. The Nix runtime does not automatically discover Fedora libraries in `/usr/lib64`, even when the host's `freetype` package is installed.

`nix run` supplies Jolt's packaged dependencies; it does not automatically package dependencies of native libraries loaded from the application workspace.

## Recommended upstream solution: package Slipstream with Nix

Slipstream should provide a Nix derivation for its native library that:

1. Pins Slughorn and the other native sources, including required submodules.
2. Supplies FreeType and the native compiler from the same Nix package set.
3. Declares the platform-specific window-system and OpenGL build dependencies.
4. Uses fixed, declared sources instead of downloading dependencies during the sandboxed CMake build. CMake's fetched dependencies should be supplied through Nix sources or packaged alternatives.
5. Installs the native library into the package output's `lib` directory.
6. Retains Nix's normal ELF fixup so runtime paths resolve FreeType and other linked dependencies from the Nix store.

The result should resolve FreeType through a path such as `/nix/store/…-freetype/lib`, independently of Fedora's installed packages. The exact package inputs and CMake overrides need to be verified against Slipstream's current native build; this document is a proposal, not an implemented derivation.

Slipstream should also expose a development shell for building its native library and running examples, and test loading the installed library without a manually configured `LD_LIBRARY_PATH`.

## Application integration

This application can then provide a flake that combines Jolt with the packaged Slipstream library:

```sh
nix run .
```

The launcher must explicitly select the packaged native library, rather than accidentally loading a stale Fedora-built `native/libslipstream.so` from the workspace. That selection should use Jolt's supported native-library configuration or a deliberate launcher/staging arrangement, verified against the current Jolt implementation.

No manual Fedora library search path should be necessary. Interactive rendering still requires access to the host display and compatible graphics drivers; packaging FreeType does not by itself solve Nix/non-Nix OpenGL driver integration.

## Jolt improvements

Jolt should distinguish these failures in its native-library diagnostics:

- The requested library does not exist.
- The requested library exists but could not load because a dependency is missing.
- The requested library or a dependency has an incompatible architecture or ABI.

Preserving the dynamic loader's error and reporting the attempted library path makes the second case actionable. Where practical, diagnostics could suggest inspecting ELF dependencies and runtime paths:

```sh
readelf -d native/libslipstream.so | grep -E 'NEEDED|RPATH|RUNPATH'
ldd native/libslipstream.so
```

Use `ldd` only on trusted binaries. Its results reflect the inspecting process's loader environment, which may differ from the Nix-launched process.

Jolt should not automatically add `/usr/lib64`: doing so mixes Fedora and Nix runtimes and can introduce C++, glibc, or other ABI conflicts.

## Temporary Fedora workaround

For the current Fedora-built library, run from the application directory:

```sh
LD_LIBRARY_PATH=/usr/lib64${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH} \
  nix run 'git+https://github.com/jolt-lang/jolt.git?submodules=1' -- -M:run
```

The host must have FreeType installed:

```sh
sudo dnf install freetype
```

This is a quick-start workaround, not a portable packaging solution. It may expose further compatibility problems if the VM, host, and Nix runtimes differ.

## Non-Nix distribution

For ordinary native builds, Slipstream should document runtime dependencies and consider platform packages or appropriately bundled binaries. A runtime search path alone does not make a VM-built binary portable: it must identify libraries that exist and are ABI-compatible.
