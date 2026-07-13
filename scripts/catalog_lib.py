#!/usr/bin/env python3
"""Shared validation and rendering helpers for the versioned kernel catalog."""

from __future__ import annotations

import hashlib
import re
import subprocess
from pathlib import Path
from typing import Any, Iterable

try:
    import yaml
except ImportError as exc:  # pragma: no cover - dependency error is user-facing
    raise SystemExit("PyYAML is required; install dependencies with: python3 -m pip install -r requirements.txt") from exc


UPSTREAM_TAG_RE = re.compile(r"^linux-msft-wsl-\d+\.\d+\.\d+\.\d+$")
RELEASE_TAG_RE = re.compile(r"^(linux-msft-wsl-\d+\.\d+\.\d+\.\d+)(?:-homelab\.([1-9]\d*))?$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
STATUSES = ("planned", "built", "validated", "published", "failed")
TRANSITIONS = {
    "planned": {None, "failed"},
    "built": {"planned", "failed", "validated"},
    "validated": {"built", "failed"},
    "published": {"validated"},
    "failed": {"planned", "built", "validated"},
}
REQUIRED_FILES = (
    "README.md",
    "manifest.yaml",
    "config/homelab.config",
    "config/config-wsl-homelab",
    "validation/build.md",
    "validation/runtime.md",
)
FORBIDDEN_TRACKED_PATTERNS = (
    re.compile(r"^(?:arch|block|crypto|drivers|fs|include|init|io_uring|ipc|kernel|lib|mm|net|rust|security|sound|tools|usr|virt)/"),
    re.compile(r"(^|/)(?:build|out|output|dist|artifacts|modules-staging)(/|$)"),
    re.compile(r"(^|/)(?:bzImage|vmlinux|System\.map|Module\.symvers|modules\.order)$"),
    re.compile(r"\.(?:vhdx?|qcow2|img)$", re.IGNORECASE),
)


class CatalogError(ValueError):
    """A catalog record failed validation."""


def repository_root(start: Path | None = None) -> Path:
    candidate = (start or Path.cwd()).resolve()
    for path in (candidate, *candidate.parents):
        if (path / "kernels").is_dir() and (path / "openspec").is_dir():
            return path
    raise CatalogError("could not locate repository root containing kernels/ and openspec/")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest(path: Path) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise CatalogError(f"{path}: cannot read YAML: {exc}") from exc
    if not isinstance(value, dict):
        raise CatalogError(f"{path}: manifest root must be a mapping")
    return value


def write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(manifest, sort_keys=False, width=100), encoding="utf-8")


def nested(data: dict[str, Any], dotted: str) -> Any:
    value: Any = data
    for part in dotted.split("."):
        if not isinstance(value, dict) or part not in value:
            raise CatalogError(f"missing required field: {dotted}")
        value = value[part]
    return value


def _require_fields(manifest: dict[str, Any]) -> None:
    fields = (
        "schema_version",
        "status",
        "previous_status",
        "failure.stage",
        "failure.reason",
        "upstream.repository",
        "upstream.tag",
        "upstream.commit",
        "kernel_release",
        "config.fragment.path",
        "config.fragment.sha256",
        "config.normalized.path",
        "config.normalized.sha256",
        "build.architecture",
        "build.compiler",
        "build.timestamp",
        "artifacts.kernel.name",
        "artifacts.kernel.sha256",
        "artifacts.kernel.size_bytes",
        "artifacts.kernel.kernel_release",
        "artifacts.modules_vhdx.name",
        "artifacts.modules_vhdx.sha256",
        "artifacts.modules_vhdx.size_bytes",
        "artifacts.modules_vhdx.kernel_release",
        "validation.build.report",
        "validation.build.status",
        "validation.runtime.report",
        "validation.runtime.status",
        "validation.validated_at",
        "capabilities.wireguard",
        "capabilities.ipv6",
        "capabilities.docker",
        "capabilities.connmark",
        "publication.release_tag",
        "publication.release_url",
        "publication.published_at",
        "publication.supersedes",
    )
    for field in fields:
        nested(manifest, field)


def _validate_checksum(record_dir: Path, label: str, path_value: Any, checksum: Any) -> None:
    if checksum is None:
        return
    if not isinstance(checksum, str) or not SHA256_RE.fullmatch(checksum):
        raise CatalogError(f"{label}.sha256 must be null or a lowercase SHA-256 digest")
    if not isinstance(path_value, str):
        raise CatalogError(f"{label}.path must be a string")
    path = record_dir / path_value
    if not path.is_file():
        raise CatalogError(f"{label}.path does not exist: {path_value}")
    actual = sha256_file(path)
    if actual != checksum:
        raise CatalogError(f"{label}.sha256 mismatch: expected {checksum}, got {actual}")


