## Why

Deploying the validated `linux-msft-wsl-6.18.35.2` kernel exposed migration steps that the current
guide does not cover: WSL must be current enough to accept `kernelModules`, the obsolete
`automount.crossDistro` setting must be removed, and the kernel and modules must be activated as a
pair. Publication is also blocked because the current 2.74 GiB modules VHDX exceeds GitHub
Releases' per-file limit.

## What Changes

- Add a concise migration guide for users moving from the stock or an older custom WSL kernel,
  including WSL update/version checks, targeted `wsl.conf` cleanup, paired `.wslconfig` settings,
  activation verification, and rollback.
- Strip debug information from installed runtime modules before generating the modules VHDX, then
  rebuild and revalidate the paired artifacts.
- Add release preflight enforcement for GitHub's strict per-asset size limit and record artifact
  sizes so an oversized release fails locally before publication.
- **BREAKING** Rename the kernel image artifact from
  `bzImage-linux-msft-wsl-6.18.35.2` to `linux-msft-wsl-6.18.35.2`; remove the `bzImage-` prefix
  from generated filenames, manifests, documentation, checksums, tests, and release expectations.
- Keep the modules artifact separately named `modules-linux-msft-wsl-6.18.35.2.vhdx` and preserve
  the requirement that the kernel image and modules VHDX are deployed and rolled back together.
- Retain GitHub Releases as the primary publication channel; do not wrap the VHDX in GitHub
  Packages or commit either binary to Git.

## Capabilities

### New Capabilities

- `wsl-kernel-migration`: Defines a safe, copyable migration from a stock or older custom WSL
  kernel to the catalog kernel/modules pair.

### Modified Capabilities

- `wsl2-kernel-build`: Requires stripped runtime modules, the simplified kernel image filename,
  and paired deployment verification on an updated WSL installation.
- `versioned-kernel-catalog`: Records and validates artifact byte sizes and the simplified kernel
  artifact name without weakening exact tag, checksum, or lifecycle identity.
- `validated-kernel-release`: Rejects oversized release assets and publishes the simplified kernel
  filename with the matching modules VHDX through GitHub Releases.
- `repository-guidance`: Exposes the migration path alongside the existing build, deployment,
  validation, and release documentation.

## Impact

- Build and packaging logic in `scripts/build_kernel.py` and `scripts/release.py`.
- Manifest schema, catalog validation, fixtures, release expectations, and generated support data.
- The validated `linux-msft-wsl-6.18.35.2` artifact checksums and evidence, which must be regenerated
  after stripping and renaming before publication.
- User documentation, examples, rollback guidance, and documentation validation.
- No Microsoft kernel source changes, source patches, Git LFS objects, or GitHub Packages artifacts.
