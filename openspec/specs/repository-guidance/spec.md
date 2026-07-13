# Repository guidance

## Purpose

Define consistent repository boundaries, layout, workflow documentation, support status, and
contributor guidance for the WSL2 homelab kernel catalog.

## Requirements

### Requirement: Repository purpose and boundaries
The root README and `AGENTS.md` SHALL state that the repository contains OpenSpec records, per-tag configurations, manifests, checksums, documentation, validation evidence, and release metadata while Microsoft kernel source remains in a separate pristine shallow clone. They SHALL distinguish Git-tracked records from binary GitHub Release assets.

#### Scenario: New contributor inspects the repository
- **WHEN** the contributor reads the root README
- **THEN** they understand what belongs in Git, what is built externally, and where released binaries are downloaded

### Requirement: Repository layout documentation
The repository SHALL document the purpose and required contents of `kernels/`, `docs/`, `scripts/`, `openspec/`, and ignored build-output locations. The documented example SHALL use the current `linux-msft-wsl-6.18.35.2` baseline rather than an obsolete kernel tag.

#### Scenario: Contributor adds a tag record
- **WHEN** the contributor follows the structure documentation
- **THEN** the new record uses the expected directory and filenames
- **AND** automated structure validation recognizes it

### Requirement: Workflow documentation set
The repository SHALL document source acquisition, config generation, stripped runtime module
packaging, migration from a stock or older custom WSL kernel, paired WSL deployment, runtime
testing, and validated GitHub Release publication. Each workflow SHALL include prerequisites,
copyable commands, expected outputs, failure handling, rollback where state changes, and links to
the relevant OpenSpec requirements. User-facing artifact examples SHALL name the kernel image
exactly after its upstream tag and MUST NOT use the removed `bzImage-` prefix.

#### Scenario: User follows the build workflow
- **WHEN** the user starts with a shallow Microsoft clone and a catalog entry
- **THEN** the documentation leads them through producing a kernel and matching stripped modules
  VHDX
- **AND** identifies the validation evidence and release-size gate required before publication

#### Scenario: User follows the migration workflow
- **WHEN** the user moves from a stock or older custom WSL kernel to a published catalog pair
- **THEN** the documentation covers WSL compatibility, legacy `wsl.conf` cleanup, checksum
  verification, global `.wslconfig` scope, pairwise activation, verification, and rollback

### Requirement: Support matrix and lifecycle explanation
The README SHALL include or link a support matrix and SHALL explain `planned`, `built`, `validated`, `published`, and `failed`. It MUST NOT describe an unvalidated build as supported or ready for homelab use.

#### Scenario: Catalog contains an unvalidated build
- **WHEN** the support matrix is rendered
- **THEN** that build is visibly marked as unvalidated
- **AND** no normal download recommendation is presented for it

### Requirement: Contributor and agent consistency
`CONTRIBUTING.md` and `AGENTS.md` SHALL use the same naming, directory, validation, source-clone, and release rules as the catalog and release specifications. Documentation validation MUST detect obsolete example tags, broken internal links, and conflicting statements about committing binaries or kernel source.

#### Scenario: Guidance becomes inconsistent
- **WHEN** one guidance file permits committed kernel binaries while another prohibits them
- **THEN** documentation validation fails
- **AND** identifies the conflicting policy text or rule
