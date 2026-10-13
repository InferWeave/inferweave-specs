#!/usr/bin/env python3
"""Regression tests for the runtime protocol gap repair (IW-RT-001..006)."""

import json
import unittest
from pathlib import Path

import yaml
from jsonschema import Draft7Validator, RefResolver


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_ROOT = ROOT / "schemas" / "v1"


def load_json(relative):
    return json.loads((ROOT / relative).read_text())


def schema_validator(relative):
    schema = load_json(f"schemas/v1/{relative}")
    store = {}
    for path in SCHEMA_ROOT.rglob("*.json"):
        candidate = json.loads(path.read_text())
        store[candidate["$id"]] = candidate
    return Draft7Validator(
        schema,
        resolver=RefResolver(base_uri=schema["$id"], referrer=schema, store=store),
    )


def normalized_schema(value):
    """Normalize presentation metadata and external/component ref spelling only."""
    ignored = {"$schema", "$id", "title", "description", "x-json-schema"}
    refs = {
        "deployment-identity.json": "#/components/schemas/DeploymentIdentity",
        "../runtime/runtime-instance.json": "#/components/schemas/RuntimeInstance",
        "../topology/allocation.json": "#/components/schemas/Allocation",
    }
    if isinstance(value, dict):
        return {
            key: refs.get(item, item) if key == "$ref" else normalized_schema(item)
            for key, item in value.items()
            if key not in ignored
        }
    if isinstance(value, list):
        return [normalized_schema(item) for item in value]
    return value


class RuntimeProtocolGapRepair(unittest.TestCase):
    def test_adapter_contract_requires_every_lifecycle_method_and_process_isolation(self):
        schema = load_json("schemas/v1/runtime/adapter.json")
        required = set(schema["properties"]["lifecycle_methods"]["required"])
        self.assertEqual(
            required,
            {
                "identity",
                "capabilities",
                "hardware_requirements",
                "validate",
                "prepare",
                "load",
                "unload",
                "health",
                "metrics",
                "cancel",
                "drain",
                "shutdown",
            },
        )
        self.assertEqual(schema["properties"]["isolation"]["properties"]["mode"]["enum"], ["process", "container"])

    def test_load_request_keys_single_flight_by_immutable_deployment(self):
        validator = schema_validator("runtime/load-request.json")
        valid = load_json("fixtures/valid/runtime-load-request.json")
        self.assertEqual([], list(validator.iter_errors(valid)))
        invalid = dict(valid)
        invalid.pop("deployment_key")
        self.assertTrue(list(validator.iter_errors(invalid)))
        self.assertEqual(valid["cancellation_scope"], "waiter")

    def test_runtime_reservation_contract_is_additive_and_complete(self):
        validator = schema_validator("resources/reservation.json")
        legacy = load_json("fixtures/valid/reservation.json")
        current = load_json("fixtures/valid/reservation-runtime.json")
        self.assertEqual([], list(validator.iter_errors(legacy)))
        self.assertEqual([], list(validator.iter_errors(current)))
        envelope = current["resourceEnvelope"]
        self.assertEqual(current["physicalResourceKey"], "node_b200-01/GPU-5f1e0c2a-7b7d-4c55-9d0e-3b3e2a1c9f01")
        self.assertNotIn(current["provenance"]["parentId"], current["physicalResourceKey"])
        self.assertEqual(
            set(envelope["gpuContributors"]),
            {"weights", "kvCache", "activations", "runtimeWorkspace", "auxiliaryModels", "loadingPeak"},
        )
        for key in ("idempotencyKey", "payloadDigest", "fencingEpoch", "placementGroupId", "resourceDomainKey", "progressTimeoutMs", "authorityClock", "lastProgressAuthorityTick", "leaseDeadlineAuthorityTick", "progressSequence"):
            broken = dict(current)
            broken.pop(key)
            self.assertTrue(list(validator.iter_errors(broken)), key)

    def test_all_three_cache_classes_require_verified_atomic_publication(self):
        validator = schema_validator("artifacts/cache-state.json")
        for cache_class in ("model", "runtime", "optimization"):
            fixture = load_json(f"fixtures/valid/cache-state-{cache_class}.json")
            self.assertEqual([], list(validator.iter_errors(fixture)), cache_class)
            self.assertTrue(fixture["integrity"]["verified"])
            self.assertEqual(fixture["publication"]["state"], "published")
            self.assertEqual(fixture["acquisition"]["mode"], "streamed")
            self.assertLessEqual(fixture["acquisition"]["max_buffer_bytes"], 67108864)
        invalid = load_json("fixtures/invalid/cache-state-published-unverified.json")
        self.assertTrue(list(validator.iter_errors(invalid)))

    def test_standalone_deployment_and_family_requests_match_openapi(self):
        openapi = yaml.safe_load((ROOT / "openapi/inferweave-v1.yaml").read_text())
        schemas = openapi["components"]["schemas"]
        pairs = {
            "Deployment": "deployments/deployment.json",
            "RerankRequest": "requests/rerank.json",
            "PredictionRequest": "requests/prediction.json",
            "EmbeddingRequest": "requests/embeddings.json",
        }
        for component, relative in pairs.items():
            standalone = load_json(f"schemas/v1/{relative}")
            self.assertEqual(schemas[component]["x-json-schema"], f"schemas/v1/{relative}")
            self.assertEqual(normalized_schema(schemas[component]), normalized_schema(standalone))

    def test_job_family_is_additive_and_succeeded_is_canonical(self):
        validator = schema_validator("jobs/job.json")
        legacy = {"job_id": "legacy-1", "state": "completed"}
        self.assertEqual([], list(validator.iter_errors(legacy)))
        schema = load_json("schemas/v1/jobs/job.json")
        state = schema["properties"]["state"]
        self.assertEqual(state["x-canonical-emitted-value"], "succeeded")
        self.assertIn("completed", state["x-legacy-read-values"])
        self.assertNotIn("family", schema["required"])

    def test_runtime_features_are_explicitly_negotiated_for_mixed_versions(self):
        features = load_json("schemas/v1/common/features.json")["properties"]
        for name in ("runtime_families", "runtime_lifecycle", "runtime_reservations", "transactional_caches", "native_link_requests"):
            self.assertIn(name, features)
        compatibility = yaml.safe_load((ROOT / "conformance/compatibility.yaml").read_text())
        self.assertEqual(compatibility["runtimeProtocol"]["legacyPeerPolicy"], "omit-additive-fields")


if __name__ == "__main__":
    unittest.main()
