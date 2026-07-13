## ADDED Requirements

### Requirement: Validation-gated publication
A repository Git tag or public kernel release SHALL be created only when the catalog record is at `validated`, the build and runtime reports pass, and the kernel image and modules VHDX checksums match the manifest.

#### Scenario: Validation is incomplete
- **WHEN** build evidence exists but runtime acceptance is pending
- **THEN** release tooling refuses to create or push a release tag
- **AND** reports the missing validation gate

### Requirement: Mirrored release tag
The first validated homelab build for an upstream tag SHALL use the exact upstream tag name, such as `linux-msft-wsl-6.18.35.2`, as an annotated tag in this repository. The annotation SHALL identify the Microsoft repository, upstream commit, homelab manifest path, and artifact checksums.

#### Scenario: Validated tag is released
- **WHEN** `linux-msft-wsl-6.18.35.2` passes all publication gates
- **THEN** the repository creates an annotated `linux-msft-wsl-6.18.35.2` tag at the commit containing its validated catalog record
- **AND** the tag is not moved after publication

### Requirement: Corrected build revisions
If a published build must be corrected without changing its Microsoft upstream tag, the original tag and release MUST remain immutable. A corrected release SHALL use `<upstream-tag>-homelab.<revision>` and SHALL document why an exception to the one-to-one mirrored tag was required.

#### Scenario: Published packaging defect is corrected
- **WHEN** the upstream kernel commit is unchanged but a modules VHDX must be rebuilt
- **THEN** the original release remains available and unchanged
- **AND** the corrected release receives the next `-homelab.<revision>` suffix with linked supersession notes

### Requirement: Required release assets
Each published release SHALL include a versioned kernel image, matching modules VHDX, `manifest.yaml`, normalized configuration, and `SHA256SUMS`. Artifact filenames MUST include the upstream tag and MUST correspond exactly to names and hashes in the manifest.

#### Scenario: User verifies downloaded artifacts
- **WHEN** a user downloads the kernel, modules VHDX, and `SHA256SUMS`
- **THEN** both binary checksums validate
- **AND** the manifest reports the same upstream tag, commit, kernel release, and checksums

### Requirement: Reproducibility and source provenance
Release notes SHALL link the exact Microsoft source tag and commit, the repository catalog record, the homelab configuration, build instructions, validation reports, and applicable license information. A release with source patches MUST additionally publish those patches and document how they were applied.

#### Scenario: Release contains config-only changes
- **WHEN** no kernel source patch was used
- **THEN** the release identifies the unmodified Microsoft tag and commit as its source
- **AND** provides the complete configuration and build procedure needed to reproduce the binaries

### Requirement: Publication status reconciliation
After release assets are uploaded successfully, the default-branch catalog SHALL mark the record `published` and store the release URL. If upload or release creation fails, the record SHALL remain `validated` until publication is completed or explicitly abandoned.

#### Scenario: Asset upload fails
- **WHEN** the annotated tag exists but one or more required assets fail to upload
- **THEN** the catalog does not claim `published`
- **AND** rerunning publication verifies existing remote state before uploading missing assets

