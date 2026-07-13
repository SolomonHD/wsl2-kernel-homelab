## ADDED Requirements

### Requirement: Release asset size gate
Release preflight SHALL compare every required asset's actual byte size with its manifest value and
MUST reject any individual release asset whose size is greater than or equal to 2 GiB
(`2147483648` bytes). This gate SHALL complete before an annotated tag or remote release operation
is applied.

#### Scenario: Modules VHDX exceeds the hosting limit
- **WHEN** the modules VHDX is at least `2147483648` bytes
- **THEN** release preflight fails locally and identifies the oversized asset and measured size
- **AND** no release tag or published status is created

#### Scenario: Manifest size differs from packaged asset
- **WHEN** a required asset's actual size does not equal its manifest `size_bytes`
- **THEN** release preflight fails even if the asset is below the hosting limit

## MODIFIED Requirements

### Requirement: Required release assets
Each published release SHALL include the kernel image named exactly after the upstream tag, the
matching `modules-<upstream-tag>.vhdx`, `manifest.yaml`, normalized configuration, and
`SHA256SUMS`. For the baseline release the binary names MUST be
`linux-msft-wsl-6.18.35.2` and `modules-linux-msft-wsl-6.18.35.2.vhdx`. Artifact filenames, byte
sizes, and hashes MUST correspond exactly to the manifest.

#### Scenario: User verifies downloaded artifacts
- **WHEN** a user downloads `linux-msft-wsl-6.18.35.2`, the matching modules VHDX, and
  `SHA256SUMS`
- **THEN** both binary checksums validate
- **AND** the manifest reports the same upstream tag, commit, kernel release, byte sizes, and
  checksums
