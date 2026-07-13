#!/usr/bin/env python3
"""Validation-gated, retry-safe release preparation for catalog kernels."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from catalog_lib import (
    CatalogError,
    RELEASE_TAG_RE,
    load_manifest,
    repository_root,
    sha256_file,
    validate_record,
    write_manifest,
)

MAX_RELEASE_ASSET_BYTES = 2 * 1024 * 1024 * 1024


def record_for_release(root: Path, release_tag: str) -> tuple[Path, dict[str, Any]]:
    match = RELEASE_TAG_RE.fullmatch(release_tag)
    if not match:
        raise CatalogError(f"malformed release tag: {release_tag}")
    upstream_tag = match.group(1)
    record = root / "kernels" / upstream_tag
    if not record.is_dir():
        raise CatalogError(f"no catalog record for {upstream_tag}")
    errors = validate_record(record)
    if errors:
        raise CatalogError("catalog validation failed:\n" + "\n".join(errors))
    return record, load_manifest(record / "manifest.yaml")


def expected_assets(manifest: dict[str, Any]) -> list[str]:
    return [
        manifest["artifacts"]["kernel"]["name"],
        manifest["artifacts"]["modules_vhdx"]["name"],
        "manifest.yaml",
        Path(manifest["config"]["normalized"]["path"]).name,
        "SHA256SUMS",
    ]


def verify_artifacts(manifest: dict[str, Any], artifacts: Path) -> None:
    if not artifacts.is_dir():
        raise CatalogError(f"artifact directory does not exist: {artifacts}")
    for key in ("kernel", "modules_vhdx"):
        item = manifest["artifacts"][key]
        path = artifacts / item["name"]
        if not path.is_file():
            raise CatalogError(f"missing {key} artifact: {path}")
        actual_size = path.stat().st_size
        if actual_size >= MAX_RELEASE_ASSET_BYTES:
            raise CatalogError(
                f"{key} artifact {path.name} is {actual_size} bytes; each release asset must be "
                f"smaller than {MAX_RELEASE_ASSET_BYTES} bytes"
            )
        if actual_size != item["size_bytes"]:
            raise CatalogError(
                f"{key} size mismatch: expected {item['size_bytes']}, got {actual_size}"
            )
        actual = sha256_file(path)
        if actual != item["sha256"]:
            raise CatalogError(f"{key} checksum mismatch: expected {item['sha256']}, got {actual}")


def preflight(
    root: Path,
    release_tag: str,
    artifacts: Path,
    correction_reason: str | None = None,
    allow_published: bool = False,
) -> tuple[Path, dict[str, Any]]:
    record, manifest = record_for_release(root, release_tag)
    allowed = {"validated", "published"} if allow_published else {"validated"}
    if manifest["status"] not in allowed:
        raise CatalogError(
            f"release requires validated status; {manifest['upstream']['tag']} is {manifest['status']}"
        )
    release_match = RELEASE_TAG_RE.fullmatch(release_tag)
    assert release_match is not None
    revision = release_match.group(2)
    if revision:
        if not correction_reason:
            raise CatalogError("corrected release tags require --correction-reason")
        if manifest["publication"]["supersedes"] is None:
            raise CatalogError("corrected releases require publication.supersedes")
    elif correction_reason:
        raise CatalogError("--correction-reason is valid only for a -homelab.<revision> release")
    verify_artifacts(manifest, artifacts)
    return record, manifest


def release_notes(record: Path, manifest: dict[str, Any], release_tag: str, reason: str | None) -> str:
    upstream = manifest["upstream"]
    lines = [
        f"Validated WSL2 homelab kernel for `{upstream['tag']}`.",
        "",
        f"- Microsoft source: {upstream['repository']}/tree/{upstream['tag']}",
        f"- Upstream commit: `{upstream['commit']}`",
        f"- Catalog manifest: `kernels/{upstream['tag']}/manifest.yaml`",
        f"- Normalized config: `kernels/{upstream['tag']}/{manifest['config']['normalized']['path']}`",
        f"- Build report: `kernels/{upstream['tag']}/{manifest['validation']['build']['report']}`",
        f"- Runtime report: `kernels/{upstream['tag']}/{manifest['validation']['runtime']['report']}`",
        "- Build instructions: `docs/build-and-deploy.md`",
        "- Source changes: none; this is a config-only build of unmodified Microsoft source.",
        "- License: GPL-2.0; exact source provenance is linked above.",
    ]
    if reason:
        lines.extend(
            [
                "",
                f"Correction release `{release_tag}`: {reason}",
                f"Supersedes: {manifest['publication']['supersedes']}",
            ]
        )
    return "\n".join(lines) + "\n"


def annotation(manifest: dict[str, Any], release_tag: str, reason: str | None) -> str:
    upstream = manifest["upstream"]
    kernel = manifest["artifacts"]["kernel"]
    modules = manifest["artifacts"]["modules_vhdx"]
    lines = [
        f"Validated WSL2 homelab kernel {release_tag}",
        "",
        f"Microsoft source: {upstream['repository']}",
        f"Upstream tag: {upstream['tag']}",
        f"Upstream commit: {upstream['commit']}",
        f"Manifest: kernels/{upstream['tag']}/manifest.yaml",
        f"{kernel['name']}: {kernel['sha256']}",
        f"{kernel['name']} size: {kernel['size_bytes']} bytes",
        f"{modules['name']}: {modules['sha256']}",
        f"{modules['name']} size: {modules['size_bytes']} bytes",
    ]
    if reason:
        lines.append(f"Correction reason: {reason}")
    return "\n".join(lines)


def package(root: Path, record: Path, manifest: dict[str, Any], artifacts: Path, output: Path) -> None:
    verify_artifacts(manifest, artifacts)
    output = output.resolve()
    kernels_root = (root / "kernels").resolve()
    if output == kernels_root or kernels_root in output.parents:
        raise CatalogError("release packages must not be written under tracked kernels/")
    output.mkdir(parents=True, exist_ok=True)
    inputs = [
        artifacts / manifest["artifacts"]["kernel"]["name"],
        artifacts / manifest["artifacts"]["modules_vhdx"]["name"],
    ]
    for source in inputs:
        shutil.copy2(source, output / source.name)
    shutil.copy2(record / "manifest.yaml", output / "manifest.yaml")
    normalized = record / manifest["config"]["normalized"]["path"]
    shutil.copy2(normalized, output / normalized.name)
    checksum_paths = [output / source.name for source in inputs]
    checksum_paths.extend((output / "manifest.yaml", output / normalized.name))
    sums = "".join(f"{sha256_file(path)}  {path.name}\n" for path in checksum_paths)
    (output / "SHA256SUMS").write_text(sums, encoding="utf-8")
    for path in output.iterdir():
        if path.is_file() and path.stat().st_size >= MAX_RELEASE_ASSET_BYTES:
            raise CatalogError(
                f"packaged asset {path.name} is {path.stat().st_size} bytes; each release asset "
                f"must be smaller than {MAX_RELEASE_ASSET_BYTES} bytes"
            )


def plan(record: Path, manifest: dict[str, Any], release_tag: str, artifacts: Path, reason: str | None) -> None:
    print("Release dry run (no state changes)")
    print(f"Annotated tag: {release_tag}")
    print(f"Release title: WSL2 homelab kernel {release_tag}")
    print(f"Catalog record: {record}")
    print("Assets:")
    for asset in expected_assets(manifest):
        size = next(
            (
                item["size_bytes"]
                for item in manifest["artifacts"].values()
                if item["name"] == asset
            ),
            None,
        )
        suffix = f" ({size} bytes)" if size is not None else ""
        print(f"  - {asset}{suffix}")
    print("Catalog update after remote confirmation: validated -> published; set release URL and timestamps")
    print("Release notes:")
    print(release_notes(record, manifest, release_tag, reason), end="")


def create_tag(
    root: Path,
    manifest: dict[str, Any],
    release_tag: str,
    target: str,
    reason: str | None,
    apply: bool,
) -> None:
    target_commit = subprocess.run(
        ["git", "rev-parse", "--verify", f"{target}^{{commit}}"],
        cwd=root,
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()
    existing = subprocess.run(
        ["git", "rev-parse", "--verify", f"refs/tags/{release_tag}^{{commit}}"],
        cwd=root,
        text=True,
        capture_output=True,
    )
    if existing.returncode == 0:
        raise CatalogError(
            f"immutable release tag already exists at {existing.stdout.strip()}; it will not be moved"
        )
    message = annotation(manifest, release_tag, reason)
    print(f"Tag target: {target_commit}")
    print(message)
    if not apply:
        print("Dry run only; pass --apply to create the local annotated tag.")
        return
    subprocess.run(
        ["git", "tag", "--annotate", release_tag, target_commit, "--message", message],
        cwd=root,
        check=True,
    )
    print(f"Created immutable local annotated tag {release_tag} at {target_commit}")


def remote_release(root: Path, release_tag: str) -> dict[str, Any]:
    try:
        result = subprocess.run(
            ["gh", "release", "view", release_tag, "--json", "tagName,url,isDraft,assets"],
            cwd=root,
            text=True,
            capture_output=True,
        )
    except FileNotFoundError as exc:
        raise CatalogError("GitHub CLI 'gh' is required for publication reconciliation") from exc
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise CatalogError(f"remote release {release_tag} was not found: {detail}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise CatalogError("GitHub CLI returned invalid release metadata") from exc


def reconcile(
    root: Path,
    record: Path,
    manifest: dict[str, Any],
    release_tag: str,
    apply: bool,
) -> None:
    remote = remote_release(root, release_tag)
    if remote.get("tagName") != release_tag:
        raise CatalogError("remote release tag does not match requested tag")
    if remote.get("isDraft"):
        raise CatalogError("remote release is still a draft")
    remote_assets = {asset.get("name"): asset for asset in remote.get("assets", [])}
    remote_names = set(remote_assets)
    missing = [name for name in expected_assets(manifest) if name not in remote_names]
    if missing:
        raise CatalogError("remote release is incomplete; missing assets: " + ", ".join(missing))
    for name in expected_assets(manifest):
        remote_size = remote_assets[name].get("size")
        if not isinstance(remote_size, int):
            raise CatalogError(f"remote release asset {name} has no usable byte size")
        if remote_size >= MAX_RELEASE_ASSET_BYTES:
            raise CatalogError(
                f"remote release asset {name} is {remote_size} bytes; each asset must be smaller "
                f"than {MAX_RELEASE_ASSET_BYTES} bytes"
            )
    for item in manifest["artifacts"].values():
        remote_size = remote_assets[item["name"]]["size"]
        if remote_size != item["size_bytes"]:
            raise CatalogError(
                f"remote asset {item['name']} size mismatch: expected {item['size_bytes']}, "
                f"got {remote_size}"
            )
    url = remote.get("url")
    if not isinstance(url, str) or not url.startswith("https://github.com/"):
        raise CatalogError("remote release URL is missing or invalid")
    print(f"Confirmed remote release {url} and all required assets.")
    if manifest["status"] == "published":
        if manifest["publication"]["release_tag"] != release_tag or manifest["publication"]["release_url"] != url:
            raise CatalogError("published manifest conflicts with confirmed remote release")
        print("Catalog is already reconciled; no update required.")
        return
    if not apply:
        print("Dry run only; pass --apply to mark the local catalog record published.")
        return
    manifest["previous_status"] = "validated"
    manifest["status"] = "published"
    manifest["publication"]["release_tag"] = release_tag
    manifest["publication"]["release_url"] = url
    manifest["publication"]["published_at"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    write_manifest(record / "manifest.yaml", manifest)
    subprocess.run([sys.executable, str(root / "scripts" / "catalog.py"), "matrix"], cwd=root, check=True)
    print("Updated catalog status to published and regenerated the support matrix.")


def add_common_release_args(parser: argparse.ArgumentParser, artifacts: bool = True) -> None:
    parser.add_argument("--tag", required=True)
    if artifacts:
        parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--correction-reason")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("preflight", "plan"):
        add_common_release_args(commands.add_parser(name))
    package_parser = commands.add_parser("package")
    add_common_release_args(package_parser)
    package_parser.add_argument("--output", type=Path, required=True)
    tag_parser = commands.add_parser("create-tag")
    add_common_release_args(tag_parser)
    tag_parser.add_argument("--target", default="HEAD")
    tag_parser.add_argument("--apply", action="store_true")
    reconcile_parser = commands.add_parser("reconcile")
    add_common_release_args(reconcile_parser)
    reconcile_parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    try:
        root = repository_root(args.root)
        record, manifest = preflight(
            root,
            args.tag,
            args.artifacts.resolve(),
            args.correction_reason,
            allow_published=args.command == "reconcile",
        )
        if args.command == "preflight":
            print(f"Release preflight passed for {args.tag}.")
        elif args.command == "plan":
            plan(record, manifest, args.tag, args.artifacts, args.correction_reason)
        elif args.command == "package":
            package(root, record, manifest, args.artifacts.resolve(), args.output)
            print(f"Packaged release assets in {args.output.resolve()}")
        elif args.command == "create-tag":
            create_tag(root, manifest, args.tag, args.target, args.correction_reason, args.apply)
        else:
            reconcile(root, record, manifest, args.tag, args.apply)
        return 0
    except (CatalogError, OSError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
