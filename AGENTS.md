# AGENTS.md

This file provides guidance to AI coding agents working in this repository.

## Repository Purpose

This is an **OpenSpec store** — a standalone specifications repository for tracking custom WSL2 kernel builds for homelab self-hosting. It does **not** contain kernel source code.

The actual kernel source lives in the upstream [microsoft/WSL2-Linux-Kernel](https://github.com/microsoft/WSL2-Linux-Kernel) repository, which is expected to be cloned separately and kept as a pristine shallow clone. This repo tracks what changes we make to the kernel config and why.

## Key Principles

1. **No kernel source in this repo** — only specs, changes, configs, and documentation
2. **Upstream stays pristine** — the WSL2 kernel clone should be shallow (`--depth=1 --no-tags`) with specific tags fetched on demand
3. **Spec-driven workflow** — all kernel build decisions are documented as OpenSpec specs before implementation
4. **Homelab focus** — changes should serve self-hosting use cases: Docker Desktop, IPv6, WireGuard, networking, and container workloads

## OpenSpec Workflow

This repo uses [OpenSpec](https://openspec.dev/) for spec-driven development. Key commands:

```bash
# Initialize OpenSpec in this repo
openspec init

# Create a new change (e.g., "enable-wireguard")
openspec new change enable-wireguard

# List active changes
openspec list

# Archive a completed change
openspec archive enable-wireguard
```

### Typical Change Flow

1. `openspec new change <name>` — scaffold the change
2. AI drafts proposal, specs, design, and tasks via `/opsx:propose`
3. Review and refine artifacts
4. Implement in the separate kernel clone
5. `openspec archive <name>` — finalize and merge specs

## Working with the Upstream Kernel

The upstream kernel is managed separately:

```bash
# Initial shallow clone (no history, no tags)
git clone --depth=1 --no-tags https://github.com/microsoft/WSL2-Linux-Kernel.git

# Fetch a specific tag when needed
TAG="linux-msft-wsl-6.6.87.0" && git fetch --depth=1 origin tag "$TAG"
git checkout "$TAG"
```

Never commit kernel source code to this repo. Kernel config files (`.config`) may be committed as artifacts within OpenSpec changes.

## File Structure

```
openspec/
├── specs/           # Source of truth — what the custom kernel includes
│   └── <domain>/
│       └── spec.md
├── changes/         # Proposed and archived changes
│   ├── <change-name>/
│   │   ├── proposal.md
│   │   ├── design.md
│   │   ├── tasks.md
│   │   └── specs/
│   └── archive/
└── config.yaml      # OpenSpec configuration
```

## Domains (Expected)

- `docker-desktop` — Docker Desktop compatibility and container runtime support
- `networking` — IPv6, WireGuard, and advanced networking features
- `kernel-config` — General kernel configuration changes and module enablement
- `selfhosting` — Self-hosting specific tunings and features

## Contributing

1. Create an OpenSpec change documenting what and why
2. Implement the kernel config changes in a separate kernel clone
3. Test the built kernel
4. Archive the change with the resulting config

## Tools

- [OpenSpec](https://openspec.dev/) — spec-driven development framework
- [Git](https://git-scm.com/) — version control for specs and changes
- The upstream kernel is built using standard Linux kernel build tooling (make, gcc, etc.) in a separate clone
