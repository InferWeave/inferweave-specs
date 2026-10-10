#!/usr/bin/env python3
"""Regression test for native /inferweave/v1 family-typed inference endpoints (specs/49, B-T02B)."""
import re
import unittest
from pathlib import Path

import yaml

SPEC = Path(__file__).resolve().parents[2] / "openapi" / "inferweave-v1.yaml"
ENDPOINTS = {
    "/rerank": ("reranking", "RerankRequest", "RerankResponse"),
    "/predictions": ("prediction", "PredictionRequest", "PredictionResponse"),
    "/embeddings": ("embeddings", "EmbeddingRequest", "EmbeddingResponse"),
}


class NativeInference(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = SPEC.read_text()
        cls.doc = yaml.safe_load(cls.text)
        cls.schemas = cls.doc["components"]["schemas"]

    def post(self, path):
        self.assertIn(path, self.doc["paths"])
        self.assertIn("post", self.doc["paths"][path])
        return self.doc["paths"][path]["post"]

    def test_parses_and_refs_resolve(self):
        for ref in re.findall(r'\$ref:\s*"#/components/schemas/(\w+)"', self.text):
            self.assertIn(ref, self.schemas, ref)

    def test_endpoint_surface(self):
        for path, (_, req, resp) in ENDPOINTS.items():
            op = self.post(path)
            body = op["requestBody"]["content"]["application/json"]["schema"]["$ref"]
            self.assertEqual(body, f"#/components/schemas/{req}")
            ok = op["responses"]["200"]["content"]["application/json"]["schema"]["$ref"]
            self.assertEqual(ok, f"#/components/schemas/{resp}")

    def test_family_binding(self):
        for path, (family, req, resp) in ENDPOINTS.items():
            for name in (req, resp):
                prop = self.schemas[name]["properties"]["family"]
                self.assertEqual(prop["enum"], [family], f"{path} {name}")
                self.assertIn("family", self.schemas[name]["required"])

    def test_family_mismatch_rejected_with_typed_error(self):
        err = self.schemas["FamilyMismatchError"]
        self.assertIn({"$ref": "#/components/schemas/Error"}, err["allOf"])
        props = {}
        for part in err["allOf"]:
            props.update(part.get("properties", {}))
        self.assertEqual(props["code"]["enum"], ["FAMILY_MISMATCH"])
        self.assertEqual(props["retryable"]["enum"], [False])
        self.assertEqual(
            set(props["details"]["properties"]["expected_family"]["enum"]),
            {f for f, _, _ in ENDPOINTS.values()},
        )
        for path in ENDPOINTS:
            ref = self.post(path)["responses"]["400"]["content"]["application/json"]["schema"]["$ref"]
            self.assertEqual(ref, "#/components/schemas/FamilyMismatchError")

    def test_output_shapes(self):
        pred = self.schemas["PredictionResponse"]["properties"]["predictions"]["items"]["properties"]
        self.assertEqual(pred["output_type"]["enum"], ["numeric", "label"])
        emb = self.schemas["EmbeddingResponse"]["properties"]["data"]["items"]["properties"]["embedding"]
        self.assertEqual(emb["items"]["type"], "number")
        rr = self.schemas["RerankResponse"]["properties"]["results"]["items"]
        self.assertIn("relevance_score", rr["required"])


if __name__ == "__main__":
    unittest.main()
