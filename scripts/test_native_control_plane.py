#!/usr/bin/env python3
"""Regression test for the native /inferweave/v1 control-plane reads (specs/49, B-T02A)."""
import json
import re
import unittest
from pathlib import Path

import yaml

SPEC = Path(__file__).resolve().parent.parent / "openapi" / "inferweave-v1.yaml"
FAMILIES = {
    "llm", "reasoning", "embeddings", "reranking", "stt", "tts", "audio",
    "prediction", "image", "video", "multimodal", "scientific", "rag",
}
DEPLOYMENT_REF = "#/components/schemas/Deployment"


class NativeControlPlane(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = SPEC.read_text()
        cls.doc = yaml.safe_load(cls.text)

    def get(self, path):
        self.assertIn(path, self.doc["paths"])
        self.assertIn("get", self.doc["paths"][path])
        return self.doc["paths"][path]["get"]

    def test_parses_and_refs_resolve(self):
        self.assertIsInstance(self.doc, dict)
        for ref in re.findall(r'\$ref:\s*"#/components/schemas/(\w+)"', self.text):
            self.assertIn(ref, self.doc["components"]["schemas"], ref)

    def test_deployments_surface(self):
        self.get("/deployments")
        op = self.get("/deployments/{deployment_id}")
        self.assertTrue(any(p["in"] == "path" and p["required"] for p in op["parameters"]))
        schema = self.doc["components"]["schemas"]["Deployment"]
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(set(schema["required"]), {"deployment_id", "deployment_key", "manifest"})
        self.assertEqual(schema["properties"]["manifest"]["$ref"], "#/components/schemas/DeploymentIdentity")
        identity = self.doc["components"]["schemas"]["DeploymentIdentity"]
        self.assertEqual(identity["properties"]["schema_version"]["const"], "inferweave.deployment-identity/v1")
        # Mutable residency never becomes part of the immutable deployment manifest.
        self.assertNotIn("instances", identity["properties"])
        self.assertNotIn("placement_reason", identity["properties"])
        live = schema["properties"]["live"]
        self.assertEqual(set(live["properties"]), {"instances", "assignment", "placement_reason"})
        self.assertNotIn("live", schema["required"])
        canonical_path = SPEC.parent.parent / schema["x-json-schema"]
        canonical = json.loads(canonical_path.read_text())
        self.assertEqual(schema["required"], canonical["required"])
        self.assertEqual(set(schema["properties"]), set(canonical["properties"]))
        self.assertEqual(schema["properties"]["deployment_key"], canonical["properties"]["deployment_key"])
        for path in ("/deployments", "/deployments/{deployment_id}"):
            self.assertIn(DEPLOYMENT_REF, str(self.get(path)["responses"]["200"]))

    def test_capabilities_family_filter(self):
        op = self.get("/capabilities")
        fam = [p for p in op["parameters"] if p["name"] == "family" and p["in"] == "query"]
        self.assertEqual(len(fam), 1)
        self.assertEqual(set(fam[0]["schema"]["enum"]), FAMILIES)
        self.assertIn("400", op["responses"])
        self.assertIn("#/components/schemas/Capability", str(op["responses"]["200"]))
        cap = self.doc["components"]["schemas"]["Capability"]
        self.assertEqual(set(cap["properties"]["family"]["enum"]), FAMILIES)


if __name__ == "__main__":
    unittest.main()
