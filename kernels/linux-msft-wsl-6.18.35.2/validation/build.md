# Build validation: `linux-msft-wsl-6.18.35.2`

Result: PASS

| Check | Expected | Actual | Result |
| --- | --- | --- | --- |
| Source tag | `linux-msft-wsl-6.18.35.2` | `linux-msft-wsl-6.18.35.2` | PASS |
| Source commit | `1bd4ed3d4ada93738eef3fc2a66b674c640dc326` | `1bd4ed3d4ada93738eef3fc2a66b674c640dc326` | PASS |
| Shallow/pristine clone | `true` / clean | `true` / clean before and after build | PASS |
| Config merge | no conflicts | completed out of tree | PASS |
| `olddefconfig` | success | success | PASS |
| Required symbols | exact values | all values match | PASS |
| Kernel build | success | `linux-msft-wsl-6.18.35.2` | PASS |
| Modules build/install | success | `modules/lib/modules/6.18.35.2-microsoft-standard-WSL2+` | PASS |
| Runtime module stripping | no staged `.debug*` sections | `961` `.ko` files checked | PASS |
| Kernel release | matches module tree | `6.18.35.2-microsoft-standard-WSL2+` | PASS |
| Kernel checksum | matches manifest | `b8ab38766bd36897ebdd629120bea9c1b779e442a9a81897b0ebaedb0bbfc435` | PASS |
| Kernel size | matches manifest | `17322496` bytes | PASS |
| Modules VHDX checksum | matches manifest | `c0cd43237a0747d75c663e333cb4912a9077d7e26093de418cec8fc5b665385f` | PASS |
| Modules VHDX size | matches manifest | `226492416` bytes | PASS |

- Compiler: `gcc (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0`
- UTC build timestamp: `2026-07-13T19:48:45+00:00`
- Normalized config SHA-256: `1f1175524f23b3cd2d9aacaaa6553c4ea8dd22cb1c7c085966e0e4ae90f3eb71`
- Source: `/home/solomong/Code/dev/build-wsl2-kernels/WSL2-Linux-Kernel`
- Ignored build directory: `/home/solomong/Code/dev/build-wsl2-kernels/wsl2-kernel-homelab/build/linux-msft-wsl-6.18.35.2`
- Entry point: `python3 scripts/build_kernel.py build --source /home/solomong/Code/dev/build-wsl2-kernels/WSL2-Linux-Kernel --jobs 8 --wsl-root-vhdx Ubuntu --record-evidence`
- Kernel artifact: `linux-msft-wsl-6.18.35.2`
- Modules artifact: `modules-linux-msft-wsl-6.18.35.2.vhdx`

The entry point copied Microsoft's `config-wsl`, merged the versioned homelab fragment, ran
`olddefconfig`, strictly validated every required symbol, built the kernel and modules together,
installed stripped runtime modules under `lib/modules/6.18.35.2-microsoft-standard-WSL2+`, verified that their ELF files
contain no `.debug*` sections, and passed that exact staged release to Microsoft's
`gen_modules_vhdx.sh`. The source clone remained shallow and pristine throughout.
