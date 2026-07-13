## Context

The repository currently contains OpenSpec scaffolding, a README, and agent guidance. It does not yet have a stable location for the config and evidence associated with an exact Microsoft kernel tag, nor does it distinguish a merely built kernel from one proven to support the target WireGuard, IPv6, Docker, and CONNMARK workloads.

Kernel images and modules VHDX files are too large and change too often for normal Git history. At the same time, a release is not trustworthy without Git-tracked configuration, provenance, checksums, and test evidence. The structure must connect those lightweight records to externally hosted binaries while preserving the separate pristine Microsoft source clone.

## Goals / Non-Goals

**Goals:**

- Make exact upstream tags the primary organizing key for configs and build evidence.
- Make validation status visible before users download or deploy a build.
- Mirror a confirmed upstream tag into this repository's tag and release namespace.
- Keep binary releases downloadable without growing Git history.
- Give maintainers and agents one consistent set of structure, build, test, and release instructions.
- Support future 6.18 tags without redesigning the repository.

**Non-Goals:**

- Committing Microsoft kernel source or maintaining a source fork.
- Committing kernel images, modules VHDX files, or build trees to Git or Git LFS.
- Automatically declaring the current upstream head supported.
- Defining the kernel build implementation already covered by `configure-6-18-homelab-kernel`.
- Promising permanent hosting or support for every Microsoft tag.

## Decisions

### Organize durable records by exact upstream tag

The catalog root will be `kernels/`, with one directory named exactly after each Microsoft tag:

```text
kernels/
└── linux-msft-wsl-6.18.35.2/
    ├── README.md
    ├── manifest.yaml
    ├── config/
    │   ├── homelab.config
    │   └── config-wsl-homelab
    └── validation/
        ├── build.md
        └── runtime.md
```

The exact tag is globally unique, sortable, and directly traceable upstream. The config fragment shows intentional homelab choices; the normalized config captures the complete build input.

Alternative considered: split paths into `kernels/6.18/35.2/`. That is visually tidy but no longer mirrors the canonical Microsoft tag and complicates tooling and links.

### Use manifests as the catalog source of truth

Each record will include a versioned YAML manifest. The README support matrix will be generated from or checked against manifests so status, commit IDs, checksums, and links do not drift across hand-maintained documents. Human-readable per-tag READMEs explain the intent and notable differences.

Alternative considered: encode all metadata only in Markdown. Markdown is readable but unreliable for validation, automation, and release gating.

### Track lightweight release records in Git and binaries in GitHub Releases

Git will contain configs, manifests, checksums, scripts, documentation, and validation reports. Kernel images and modules VHDX files will be uploaded as release assets. This keeps clones small and makes binary retention and download behavior explicit.

Alternative considered: Git LFS. LFS still makes normal repository operations depend on a large-file service, consumes storage/bandwidth quotas, and obscures the distinction between source records and published builds.

### Gate mirrored tags on validation

A catalog directory can exist in `planned`, `built`, or `failed` state without creating a repository tag. After build and runtime validation pass, an annotated repository tag matching the exact Microsoft tag may be created at the validated record commit, followed by a GitHub Release. The default branch is updated to `published` only after all required assets upload successfully.

This avoids presenting untested builds as releases while preserving a direct upstream-to-homelab tag mapping.

Alternative considered: tag every attempted build. That mirrors upstream more aggressively but makes tags ambiguous and encourages users to consume failed or incomplete builds.

### Keep published tags immutable and suffix exceptional rebuilds

The mirrored tag is immutable. If the packaging or homelab config must be corrected for the same upstream source after publication, the correction uses `<upstream-tag>-homelab.<revision>` and explicitly supersedes the prior release. Normal updates should prefer the next Microsoft tag.

Alternative considered: move or replace the mirrored tag. Moving published tags breaks checksums, caches, citations, and user trust.

### Separate user, contributor, and automation documentation

The root README will focus on purpose, support status, downloads, and quick start. `docs/` will contain build, validation, release, repository-structure, and networking-boundary guides. `CONTRIBUTING.md` will describe the human workflow, while `AGENTS.md` will encode matching automation constraints.

## Risks / Trade-offs

- **GitHub Release quotas or availability limit binary distribution** → Keep manifests and checksums host-independent and document how to reproduce artifacts locally.
- **Exact mirrored tags leave little room for rebuilds** → Keep tags immutable and use a documented `-homelab.<revision>` suffix only for corrections.
- **Manifests and Markdown drift** → Validate schema and generate or compare the support matrix from manifests in CI.
- **Validation evidence becomes stale or subjective** → Define required commands and structured result fields while retaining human-readable logs and environment details.
- **Publishing binaries creates source and license obligations** → Link exact upstream source and commit, retain complete configs and patches, include applicable license notices, and review release packaging before publication.
- **Two active OpenSpec changes overlap around artifact naming** → Treat this change as the repository/release envelope and `configure-6-18-homelab-kernel` as the build/config implementation; reconcile shared names during apply.

## Migration Plan

1. Add manifest schema, catalog templates, ignore rules, and structure validation.
2. Rewrite README and agent guidance, then add contributor and focused `docs/` guides.
3. Create the first `kernels/linux-msft-wsl-6.18.35.2/` planned record using outputs from the active build/config change.
4. Generate or validate the support matrix from the first manifest.
5. Exercise lifecycle validation without publishing a tag or release.
6. After the kernel build passes runtime acceptance, mark the record validated and run the release workflow.
7. Mark it published only after all release assets and checksums are confirmed remotely.

Rollback consists of removing an unpublished catalog entry and reverting documentation changes. Published tags and releases are immutable; corrections use a superseding release rather than deletion or tag movement.

## Open Questions

- Whether future release publication should be fully automated in GitHub Actions or remain an approval-gated local workflow will be decided after the first manual release.
- A secondary artifact mirror can be added later without changing the catalog schema because release URLs and checksums are manifest fields.
