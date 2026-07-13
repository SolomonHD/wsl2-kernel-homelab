## 1. Configuration Contract

- [x] 1.1 Add a versioned 6.18 homelab config fragment containing every required built-in and modular `CONFIG_*` value from the capability spec.
- [x] 1.2 Add a machine-readable baseline definition pinning `linux-msft-wsl-6.18.35.2` and commit `1bd4ed3d4ada93738eef3fc2a66b674c640dc326`.
- [x] 1.3 Add a config validation command that reports missing or mismatched required symbols and exits nonzero.
- [x] 1.4 Add automated checks covering successful validation and representative missing, disabled, and wrong-mode symbols.

## 2. Reproducible Build Workflow

- [x] 2.1 Add a build entry point that verifies the separate kernel clone is pristine and at the pinned tag and commit, fetching only that tag at depth one when explicitly requested.
- [x] 2.2 Generate the build `.config` out of tree by merging Microsoft's `arch/x86/configs/config-wsl` with the homelab fragment and running `olddefconfig`.
- [x] 2.3 Run strict config validation before compiling the x86_64 kernel and enabled modules in the out-of-tree build directory.
- [x] 2.4 Install modules into a staging tree and package the matching `modules.vhdx` with Microsoft's `gen_modules_vhdx.sh` workflow.
- [x] 2.5 Emit a manifest containing the tag, commit, kernel release, compiler, timestamp, configuration checksum, kernel checksum, and modules VHDX checksum.
- [x] 2.6 Add ignore rules that prevent kernel images, module staging trees, VHDX files, and other large build outputs from being committed.

## 3. Build and Deployment Documentation

- [x] 3.1 Document prerequisites, the shallow per-tag source workflow, config generation, build commands, expected outputs, and cleanup behavior.
- [x] 3.2 Document `.wslconfig` `kernel` and `kernelModules` configuration, `wsl --shutdown`, activation checks, and rollback to Microsoft's packaged kernel.
- [x] 3.3 Document the boundary between kernel capability and Windows/WSL networking policy for WireGuard UDP exposure and routed IPv6.

## 4. Verification and Evidence

- [x] 4.1 Verify the generated normalized config against every required symbol and retain its checksum with the build manifest.
- [x] 4.2 Complete one clean build of the pinned tag and verify the kernel release matches the module tree packaged in `modules.vhdx`.
- [x] 4.3 Deploy the paired artifacts and record WireGuard module/interface, IPv6 route/rule, and CONNMARK save/restore acceptance results.
- [x] 4.4 Run Docker with overlay storage, start disposable containers, verify bridge connectivity and published-port NAT, and record the results.
- [x] 4.5 Confirm the Microsoft source clone remains clean and shallow after the build, then retain the manifest, normalized config, and test evidence in the specifications repository.
