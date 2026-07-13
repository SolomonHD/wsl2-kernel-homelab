## 1. Catalog Foundation

- [x] 1.1 Add the `kernels/<upstream-tag>/` directory contract and a reusable catalog-entry template with the required config, manifest, and validation paths.
- [x] 1.2 Define and document the versioned `manifest.yaml` schema, including lifecycle, upstream identity, build, config, artifact, validation, and publication fields.
- [x] 1.3 Add a manifest and directory validator that rejects malformed tag names, missing required files, invalid statuses, illegal lifecycle transitions, and inconsistent checksums or release metadata.
- [x] 1.4 Add catalog tooling that generates or verifies the repository support matrix from manifests.
- [x] 1.5 Add ignore rules and a validation check preventing kernel images, VHDX files, module staging trees, and build directories from entering Git history.

## 2. Initial 6.18 Catalog Entry

- [x] 2.1 Create `kernels/linux-msft-wsl-6.18.35.2/` with a planned manifest pinned to commit `1bd4ed3d4ada93738eef3fc2a66b674c640dc326`.
- [x] 2.2 Add the homelab config fragment path and normalized config placeholder, then connect their final values and checksums to the `configure-6-18-homelab-kernel` change outputs.
- [x] 2.3 Add build and runtime validation report templates covering exact tag identity, `olddefconfig`, kernel/modules matching, WireGuard, IPv6, Docker, and CONNMARK.
- [x] 2.4 Add the initial catalog entry to the generated support matrix without presenting it as validated or downloadable.

## 3. Repository Documentation

- [x] 3.1 Rewrite the root README with repository boundaries, the current 6.18 example, support matrix, lifecycle states, downloads, quick start, and links to detailed workflows.
- [x] 3.2 Add repository-structure documentation describing `kernels/`, `docs/`, `scripts/`, `openspec/`, build outputs, and ownership of each file class.
- [x] 3.3 Add build and deployment documentation covering the pristine shallow clone, per-tag fetch, config merge, `olddefconfig`, kernel/modules build, modules VHDX, `.wslconfig`, and rollback.
- [x] 3.4 Add validation documentation defining required build evidence and WireGuard, IPv6, Docker, overlayfs, bridge/NAT, and CONNMARK runtime acceptance.
- [x] 3.5 Add release documentation covering gates, annotated mirrored tags, corrected build suffixes, required assets, checksums, source provenance, and publication reconciliation.
- [x] 3.6 Add `CONTRIBUTING.md` and reconcile `AGENTS.md` with the catalog, binary-storage, source-clone, validation, and release policies.
- [x] 3.7 Add documentation checks for internal links, obsolete example tags, and conflicting statements about source or binary storage.

## 4. Validation-Gated Release Workflow

- [x] 4.1 Add a release preflight that requires `validated` status, passing reports, exact upstream tag and commit, matching kernel/module release, and verified artifact checksums.
- [x] 4.2 Add dry-run support that reports the annotated tag, release title, release notes, assets, and catalog updates without changing GitHub state.
- [x] 4.3 Implement immutable mirrored tag creation and the documented `-homelab.<revision>` exception for corrected builds.
- [x] 4.4 Package the versioned kernel image, modules VHDX, manifest, normalized config, and `SHA256SUMS` for GitHub Release upload without copying binaries into tracked catalog paths.
- [x] 4.5 Update a catalog record to `published` only after confirming the remote release and all required assets, and make retries reconcile existing remote state safely.

## 5. Verification

- [x] 5.1 Add positive and negative fixtures for catalog schema, lifecycle, directory structure, checksum, and release-gate validation.
- [x] 5.2 Verify the planned 6.18.35.2 entry passes structural validation while correctly failing publication preflight until runtime evidence is complete.
- [x] 5.3 Verify the support matrix matches manifests and all repository documentation checks pass.
- [x] 5.4 Verify no kernel source or large binary build artifacts are tracked and that the separate Microsoft clone remains shallow and pristine.
- [x] 5.5 Run strict OpenSpec validation for both active changes and document the dependency between the catalog entry and the first kernel build outputs.
