## Why

The repository currently explains its intent but has no durable structure for finding the configuration, provenance, and validation status of a build for a specific Microsoft WSL2 kernel tag. As validated builds accumulate, contributors need an obvious mapping from an upstream tag to the exact homelab configuration, test evidence, and downloadable artifacts without putting large binaries into Git history.

## What Changes

- Introduce a `kernels/<upstream-tag>/` catalog that mirrors exact `linux-msft-wsl-*` tag names and stores per-tag configs, manifests, documentation, checksums, and validation evidence.
- Define lifecycle states for planned, built, validated, and published kernel entries.
- Create a validation gate that permits a matching repository Git tag and GitHub Release only after the kernel and modules pass the documented acceptance checks.
- Publish kernel images and modules VHDX files as GitHub Release assets rather than committing large binaries to Git.
- Use the exact Microsoft upstream tag for the corresponding repository tag and release, preserving a one-to-one mapping.
- Rewrite the README and contributor/agent guidance around the versioned catalog, build workflow, support matrix, validation process, artifact policy, and release lifecycle.
- Keep Microsoft kernel source outside this repository and link every published build back to its exact upstream tag and commit.

## Capabilities

### New Capabilities

- `versioned-kernel-catalog`: Defines the per-upstream-tag repository layout, metadata, configuration, evidence, and discoverability requirements.
- `validated-kernel-release`: Defines validation gates, mirrored Git tags, release assets, checksums, provenance, and publication rules.
- `repository-guidance`: Defines the README, contributor, build, test, release, and agent documentation required to make the repository usable and internally consistent.

### Modified Capabilities

None.

## Impact

- Adds a stable top-level layout for versioned kernel records and documentation.
- Changes the repository description from specs-only to specifications plus lightweight, versioned kernel release records.
- Establishes GitHub Releases as the distribution channel for large `bzImage` and `modules.vhdx` artifacts.
- Reserves exact upstream `linux-msft-wsl-*` tag names for builds that have passed validation.
- Requires release automation or a documented manual release workflow in a later implementation phase.
- Does not change or vendor any Microsoft kernel source.
