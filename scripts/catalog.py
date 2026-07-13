#!/usr/bin/env python3
"""Validate the kernel catalog and generate or verify its support matrix."""

from __future__ import annotations

import argparse
from pathlib import Path

from catalog_lib import CatalogError, print_errors, repository_root, support_matrix, tracked_artifact_errors, validate_catalog

START = "<!-- BEGIN GENERATED SUPPORT MATRIX -->"
END = "<!-- END GENERATED SUPPORT MATRIX -->"


def update_matrix(readme: Path, matrix: str, check: bool) -> int:
    text = readme.read_text(encoding="utf-8")
    if START not in text or END not in text:
        raise CatalogError(f"{readme}: missing generated matrix markers")
    before, remainder = text.split(START, 1)
    _, after = remainder.split(END, 1)
    rendered = f"{before}{START}\n{matrix}\n{END}{after}"
    if check:
        if rendered != text:
            print("ERROR: README support matrix does not match manifests; run scripts/catalog.py matrix")
            return 1
        print("Support matrix matches manifests.")
        return 0
    readme.write_text(rendered, encoding="utf-8")
    print(f"Updated {readme}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate")
    matrix = subparsers.add_parser("matrix")
    matrix.add_argument("--check", action="store_true")
    subparsers.add_parser("tracked-artifacts")
    args = parser.parse_args()
    try:
        root = repository_root(args.root)
        if args.command == "validate":
            errors = validate_catalog(root)
            if not errors:
                print(f"Validated {len(list((root / 'kernels').glob('linux-msft-wsl-*')))} catalog record(s).")
            return print_errors(errors)
        if args.command == "matrix":
            return update_matrix(root / "README.md", support_matrix(root), args.check)
        return print_errors(tracked_artifact_errors(root))
    except (CatalogError, OSError) as exc:
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

