from __future__ import annotations

import copy
import hashlib
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from catalog_lib import load_manifest, sha256_file, support_matrix, validate_record, write_manifest  # noqa: E402
from release import (  # noqa: E402
    MAX_RELEASE_ASSET_BYTES,
    CatalogError,
    package,
    preflight,
    reconcile,
)


TAG = "linux-msft-wsl-6.18.35.2"


def merge(target: dict, patch: dict) -> None:
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            merge(target[key], value)
        else:
            target[key] = value


class CatalogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        (self.root / "kernels").mkdir()
        (self.root / "openspec").mkdir()
        self.record = self.root / "kernels" / TAG
        shutil.copytree(ROOT / "kernels" / TAG, self.record)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def apply_fixture(self, relative: str) -> None:
        patch = yaml.safe_load((ROOT / "tests" / "fixtures" / relative).read_text())
        manifest = load_manifest(self.record / "manifest.yaml")
        merge(manifest, patch)
        write_manifest(self.record / "manifest.yaml", manifest)

    def make_planned(self) -> None:
        manifest = load_manifest(self.record / "manifest.yaml")
        manifest.update(status="planned", previous_status=None, kernel_release=None)
        manifest["config"]["normalized"]["sha256"] = None
        manifest["build"].update(compiler=None, timestamp=None)
        for artifact in manifest["artifacts"].values():
            artifact.update(name=None, sha256=None, size_bytes=None, kernel_release=None)
        manifest["validation"]["build"]["status"] = "pending"
        report = self.record / manifest["validation"]["build"]["report"]
        report.write_text(
            report.read_text(encoding="utf-8").replace("Result: PASS", "Result: PENDING"),
            encoding="utf-8",
        )
        write_manifest(self.record / "manifest.yaml", manifest)

    def test_planned_record_is_valid_and_not_downloadable(self) -> None:
        self.make_planned()
        self.assertEqual([], validate_record(self.record))
        matrix = support_matrix(self.root)
        self.assertIn("**planned**", matrix)
        self.assertIn("Not available", matrix)

    def test_malformed_directory_is_rejected(self) -> None:
        malformed = self.record.with_name("6.18-latest")
        self.record.rename(malformed)
        self.assertTrue(any("malformed" in error for error in validate_record(malformed)))

    def test_missing_required_file_is_rejected(self) -> None:
        missing = (ROOT / "tests/fixtures/negative/missing-required-file.txt").read_text().strip()
        (self.record / missing).unlink()
        self.assertTrue(any("missing required file" in error for error in validate_record(self.record)))

    def test_invalid_status_is_rejected(self) -> None:
        self.apply_fixture("negative/invalid-status.yaml")
        self.assertTrue(any("status must be" in error for error in validate_record(self.record)))

    def test_schema_version_one_is_rejected_after_migration(self) -> None:
        self.apply_fixture("negative/schema-v1.yaml")
        self.assertTrue(any("schema_version must equal 2" in error for error in validate_record(self.record)))

    def test_illegal_transition_is_rejected(self) -> None:
        self.apply_fixture("negative/illegal-transition.yaml")
        self.assertTrue(any("illegal lifecycle transition" in error for error in validate_record(self.record)))

    def test_unpublished_validated_record_can_return_to_built_when_runtime_is_cleared(self) -> None:
        manifest = load_manifest(self.record / "manifest.yaml")
        manifest["status"] = "built"
        manifest["previous_status"] = "validated"
        manifest["validation"]["runtime"]["status"] = "pending"
        manifest["validation"]["validated_at"] = None
        for capability in manifest["capabilities"]:
            manifest["capabilities"][capability] = None
        runtime_report = self.record / manifest["validation"]["runtime"]["report"]
        runtime_report.write_text(
            runtime_report.read_text(encoding="utf-8").replace("Result: PASS", "Result: PENDING"),
            encoding="utf-8",
        )
        write_manifest(self.record / "manifest.yaml", manifest)
        self.assertEqual([], validate_record(self.record))

        manifest["validation"]["runtime"]["status"] = "pass"
        runtime_report.write_text(
            runtime_report.read_text(encoding="utf-8").replace("Result: PENDING", "Result: PASS"),
            encoding="utf-8",
        )
        write_manifest(self.record / "manifest.yaml", manifest)
        self.assertTrue(any("pending runtime" in error for error in validate_record(self.record)))

    def test_published_record_cannot_return_to_built(self) -> None:
        manifest = load_manifest(self.record / "manifest.yaml")
        manifest["previous_status"] = "published"
        write_manifest(self.record / "manifest.yaml", manifest)
        self.assertTrue(any("illegal lifecycle transition" in error for error in validate_record(self.record)))

    def test_legacy_kernel_artifact_name_is_rejected(self) -> None:
        manifest = load_manifest(self.record / "manifest.yaml")
        manifest["artifacts"]["kernel"]["name"] = f"bzImage-{TAG}"
        write_manifest(self.record / "manifest.yaml", manifest)
        self.assertTrue(any("must equal" in error for error in validate_record(self.record)))

    def test_built_artifact_requires_positive_size(self) -> None:
        manifest = load_manifest(self.record / "manifest.yaml")
        manifest["artifacts"]["kernel"]["size_bytes"] = 0
        write_manifest(self.record / "manifest.yaml", manifest)
        self.assertTrue(any("positive integer" in error for error in validate_record(self.record)))

    def test_checksum_mismatch_is_rejected(self) -> None:
        self.apply_fixture("negative/checksum-mismatch.yaml")
        self.assertTrue(any("sha256 mismatch" in error for error in validate_record(self.record)))

    def test_inconsistent_release_metadata_is_rejected(self) -> None:
        self.apply_fixture("negative/inconsistent-release.yaml")
        self.assertTrue(any("unpublished records" in error for error in validate_record(self.record)))

    def test_planned_record_fails_release_preflight(self) -> None:
        self.make_planned()
        artifacts = self.root / "artifacts"
        artifacts.mkdir()
        with self.assertRaisesRegex(CatalogError, "requires validated status"):
            preflight(self.root, TAG, artifacts)

    def make_validated(self) -> Path:
        self.apply_fixture("positive/validated-values.yaml")
        manifest = load_manifest(self.record / "manifest.yaml")
        normalized = self.record / manifest["config"]["normalized"]["path"]
        normalized.write_text("CONFIG_FIXTURE=y\n# CONFIG_DISABLED is not set\n")
        manifest["config"]["normalized"]["sha256"] = sha256_file(normalized)
        artifacts = self.root / "artifacts"
        artifacts.mkdir()
        release = manifest["kernel_release"]
        for key, name, content in (
            ("kernel", TAG, b"fixture kernel"),
            ("modules_vhdx", f"modules-{TAG}.vhdx", b"fixture modules"),
        ):
            path = artifacts / name
            path.write_bytes(content)
            manifest["artifacts"][key].update(
                name=name,
                sha256=sha256_file(path),
                size_bytes=path.stat().st_size,
                kernel_release=release,
            )
        for report_name in ("build", "runtime"):
            report = self.record / manifest["validation"][report_name]["report"]
            report.write_text(report.read_text().replace("Result: PENDING", "Result: PASS"))
        write_manifest(self.record / "manifest.yaml", manifest)
        return artifacts

    def test_validated_record_preflight_and_package(self) -> None:
        artifacts = self.make_validated()
        record, manifest = preflight(self.root, TAG, artifacts)
        output = self.root / "dist" / TAG
        package(self.root, record, manifest, artifacts, output)
        self.assertEqual(
            {TAG, f"modules-{TAG}.vhdx", "manifest.yaml", "config-wsl-homelab", "SHA256SUMS"},
            {path.name for path in output.iterdir()},
        )
        sums = (output / "SHA256SUMS").read_text()
        self.assertIn(hashlib.sha256(b"fixture kernel").hexdigest(), sums)

    def test_release_preflight_rejects_manifest_size_mismatch(self) -> None:
        artifacts = self.make_validated()
        manifest = load_manifest(self.record / "manifest.yaml")
        manifest["artifacts"]["kernel"]["size_bytes"] += 1
        write_manifest(self.record / "manifest.yaml", manifest)
        with self.assertRaisesRegex(CatalogError, "size mismatch"):
            preflight(self.root, TAG, artifacts)

    def test_release_preflight_rejects_exact_two_gib_boundary(self) -> None:
        artifacts = self.make_validated()
        kernel = artifacts / TAG
        kernel.write_bytes(b"")
        with kernel.open("r+b") as stream:
            stream.truncate(MAX_RELEASE_ASSET_BYTES)
        manifest = load_manifest(self.record / "manifest.yaml")
        manifest["artifacts"]["kernel"]["size_bytes"] = MAX_RELEASE_ASSET_BYTES
        write_manifest(self.record / "manifest.yaml", manifest)
        with self.assertRaisesRegex(CatalogError, "smaller than 2147483648"):
            preflight(self.root, TAG, artifacts)

    def test_release_preflight_rejects_oversized_asset(self) -> None:
        artifacts = self.make_validated()
        kernel = artifacts / TAG
        kernel.write_bytes(b"")
        with kernel.open("r+b") as stream:
            stream.truncate(MAX_RELEASE_ASSET_BYTES + 1)
        manifest = load_manifest(self.record / "manifest.yaml")
        manifest["artifacts"]["kernel"]["size_bytes"] = MAX_RELEASE_ASSET_BYTES + 1
        write_manifest(self.record / "manifest.yaml", manifest)
        with self.assertRaisesRegex(CatalogError, "smaller than 2147483648"):
            preflight(self.root, TAG, artifacts)

    def test_published_remote_reconciliation_is_retry_safe(self) -> None:
        artifacts = self.make_validated()
        manifest = load_manifest(self.record / "manifest.yaml")
        manifest["status"] = "published"
        manifest["previous_status"] = "validated"
        manifest["publication"].update(
            release_tag=TAG,
            release_url=f"https://github.com/example/releases/tag/{TAG}",
            published_at="2026-01-03T00:00:00+00:00",
        )
        assets = [
            {"name": name, "size": (artifacts / name).stat().st_size}
            if (artifacts / name).exists()
            else {"name": name, "size": 1}
            for name in (
                TAG,
                f"modules-{TAG}.vhdx",
                "manifest.yaml",
                "config-wsl-homelab",
                "SHA256SUMS",
            )
        ]
        remote = {
            "tagName": TAG,
            "url": manifest["publication"]["release_url"],
            "isDraft": False,
            "assets": assets,
        }
        with mock.patch("release.remote_release", return_value=remote):
            reconcile(self.root, self.record, manifest, TAG, apply=True)

    def test_corrected_release_requires_reason_and_supersession(self) -> None:
        artifacts = self.make_validated()
        with self.assertRaisesRegex(CatalogError, "correction-reason"):
            preflight(self.root, f"{TAG}-homelab.1", artifacts)
        with self.assertRaisesRegex(CatalogError, "supersedes"):
            preflight(self.root, f"{TAG}-homelab.1", artifacts, "packaging fix")


if __name__ == "__main__":
    unittest.main()
