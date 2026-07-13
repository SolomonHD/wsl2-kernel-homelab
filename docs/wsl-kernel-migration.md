# Migrate to a catalog kernel

Use this sequence to move from the Microsoft-packaged kernel or an older custom kernel to a
checksummed catalog kernel/modules pair. `%UserProfile%\.wslconfig` applies globally to every WSL2
distribution, so schedule a shutdown and test all affected distributions. The validated baseline
environment used WSL 2.7.10.0; that is recorded evidence, not a permanent minimum version.

## Check and update WSL

In PowerShell, inspect the installed version and update through WSL's supported updater when needed:

```powershell
wsl --version
wsl --update
wsl --version
```

Do not activate `kernelModules` on an older installation that rejects or misinterprets the setting.
Finish the update first. Save the current `%UserProfile%\.wslconfig` before editing it:

```powershell
Copy-Item "$env:USERPROFILE\.wslconfig" "$env:USERPROFILE\.wslconfig.pre-homelab" -ErrorAction SilentlyContinue
```

## Back up and narrowly clean `/etc/wsl.conf`

Inside each distribution that will be tested, inspect the existing file and retain a timestamped
backup. If `crossDistro=true` or `crossDistro=false` exists under `[automount]`, remove only that
key. Preserve every other automount, network, interop, user, boot, GPU, and time setting. If the key
is absent, make no edit.

```bash
sudo cp -a /etc/wsl.conf "/etc/wsl.conf.pre-homelab.$(date -u +%Y%m%dT%H%M%SZ)"
sudo sed -n '/^[[:space:]]*\[automount\][[:space:]]*$/,/^[[:space:]]*\[/p' /etc/wsl.conf
sudo sed -i '/^[[:space:]]*\[automount\][[:space:]]*$/,/^[[:space:]]*\[/ {
  /^[[:space:]]*crossDistro[[:space:]]*=/d
}' /etc/wsl.conf
```

Review the diff against the backup before continuing. The edit is intentionally scoped to the
`[automount]` range and does not recreate or replace the configuration file.

## Download and verify the pair

Download these four files from the same GitHub Release: `linux-msft-wsl-6.18.35.2`,
`modules-linux-msft-wsl-6.18.35.2.vhdx`, `manifest.yaml`, and `SHA256SUMS`. In PowerShell, compare
both binary hashes with `SHA256SUMS` and the manifest before copying them to stable paths:

```powershell
Get-Content .\SHA256SUMS
Get-FileHash -Algorithm SHA256 .\linux-msft-wsl-6.18.35.2
Get-FileHash -Algorithm SHA256 .\modules-linux-msft-wsl-6.18.35.2.vhdx
New-Item -ItemType Directory -Force C:\WSL | Out-Null
Copy-Item .\linux-msft-wsl-6.18.35.2 C:\WSL\linux-msft-wsl-6.18.35.2
Copy-Item .\modules-linux-msft-wsl-6.18.35.2.vhdx C:\WSL\modules-linux-msft-wsl-6.18.35.2.vhdx
```

Stop if either digest differs. The kernel and VHDX are one deployment unit.

## Activate and verify together

Set both paths in `%UserProfile%\.wslconfig` in the same edit:

```ini
[wsl2]
kernel=C:\\WSL\\linux-msft-wsl-6.18.35.2
kernelModules=C:\\WSL\\modules-linux-msft-wsl-6.18.35.2.vhdx
```

Then shut down every WSL2 VM and start the test distribution:

```powershell
wsl --shutdown
wsl --distribution <TestDistribution>
```

Inside it, compare `uname -r` with `kernel_release` in `manifest.yaml`, then verify the matching
module tree and a representative module:

```bash
uname -r
test -d "/lib/modules/$(uname -r)"
modinfo -F vermagic wireguard
sudo modprobe wireguard
```

Continue through [`validation.md`](validation.md) for WireGuard, IPv6, Docker, overlayfs,
bridge/NAT, and CONNMARK acceptance.

## Roll back as a pair

If startup or identity checks fail, restore the saved `.wslconfig`, or remove both `kernel` and
`kernelModules` together. Never retain one new path with one old path. Restore the saved
`/etc/wsl.conf` only if that targeted change also needs reversal, then shut WSL down again:

```powershell
Copy-Item "$env:USERPROFILE\.wslconfig.pre-homelab" "$env:USERPROFILE\.wslconfig" -ErrorAction SilentlyContinue
wsl --shutdown
```

The normative identity, lifecycle, and paired-deployment rules are in the
[`versioned-kernel-catalog`](../openspec/specs/versioned-kernel-catalog/spec.md) and
[`wsl2-kernel-build`](../openspec/specs/wsl2-kernel-build/spec.md) specifications.
