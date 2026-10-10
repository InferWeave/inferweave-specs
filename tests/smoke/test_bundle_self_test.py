"""Smoke: bundle metadata is present and the validator self-test is green (IW-RT-006)."""

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class BundleSelfTest(unittest.TestCase):
    def test_bundle_metadata_present(self):
        assert (ROOT / "checksums.json").is_file()
        assert (ROOT / "BUNDLE_INDEX.md").is_file()

    def test_index_lists_workstream_b_specs(self):
        index = (ROOT / "BUNDLE_INDEX.md").read_text()
        listed = [p.name for p in sorted((ROOT / "specs").glob("*.md")) if p.name[:2] in {"48", "49", "50", "51", "52", "53"}]
        assert len(listed) == 6
        for name in listed:
            assert f"`specs/{name}`" in index

    def test_validate_specs_self_test_exits_zero(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "validate_specs.py"), "--self-test"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr


if __name__ == "__main__":
    unittest.main()
