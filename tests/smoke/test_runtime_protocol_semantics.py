#!/usr/bin/env python3
"""Executable semantics for the amended IW-RT runtime contracts."""

import json
import unittest
from pathlib import Path

import yaml
from jsonschema import Draft7Validator, RefResolver

from conformance.runtime_protocol import (
    IdempotencyConflict,
    ReservationAuthority,
    SingleFlightLoads,
    canonical_deployment_key,
    link_dispatch_decision,
    safe_peak_admissible,
)


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_ROOT = ROOT / "schemas" / "v1"


def load_json(relative):
    return json.loads((ROOT / relative).read_text())


def validator(relative):
    schema = load_json(f"schemas/v1/{relative}")
    store = {}
    for path in SCHEMA_ROOT.rglob("*.json"):
        candidate = json.loads(path.read_text())
        store[candidate["$id"]] = candidate
    return Draft7Validator(
        schema,
        resolver=RefResolver(base_uri=schema["$id"], referrer=schema, store=store),
    )


class CacheStateSemantics(unittest.TestCase):
    def test_inconsistent_v1_states_are_executable_negative_fixtures(self):
        cache_validator = validator("artifacts/cache-state.json")
        fixtures = (
            "cache-state-cached-staging.json",
            "cache-state-missing-published.json",
            "cache-state-offline-unverified.json",
            "cache-state-pinned-flag-false.json",
            "cache-state-evictable-flag-true.json",
        )
        for name in fixtures:
            payload = load_json(f"fixtures/invalid/{name}")
            self.assertTrue(list(cache_validator.iter_errors(payload)), name)


class ReservationSemantics(unittest.TestCase):
    def setUp(self):
        self.payload = load_json("fixtures/valid/reservation-runtime.json")
        self.envelope = self.payload["resourceEnvelope"]

    def test_every_byte_value_is_an_evidenced_quantity(self):
        quantity_validator = validator("resources/quantity.json")
        quantities = [
            self.envelope["gpuSafePeak"],
            self.envelope["gpuHeadroom"],
            self.envelope["cpuRamSafePeak"],
            self.envelope["diskSafePeak"],
            *self.envelope["gpuContributors"].values(),
        ]
        for quantity in quantities:
            self.assertEqual([], list(quantity_validator.iter_errors(quantity)))
            self.assertIn("source", quantity)
            self.assertIn("confidence", quantity)

    def test_safe_peak_arithmetic_rejects_unknown_understated_and_over_capacity(self):
        self.assertTrue(safe_peak_admissible(self.envelope, available_bytes=20_000_000_000))
        unknown = json.loads(json.dumps(self.envelope))
        unknown["gpuContributors"]["kvCache"] = {"basis": "unknown", "source": "iw-sizer", "confidence": "low"}
        self.assertFalse(safe_peak_admissible(unknown, available_bytes=20_000_000_000))
        understated = json.loads(json.dumps(self.envelope))
        understated["gpuSafePeak"]["bytes"] = 1
        self.assertFalse(safe_peak_admissible(understated, available_bytes=20_000_000_000))
        self.assertFalse(safe_peak_admissible(self.envelope, available_bytes=1))

    def test_authority_enforces_idempotency_fence_and_physical_dedupe(self):
        authority = ReservationAuthority(progress_timeout_ms=30_000)
        with self.assertRaises(PermissionError):
            authority.reserve("rogue", "payload", 7, "node/gpu", self.envelope, 0, caller="adapter")
        first = authority.reserve("same", "payload-a", 7, "node/gpu", self.envelope, authority_tick_ms=100)
        retry = authority.reserve("same", "payload-a", 7, "node/gpu", self.envelope, authority_tick_ms=200)
        self.assertEqual(first["reservationId"], retry["reservationId"])
        with self.assertRaises(IdempotencyConflict):
            authority.reserve("same", "payload-b", 7, "node/gpu", self.envelope, authority_tick_ms=300)
        self.assertFalse(authority.authorize(first["reservationId"], fencing_epoch=6))
        self.assertTrue(authority.authorize(first["reservationId"], fencing_epoch=7))
        duplicate_path = authority.reserve("other", "payload-c", 8, "node/gpu", self.envelope, authority_tick_ms=400)
        self.assertEqual(duplicate_path["reservationId"], first["reservationId"])

    def test_progress_extends_authority_lease_and_silence_releases_every_resource(self):
        authority = ReservationAuthority(progress_timeout_ms=1_000)
        reservation = authority.reserve("load", "payload", 2, "node/gpu", self.envelope, authority_tick_ms=0)
        self.assertEqual([], authority.reconcile(authority_tick_ms=900))
        self.assertTrue(authority.observe_progress(reservation["reservationId"], 1, authority_tick_ms=900))
        self.assertEqual([], authority.reconcile(authority_tick_ms=1_800))
        self.assertEqual([reservation["reservationId"]], authority.reconcile(authority_tick_ms=1_901))
        self.assertTrue(authority.released_all_resources(reservation["reservationId"]))


