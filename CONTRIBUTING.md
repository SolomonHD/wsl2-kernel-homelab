# Contributing

Start with an OpenSpec change that names the homelab need and exact Microsoft tag. Copy
`kernels/_template/` to `kernels/<exact-upstream-tag>/`, pin the full commit, and keep unknown
lifecycle outputs explicitly null. Use the separate pristine shallow Microsoft source clone in
[`docs/build-and-deploy.md`](docs/build-and-deploy.md); never vendor or modify that source here.

Merge intentional config through `olddefconfig`, retain the complete normalized config, and build
the kernel and modules VHDX as an inseparable pair. Generated build trees, module staging, kernel
images, and VHDX files stay in ignored paths and GitHub Releases, never Git or Git LFS.
Use [`docs/wsl-kernel-migration.md`](docs/wsl-kernel-migration.md) for compatibility checks and
pairwise deployment; do not replace an entire `/etc/wsl.conf` to remove one legacy key.

Before review, run:

```bash
python3 scripts/catalog.py validate
python3 scripts/catalog.py matrix --check
python3 scripts/check_docs.py
python3 scripts/catalog.py tracked-artifacts
python3 -m unittest discover -s tests -v
openspec validate --all --strict --store wsl2-kernel-homelab
```

Supply build and runtime evidence according to [`docs/validation.md`](docs/validation.md). Do not
call a record supported until it is validated, and do not publish until release preflight passes.
Mirrored release tags are immutable; corrected same-upstream builds use the documented
`-homelab.<revision>` exception in [`docs/release.md`](docs/release.md).

Keep changes focused, explain failures in the manifest, and update the generated support matrix after
manifest changes. Pull requests must not contain credentials, Microsoft kernel source, or binary
build outputs.
