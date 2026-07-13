# WSL2 kernel build

## Purpose

Define how the pristine Microsoft source is configured, built, packaged, deployed, and validated as
a matching WSL2 kernel and modules pair.

## Requirements

### Requirement: Pristine shallow source acquisition
The build workflow SHALL use a separate `microsoft/WSL2-Linux-Kernel` clone created with `--depth=1 --no-tags` and SHALL fetch only `linux-msft-wsl-6.18.35.2` with depth one when the tag is not already present. It MUST NOT commit or permanently modify upstream kernel source files.

#### Scenario: Required tag is absent
- **WHEN** the source clone does not contain `linux-msft-wsl-6.18.35.2`
- **THEN** the workflow fetches only that tag with `--depth=1`
- **AND** checks out the tag in detached-HEAD state

#### Scenario: Source clone contains local changes
- **WHEN** tracked or untracked source-tree changes are detected before a build
- **THEN** the workflow stops without cleaning or overwriting them
- **AND** reports that a pristine source checkout is required

### Requirement: Versioned homelab configuration overlay
The specifications repository SHALL contain a versioned configuration fragment that declares the required homelab `CONFIG_*` values. The build workflow SHALL merge that fragment over the pinned tag's Microsoft WSL2 base configuration in an out-of-tree build directory.

#### Scenario: Build configuration is generated
- **WHEN** the pinned base configuration and homelab fragment are merged
- **THEN** the resulting `.config` is stored in the build directory rather than the source clone
- **AND** the source clone remains clean

### Requirement: Matching kernel and module artifacts
The workflow SHALL build the x86_64 WSL2 kernel image and all enabled modules from the same
generated configuration. It SHALL name the kernel image exactly after the upstream tag, such as
`linux-msft-wsl-6.18.35.2`, install runtime modules with `INSTALL_MOD_STRIP=1`, and produce
`modules-linux-msft-wsl-6.18.35.2.vhdx` whose module release exactly matches the kernel release. The
stripping step MUST remove debug information only from the installed staging tree and MUST NOT
change any required built-in or modular `CONFIG_*` selection.

#### Scenario: Build completes successfully
- **WHEN** compilation, stripped module installation, and module packaging finish
- **THEN** the output contains `linux-msft-wsl-6.18.35.2` and
  `modules-linux-msft-wsl-6.18.35.2.vhdx`
- **AND** the modules VHDX contains `/lib/modules/<kernel-release>` matching the built kernel
- **AND** staged runtime modules do not retain `.debug*` sections

### Requirement: Reproducible build provenance
Each build SHALL emit a manifest containing the upstream tag, upstream commit, kernel release,
configuration checksum, compiler identity, build timestamp, kernel image name, checksum and byte
size, and modules VHDX name, checksum and byte size. Large binary build outputs MUST remain outside
Git; the manifest and final normalized configuration MAY be retained as versioned evidence.

#### Scenario: Build artifacts are handed off
- **WHEN** a kernel image and modules VHDX are ready for deployment
- **THEN** their names, byte sizes, and checksums match the accompanying manifest
- **AND** the manifest identifies `linux-msft-wsl-6.18.35.2` and its pinned commit

### Requirement: WSL2 deployment pair
Deployment instructions SHALL require a current WSL installation that accepts the `.wslconfig`
`kernelModules` path, warn that `.wslconfig` applies globally to WSL2 distributions, configure both
the `kernel` and `kernelModules` paths, and require `wsl --shutdown` before starting a distribution
with new artifacts.

#### Scenario: Custom build is activated
- **WHEN** Windows points `.wslconfig` at `linux-msft-wsl-6.18.35.2` and the matching modules VHDX
  and WSL is restarted
- **THEN** `uname -r` reports the expected custom kernel release
- **AND** modules load from the matching module release

### Requirement: Runtime acceptance evidence
The build SHALL not be considered validated until runtime checks cover WireGuard device creation, IPv6 policy routing, Docker container startup and bridge connectivity, overlay storage, and CONNMARK rule installation. The resulting commands, versions, and outcomes SHALL be recorded as test evidence.

#### Scenario: Runtime acceptance passes
- **WHEN** all required runtime checks execute under the deployed custom kernel
- **THEN** every check completes without missing-feature or missing-module errors
- **AND** the evidence identifies the tested kernel release and artifact checksums
