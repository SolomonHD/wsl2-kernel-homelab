# AGENTS.md

This repository is the lightweight OpenSpec and release-record catalog for custom WSL2 homelab
kernels. It tracks specifications, exact-tag config fragments and normalized configs, manifests,
checksums, documentation, validation evidence, and release metadata.

## Non-negotiable boundaries

- Keep Microsoft kernel source in a separate pristine shallow `microsoft/WSL2-Linux-Kernel` clone.
- Never copy kernel source, a build tree, kernel image, module staging tree, or VHDX into this repo.
- Store generated binaries only in ignored output paths and validated GitHub Release assets.
- Key every record by the exact `linux-msft-wsl-*` upstream tag and full commit.
- Prefer config-only changes. Propose and justify any patch, store it as a patch artifact, and include
  it with release source provenance; never edit the upstream clone in place.
- Treat the kernel and matching modules VHDX as one build and deployment unit.

## Required workflow

1. Create or update an OpenSpec change before implementing a kernel configuration decision.
2. Copy `kernels/_template/` to `kernels/<upstream-tag>/`; use only required record filenames.
3. Keep unknown planned fields explicit as null and follow `planned → built → validated → published`.
4. On a failed stage, use `failed` and record both the stage and reason before resuming work.
5. Generate config out of tree, run `olddefconfig`, strictly verify required symbols, and retain its
   complete normalized snapshot and checksum.
6. Install runtime modules with `INSTALL_MOD_STRIP=1`, verify staged `.ko` files have no `.debug*`
   sections, and record artifact names, byte sizes, and checksums.
7. Require build and runtime `PASS` evidence for WireGuard, IPv6, Docker/overlayfs/bridge/NAT, and
   CONNMARK before `validated`.
8. Run release preflight before tags or releases. Exact mirrored tags are immutable; corrected builds
   use the next `-homelab.<revision>` suffix and supersession notes.
9. Mark `published` only after remote release and required assets are confirmed.

Run the commands in [`CONTRIBUTING.md`](CONTRIBUTING.md) before completion. Regenerate the README
matrix with `python3 scripts/catalog.py matrix` after manifest edits. Never bypass a failing catalog,
documentation, tracked-artifact, release, test, or strict OpenSpec validation.

Detailed policies live in [`docs/repository-structure.md`](docs/repository-structure.md),
[`docs/build-and-deploy.md`](docs/build-and-deploy.md), [`docs/validation.md`](docs/validation.md), and
[`docs/release.md`](docs/release.md). Migration and pairwise rollback live in
[`docs/wsl-kernel-migration.md`](docs/wsl-kernel-migration.md).
