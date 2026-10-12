#!/usr/bin/env python3
"""Regression test for native family-aware routing metadata and parity note (specs/49, B-T02D)."""
import unittest
from pathlib import Path

import yaml

SPEC = Path(__file__).resolve().parents[2] / "openapi" / "inferweave-v1.yaml"


class FamilyRouting(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = yaml.safe_load(SPEC.read_text())
        cls.schemas = cls.doc["components"]["schemas"]

    def test_selection_reason_declared(self):
        item = self.doc["paths"]["/runtimes"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]["items"]
        assert item["$ref"] == "#/components/schemas/RuntimeInstance"
        assert "selection_reason" in self.schemas["RuntimeInstance"]["properties"]

    def test_placement_reason_declared(self):
        item = self.doc["paths"]["/deployments"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]["items"]
        assert item["$ref"] == "#/components/schemas/Deployment"
        assert "placement_reason" in self.schemas["Deployment"]["properties"]["live"]["properties"]

    def test_parity_note_present(self):
        desc = " ".join(self.doc["info"]["description"].split())
        assert "same admission, capacity, and fairshare controls" in desc
        assert "conformance fixture" in desc

    def test_refs_resolve(self):
        def walk(n):
            if isinstance(n, dict):
                for k, v in n.items():
                    if k == "$ref" and isinstance(v, str) and v.startswith("#/components/schemas/"):
                        assert v.rsplit("/", 1)[1] in self.schemas, v
                    walk(v)
            elif isinstance(n, list):
                for v in n:
                    walk(v)
        walk(self.doc)


if __name__ == "__main__":
    unittest.main()
