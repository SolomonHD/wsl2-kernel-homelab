from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_config.py"
REQUIRED = "CONFIG_ALPHA=y\nCONFIG_BRAVO=m\nCONFIG_CHARLIE=y\n"


class ValidateConfigCliTests(unittest.TestCase):
    def run_validator(self, actual: str) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            required = root / "required.config"
            config = root / ".config"
            required.write_text(REQUIRED, encoding="utf-8")
            config.write_text(actual, encoding="utf-8")
            return subprocess.run(
                [
                    sys.executable,
                    str(VALIDATOR),
                    "--required",
                    str(required),
                    "--config",
                    str(config),
                ],
                check=False,
                capture_output=True,
                text=True,
            )

    def test_successful_validation(self) -> None:
        result = self.run_validator(
            "CONFIG_ALPHA=y\nCONFIG_BRAVO=m\nCONFIG_CHARLIE=y\nCONFIG_EXTRA=y\n"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("3 required symbol(s) match", result.stdout)

    def test_missing_symbol(self) -> None:
        result = self.run_validator("CONFIG_ALPHA=y\nCONFIG_BRAVO=m\n")
        self.assertEqual(result.returncode, 1)
        self.assertIn("CONFIG_CHARLIE: missing (expected y)", result.stderr)

    def test_disabled_symbol(self) -> None:
        result = self.run_validator(
            "# CONFIG_ALPHA is not set\nCONFIG_BRAVO=m\nCONFIG_CHARLIE=y\n"
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("CONFIG_ALPHA: expected y, got n", result.stderr)

    def test_wrong_builtin_module_mode(self) -> None:
        result = self.run_validator(
            "CONFIG_ALPHA=y\nCONFIG_BRAVO=y\nCONFIG_CHARLIE=y\n"
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("CONFIG_BRAVO: expected m, got y", result.stderr)


if __name__ == "__main__":
    unittest.main()
