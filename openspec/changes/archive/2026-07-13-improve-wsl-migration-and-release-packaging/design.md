## Context

The first validated catalog build produced a working kernel/modules pair, but deploying it exposed
prerequisites that are absent from the current user path. Older WSL installations do not correctly
accept the `.wslconfig` `kernelModules` path, `.wslconfig` applies globally rather than to one test
distribution, and an obsolete `automount.crossDistro` entry in `/etc/wsl.conf` is rejected by
current WSL. Those conditions need an explicit migration path rather than being left to runtime
troubleshooting.

Publication is separately blocked by artifact shape. The current modules staging tree retains
DWARF debug data and produces a 2,944,401,408-byte VHDX, while GitHub Releases requires each asset
to be smaller than 2 GiB. Analysis of the staged modules found about 1.42 GB in `.debug*` sections;
the debug payload is not needed to load or run the modules. The catalog record is validated but has
not been published, so its artifacts and evidence can be replaced and revalidated without creating
a correction release.

The current kernel artifact is named `bzImage-linux-msft-wsl-6.18.35.2`. The desired public and
local filename is the exact upstream tag, `linux-msft-wsl-6.18.35.2`, while the modules VHDX keeps
its `modules-` prefix so the pair remains unambiguous.

## Goals / Non-Goals

**Goals:**

- Give users a short, safe migration from the stock or an older custom WSL kernel.
- Produce runtime module media below GitHub Releases' per-file limit without removing required
  module functionality or changing Microsoft kernel source.
- Rename the kernel binary consistently across build output, manifests, checksums, release tooling,
  documentation, tests, and deployment examples.
- Make artifact byte size a validated part of release provenance and fail oversized packages before
  any tag or remote release operation.
- Rebuild and revalidate the unpublished baseline through an explicit, legal lifecycle transition.

**Non-Goals:**

- Changing the required homelab `CONFIG_*` values or converting modular features to built-ins.
- Publishing debug-symbol packages, headers, Microsoft kernel source, or source patches.
- Using Git LFS, GitHub Packages, or an OCI wrapper as the normal download path.
- Automatically editing a user's `.wslconfig` or `/etc/wsl.conf`.
- Publishing or mutating a GitHub Release as part of implementation.

## Decisions

### Strip only the installed runtime module tree

The build will continue compiling the same modular features with the normalized configuration. The
`modules_install` step will pass `INSTALL_MOD_STRIP=1`, which uses the kernel build system's
`--strip-debug` behavior before the staging tree is handed to Microsoft's
`gen_modules_vhdx.sh`. The out-of-tree build products remain available locally for diagnostics, but
only stripped runtime modules enter the VHDX.

This keeps `CONFIG_WIREGUARD=m`, CONNMARK/netfilter modules, container networking modules, and every
other selected modular feature modular. It changes packaging, not kernel feature selection. Build
evidence will verify that staged `.ko` files no longer contain `.debug*` sections, while runtime
evidence will re-run module identity, `modinfo`, `modprobe`, WireGuard, Docker, IPv6, and CONNMARK
acceptance.

Alternative considered: enable in-kernel module compression. That would change the normalized
kernel configuration and module loader requirements, and it is unnecessary if stripping brings the
VHDX below the hosting limit. Alternative considered: compress or split the completed VHDX. That
adds an extraction or assembly step for every user and weakens the direct `.wslconfig` download
path.

### Use canonical artifact names derived from the upstream tag

For `linux-msft-wsl-6.18.35.2`, the kernel file will be named exactly
`linux-msft-wsl-6.18.35.2`. The matching modules file remains
`modules-linux-msft-wsl-6.18.35.2.vhdx`. The exact names will be generated from the manifest's
upstream tag rather than maintained as independent constants.

Alternative considered: keep the `bzImage-` prefix. It exposes a build-format detail in the user
contract and conflicts with the requested simple, tag-addressed download name.

### Record byte sizes in manifest schema version 2

Both binary artifact records will gain a required `size_bytes` field. Planned records use null;
`built`, `validated`, and `published` records require a positive integer matching the packaging
input. The manifest schema version will advance to 2, and the template, baseline, fixtures,
documentation, catalog validation, and release preflight will migrate together.

