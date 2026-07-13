## 1. Manifest and Catalog Contract

- [x] 1.1 Advance the manifest schema and template to version 2 with nullable artifact `size_bytes`
  fields for planned records and required positive sizes for built records.
- [x] 1.2 Enforce canonical artifact names: kernel `<upstream-tag>` and modules
  `modules-<upstream-tag>.vhdx`, rejecting the legacy `bzImage-` prefix.
- [x] 1.3 Allow `validated -> built` only for unpublished artifact replacement, clear stale runtime
  validation on that transition, and continue rejecting backward transitions from `published`.
- [x] 1.4 Update catalog fixtures, schema documentation, and unit tests for artifact names, sizes,
  schema migration, and the constrained revalidation transition.

## 2. Stripped Build Artifacts

- [x] 2.1 Change the kernel build output name to the exact pinned tag
  `linux-msft-wsl-6.18.35.2` throughout build generation, evidence, and manifest updates.
- [x] 2.2 Install the matching runtime modules with `INSTALL_MOD_STRIP=1` before invoking Microsoft's
  `gen_modules_vhdx.sh`, without changing the normalized `CONFIG_*` selections.
- [x] 2.3 Record the exact byte sizes and SHA-256 digests of the kernel and modules VHDX in build
  evidence and the schema-version-2 manifest.
- [x] 2.4 Add build tests or deterministic checks proving staged `.ko` files lack `.debug*` sections,
  the module release matches `make kernelrelease`, and the source clone remains shallow and pristine.

## 3. Release Packaging and Size Gates

- [x] 3.1 Update release packaging, notes, tag annotations, expected assets, and reconciliation to use
  `linux-msft-wsl-6.18.35.2` with no `bzImage-` prefix.
- [x] 3.2 Validate packaged asset sizes against manifest `size_bytes` and reject every individual
  asset at or above `2147483648` bytes before tag creation or remote publication.
- [x] 3.3 Add release tests for a valid stripped VHDX, manifest-size mismatch, exact 2 GiB boundary,
  oversized asset, legacy kernel filename, and retry-safe remote reconciliation.
- [x] 3.4 Update release documentation to retain GitHub Releases as the binary channel and explain
  why GitHub Packages, Git LFS, and committed binaries remain out of scope.

## 4. WSL Migration Guidance

- [x] 4.1 Add a focused migration guide with `wsl --version`, `wsl --update`, WSL 2.7.10.0 tested
  baseline, shutdown semantics, and a warning that `.wslconfig` affects every WSL2 distribution.
- [x] 4.2 Document backup and targeted removal of only `automount.crossDistro` from `/etc/wsl.conf`,
  preserving every supported setting and treating an absent key as a no-op.
- [x] 4.3 Document download and checksum verification, stable Windows paths, paired `kernel` and
  `kernelModules` configuration, restart, `uname`, `/lib/modules`, `modinfo`, and `modprobe` checks.
- [x] 4.4 Add pairwise rollback instructions and link the migration guide from the README, build and
  deployment guide, per-tag record, contributor guidance, and relevant OpenSpec references.
- [x] 4.5 Extend documentation validation to catch the removed `bzImage-` artifact name, unsupported
  migration examples, broken migration links, and guidance that edits `wsl.conf` too broadly.

## 5. Baseline Rebuild and Revalidation

- [x] 5.1 Transition the unpublished `linux-msft-wsl-6.18.35.2` record from `validated` to `built`,
  clear stale runtime acceptance, and retain the exact upstream tag and commit.
- [x] 5.2 Perform a clean out-of-tree config merge and `olddefconfig`, strictly validate the complete
  normalized configuration, and confirm no intended `CONFIG_*=y` or `CONFIG_*=m` value changed.
- [x] 5.3 Build `linux-msft-wsl-6.18.35.2` and the stripped matching modules VHDX, confirm both are
  below the release limit, and update manifest sizes, checksums, and build evidence.
- [x] 5.4 Deploy the renamed kernel/modules pair on updated WSL and rerun WireGuard, IPv6, Docker,
  overlayfs, bridge/NAT, and CONNMARK runtime acceptance with cleanup.
- [x] 5.5 Record the WSL, Windows, distribution, tool versions, artifact identities, and runtime
  results, then return the record to `validated` only after every acceptance check passes.

## 6. Repository Verification

- [x] 6.1 Regenerate the README support matrix and run catalog, manifest, documentation, tracked
  artifact, release preflight, and strict OpenSpec validation.
- [x] 6.2 Run the full Python test suite and verify no kernel source, build tree, kernel image, modules
  staging tree, VHDX, or distribution archive entered Git history.
- [x] 6.3 Run a release dry plan and confirm the exact filenames, byte sizes, checksums, notes, and
  post-publication reconciliation without creating a tag or mutating GitHub.