class DeploymentAndLoadSemantics(unittest.TestCase):
    def test_deployment_key_known_answers_and_live_field_exclusion(self):
        vectors = load_json("conformance/deployment-key-vectors.json")
        base = vectors["cases"][0]
        self.assertEqual(canonical_deployment_key(base["identity"]), base["expectedDeploymentKey"])
        reordered = vectors["cases"][1]
        self.assertEqual(canonical_deployment_key(reordered["identity"]), base["expectedDeploymentKey"])
        changed = vectors["cases"][2]
        self.assertNotEqual(canonical_deployment_key(changed["identity"]), base["expectedDeploymentKey"])
        self.assertFalse(set(vectors["excludedLiveFields"]) & set(base["identity"]))

    def test_two_waiters_cancel_independently_and_final_waiter_cancels_load(self):
        loads = SingleFlightLoads()
        self.assertTrue(loads.attach("sha256:key", "w1"))
        self.assertFalse(loads.attach("sha256:key", "w2"))
        self.assertEqual(loads.cancel("sha256:key", "w1"), {"cancel_underlying": False})
        self.assertEqual(loads.waiters("sha256:key"), {"w2"})
        self.assertEqual(loads.cancel("sha256:key", "w2"), {"cancel_underlying": True})
        self.assertEqual(loads.waiters("sha256:key"), set())


class NativeLinkDispatchSemantics(unittest.TestCase):
    def test_native_dispatch_is_negotiated_whitelisted_and_bounded(self):
        valid = load_json("fixtures/valid/link-request-meta-native.json")
        link_validator = validator("requests/link-request-meta.json")
        self.assertEqual([], list(link_validator.iter_errors(valid)))
        self.assertEqual(link_dispatch_decision(valid, {"native_link_requests": "1"}), {"allowed": True})
        self.assertEqual(
            link_dispatch_decision(valid, {}),
            {"allowed": False, "code": "FEATURE_UNSUPPORTED"},
        )
        for name in (
            "link-request-meta-native-absolute-uri.json",
            "link-request-meta-native-family-path-mismatch.json",
            "link-request-meta-native-binary-content.json",
            "link-request-meta-native-oversize.json",
        ):
            payload = load_json(f"fixtures/invalid/{name}")
            schema_errors = list(link_validator.iter_errors(payload))
            decision = link_dispatch_decision(payload, {"native_link_requests": "1"})
            self.assertTrue(schema_errors or not decision["allowed"], name)


class FullOpenApiParity(unittest.TestCase):
    def test_openapi_and_standalone_validation_decisions_match(self):
        openapi = yaml.safe_load((ROOT / "openapi/inferweave-v1.yaml").read_text())
        components = openapi["components"]["schemas"]
        openapi_resolver = RefResolver(base_uri="", referrer=openapi)
        pairs = {
            "Deployment": "deployments/deployment.json",
            "RerankRequest": "requests/rerank.json",
            "PredictionRequest": "requests/prediction.json",
            "EmbeddingRequest": "requests/embeddings.json",
        }
        invalid_cases = {
            "Deployment": [
                {"deployment_id": "", "deployment_key": "sha256:" + "0" * 64, "manifest": {}},
                {"deployment_id": "d", "deployment_key": "not-a-digest", "manifest": {}},
            ],
            "RerankRequest": [{"family": "reranking", "model": "m", "query": "q", "documents": []}],
            "PredictionRequest": [{"family": "prediction", "model": "m", "inputs": []}],
            "EmbeddingRequest": [{"family": "embeddings", "model": "m", "input": []}],
        }
        for component, relative in pairs.items():
            standalone = validator(relative)
            inline = Draft7Validator(components[component], resolver=openapi_resolver)
            for payload in invalid_cases[component]:
                self.assertEqual(bool(list(standalone.iter_errors(payload))), bool(list(inline.iter_errors(payload))), component)
                self.assertTrue(list(standalone.iter_errors(payload)), component)


if __name__ == "__main__":
    unittest.main()
