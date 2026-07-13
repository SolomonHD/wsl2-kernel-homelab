# WSL kernel migration

## Purpose

Define a safe migration from the stock or an older custom WSL kernel to a verified, matching kernel
and modules pair, including compatibility checks, targeted cleanup, activation, and rollback.

## Requirements

### Requirement: WSL compatibility preflight
The migration guide SHALL require the user to inspect `wsl --version`, update WSL with the supported
Windows update command when necessary, and shut down WSL before activating custom kernel media. It
SHALL identify WSL 2.7.10.0 as the validated baseline without representing that version as a
permanent minimum.

#### Scenario: Older WSL does not accept the modules path
- **WHEN** a user is migrating from a WSL installation that rejects or misinterprets the
  `.wslconfig` `kernelModules` value
- **THEN** the guide directs the user to update WSL and confirm the resulting version before
  activating the custom kernel

### Requirement: Targeted legacy configuration cleanup
The migration guide SHALL instruct the user to back up `/etc/wsl.conf` and remove only the
unsupported `crossDistro` key from its `[automount]` section when that key is present. It MUST
preserve supported automount, network, interop, user, boot, GPU, and time settings.

#### Scenario: Legacy cross-distribution automount key is present
- **WHEN** `/etc/wsl.conf` contains `crossDistro=true` or `crossDistro=false` under `[automount]`
- **THEN** the migration removes that key without replacing or discarding unrelated settings
- **AND** retains a backup that can be restored during rollback

#### Scenario: Legacy key is absent
- **WHEN** `/etc/wsl.conf` does not contain `crossDistro`
- **THEN** the migration leaves the file unchanged and continues

### Requirement: Verified artifact handoff
The migration guide SHALL direct the user to download the kernel image, modules VHDX, manifest, and
`SHA256SUMS`, verify both binary checksums, and copy the verified pair to stable Windows paths before
editing `.wslconfig`.

#### Scenario: Downloaded pair is ready for activation
- **WHEN** the user compares the downloaded `linux-msft-wsl-6.18.35.2` and
  `modules-linux-msft-wsl-6.18.35.2.vhdx` against `SHA256SUMS`
- **THEN** activation proceeds only when both checksums match the manifest

### Requirement: Pairwise activation and global-scope warning
The migration guide SHALL state that `%UserProfile%\.wslconfig` applies to every WSL2 distribution.
It SHALL configure `kernel` to `linux-msft-wsl-6.18.35.2` and `kernelModules` to
`modules-linux-msft-wsl-6.18.35.2.vhdx` together, require `wsl --shutdown`, and verify the running
kernel and module release after restart.

#### Scenario: Migrated kernel starts successfully
- **WHEN** the user restarts WSL with both paths configured
- **THEN** `uname -r` equals the manifest's kernel release
- **AND** `/lib/modules/$(uname -r)`, `modinfo`, and `modprobe` resolve the matching modules

### Requirement: Pairwise rollback
The migration guide SHALL preserve the prior `.wslconfig` state and SHALL instruct the user to
restore or remove `kernel` and `kernelModules` together followed by `wsl --shutdown`.

#### Scenario: Activation must be reverted
- **WHEN** the custom kernel fails to start or pass identity checks
- **THEN** the user restores both prior paths or removes both custom settings
- **AND** no new kernel is left paired with an old modules VHDX or vice versa
