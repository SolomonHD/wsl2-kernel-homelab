## MODIFIED Requirements

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
