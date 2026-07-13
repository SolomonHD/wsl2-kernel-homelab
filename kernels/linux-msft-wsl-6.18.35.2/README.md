# `linux-msft-wsl-6.18.35.2`

This is the first homelab catalog record, pinned to Microsoft commit
`1bd4ed3d4ada93738eef3fc2a66b674c640dc326`. Its normalized WireGuard, IPv6, Docker, and CONNMARK
configuration is unchanged. Its unpublished kernel/modules pair is being replaced with canonical
artifact naming and a stripped runtime modules VHDX for kernel release
`6.18.35.2-microsoft-standard-WSL2+`.

There is no published download for this record yet. Binary outputs remain in ignored local storage
until the separate publication workflow passes; their names and SHA-256 checksums are retained in
the manifest.

## Specifications

The [`versioned-kernel-catalog`](../../openspec/specs/versioned-kernel-catalog/spec.md) and
[`validated-kernel-release`](../../openspec/specs/validated-kernel-release/spec.md) specifications
own the catalog/release envelope. The [`homelab-kernel-config`](../../openspec/specs/homelab-kernel-config/spec.md)
and [`wsl2-kernel-build`](../../openspec/specs/wsl2-kernel-build/spec.md) specifications own config
normalization, build, paired artifact identity, deployment, and runtime acceptance. The replacement
pair is `built`; runtime validation must pass again before publication.

- Upstream source: [microsoft/WSL2-Linux-Kernel](https://github.com/microsoft/WSL2-Linux-Kernel/tree/linux-msft-wsl-6.18.35.2)
- Intentional config: [`config/homelab.config`](config/homelab.config)
- Normalized config: [`config/config-wsl-homelab`](config/config-wsl-homelab)
- Build evidence: [`validation/build.md`](validation/build.md)
- Runtime evidence: [`validation/runtime.md`](validation/runtime.md)
- Migration guide: [`../../docs/wsl-kernel-migration.md`](../../docs/wsl-kernel-migration.md)
