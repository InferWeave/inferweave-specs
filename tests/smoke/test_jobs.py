#!/usr/bin/env python3
"""Regression test for the durable inference job contract (specs/52, B-T05A)."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JOB = ROOT / "schemas" / "v1" / "jobs" / "job.json"


class DurableJobContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads(JOB.read_text())
        cls.props = cls.schema["properties"]

    def test_family_and_result_ref_declared(self):
        assert self.props["family"]["type"] == "string"
        assert "family" in self.schema["required"]
        assert self.props["result_ref"]["$ref"].endswith("artifacts/artifact.json")

    def test_job_lifecycle(self):
        states = set(self.props["state"]["enum"])
        for s in ("queued", "running", "succeeded", "failed", "cancelled"):
            assert s in states, s
        assert self.props["progress"]["$ref"] == "progress.json"

    def test_restart_resume_durable_progress(self):
        progress = json.loads((JOB.parent / "progress.json").read_text())
        assert "fraction" in progress["properties"]
        assert "stage" in progress["properties"]
        assert "resumes from durable progress" in self.schema["description"]

    def test_circumvention_control(self):
        desc = self.schema["description"]
        for term in ("admission", "capacity", "fairshare", "owner-priority", "synchronous inference"):
            assert term in desc, term
        assert "do not bypass" in desc


if __name__ == "__main__":
    unittest.main()
