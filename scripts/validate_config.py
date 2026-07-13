#!/usr/bin/env python3
"""Validate a normalized kernel configuration against a required fragment."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


SET_RE = re.compile(r"^(CONFIG_[A-Za-z0-9_]+)=(.*)$")
UNSET_RE = re.compile(r"^# (CONFIG_[A-Za-z0-9_]+) is not set$")


class ConfigError(ValueError):
    """A kernel config cannot be parsed or does not satisfy its contract."""


@dataclass(frozen=True)
class Mismatch:
    symbol: str
    expected: str
    actual: str | None

    def render(self) -> str:
        if self.actual is None:
            return f"{self.symbol}: missing (expected {self.expected})"
        return f"{self.symbol}: expected {self.expected}, got {self.actual}"


def parse_config(path: Path) -> dict[str, str]:
    """Return CONFIG symbol values, normalizing disabled symbols to ``n``."""
    values: dict[str, str] = {}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ConfigError(f"cannot read {path}: {exc}") from exc

    for line_number, line in enumerate(lines, start=1):
        match = SET_RE.fullmatch(line) or UNSET_RE.fullmatch(line)
        if not match:
            continue
        symbol = match.group(1)
        value = match.group(2) if line.startswith("CONFIG_") else "n"
        previous = values.get(symbol)
        if previous is not None and previous != value:
            raise ConfigError(
                f"{path}:{line_number}: {symbol} is defined as both {previous} and {value}"
            )
        values[symbol] = value
    return values


def validate_config(required_path: Path, config_path: Path) -> list[Mismatch]:
    """Compare all symbols declared by ``required_path`` with ``config_path``."""
    required = parse_config(required_path)
    if not required:
        raise ConfigError(f"required fragment contains no CONFIG symbols: {required_path}")
    actual = parse_config(config_path)
    return [
        Mismatch(symbol, expected, actual.get(symbol))
        for symbol, expected in sorted(required.items())
        if actual.get(symbol) != expected
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check every CONFIG value in a required fragment against a normalized config."
    )
    parser.add_argument("--required", type=Path, required=True, help="required config fragment")
    parser.add_argument("--config", type=Path, required=True, help="normalized .config to check")
    args = parser.parse_args(argv)

    try:
        mismatches = validate_config(args.required, args.config)
    except ConfigError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if mismatches:
        for mismatch in mismatches:
            print(f"ERROR: {mismatch.render()}", file=sys.stderr)
        print(
            f"Config validation failed: {len(mismatches)} required symbol(s) mismatched.",
            file=sys.stderr,
        )
        return 1

    required_count = len(parse_config(args.required))
    print(f"Config validation passed: {required_count} required symbol(s) match.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
