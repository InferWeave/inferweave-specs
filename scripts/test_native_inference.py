#!/usr/bin/env python3
"""Regression test for native /inferweave/v1 family-typed inference endpoints (specs/49, B-T02B)."""
import re
import unittest
from pathlib import Path

import yaml

SPEC = Path(__file__).resolve().parent.parent / "openapi" / "inferweave-v1.yaml"
BINDINGS = {
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

    def test_parses_and_refs_resolve(self):
        for ref in re.findall(r'\$ref:\s*"#/components/schemas/(\w+)"', self.text):
            self.assertIn(ref, self.schemas, ref)

    def test_endpoint_surface(self):
        for path in BINDINGS:
            self.assertIn(path, self.doc["paths"])
            self.assertIn("post", self.doc["paths"][path])

    def test_family_routing(self):
        known = set(self.schemas["Capability"]["properties"]["family"]["enum"])
        for path, (family, req, resp) in BINDINGS.items():
            self.assertIn(family, known)
            op = self.doc["paths"][path]["post"]
            self.assertEqual(op["x-inferweave-family"], family, path)
            body = op["requestBody"]["content"]["application/json"]["schema"]["$ref"]
            self.assertTrue(body.endswith("/" + req), path)
            ok = op["responses"]["200"]["content"]["application/json"]["schema"]["$ref"]
            self.assertTrue(ok.endswith("/" + resp), path)
            for name in (req, resp):
                schema = self.schemas[name]
                self.assertIn("family", schema["required"], name)
                # a mismatched family must be rejected by the schema
                self.assertEqual(schema["properties"]["family"]["enum"], [family], name)

    def test_typed_error_on_mismatch(self):
        for path in BINDINGS:
            responses = self.doc["paths"][path]["post"]["responses"]
            self.assertIn("409", responses, path)
            self.assertIn("FAMILY_MISMATCH", responses["409"]["description"])
            ref = responses["409"]["content"]["application/json"]["schema"]["$ref"]
            self.assertEqual(ref, "#/components/schemas/Error")

    def test_output_shapes(self):
        self.assertIn("score", self.schemas["RerankResponse"]["properties"]["results"]["items"]["properties"])
        preds = self.schemas["PredictionResponse"]["properties"]["predictions"]["items"]["properties"]
        self.assertTrue({"value", "label"} <= set(preds))
        data = self.schemas["EmbeddingResponse"]["properties"]["data"]["items"]["properties"]
        self.assertEqual(data["vector"]["items"]["type"], "number")


if __name__ == "__main__":
    unittest.main()
