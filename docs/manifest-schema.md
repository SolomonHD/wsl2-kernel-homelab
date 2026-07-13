# Kernel manifest schema v2

[`schemas/kernel-manifest-v2.schema.json`](../schemas/kernel-manifest-v2.schema.json) is the
machine-readable contract. `scripts/catalog.py validate` additionally enforces path, checksum,
report-content, lifecycle, and publication relationships that JSON Schema alone cannot express.

Every `manifest.yaml` contains these groups:

| Field | Meaning |
| --- | --- |
| `schema_version` | Integer `2` for this schema |
| `status`, `previous_status` | Current lifecycle state and immediately prior state |
| `failure` | Failed stage and reason; null outside `failed` |
| `upstream` | Canonical Microsoft repository, exact tag, and full commit |
| `kernel_release` | `make kernelrelease` output; null until built |
| `config` | Relative fragment and normalized-config paths plus SHA-256 digests |
| `build` | `x86_64`, compiler identity, and UTC timestamp |
| `artifacts` | Canonical kernel/modules filenames, hashes, byte sizes, and matching kernel releases |
| `validation` | Build/runtime report paths and `pending`, `pass`, or `fail` results |
| `capabilities` | WireGuard, IPv6, Docker, and CONNMARK acceptance; null until tested |
| `publication` | Release tag, URL, timestamp, and optional superseded release |

Unknown lifecycle-dependent values are explicit `null`, never omitted. A planned record still pins
its exact tag and commit and provides every required path. Config hashes are verified against tracked
files when non-null. Planned artifact names, hashes, byte sizes, and releases are null. Built,
validated, and published artifacts require positive `size_bytes`, the kernel name must equal the
exact upstream tag, and the modules name must equal `modules-<upstream-tag>.vhdx`. Artifact hashes
and byte sizes are verified against packaging inputs during release preflight.

Allowed normal transitions are `planned → built → validated → published`. A verification failure
from `planned`, `built`, or `validated` moves to `failed` and requires both `failure.stage` and
`failure.reason`. Resuming work creates a reviewed manifest transition back to the appropriate normal
stage; validate the new record before proceeding. An unpublished `validated` record may return to
`built` only to replace artifacts; it records `previous_status: validated`, clears the validation
timestamp and capability results, and resets runtime validation to pending. Published records are
immutable. Corrected assets
use the release suffix described in [`release.md`](release.md), not a moved tag.

The detailed behavior derives from the
[`versioned-kernel-catalog`](../openspec/specs/versioned-kernel-catalog/spec.md)
and [`validated-kernel-release`](../openspec/specs/validated-kernel-release/spec.md)
requirements.
