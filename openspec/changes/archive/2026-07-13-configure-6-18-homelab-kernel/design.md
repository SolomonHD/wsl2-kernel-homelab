## Context

The Microsoft `linux-msft-wsl-6.18.35.2` configuration already enables the core IPv6, namespace, cgroup, overlayfs, veth, VXLAN, conntrack, NAT, and nftables features required by homelab workloads. WireGuard, CONNMARK, bridge netfilter, iptables, TUN/TAP, and related networking features are configured as modules. A custom WSL2 deployment therefore needs both a kernel image and the exactly matching module tree.

The kernel source remains in a separate shallow clone. This repository owns only the configuration contract, build workflow, documentation, normalized configuration evidence, and build/test manifests.

## Goals / Non-Goals

**Goals:**

- Produce a reproducible x86_64 WSL2 kernel from `linux-msft-wsl-6.18.35.2`.
- Make the WireGuard, IPv6, Docker networking, NAT, and CONNMARK requirements machine-verifiable.
- Preserve the Microsoft WSL2 base configuration and module compatibility.
- Build without dirtying the upstream source clone.
- Produce a kernel image, matching modules VHDX, provenance manifest, and runtime test evidence.

**Non-Goals:**

- Changing Microsoft kernel source or carrying source patches.
- Vendoring kernel source or binary build products in this repository.
- Configuring Windows firewall, WSL mirrored/NAT networking, public DNS, or router port forwarding.
- Pinning Docker daemon configuration or a WireGuard peer topology.
- Supporting ARM64 or kernel lines other than the pinned 6.18 tag in this first change.

## Decisions

### Pin the exact 6.18.35.2 tag and commit

The build will use `linux-msft-wsl-6.18.35.2` at `1bd4ed3d4ada93738eef3fc2a66b674c640dc326`, not the moving `linux-msft-wsl-6.18.y` branch. The source clone will remain shallow and fetch only this tag when necessary.

Alternative considered: use `linux-msft-wsl-6.6.123.2` for a more conservative baseline. It has the same relevant configuration coverage, but 6.18 is Microsoft's current WSL line and is already present in the local shallow clone.

### Layer a small config fragment over Microsoft's WSL config

The implementation will record required symbols in a versioned fragment and merge it over `arch/x86/configs/config-wsl`. The generated configuration will run through `olddefconfig` and a strict symbol-value check before compilation.

Alternative considered: commit a complete hand-maintained `.config`. A full normalized config is useful as build evidence, but using it as the primary input obscures the intentional homelab delta and creates noisy upgrades.

### Retain Microsoft's built-in versus modular split

Core facilities such as IPv6, namespaces, cgroups, overlayfs, VETH, VXLAN, conntrack, NAT, and nftables remain built in. WireGuard, bridge networking, bridge netfilter, CONNMARK/xtables, iptables, TUN, and TAP remain modules. This follows Microsoft's tested configuration, keeps optional features unloadable, and matches tooling that expects to load network modules.

Alternative considered: convert every required network feature to `y` and deploy only a kernel image. That simplifies artifact deployment but diverges further from Microsoft, increases kernel image size, makes module-oriented diagnostics misleading, and can break scripts that expect `modprobe` to load these facilities.

### Treat the kernel and modules VHDX as an inseparable release

Compilation will include modules, install them into a staging tree, and invoke Microsoft's `gen_modules_vhdx.sh` to create `modules.vhdx`. The manifest will bind the kernel image and VHDX using their kernel release and checksums. `.wslconfig` must point at both artifacts.

Alternative considered: install modules separately inside each WSL distribution. The modules VHDX is preferred because WSL supports it globally and it prevents per-distribution module drift.

### Build out of tree and retain only lightweight evidence

All generated files will live under an ignored build/output directory outside the kernel source worktree. The binary kernel and VHDX will not be committed. The final normalized config, manifest, checksums, and runtime results may be copied into this repository under a versioned evidence directory.

## Risks / Trade-offs

- **A required module is omitted from the VHDX** → Validate module presence before packaging and run `modprobe` acceptance checks after deployment.
- **The base config changes when moving to a later 6.18 tag** → Pin both tag and commit, run `olddefconfig`, and fail on any required-symbol drift.
- **Kernel and modules are deployed from different builds** → Record kernel release and checksums in one manifest and validate the module tree before activation.
- **Docker behavior depends on userspace and Windows networking as well as kernel flags** → Separate kernel acceptance tests from Docker daemon, `.wslconfig`, firewall, and port-exposure documentation.
- **Module packaging requires privileged loop-device and filesystem operations** → Keep the privileged step narrow, use Microsoft's script, and verify output ownership and checksums.
- **Building from a shallow detached tag complicates future updates** → Document a deliberate per-tag fetch workflow and create a separate OpenSpec change for each baseline upgrade.

## Migration Plan

1. Create the config fragment, build tooling, and ignored output layout in this repository.
2. Verify or fetch the exact 6.18.35.2 tag in the pristine shallow Microsoft clone.
3. Generate and validate the merged configuration in an out-of-tree directory.
4. Build the kernel and modules, then package the modules VHDX and manifest.
5. Point `.wslconfig` at both artifacts, shut down WSL, and start the test distribution.
6. Run and record the runtime acceptance suite before adopting the build for homelab workloads.
7. Roll back by restoring the prior `.wslconfig` kernel and module paths, or removing both custom paths to return to Microsoft's packaged kernel.

## Open Questions

- The long-term storage location for binary release artifacts is intentionally deferred until the first build establishes their size and release cadence.
- Windows-side networking policy for exposing the WireGuard UDP port and routed IPv6 prefixes will be specified separately from the kernel build.
