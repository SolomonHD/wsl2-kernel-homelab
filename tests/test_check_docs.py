from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from check_docs import (  # noqa: E402
    BROAD_WSL_CONF_EDIT_RE,
    LEGACY_KERNEL_ARTIFACT_RE,
    MIGRATION_REQUIRED_TEXT,
)


class DocumentationPolicyTests(unittest.TestCase):
    def test_legacy_kernel_name_is_detected(self) -> None:
        self.assertIsNotNone(
            LEGACY_KERNEL_ARTIFACT_RE.search("kernel=C:\\WSL\\bzImage-linux-msft-wsl-6.18.35.2")
        )

    def test_broad_wsl_conf_edits_are_detected(self) -> None:
        self.assertIsNotNone(BROAD_WSL_CONF_EDIT_RE.search("sudo rm /etc/wsl.conf"))
        self.assertIsNotNone(BROAD_WSL_CONF_EDIT_RE.search("cat defaults > /etc/wsl.conf"))
        self.assertIsNone(BROAD_WSL_CONF_EDIT_RE.search("sudo sed -i '/crossDistro/d' /etc/wsl.conf"))

    def test_migration_guide_contains_required_guidance(self) -> None:
        text = (ROOT / "docs" / "wsl-kernel-migration.md").read_text(encoding="utf-8")
        self.assertEqual([], [required for required in MIGRATION_REQUIRED_TEXT if required not in text])


if __name__ == "__main__":
    unittest.main()
