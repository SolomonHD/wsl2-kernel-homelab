#!/usr/bin/env python3
"""Check internal Markdown links and repository-boundary policy consistency."""

from __future__ import annotations

import re
from pathlib import Path

from catalog_lib import print_errors, repository_root

LINK_RE = re.compile(r"(?<!!)\[[^]]+\]\(([^)]+)\)")
OBSOLETE_TAG_RE = re.compile(r"linux-msft-wsl-6\.6\.87\.0")
LEGACY_KERNEL_ARTIFACT_RE = re.compile(r"\bbzImage-linux-msft-wsl-")
BROAD_WSL_CONF_EDIT_RE = re.compile(
    r"(?:\brm\b[^\n]*|\btruncate\b[^\n]*|\bcat\b[^\n]*>\s*|\btee\b[^\n]*)/etc/wsl\.conf",
    re.IGNORECASE,
)
MIGRATION_REQUIRED_TEXT = (
    "wsl --version",
    "wsl --update",
    "WSL 2.7.10.0",
    "crossDistro",
    "kernelModules",
    "wsl --shutdown",
    "modinfo",
    "modprobe",
    "Roll back as a pair",
)
CONFLICTS = (
    re.compile(r"\b(?:commit|committing|track|tracking)\s+(?:the\s+)?(?:kernel\s+)?(?:images?|binaries|VHDX)", re.IGNORECASE),
    re.compile(r"kernel source (?:is|may be|can be) (?:stored|committed|vendored) (?:in|to) this", re.IGNORECASE),
)


def markdown_files(root: Path) -> list[Path]:
    files = [root / "README.md", root / "CONTRIBUTING.md", root / "AGENTS.md"]
    files.extend((root / "docs").glob("*.md"))
    files.extend((root / "kernels").glob("*/README.md"))
    return sorted(path for path in files if path.is_file())


def main() -> int:
    root = repository_root()
    errors: list[str] = []
    for path in markdown_files(root):
        text = path.read_text(encoding="utf-8")
        if OBSOLETE_TAG_RE.search(text):
            errors.append(f"{path.relative_to(root)}: obsolete example tag")
        if LEGACY_KERNEL_ARTIFACT_RE.search(text):
            errors.append(f"{path.relative_to(root)}: legacy kernel artifact name")
        if BROAD_WSL_CONF_EDIT_RE.search(text):
            errors.append(f"{path.relative_to(root)}: broad /etc/wsl.conf replacement or removal")
        for pattern in CONFLICTS:
            match = pattern.search(text)
            if match and "never " not in text[max(0, match.start() - 12):match.start()].lower():
                errors.append(f"{path.relative_to(root)}: conflicting storage policy near {match.group(0)!r}")
        for raw_target in LINK_RE.findall(text):
            target = raw_target.strip().split("#", 1)[0]
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            destination = (path.parent / target).resolve()
            try:
                destination.relative_to(root)
            except ValueError:
                errors.append(f"{path.relative_to(root)}: internal link escapes repository: {raw_target}")
                continue
            if not destination.exists():
                errors.append(f"{path.relative_to(root)}: broken internal link: {raw_target}")
    migration = root / "docs" / "wsl-kernel-migration.md"
    if not migration.is_file():
        errors.append("docs/wsl-kernel-migration.md: missing migration guide")
    else:
        migration_text = migration.read_text(encoding="utf-8")
        for required in MIGRATION_REQUIRED_TEXT:
            if required not in migration_text:
                errors.append(
                    f"docs/wsl-kernel-migration.md: missing required migration guidance {required!r}"
                )
    if not errors:
        print(f"Validated {len(markdown_files(root))} documentation files.")
    return print_errors(errors)


if __name__ == "__main__":
    raise SystemExit(main())
