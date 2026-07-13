#!/usr/bin/env python3
"""Verify that a separate Microsoft kernel clone is shallow, pristine, and pinned."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


def git(source: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(source), *args], check=True, text=True, capture_output=True
    )
    return result.stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--expected-commit")
    args = parser.parse_args()
    try:
        source = args.source.resolve()
        if git(source, "rev-parse", "--is-shallow-repository") != "true":
            raise ValueError("source clone is not shallow")
        dirty = git(source, "status", "--porcelain=v1", "--untracked-files=all")
        if dirty:
            raise ValueError("source clone is not pristine")
        head = git(source, "rev-parse", "HEAD")
        if not re.fullmatch(r"[0-9a-f]{40}", head):
            raise ValueError("source HEAD is not a full commit")
        if args.expected_commit and head != args.expected_commit:
            raise ValueError(f"source HEAD {head} does not equal expected commit {args.expected_commit}")
        print(f"Source clone is shallow and pristine at {head}.")
        return 0
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

