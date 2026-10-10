#!/usr/bin/env python3
"""Regression test for native /inferweave/v1 pipeline + durable-job surface (specs/49, specs/51, B-T02C)."""
import re
import unittest
from pathlib import Path

import yaml

SPEC = Path(__file__).resolve().parents[2] / "openapi" / "inferweave-v1.yaml"


class NativePipelineJob(unittest.TestCase):
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

    def test_pipeline_surface(self):
        submit = self.post("/pipelines")
        self.assertEqual(
            submit["requestBody"]["content"]["application/json"]["schema"]["$ref"],
            "#/components/schemas/PipelineDefinitionRequest",
        )
        execute = self.post("/pipelines/execute")
        self.assertEqual(
            execute["requestBody"]["content"]["application/json"]["schema"]["$ref"],
            "#/components/schemas/PipelineExecuteRequest",
        )

    def test_pipeline_responses_return_protocol_envelope(self):
        for path, codes in (("/pipelines", ["201"]), ("/pipelines/execute", ["200", "202"])):
            op = self.post(path)
            for code in codes:
                ref = op["responses"][code]["content"]["application/json"]["schema"]["$ref"]
                self.assertEqual(ref, "#/components/schemas/PipelineEnvelope")
        env = self.schemas["PipelineEnvelope"]
        self.assertIn("protocol", env["required"])
        self.assertIn("result", env["required"])
        self.assertEqual(env["properties"]["protocol"]["$ref"], "#/components/schemas/Protocol")

    def test_jobs_documented_as_durable_job_surface(self):
        op = self.post("/jobs")
        self.assertIn("durable-job", op["summary"])
        self.assertIn("durable-job", op["description"])


if __name__ == "__main__":
    unittest.main()
