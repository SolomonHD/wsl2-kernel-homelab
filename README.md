# WSL2 kernel homelab catalog

Reproducible custom Microsoft WSL2 kernel records for WireGuard, IPv6, Docker, and CONNMARK
homelab workloads.

This repository tracks OpenSpec requirements, per-tag config fragments and normalized configs,
manifests, checksums, documentation, validation reports, and release metadata. Microsoft kernel
source stays in a separate pristine shallow clone. Kernel images and modules VHDX files are never
committed here; validated binaries are distributed as GitHub Release assets.

## Support matrix

Lifecycle status is evidence, not aspiration:

- `planned`: identity and intended config exist; no build is available.
- `built`: paired kernel and modules exist and build evidence passes; runtime use is unproven.
- `validated`: build and runtime acceptance pass; publication may proceed.
- `published`: the validated assets and checksums were reconciled with a GitHub Release.
- `failed`: a build or validation stage failed and records its stage and reason.

Only `published` rows offer normal downloads. A planned or built row is not supported for homelab
deployment.

<!-- BEGIN GENERATED SUPPORT MATRIX -->
| Upstream tag | Commit | Kernel release | Status | Validated | Capabilities | Release |
| --- | --- | --- | --- | --- | --- | --- |
| [linux-msft-wsl-6.18.35.2](kernels/linux-msft-wsl-6.18.35.2/) | `1bd4ed3d4ada` | 6.18.35.2-microsoft-standard-WSL2+ | **validated** | 2026-07-13T20:37:40+00:00 | wireguard, ipv6, docker, connmark | Not available |
<!-- END GENERATED SUPPORT MATRIX -->

## Current baseline

[`linux-msft-wsl-6.18.35.2`](kernels/linux-msft-wsl-6.18.35.2/) at Microsoft commit
`1bd4ed3d4ada93738eef3fc2a66b674c640dc326` is the first catalog record. Its unpublished artifacts
are being repackaged with stripped runtime modules and canonical filenames. The record is `built`
until the replacement pair completes runtime revalidation; no normal download is available.

## Quick start

Install the one tooling dependency, validate records, and verify generated documentation:

```bash
python3 -m pip install -r requirements.txt
python3 scripts/catalog.py validate
python3 scripts/catalog.py matrix --check
python3 scripts/check_docs.py
python3 scripts/catalog.py tracked-artifacts
```

Expected output reports one valid catalog record, a matching support matrix, valid documentation,
and no tracked build artifacts. A nonzero exit identifies the record or policy that must be fixed.

For a reproducible local build and paired WSL deployment, follow
[`docs/build-and-deploy.md`](docs/build-and-deploy.md). It creates ignored outputs outside the
Microsoft source worktree. To move from the stock or an older custom kernel, use
[`docs/wsl-kernel-migration.md`](docs/wsl-kernel-migration.md). A release is permitted only after the checks in
[`docs/validation.md`](docs/validation.md) pass and the workflow in
[`docs/release.md`](docs/release.md) completes.

## Repository guide

- [`docs/repository-structure.md`](docs/repository-structure.md): ownership and allowed contents.
- [`docs/manifest-schema.md`](docs/manifest-schema.md): manifest fields and lifecycle transitions.
- [`docs/build-and-deploy.md`](docs/build-and-deploy.md): source, build, modules VHDX, `.wslconfig`, rollback.
- [`docs/wsl-kernel-migration.md`](docs/wsl-kernel-migration.md): compatibility, safe migration, verification, rollback.
- [`docs/validation.md`](docs/validation.md): build and runtime acceptance evidence.
- [`docs/release.md`](docs/release.md): preflight, immutable tags, assets, and reconciliation.
- [`CONTRIBUTING.md`](CONTRIBUTING.md): contributor workflow.
- [`AGENTS.md`](AGENTS.md): automation constraints.

## Downloads and reproducibility

Published binaries live on this repository's [GitHub Releases](https://github.com/SolomonHD/wsl2-kernel-homelab/releases).
Each release must contain the versioned kernel, matching modules VHDX, normalized config,
`manifest.yaml`, and `SHA256SUMS`, with exact Microsoft source provenance. If hosting is unavailable,
the tracked config, manifest, build procedure, and evidence remain sufficient to reproduce a build.

The Microsoft WSL2 Linux kernel is GPL-2.0. Review [`docs/release.md`](docs/release.md) for source and
license obligations before publication.