Checksums remain the identity authority; byte sizes provide early validation and allow the release
plan to explain why an asset is rejected without attempting an upload.

Alternative considered: inspect sizes only during upload. That makes the local plan incomplete and
allows known-invalid publication attempts to proceed too far.

### Enforce GitHub's limit before tag creation

Release preflight will reject each required release asset whose actual size is greater than or
equal to 2 GiB (`2 * 1024 * 1024 * 1024` bytes), or whose actual size differs from the manifest.
The check applies to the final files users download and runs for preflight, plan, package,
create-tag, and reconciliation paths as appropriate. GitHub Releases remains the publication
channel because it supports the simplified kernel and stripped VHDX directly without package
client authentication or OCI extraction.

### Permit revalidation of an unpublished validated record

The lifecycle will allow `validated -> built` only when every publication field remains null. The
rebuild replaces checksums and sizes, resets runtime validation to pending, and records the prior
validated state. Runtime acceptance then returns the record through `built -> validated`. A
published record remains immutable and cannot use this transition.

Alternative considered: mark the record failed before rebuilding. Failure would misrepresent an
intentional packaging correction and obscure the reason evidence was invalidated.

### Keep migration documentation explicit and non-destructive

The migration guide will require users to inspect and back up both configuration files. It will
direct them to run `wsl --version`, update WSL when needed, remove only the unsupported
`crossDistro` line from `[automount]`, place the checksummed artifact pair at stable Windows paths,
and update both `.wslconfig` keys together. It will warn that `.wslconfig` affects every WSL2
distribution and will include activation checks and pairwise rollback.

The guide will cite the baseline tested on WSL 2.7.10.0 but use `wsl --update` rather than freezing a
minimum version that could become stale.

## Risks / Trade-offs

- **Stripping unexpectedly removes data required by a module** → Rebuild from the same config and
  require complete runtime acceptance before restoring `validated` status.
- **The stripped VHDX still reaches 2 GiB** → Keep the record at `built` or `failed`, report the
  measured size, and propose module compression or external object storage separately.
- **Renaming breaks scripts or existing local `.wslconfig` paths** → Treat the rename as breaking,
  update every manifest/tool/test/documentation reference, and make the migration guide show both
  replacement and rollback paths.
- **Users remove unrelated `wsl.conf` configuration** → Show a targeted edit that removes only
  `crossDistro`, requires a backup, and preserves supported automount settings.
- **Global `.wslconfig` changes disrupt other distributions** → State the global scope before the
  edit and require shutdown, verification, and rollback as one controlled sequence.
- **Allowing lifecycle regression weakens immutability** → Permit `validated -> built` only before
  publication and reject the transition whenever publication metadata exists.

## Migration Plan

1. Update the manifest schema, catalog validator, templates, and fixtures for schema version 2 and
   artifact `size_bytes`.
2. Update build output naming and install staged modules with `INSTALL_MOD_STRIP=1`.
3. Add release size/name checks and update packaging, plans, annotations, and reconciliation.
4. Add the migration guide and reconcile all README, build, release, contributor, and agent-facing
   examples.
5. Invalidate the unpublished baseline's old runtime evidence, transition it from `validated` to
   `built`, and perform a clean rebuild with the simplified kernel name and stripped VHDX.
6. Verify filenames, sizes, checksums, absence of staged `.debug*` sections, pristine source state,
   and all build/catalog/documentation tests.
7. Deploy the new pair on current WSL, repeat runtime acceptance, and transition back to
   `validated` only after every check passes.
8. Run release preflight and plan; leave actual tag creation and GitHub publication approval-gated.

Rollback before publication restores the prior ignored artifacts and reverts the catalog change.
After publication, normal immutable-tag and superseding-release rules apply.

## Open Questions

- Whether to publish a separate debug-symbol artifact can be considered later; it is deliberately
  excluded from the first public runtime release.
- An external object-storage mirror remains a future option if later kernel configurations cannot
  stay below GitHub's per-asset limit after safe runtime stripping.
