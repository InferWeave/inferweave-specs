#!/usr/bin/env python3
"""Regression test for native POST /jobs durable inference-job submission (specs/52, B-T05B)."""
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "openapi" / "inferweave-v1.yaml"
MACHINE = ROOT / "state-machines" / "job.md"


class JobsEndpoint(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = yaml.safe_load(SPEC.read_text())
        cls.post = cls.doc["paths"]["/jobs"]["post"]
        cls.machine = MACHINE.read_text()
        cls.desc = " ".join(cls.post["description"].split())

    def test_endpoint_surface(self):
        assert self.post.get("x-durable-job-submission") is True
        assert "single runtime-family inference request" in self.desc
        assert "pipeline reference" in self.desc

    def test_lifecycle_and_reference(self):
        assert "queued -> running -> succeeded | failed | cancelled" in self.machine
        assert "durable" in self.machine.lower()
        assert "never as an inline result body" in self.desc
        ref = self.post["responses"]["201"]["content"]["application/json"]["schema"]["$ref"]
        assert ref == "#/components/schemas/Job"

    def test_no_bypass(self):
        assert "admission, capacity, fairshare" in self.desc
        assert "does not bypass" in self.desc


if __name__ == "__main__":
    unittest.main()
