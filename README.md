# wsl2-kernel-homelab

Custom WSL2 Linux kernel builds for homelab self-hosting.

## Why?

The stock Microsoft WSL2 kernel works for general use, but homelab and self-hosting workloads often need features that aren't enabled by default or need patches:

- **Docker Desktop compatibility** — kernel configs that play nice with Docker Desktop's integration
- **IPv6 support** — full IPv6 networking inside WSL2
- **WireGuard** — kernel-level WireGuard VPN support
- **General self-hosting** — additional modules and tunings for running services, containers, and network utilities

This repo uses [OpenSpec](https://openspec.dev/) to track specs and changes against the upstream [microsoft/WSL2-Linux-Kernel](https://github.com/microsoft/WSL2-Linux-Kernel) repository. The kernel source code itself is **not** stored here — only the planning, specs, and change history for custom builds.

## How It Works

1. The upstream kernel is cloned shallowly (no full history, no tags)
2. Specific kernel version tags are fetched on demand
3. OpenSpec tracks what changes we make and why
4. Build instructions and kernel configs are documented in specs

```bash
# Clone the upstream kernel (shallow, no tags)
TAG="linux-msft-wsl-6.6.87.0" && git clone --depth=1 --no-tags https://github.com/microsoft/WSL2-Linux-Kernel.git

# Or if already cloned, fetch a specific tag
cd WSL2-Linux-Kernel
TAG="linux-msft-wsl-6.6.87.0" && git fetch --depth=1 origin tag "$TAG"
git checkout "$TAG"
```

## OpenSpec

This repo is an [OpenSpec store](https://openspec.dev/docs/customization) — a standalone repository for specifications and change tracking. The `openspec/` directory contains:

- `specs/` — source of truth for kernel build configurations and features
- `changes/` — proposed and archived changes to the kernel config

To work with these specs locally:

```bash
npm install -g @fission-ai/openspec
openspec store setup wsl2-kernel-homelab --path /path/to/this/repo
openspec list --store wsl2-kernel-homelab
```

## Upstream

- Source: [microsoft/WSL2-Linux-Kernel](https://github.com/microsoft/WSL2-Linux-Kernel)
- Tags: [Releases](https://github.com/microsoft/WSL2-Linux-Kernel/tags)

## License

The WSL2 Linux Kernel is licensed under GPL-2.0. This repo contains only specs and documentation.