def _validate_report(record_dir: Path, report: Any, status: Any, label: str) -> None:
    if status not in ("pending", "pass", "fail"):
        raise CatalogError(f"validation.{label}.status must be pending, pass, or fail")
    if not isinstance(report, str) or not (record_dir / report).is_file():
        raise CatalogError(f"validation.{label}.report does not exist: {report!r}")
    text = (record_dir / report).read_text(encoding="utf-8")
    expected = {"pending": "PENDING", "pass": "PASS", "fail": "FAIL"}[status]
    if f"Result: {expected}" not in text:
        raise CatalogError(f"validation.{label}.report must contain 'Result: {expected}'")


def validate_record(record_dir: Path) -> list[str]:
    errors: list[str] = []
    tag = record_dir.name
    if not UPSTREAM_TAG_RE.fullmatch(tag):
        return [f"{record_dir}: malformed upstream tag directory name"]
    for required in REQUIRED_FILES:
        if not (record_dir / required).is_file():
            errors.append(f"{record_dir}: missing required file {required}")
    if errors:
        return errors

    try:
        manifest = load_manifest(record_dir / "manifest.yaml")
        _require_fields(manifest)
        if manifest["schema_version"] != 2:
            raise CatalogError("schema_version must equal 2")
        status = manifest["status"]
        previous = manifest["previous_status"]
        if status not in STATUSES:
            raise CatalogError(f"status must be one of: {', '.join(STATUSES)}")
        if previous not in TRANSITIONS[status]:
            raise CatalogError(f"illegal lifecycle transition: {previous!r} -> {status!r}")
        if nested(manifest, "upstream.tag") != tag:
            raise CatalogError("upstream.tag must exactly match the record directory")
        if nested(manifest, "upstream.repository") != "https://github.com/microsoft/WSL2-Linux-Kernel":
            raise CatalogError("upstream.repository must identify microsoft/WSL2-Linux-Kernel")
        commit = nested(manifest, "upstream.commit")
        if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}", commit):
            raise CatalogError("upstream.commit must be a full lowercase Git commit")

        fragment = nested(manifest, "config.fragment")
        normalized = nested(manifest, "config.normalized")
        _validate_checksum(record_dir, "config.fragment", fragment["path"], fragment["sha256"])
        _validate_checksum(record_dir, "config.normalized", normalized["path"], normalized["sha256"])

        expected_names = {
            "kernel": tag,
            "modules_vhdx": f"modules-{tag}.vhdx",
        }
        for artifact_key in ("kernel", "modules_vhdx"):
            artifact = nested(manifest, f"artifacts.{artifact_key}")
            name, checksum, size = artifact["name"], artifact["sha256"], artifact["size_bytes"]
            if name is not None and name != expected_names[artifact_key]:
                raise CatalogError(
                    f"artifacts.{artifact_key}.name must equal {expected_names[artifact_key]!r}"
                )
            if checksum is not None and (not isinstance(checksum, str) or not SHA256_RE.fullmatch(checksum)):
                raise CatalogError(f"artifacts.{artifact_key}.sha256 must be null or a lowercase SHA-256 digest")
            if size is not None and (isinstance(size, bool) or not isinstance(size, int) or size <= 0):
                raise CatalogError(f"artifacts.{artifact_key}.size_bytes must be null or a positive integer")

        _validate_report(record_dir, nested(manifest, "validation.build.report"), nested(manifest, "validation.build.status"), "build")
        _validate_report(record_dir, nested(manifest, "validation.runtime.report"), nested(manifest, "validation.runtime.status"), "runtime")

        publication = nested(manifest, "publication")
        if status == "planned":
            if manifest["kernel_release"] is not None or manifest["build"]["timestamp"] is not None:
                raise CatalogError("planned records cannot claim a kernel release or build timestamp")
            for key in ("kernel", "modules_vhdx"):
                artifact = manifest["artifacts"][key]
                if any(artifact[field] is not None for field in ("name", "sha256", "size_bytes", "kernel_release")):
                    raise CatalogError(f"planned records require null {key} artifact fields")
        if status in ("built", "validated", "published"):
            release = manifest["kernel_release"]
            if not release or manifest["build"]["compiler"] is None or manifest["build"]["timestamp"] is None:
                raise CatalogError(f"{status} records require kernel_release, compiler, and build timestamp")
            if normalized["sha256"] is None:
                raise CatalogError(f"{status} records require a normalized config checksum")
            for key in ("kernel", "modules_vhdx"):
                artifact = manifest["artifacts"][key]
                if artifact["name"] is None or artifact["sha256"] is None or artifact["size_bytes"] is None:
                    raise CatalogError(f"{status} records require {key} name, checksum, and size_bytes")
                if artifact["kernel_release"] != release:
                    raise CatalogError(f"artifacts.{key}.kernel_release must match kernel_release")
        if status == "built" and previous == "validated":
            if manifest["validation"]["runtime"]["status"] != "pending":
                raise CatalogError("validated -> built requires pending runtime validation")
            if manifest["validation"]["validated_at"] is not None:
                raise CatalogError("validated -> built requires null validation.validated_at")
            if any(value is not None for value in manifest["capabilities"].values()):
                raise CatalogError("validated -> built requires cleared runtime capabilities")
        if status in ("validated", "published"):
            if manifest["validation"]["build"]["status"] != "pass" or manifest["validation"]["runtime"]["status"] != "pass":
                raise CatalogError(f"{status} records require passing build and runtime reports")
            if manifest["validation"]["validated_at"] is None:
                raise CatalogError(f"{status} records require validation.validated_at")
        if status == "failed":
            if manifest["failure"]["stage"] is None or manifest["failure"]["reason"] is None:
                raise CatalogError("failed records require failure.stage and failure.reason")
        elif manifest["failure"]["stage"] is not None or manifest["failure"]["reason"] is not None:
            raise CatalogError("non-failed records must have null failure fields")
        if status == "published":
            if not all(publication.get(key) for key in ("release_tag", "release_url", "published_at")):
                raise CatalogError("published records require release_tag, release_url, and published_at")
            if not RELEASE_TAG_RE.fullmatch(publication["release_tag"]):
                raise CatalogError("publication.release_tag is malformed")
        elif any(publication.get(key) is not None for key in ("release_tag", "release_url", "published_at")):
            raise CatalogError("unpublished records must have null release tag, URL, and timestamp")
    except CatalogError as exc:
        errors.append(f"{record_dir / 'manifest.yaml'}: {exc}")
    return errors


