# Validated release workflow

Publication is approval-gated and starts only from a `validated` record with passing reports,
matching kernel/module releases, verified inputs, and exact Microsoft tag and commit. GitHub assets,
not Git history, store binaries.

## Preflight and dry run

```bash
TAG=linux-msft-wsl-6.18.35.2
ARTIFACTS=build/$TAG
python3 scripts/release.py preflight --tag "$TAG" --artifacts "$ARTIFACTS"
python3 scripts/release.py plan --tag "$TAG" --artifacts "$ARTIFACTS"
```

Preflight refuses `planned`, `built`, `failed`, or incomplete records and validates report results,
tag/commit identity, kernel/module release equality, canonical filenames, hashes, and manifest byte
sizes. Every binary must match `size_bytes`, and every individual final asset must be smaller than
2 GiB (`2147483648` bytes). Plan prints the annotated
tag, title, notes, assets, and post-publication catalog changes without modifying Git or GitHub.

The first release mirrors the exact Microsoft tag. A published tag is immutable. If the same
Microsoft source requires a corrected config or package, retain the original and use the next
`<upstream-tag>-homelab.<revision>` suffix with a required reason and `supersedes` link. Prefer a new
Microsoft tag for routine updates.

## Package and tag

```bash
python3 scripts/release.py package --tag "$TAG" --artifacts "$ARTIFACTS" --output "dist/$TAG"
python3 scripts/release.py create-tag --tag "$TAG" --artifacts "$ARTIFACTS"
```

Packaging creates an ignored directory containing versioned kernel and modules VHDX files,
`manifest.yaml`, the normalized config, and `SHA256SUMS`; it never copies binaries under `kernels/`.
The tag command defaults to dry-run. Its explicit `--apply` form creates an annotated local tag at
the validated catalog commit only after re-running preflight and confirming the intended target.
The annotation identifies Microsoft source, the manifest path, and artifact hashes. Review it before
any push.

Release notes must link the exact Microsoft tag and commit, catalog record, normalized config, build
instructions, validation reports, GPL-2.0 license information, and any source patches. Config-only
builds state that Microsoft source is unmodified. If patches ever exist, package and document each
patch and its application order.

Required GitHub Release assets are:

- `<upstream-tag>` (for example, `linux-msft-wsl-6.18.35.2`)
- `modules-<upstream-tag>.vhdx`
- `manifest.yaml`
- `config-wsl-homelab`
- `SHA256SUMS`

GitHub Releases remains the binary channel because the checksummed kernel and stripped modules VHDX
can be downloaded directly into stable Windows paths. GitHub Packages would add package-client or
OCI extraction steps, Git LFS would couple large binaries to repository history, and committed
binaries violate the lightweight catalog boundary; none are part of this workflow.

## Publication reconciliation

After an authorized GitHub Release upload, reconcile remote state before editing status:

```bash
python3 scripts/release.py reconcile --tag "$TAG" --artifacts "dist/$TAG"
```

The command reads the remote release and verifies all required asset names and byte sizes. Its default is a dry run;
`--apply` updates the local manifest from `validated` to `published` only when the remote release is
complete. A failed creation or upload leaves the record `validated`. Retry reconciliation safely:
existing matching assets are accepted, missing assets remain listed, and a published tag is never
moved. Run catalog validation and regenerate the support matrix after applying reconciliation.

See the normative
[`validated-kernel-release` requirements](../openspec/specs/validated-kernel-release/spec.md).
