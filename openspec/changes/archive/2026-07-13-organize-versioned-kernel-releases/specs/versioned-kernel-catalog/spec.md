## ADDED Requirements

### Requirement: Upstream-tag catalog layout
The repository SHALL store each kernel record at `kernels/<upstream-tag>/`, where `<upstream-tag>` is the exact Microsoft tag such as `linux-msft-wsl-6.18.35.2`. A record MUST NOT use a branch name, abbreviated version, or mutable alias as its directory key.

#### Scenario: New kernel tag is prepared
- **WHEN** work begins for Microsoft tag `linux-msft-wsl-6.18.35.2`
- **THEN** its repository record is created at `kernels/linux-msft-wsl-6.18.35.2/`
- **AND** the record identifies the exact upstream commit

### Requirement: Required record contents
Each kernel record SHALL contain `README.md`, `manifest.yaml`, `config/homelab.config`, `config/config-wsl-homelab`, `validation/build.md`, and `validation/runtime.md`. The fragment SHALL record intentional homelab values such as `CONFIG_WIREGUARD=m`, `CONFIG_IPV6=y`, `CONFIG_IPV6_MULTIPLE_TABLES=y`, `CONFIG_NETFILTER_XT_TARGET_CONNMARK=m`, and `CONFIG_NETFILTER_XT_MATCH_CONNMARK=m`; the normalized configuration SHALL preserve the complete resulting set of exact `CONFIG_*=y`, `CONFIG_*=m`, and disabled values.

#### Scenario: Catalog entry is reviewed
- **WHEN** a contributor opens a kernel record
- **THEN** the upstream identity, intentional config overlay, complete normalized config, build result, and runtime result are available at predictable paths

### Requirement: Machine-readable manifest
Each `manifest.yaml` SHALL declare a schema version, lifecycle status, upstream repository, upstream tag, upstream commit, kernel release, config checksums, build toolchain, build timestamp, artifact names and checksums, validation summary, and release URL when published. Unknown values MUST be represented explicitly rather than omitted when the lifecycle has not produced them yet.

#### Scenario: Tool reads an incomplete record
- **WHEN** the record has status `planned`
- **THEN** the manifest still identifies the upstream tag and commit
- **AND** fields not yet produced are explicitly null or marked pending according to the manifest schema

### Requirement: Kernel record lifecycle
Every record SHALL use one of `planned`, `built`, `validated`, `published`, or `failed`. Transitions MUST follow `planned` to `built` to `validated` to `published`; a failure at any verification stage SHALL set `failed` and record the failed stage and reason before work resumes.

#### Scenario: Runtime validation fails
- **WHEN** a built kernel fails WireGuard, IPv6, Docker, or CONNMARK acceptance
- **THEN** its manifest is marked `failed`
- **AND** no published status or release tag is assigned

### Requirement: Repository support index
The repository SHALL provide a support matrix generated or verified from kernel manifests. It SHALL show the upstream tag, commit, kernel release, lifecycle status, validation date, supported homelab capabilities, and release link for each catalog entry.

#### Scenario: User selects a kernel build
- **WHEN** a user reads the repository support matrix
- **THEN** they can distinguish planned, validated, and published tags
- **AND** navigate directly to the corresponding catalog record or release

### Requirement: Lightweight Git history
Kernel images, modules VHDX files, module staging trees, and intermediate build directories MUST NOT be committed to Git. Git SHALL retain configuration, manifests, checksums, documentation, scripts, and validation evidence needed to understand and reproduce a build.

#### Scenario: Binary artifact is produced
- **WHEN** a build creates a kernel image or modules VHDX
- **THEN** ignore rules prevent the binary from entering normal Git staging
- **AND** the catalog stores its expected filename and checksum instead

