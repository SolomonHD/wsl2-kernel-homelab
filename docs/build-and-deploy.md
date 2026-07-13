# Build and deploy a catalog kernel

The repository build entry point produces a pinned x86_64 WSL2 kernel and its matching modules
VHDX without writing generated files into the Microsoft source tree. Use a Linux environment with
enough free disk space for a kernel build.

## Prerequisites

Install Git, Python 3, PyYAML, GNU make, GCC/binutils, bc, bison, flex, OpenSSL and ELF development
headers, dwarves (`pahole`), cpio, rsync, QEMU image tools (`qemu-img`), and ext4/loop-device
utilities. Install the repository Python dependency with:

```bash
python3 -m pip install -r requirements.txt
```

Microsoft's `gen_modules_vhdx.sh` performs privileged loop-device, filesystem, and mount operations.
The build script elevates only that packaging command, and only when `--sudo-vhdx` is present.
If this WSL account cannot use non-interactive sudo, `--wsl-root-vhdx <Distribution>` instead runs
only that script through Windows' root launch for the named distribution and returns ownership of
the output to the invoking Linux user. Review the Microsoft script in the pinned source before
authorizing either method.

## Acquire and verify the exact source

Keep the Microsoft clone beside, never inside, this repository:

```bash
git clone --depth=1 --no-tags \
  https://github.com/microsoft/WSL2-Linux-Kernel.git \
  ../WSL2-Linux-Kernel
```

The baseline manifest pins `linux-msft-wsl-6.18.35.2` at
`1bd4ed3d4ada93738eef3fc2a66b674c640dc326`. The first configuration command may explicitly fetch
only that tag at depth one and check it out in detached-HEAD state:

```bash
python3 scripts/build_kernel.py configure \
  --source ../WSL2-Linux-Kernel \
  --fetch-tag
```

Later runs omit `--fetch-tag`. Without it, the command performs no source mutation and stops unless
the tag ref exists, resolves to the pinned commit, and is already checked out. Every configure/build
run also requires a shallow, pristine clone before proceeding and confirms it is still pristine
afterward. The command never cleans, resets, or overwrites source changes.

## Generate and strictly validate configuration

The `configure` action copies the pinned tag's `arch/x86/configs/config-wsl` into the ignored build
directory, merges the versioned `homelab.config`, runs `olddefconfig`, and checks every required
symbol and built-in/module mode:

```bash
python3 scripts/build_kernel.py configure --source ../WSL2-Linux-Kernel
```

A missing symbol, a disabled requirement, or a `y`/`m` mismatch is reported by name and exits
nonzero before compilation. The standalone equivalent is:

```bash
python3 scripts/validate_config.py \
  --required kernels/linux-msft-wsl-6.18.35.2/config/homelab.config \
  --config build/linux-msft-wsl-6.18.35.2/.config
```

## Build and package the paired artifacts

After reviewing the generated config, run the full build. `--record-evidence` is appropriate for a
clean evidence build: after every build and packaging check passes, it copies the complete normalized
config into the catalog record, records its checksum and artifact provenance, changes the lifecycle
to `built`, writes a passing build report, and regenerates the support matrix. For an unpublished
validated record whose artifacts are being replaced, it also invalidates prior runtime evidence.

```bash
python3 scripts/build_kernel.py clean
python3 scripts/build_kernel.py build \
  --source ../WSL2-Linux-Kernel \
  --jobs "$(nproc)" \
  --sudo-vhdx \
  --record-evidence
```

The entry point performs these gates in order:

1. Verify the shallow source tag, commit, detached checkout, and cleanliness.
2. Merge and normalize the config out of tree, then strictly validate all required symbols.
3. Build the kernel image and enabled modules from that same config.
4. Obtain `make kernelrelease`, install modules with `INSTALL_MOD_STRIP=1` under
   `modules/lib/modules/<release>`, require that exact directory, and verify every staged `.ko`
   lacks `.debug*` ELF sections.
5. Pass the stripped staged tree and exact release to Microsoft's `gen_modules_vhdx.sh`.
6. Reconfirm the source clone is shallow and clean, then record exact byte sizes and SHA-256
   digests for the normalized config, kernel, and modules VHDX in the schema-version-2 manifest.

Expected ignored outputs under `build/linux-msft-wsl-6.18.35.2/` include:

```text
.config
config-wsl-homelab
linux-msft-wsl-6.18.35.2
modules-linux-msft-wsl-6.18.35.2.vhdx
modules/lib/modules/<kernel-release>/
manifest.yaml
SHA256SUMS
```

The build refuses to overwrite final artifacts or an existing module-staging tree. Start a fresh
evidence build with `python3 scripts/build_kernel.py clean`; this deletes only the selected ignored
directory beneath this repository's `build/`. If compilation or VHDX creation fails, preserve useful
logs outside Git, record the failed stage and reason before advancing the lifecycle, fix the cause,
and explicitly clean before retrying.

## Deploy the kernel/modules pair

Copy both checksummed binaries to stable Windows paths. Edit `%UserProfile%\.wslconfig` so the same
build supplies both settings:

```ini
[wsl2]
kernel=C:\\WSL\\linux-msft-wsl-6.18.35.2
kernelModules=C:\\WSL\\modules-linux-msft-wsl-6.18.35.2.vhdx
```

In PowerShell, stop all WSL2 virtual machines before starting the isolated test distribution:

```powershell
wsl --shutdown
wsl --distribution <TestDistribution>
```

Inside that distribution, compare the active release with `kernel_release` in the manifest and
confirm modules resolve from the paired VHDX before running the complete acceptance procedure:

```bash
uname -r
test -d "/lib/modules/$(uname -r)"
modinfo -F vermagic wireguard
modprobe wireguard
```

Continue with [`validation.md`](validation.md) and record actual output, versions, UTC time, and
cleanup. A kernel name alone is not proof that the matching modules VHDX is active.

For a stock-kernel or older-custom-kernel transition, follow the compatibility checks, targeted
legacy cleanup, checksum handoff, activation, and rollback sequence in
[`wsl-kernel-migration.md`](wsl-kernel-migration.md).

## Roll back as a pair

Restore both prior `.wslconfig` paths together, or remove both `kernel` and `kernelModules` entries
to return to Microsoft's packaged kernel. Run `wsl --shutdown` again before restarting the
distribution. Never leave a new kernel paired with an old modules VHDX (or vice versa).

## Kernel capability versus network policy

The build enables WireGuard, routed IPv6, firewall/NAT, bridge, and CONNMARK kernel mechanisms. It
does not configure Windows firewall rules, WSL NAT or mirrored networking mode, Hyper-V firewall,
router forwarding, public DNS, WireGuard peers, UDP port exposure, or allocation/advertisement of
routed IPv6 prefixes.

Consequently, successful in-distribution module/interface and rule tests prove kernel capability;
they do not prove that an Internet peer can reach the WireGuard UDP listener or that an upstream
router will forward an IPv6 prefix through WSL. Treat those Windows, LAN, and edge-router policies
as separate deployment work, and diagnose them independently from this kernel acceptance record.
