from __future__ import annotations

import copy
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_kernel import Baseline, BuildError, built_manifest, verify_stripped_modules  # noqa: E402
from catalog_lib import load_manifest  # noqa: E402


TAG = "linux-msft-wsl-6.18.35.2"


class BuildKernelTests(unittest.TestCase):
    def baseline(self) -> Baseline:
        record = ROOT / "kernels" / TAG
        manifest = copy.deepcopy(load_manifest(record / "manifest.yaml"))
        manifest["status"] = "validated"
        manifest["previous_status"] = "built"
        manifest["validation"]["runtime"]["status"] = "pass"
        manifest["validation"]["validated_at"] = "2026-01-02T00:00:00+00:00"
        for capability in manifest["capabilities"]:
            manifest["capabilities"][capability] = True
        manifest["publication"].update(
            release_tag=None,
            release_url=None,
            published_at=None,
            supersedes=None,
        )
        return Baseline(
            record=record,
            manifest=manifest,
            tag=TAG,
            commit=manifest["upstream"]["commit"],
            fragment=record / manifest["config"]["fragment"]["path"],
            normalized=record / manifest["config"]["normalized"]["path"],
        )

    def test_rebuild_of_unpublished_validated_record_clears_runtime(self) -> None:
        manifest = built_manifest(
            self.baseline(),
            "6.18.35.2-microsoft-standard-WSL2+",
            "gcc fixture",
            "2026-01-03T00:00:00+00:00",
            "a" * 64,
            TAG,
            "b" * 64,
            123,
            f"modules-{TAG}.vhdx",
            "c" * 64,
            456,
            True,
        )
        self.assertEqual(2, manifest["schema_version"])
        self.assertEqual(("built", "validated"), (manifest["status"], manifest["previous_status"]))
        self.assertEqual("pending", manifest["validation"]["runtime"]["status"])
        self.assertIsNone(manifest["validation"]["validated_at"])
        self.assertTrue(all(value is None for value in manifest["capabilities"].values()))
        self.assertEqual(123, manifest["artifacts"]["kernel"]["size_bytes"])

    def test_rebuild_rejects_published_artifact_replacement(self) -> None:
        baseline = self.baseline()
        baseline.manifest["status"] = "published"
        baseline.manifest["publication"]["release_tag"] = TAG
        with self.assertRaisesRegex(BuildError, "lifecycle status published"):
            built_manifest(
                baseline,
                "release",
                "gcc",
                "timestamp",
                "a" * 64,
                TAG,
                "b" * 64,
                1,
                f"modules-{TAG}.vhdx",
                "c" * 64,
                1,
                False,
            )

    def test_stripped_module_check_accepts_no_debug_sections(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            module = Path(directory) / "kernel" / "wireguard.ko"
            module.parent.mkdir()
            module.write_bytes(b"fixture")
            result = mock.Mock(stdout="[ 1] .text PROGBITS")
            with mock.patch("build_kernel.require_tools"), mock.patch(
                "build_kernel.subprocess.run", return_value=result
            ):
                self.assertEqual(1, verify_stripped_modules(Path(directory)))

    def test_stripped_module_check_rejects_debug_sections(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            module = Path(directory) / "wireguard.ko"
            module.write_bytes(b"fixture")
            result = mock.Mock(stdout="[20] .debug_info PROGBITS")
            with mock.patch("build_kernel.require_tools"), mock.patch(
                "build_kernel.subprocess.run", return_value=result
            ):
                with self.assertRaisesRegex(BuildError, "retain .debug"):
                    verify_stripped_modules(Path(directory))


if __name__ == "__main__":
    unittest.main()
