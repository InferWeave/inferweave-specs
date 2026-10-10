#!/usr/bin/env python3
"""Regression test for the canonical rag pipeline + POST /pipelines/execute wiring (specs/51, B-T04B)."""
import json
import unittest
from pathlib import Path

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "openapi" / "inferweave-v1.yaml"
PIPELINE_SCHEMA = ROOT / "schemas" / "v1" / "pipelines" / "pipeline.json"
RAG_REF = "#/components/schemas/CanonicalRagPipeline"
DAG_REF = "#/components/schemas/PipelineDag"


def topo_order(stages):
    """Return stage_ids in dependency order; None when an edge is unknown or the graph is cyclic."""
    deps = {s["stage_id"]: list(s["dependencies"]) for s in stages}
    order, done = [], set()
    while len(order) < len(deps):
        ready = [n for n, d in deps.items() if n not in done and all(x in done for x in d)]
        if not ready or any(x not in deps for d in deps.values() for x in d):
            return None
        for n in sorted(ready):
            order.append(n)
            done.add(n)
    return order


class RagPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = yaml.safe_load(SPEC.read_text())
        cls.schemas = cls.doc["components"]["schemas"]
        cls.execute = cls.doc["paths"]["/pipelines/execute"]["post"]
        cls.rag = cls.schemas.get("CanonicalRagPipeline", {})
        cls.example = cls.rag.get("example", {})
        cls.pipeline_schema = json.loads(PIPELINE_SCHEMA.read_text())

    def test_endpoint_wired_to_pipeline_contract(self):
        assert self.execute["x-pipeline-contract"] == "schemas/v1/pipelines/pipeline.json"
        req = self.schemas["PipelineExecuteRequest"]["properties"]["definition"]
        assert [a["$ref"] for a in req["allOf"]] == [DAG_REF]
        dag = self.schemas["PipelineDag"]
        assert dag["x-schema"] == "schemas/v1/pipelines/pipeline.json"
        self.assertEqual(sorted(dag["required"]), sorted(self.pipeline_schema["required"]))
        stage_families = self.schemas["PipelineStage"]["properties"]["family"]["enum"]
        self.assertEqual(stage_families, self.pipeline_schema["definitions"]["family"]["enum"])

    def test_endpoint_validates_dag(self):
        desc = self.execute["description"]
        for phrase in ("acyclic", "canonical registry", "admitted runtime", "modality"):
            assert phrase in desc, phrase
        err = self.execute["responses"]["400"]["content"]["application/json"]["schema"]["$ref"]
        assert err == "#/components/schemas/PipelineValidationError"
        codes = self.schemas["PipelineValidationError"]["allOf"][1]["properties"]["code"]["enum"]
        self.assertEqual(sorted(codes), sorted(self.pipeline_schema["x-validation-errors"]))

    def test_rag_composition(self):
        assert self.execute["x-canonical-pipelines"]["rag"]["$ref"] == RAG_REF
        assert [a["$ref"] for a in self.rag["allOf"]] == [DAG_REF]
        jsonschema.validate(self.example, self.pipeline_schema)
        stages = {s["stage_id"]: s for s in self.example["stages"]}
        order = topo_order(self.example["stages"])
        assert order is not None, "rag DAG must be acyclic with resolvable edges"
        families = [stages[n]["family"] for n in order]
        assert families[-1] == "llm"
        retrieval = [f for f in families[:-1] if f in ("embeddings", "reranking")]
        assert retrieval and len(retrieval) == len(families) - 1
        assert "rag" not in families, "rag must be composed of stages, not a single opaque stage"
        gen = stages[order[-1]]
        assert gen["dependencies"], "llm generation must be wired by explicit DAG edges"
        for s in self.example["stages"]:
            for d in s["dependencies"]:
                upstream = stages[d]["outputs"]
                for name, io in s["inputs"].items():
                    if name in upstream:
                        self.assertEqual(io["modality"], upstream[name]["modality"])

    def test_rag_uses_per_stage_capacity_accounting(self):
        acct = self.rag["x-admission-accounting"]
        assert acct["mode"] == "per-stage"
        assert acct["ad-hoc-path"] is False
        for control in ("admission", "capacity"):
            assert control in acct["controls"]
        families = {s["family"] for s in self.example["stages"]}
        assert families == set(acct["stage-families"])
        native = self.doc["paths"]
        for family, endpoint in acct["stage-families"].items():
            if endpoint.startswith("/v1/"):
                # OpenAI-compatible data-plane, preserved per specs/45; parity per specs/49.
                assert "admission, capacity" in self.doc["info"]["description"]
            else:
                assert endpoint in native, endpoint
                assert "post" in native[endpoint]
        assert "/rag" not in native, "no ad-hoc RAG endpoint may bypass the pipeline"


if __name__ == "__main__":
    unittest.main()