def catalog_records(root: Path) -> list[Path]:
    kernels = root / "kernels"
    if not kernels.is_dir():
        raise CatalogError(f"missing catalog directory: {kernels}")
    return sorted(path for path in kernels.iterdir() if path.is_dir() and not path.name.startswith("_"))


def validate_catalog(root: Path) -> list[str]:
    errors: list[str] = []
    seen_tags: set[str] = set()
    for record in catalog_records(root):
        if record.name in seen_tags:
            errors.append(f"duplicate catalog tag: {record.name}")
        seen_tags.add(record.name)
        errors.extend(validate_record(record))
    return errors


def support_matrix(root: Path) -> str:
    rows = [
        "| Upstream tag | Commit | Kernel release | Status | Validated | Capabilities | Release |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for record in catalog_records(root):
        manifest = load_manifest(record / "manifest.yaml")
        tag = manifest["upstream"]["tag"]
        commit = manifest["upstream"]["commit"][:12]
        release = manifest["kernel_release"] or "Pending"
        status = manifest["status"]
        validated = manifest["validation"]["validated_at"] or "Not validated"
        capabilities = ", ".join(
            name for name, enabled in manifest["capabilities"].items() if enabled is True
        ) or "Pending validation"
        url = manifest["publication"]["release_url"]
        release_link = f"[Download]({url})" if status == "published" and url else "Not available"
        rows.append(
            f"| [{tag}](kernels/{tag}/) | `{commit}` | {release} | **{status}** | {validated} | {capabilities} | {release_link} |"
        )
    return "\n".join(rows)


def tracked_artifact_errors(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"], cwd=root, check=True, capture_output=True
    )
    files = [item.decode() for item in result.stdout.split(b"\0") if item]
    errors: list[str] = []
    for relative in files:
        if any(pattern.search(relative) for pattern in FORBIDDEN_TRACKED_PATTERNS):
            errors.append(f"forbidden generated or binary artifact is tracked: {relative}")
        path = root / relative
        if path.is_file() and path.stat().st_size > 5 * 1024 * 1024:
            errors.append(f"tracked file exceeds 5 MiB lightweight-history limit: {relative}")
    return errors


def print_errors(errors: Iterable[str]) -> int:
    materialized = list(errors)
    for error in materialized:
        print(f"ERROR: {error}")
    return 1 if materialized else 0
