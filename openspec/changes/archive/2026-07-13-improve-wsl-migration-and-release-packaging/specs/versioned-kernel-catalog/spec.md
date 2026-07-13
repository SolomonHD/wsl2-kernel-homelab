## ADDED Requirements

### Requirement: Canonical binary artifact names
For each catalog record, the kernel artifact name SHALL equal the exact upstream tag with no
`bzImage-` prefix, and the modules artifact name SHALL equal `modules-<upstream-tag>.vhdx`.

#### Scenario: Baseline artifact names are validated
- **WHEN** the catalog validates the `linux-msft-wsl-6.18.35.2` record
- **THEN** the kernel name is exactly `linux-msft-wsl-6.18.35.2`
- **AND** the modules name is exactly `modules-linux-msft-wsl-6.18.35.2.vhdx`

## MODIFIED Requirements

### Requirement: Machine-readable manifest
Each `manifest.yaml` SHALL use schema version 2 and declare a lifecycle status, upstream repository,
upstream tag, upstream commit, kernel release, config checksums, build toolchain, build timestamp,
artifact names, artifact checksums, artifact byte sizes, validation summary, and release URL when
published. Unknown values MUST be represented explicitly rather than omitted when the lifecycle has
not produced them yet. Artifact `size_bytes` values MUST be null for unbuilt artifacts and positive
integers for built artifacts.

#### Scenario: Tool reads an incomplete record
- **WHEN** the record has status `planned`
- **THEN** the manifest still identifies the upstream tag and commit
- **AND** fields not yet produced, including artifact sizes, are explicitly null or marked pending
  according to the manifest schema

#### Scenario: Tool reads a built record
- **WHEN** the record has status `built`, `validated`, or `published`
- **THEN** each binary artifact has a canonical name, lowercase SHA-256 digest, matching kernel
  release, and positive byte size

### Requirement: Kernel record lifecycle
Every record SHALL use one of `planned`, `built`, `validated`, `published`, or `failed`. Normal
transitions MUST follow `planned` to `built` to `validated` to `published`; a failure at any
verification stage SHALL set `failed` and record the failed stage and reason before work resumes. An
unpublished `validated` record MAY transition back to `built` only when replacing artifacts
invalidates its prior runtime evidence, and that transition MUST clear the validation timestamp and
set runtime validation to pending. A `published` record MUST NOT transition backward.

#### Scenario: Runtime validation fails
- **WHEN** a built kernel fails WireGuard, IPv6, Docker, or CONNMARK acceptance
- **THEN** its manifest is marked `failed`
- **AND** no published status or release tag is assigned

#### Scenario: Unpublished validated artifacts are rebuilt
- **WHEN** a validated record has null publication metadata and its kernel or modules artifact is
  renamed, stripped, or otherwise replaced
- **THEN** the record transitions to `built` with `previous_status: validated`
- **AND** the prior runtime pass and validation timestamp are invalidated until acceptance is rerun

#### Scenario: Published artifacts would be replaced
- **WHEN** a published record is selected for an artifact rebuild
- **THEN** the catalog rejects a backward lifecycle transition
- **AND** requires an immutable superseding release instead
