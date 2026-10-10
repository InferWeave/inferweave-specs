#!/usr/bin/env python3
"""Regression test for the typed pipeline DAG contract (specs/51, B-T04A)."""
import json
import unittest
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "schemas" / "v1" / "pipelines" / "pipeline.json"


class PipelineError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.envelope = {"code": code, "category": "protocol", "message": message, "retryable": False}


def find_cycle(stages):
    """Return True when the dependency graph has a cycle (DAG-acyclicity control)."""
    deps = {s["stage_id"]: s["dependencies"] for s in stages}
    state = {}

    def visit(n):
        if state.get(n) == 1:
            return True
        if state.get(n) == 2:
            return False
        state[n] = 1
        if any(visit(d) for d in deps[n]):
            return True
        state[n] = 2
        return False

    return any(visit(n) for n in deps)


def validate_pipeline(doc, schema, admitted):
    jsonschema.validate(doc, schema)
    stages = doc["stages"]
    ids = {s["stage_id"] for s in stages}
    for s in stages:
        if s["family"] not in admitted:
            raise PipelineError("pipeline_unknown_family", "family not admitted: " + s["family"])
        for d in s["dependencies"]:
            if d not in ids:
                raise PipelineError("pipeline_unknown_dependency", "unknown dependency: " + d)
    if find_cycle(stages):
        raise PipelineError("pipeline_cycle", "pipeline stage graph contains a cycle")


def stage(sid, family, deps):
    io = {"x": {"modality": "text"}}
    return {"stage_id": sid, "family": family, "inputs": io, "outputs": io, "dependencies": deps}


def pipeline(stages):
    return {"pipeline_id": "p1", "stages": stages, "inputs": {"q": {"modality": "text"}}}


class Pipelines(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads(SCHEMA.read_text())
        cls.admitted = set(cls.schema["definitions"]["family"]["enum"])

    def test_schema_validity(self):
        jsonschema.Draft7Validator.check_schema(self.schema)
        assert self.schema["$schema"].endswith("draft-07/schema#")
        assert {"pipeline_id", "stages", "inputs"} <= set(self.schema["required"])
        assert "dependencies" in self.schema["definitions"]["stage"]["required"]

    def test_valid_rag_dag_accepted(self):
        doc = pipeline([
            stage("retrieve", "embeddings", []),
            stage("rerank", "reranking", ["retrieve"]),
            stage("generate", "llm", ["rerank"]),
        ])
        validate_pipeline(doc, self.schema, self.admitted)
        assert not find_cycle(doc["stages"])

    def test_dag_acyclicity(self):
        doc = pipeline([stage("a", "llm", ["b"]), stage("b", "llm", ["a"])])
        with self.assertRaises(PipelineError) as ctx:
            validate_pipeline(doc, self.schema, self.admitted)
        assert ctx.exception.code == "pipeline_cycle"
        assert ctx.exception.envelope["retryable"] is False

    def test_stage_family_resolution(self):
        doc = pipeline([stage("a", "not-a-family", [])])
        with self.assertRaises(jsonschema.ValidationError):
            validate_pipeline(doc, self.schema, self.admitted)
        doc = pipeline([stage("a", "video", [])])
        with self.assertRaises(PipelineError) as ctx:
            validate_pipeline(doc, self.schema, self.admitted - {"video"})
        assert ctx.exception.code == "pipeline_unknown_family"


if __name__ == "__main__":
    unittest.main()
