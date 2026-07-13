# Repository structure

The repository is a lightweight release catalog. It owns records and tooling, not Microsoft source
or generated kernel binaries.

| Path | Owner and purpose | Git policy |
| --- | --- | --- |
| `kernels/<upstream-tag>/` | Maintainer-owned config, manifest, per-tag README, checksums, and validation evidence | Track required record files only |
| `kernels/_template/` | Reusable starting layout for an exact Microsoft tag | Track |
| `docs/` | User migration, build, validation, and release workflows | Track |
| `scripts/` | Catalog validation, documentation checks, and release gates | Track |
| `schemas/` | Versioned machine-readable manifest contracts | Track |
| `openspec/` | Requirements, designs, and implementation tasks | Track |
| `tests/` | Positive and negative fixtures and automated checks | Track |
| `build/`, `out/`, `dist/`, `artifacts/`, `modules-staging/` | Generated compilation, staging, and packaging output | Ignore; never commit |
| separate `WSL2-Linux-Kernel/` clone | Pristine shallow Microsoft source checkout | Outside this repository |

Every real record is named by the exact upstream tag, for example:

```text
kernels/linux-msft-wsl-6.18.35.2/
├── README.md
├── manifest.yaml
├── config/
│   ├── homelab.config
│   └── config-wsl-homelab
└── validation/
    ├── build.md
    └── runtime.md
```

Copy `kernels/_template/`, fill every known field, and leave lifecycle-dependent unknowns explicitly
`null`. Run `python3 scripts/catalog.py validate` and `python3 scripts/catalog.py matrix` after any
manifest edit. The validator reports missing filenames, malformed tag keys, lifecycle errors, and
checksum drift. See the OpenSpec requirements in
[`versioned-kernel-catalog`](../openspec/specs/versioned-kernel-catalog/spec.md).

Do not copy a source tree, kernel image, modules tree, VHDX, `bzImage`, or output directory into a
record. `python3 scripts/catalog.py tracked-artifacts` enforces the lightweight-history boundary.
