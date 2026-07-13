## MODIFIED Requirements

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
