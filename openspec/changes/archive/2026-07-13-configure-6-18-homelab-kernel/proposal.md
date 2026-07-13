## Why

Homelab workloads in WSL2 need a reproducible kernel baseline with WireGuard server support, complete IPv6 routing, Docker-compatible container networking, and CONNMARK-based packet marking. The Microsoft configuration enables many of these features as modules, so a custom kernel image alone is insufficient unless the matching modules are also built, packaged, and deployed.

## What Changes

- Pin the first homelab build to `linux-msft-wsl-6.18.35.2` from `microsoft/WSL2-Linux-Kernel`.
- Define the exact `CONFIG_*` values required for WireGuard, IPv6, namespaces and cgroups, overlay networking, netfilter/NAT, and CONNMARK.
- Preserve Microsoft's module-oriented configuration and require a matching modules VHDX alongside the kernel image.
- Define reproducible shallow-tag acquisition, configuration validation, build outputs, provenance, and runtime verification.
- Keep upstream kernel source and source patches outside this specifications repository.

## Capabilities

### New Capabilities

- `homelab-kernel-config`: Defines the pinned WSL2 kernel baseline and the required kernel configuration contract for WireGuard, IPv6, Docker, and CONNMARK workloads.
- `wsl2-kernel-build`: Defines how the pristine shallow source clone is prepared, built, packaged, and verified as a kernel image plus matching modules VHDX.

### Modified Capabilities

None.

## Impact

- Adds the first source-of-truth specifications for the homelab WSL2 kernel.
- Establishes `linux-msft-wsl-6.18.35.2` as the initial build baseline.
- Future implementation will read the separate `WSL2-Linux-Kernel` clone and produce build artifacts without committing kernel source here.
- Deployment will require both `.wslconfig` `kernel` and `kernelModules` paths.
