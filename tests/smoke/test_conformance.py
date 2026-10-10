#!/usr/bin/env python3
"""Regression test for runtime-family conformance vectors and runner coverage (specs/53, B-T06A)."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VECTORS = ROOT / "conformance" / "runtime-family-vectors.json"
FAMILIES = ["embeddings", "reranking", "prediction", "stt", "rag"]


def run_runner(vectors_text=None):
    """Run the runner; optionally against a modified vectors file (restored afterwards)."""
    original = VECTORS.read_text()
    try:
        if vectors_text is not None:
            VECTORS.write_text(vectors_text)
        return subprocess.run([sys.executable, str(ROOT / "conformance" / "runner.py")],
                              capture_output=True, text=True, cwd=ROOT)
    finally:
        VECTORS.write_text(original)


class Conformance(unittest.TestCase):
    def test_family_vectors_present(self):
        doc = json.loads(VECTORS.read_text())
        for fam in FAMILIES:
            assert fam in doc["families"], fam
            assert doc["families"][fam]["advertisement"]["family"] == fam

    def test_native_smoke_vectors_present(self):
        doc = json.loads(VECTORS.read_text())
        for fam in FAMILIES:
            assert doc["families"][fam]["nativeSmoke"]["path"].startswith("/")

    def test_runner_reports_per_family(self):
        res = run_runner()
        assert res.returncode == 0, res.stdout + res.stderr
        for fam in FAMILIES:
            assert f"PASS  runtime-family {fam}" in res.stdout

    def test_runner_fails_when_family_vector_removed(self):
        doc = json.loads(VECTORS.read_text())
        del doc["families"]["rag"]
        res = run_runner(json.dumps(doc))
        assert res.returncode != 0
        assert "FAIL  runtime-family rag" in res.stdout

    def test_runner_fails_when_smoke_removed(self):
        doc = json.loads(VECTORS.read_text())
        del doc["families"]["stt"]["nativeSmoke"]
        res = run_runner(json.dumps(doc))
        assert res.returncode != 0
        assert "FAIL  runtime-family stt" in res.stdout


if __name__ == "__main__":
    unittest.main()
