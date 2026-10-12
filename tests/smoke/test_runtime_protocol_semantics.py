#!/usr/bin/env python3
"""Executable semantics for the amended IW-RT runtime contracts."""

import json
import hashlib
import unittest
from pathlib import Path

import yaml
from jsonschema import Draft7Validator, RefResolver

from conformance.runtime_protocol import (
    IdempotencyConflict,
    PhysicalResourceConflict,
    ReservationAuthority,
    SingleFlightLoads,
    canonical_deployment_key,
    canonical_reservation_request_digest,
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

    def reserve(self, authority, key, payload, epoch, tick, **kwargs):
        envelope = kwargs.pop("envelope", self.envelope)
        resource_domain_key = kwargs.pop("resource_domain_key", "node")
        physical_key = kwargs.pop("physical_key", resource_domain_key + "/" + envelope["deviceIds"][0])
        owner_id = kwargs.pop("owner_id", "runtime-manager/deployment-a")
        placement_group_id = kwargs.pop("placement_group_id", "placement-a")
        requested_bytes = kwargs.pop("requested_bytes", self.payload["requestedBytes"])
        request_identity = {
            "schema_version": "inferweave.reservation-request/v1",
            "deployment_key": "sha256:" + hashlib.sha256(payload.encode()).hexdigest(),
            "owner_id": owner_id,
            "kind": self.payload["kind"],
            "physical_resource_key": physical_key,
            "resource_domain_key": resource_domain_key,
            "placement_group_id": placement_group_id,
            "requested_bytes_decimal": str(requested_bytes),
        }
        payload_digest = canonical_reservation_request_digest(request_identity)
        return authority.reserve(
            key, payload_digest, request_identity, epoch,
            physical_key, resource_domain_key, envelope, tick,
            requested_bytes=requested_bytes,
            effective_bytes=kwargs.pop("effective_bytes", self.payload["effectiveBytes"]),
            gpu_capacity_bytes=kwargs.pop("gpu_capacity_bytes", 20_000_000_000),
            cpu_ram_capacity_bytes=kwargs.pop("cpu_ram_capacity_bytes", 100_000_000_000),
            disk_capacity_bytes=kwargs.pop("disk_capacity_bytes", 100_000_000_000),
            owner_id=owner_id,
            placement_group_id=placement_group_id,
            **kwargs,
        )

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

    def test_reservation_payload_digest_is_bound_to_exact_request_identity(self):
        identity = self.payload["requestIdentity"]
        self.assertEqual(self.payload["payloadDigest"], canonical_reservation_request_digest(identity))
        mutated = json.loads(json.dumps(identity))
        mutated["requested_bytes_decimal"] = str(int(mutated["requested_bytes_decimal"]) + 1)
        self.assertNotEqual(self.payload["payloadDigest"], canonical_reservation_request_digest(mutated))
        mismatch = load_json("fixtures/invalid/reservation-runtime-payload-digest-mismatch.json")
        self.assertNotEqual(mismatch["payloadDigest"], canonical_reservation_request_digest(mismatch["requestIdentity"]))

    def test_safe_peak_arithmetic_rejects_unknown_understated_and_over_capacity(self):
        self.assertTrue(safe_peak_admissible(self.envelope, available_bytes=20_000_000_000))
        unknown = json.loads(json.dumps(self.envelope))
        unknown["gpuContributors"]["kvCache"] = {"basis": "unknown", "source": "iw-sizer", "confidence": "low"}
        self.assertFalse(safe_peak_admissible(unknown, available_bytes=20_000_000_000))
        understated = json.loads(json.dumps(self.envelope))
        understated["gpuSafePeak"]["bytes"] = 1
        self.assertFalse(safe_peak_admissible(understated, available_bytes=20_000_000_000))
        self.assertFalse(safe_peak_admissible(self.envelope, available_bytes=1))
        wrong_provenance = json.loads(json.dumps(self.envelope))
        wrong_provenance["gpuSafePeak"]["basis"] = "derived"
        wrong_provenance["gpuSafePeak"]["confidence"] = "medium"
        self.assertFalse(safe_peak_admissible(wrong_provenance, available_bytes=20_000_000_000))
        declared = json.loads(json.dumps(self.envelope))
        declared["gpuContributors"]["weights"].update(basis="declared", confidence="low")
        declared["gpuSafePeak"].update(basis="derived", confidence="medium")
        self.assertFalse(safe_peak_admissible(declared, available_bytes=20_000_000_000))
        declared["gpuSafePeak"].update(basis="estimated", confidence="low")
        self.assertTrue(safe_peak_admissible(declared, available_bytes=20_000_000_000))
        derived_low = json.loads(json.dumps(self.envelope))
        for quantity in [*derived_low["gpuContributors"].values(), derived_low["gpuHeadroom"]]:
            quantity.update(basis="derived", confidence="medium")
        derived_low["gpuContributors"]["weights"]["confidence"] = "low"
        derived_low["gpuSafePeak"].update(basis="derived", confidence="low")
        self.assertTrue(safe_peak_admissible(derived_low, available_bytes=20_000_000_000))

    def test_cpu_only_grant_uses_host_capacity_without_fake_gpu(self):
        cpu = load_json("fixtures/valid/reservation-runtime-cpu.json")
        self.assertEqual([], list(validator("resources/reservation.json").iter_errors(cpu)))
        envelope = cpu["resourceEnvelope"]
        self.assertEqual(envelope["accelerator"], "cpu")
        self.assertEqual(envelope["gpuCount"], 0)
        self.assertEqual(envelope["deviceIds"], [])
        self.assertEqual(cpu["resourceDomainKey"], "node_cpu-01")
        self.assertTrue(cpu["physicalResourceKey"].startswith(cpu["resourceDomainKey"] + "/"))
        self.assertTrue(safe_peak_admissible(envelope, 0, 10_000_000_000, 20_000_000_000))
        self.assertFalse(safe_peak_admissible(envelope, 0, 1, 20_000_000_000))

    def test_gpu_grants_are_per_device_and_multi_gpu_uses_placement_group(self):
        broken = json.loads(json.dumps(self.payload))
        broken["resourceEnvelope"]["gpuCount"] = 2
        broken["resourceEnvelope"]["deviceIds"].append("GPU-second")
        self.assertTrue(list(validator("resources/reservation.json").iter_errors(broken)))
        authority = ReservationAuthority(progress_timeout_ms=1_000)
        with self.assertRaises(ValueError):
            self.reserve(authority, "multi", "payload", 1, 0,
                         physical_key="node/group", envelope=broken["resourceEnvelope"],
                         requested_bytes=broken["requestedBytes"], effective_bytes=broken["effectiveBytes"],
                         gpu_capacity_bytes=100_000_000_000, cpu_ram_capacity_bytes=100_000_000_000,
                         disk_capacity_bytes=100_000_000_000, owner_id="runtime-manager/group",
                         placement_group_id="placement-group")

    def test_authority_enforces_idempotency_fence_and_physical_dedupe(self):
        authority = ReservationAuthority(progress_timeout_ms=30_000)
        with self.assertRaises(PermissionError):
            self.reserve(authority, "rogue", "payload", 7, 0, caller="adapter")
        with self.assertRaises(ValueError):
            self.reserve(authority, "under", "payload", 7, 0, requested_bytes=1, effective_bytes=1)
        first = self.reserve(authority, "same", "payload-a", 7, 100, gpu_capacity_bytes=40_000_000_000)
        retry = self.reserve(authority, "same", "payload-a", 7, 200, gpu_capacity_bytes=40_000_000_000)
        self.assertEqual(first["reservationId"], retry["reservationId"])
        with self.assertRaises(IdempotencyConflict):
            self.reserve(authority, "same", "payload-b", 7, 300, gpu_capacity_bytes=40_000_000_000)
        with self.assertRaises(IdempotencyConflict):
            self.reserve(authority, "same", "payload-a", 8, 300, gpu_capacity_bytes=40_000_000_000)
        changed_contract = json.loads(json.dumps(self.envelope))
        changed_contract["topology"]["sameHost"] = False
        with self.assertRaises(IdempotencyConflict):
            self.reserve(authority, "same", "payload-a", 7, 300, gpu_capacity_bytes=40_000_000_000,
                         envelope=changed_contract)
        self.assertFalse(authority.authorize(first["reservationId"], fencing_epoch=6))
        self.assertTrue(authority.authorize(first["reservationId"], fencing_epoch=7))
        self.assertFalse(authority.authorize(first["reservationId"], fencing_epoch=8))
        duplicate_path = self.reserve(authority, "other", "payload-a", 7, 400, gpu_capacity_bytes=40_000_000_000)
        self.assertEqual(duplicate_path["reservationId"], first["reservationId"])
        coresident = self.reserve(authority, "coresident", "payload-b", 8, 450,
                                  gpu_capacity_bytes=40_000_000_000, owner_id="runtime-manager/deployment-b",
                                  placement_group_id="placement-b")
        self.assertNotEqual(coresident["reservationId"], first["reservationId"])
        with self.assertRaises(PhysicalResourceConflict):
            self.reserve(authority, "incompatible", "payload-c", 9, 500,
                         gpu_capacity_bytes=40_000_000_000, owner_id="runtime-manager/deployment-c")

        grouped_gpu = self.reserve(authority, "grouped-gpu", "payload-a", 7, 525,
                                   physical_key="node/" + self.envelope["deviceIds"][0] + "-group",
                                   envelope={**self.envelope, "deviceIds": [self.envelope["deviceIds"][0] + "-group"]},
                                   gpu_capacity_bytes=20_000_000_000,
                                   cpu_ram_capacity_bytes=60_000_000_000,
                                   placement_group_id="placement-a")
        self.assertNotEqual(grouped_gpu["reservationId"], first["reservationId"])
        with self.assertRaises(PhysicalResourceConflict):
            self.reserve(authority, "forged-group", "different-payload", 7, 530,
                         physical_key="node/" + self.envelope["deviceIds"][0] + "-forged",
                         envelope={**self.envelope, "deviceIds": [self.envelope["deviceIds"][0] + "-forged"]},
                         gpu_capacity_bytes=20_000_000_000,
                         cpu_ram_capacity_bytes=60_000_000_000,
                         owner_id="different-owner", placement_group_id="placement-a")

        other_gpu = self.reserve(authority, "other-gpu", "payload-d", 10, 550,
                                 physical_key="node/" + self.envelope["deviceIds"][0] + "-2",
                                 envelope={**self.envelope, "deviceIds": [self.envelope["deviceIds"][0] + "-2"]},
                                 gpu_capacity_bytes=20_000_000_000,
                                 cpu_ram_capacity_bytes=60_000_000_000,
                                 owner_id="runtime-manager/deployment-d", placement_group_id="placement-d")
        self.assertNotEqual(other_gpu["reservationId"], first["reservationId"])
        with self.assertRaises(PhysicalResourceConflict):
            self.reserve(authority, "host-ram-overcommit", "payload-e", 11, 600,
                         physical_key="node/" + self.envelope["deviceIds"][0] + "-3",
                         envelope={**self.envelope, "deviceIds": [self.envelope["deviceIds"][0] + "-3"]},
                         gpu_capacity_bytes=20_000_000_000,
                         cpu_ram_capacity_bytes=60_000_000_000,
                         owner_id="runtime-manager/deployment-e", placement_group_id="placement-e")

    def test_progress_extends_authority_lease_and_silence_releases_every_resource(self):
        authority = ReservationAuthority(progress_timeout_ms=1_000)
        reservation = self.reserve(authority, "load", "payload", 2, 0)
        self.assertEqual([], authority.reconcile(authority_tick_ms=900))
        self.assertFalse(authority.observe_progress(reservation["reservationId"], 1, 500, fencing_epoch=1))
        self.assertFalse(authority.observe_progress(reservation["reservationId"], 1, 500, fencing_epoch=3))
        self.assertFalse(authority.observe_progress(reservation["reservationId"], 1, 0, fencing_epoch=2))
        self.assertTrue(authority.observe_progress(reservation["reservationId"], 1, 900, fencing_epoch=2))
        self.assertEqual([], authority.reconcile(authority_tick_ms=1_800))
        self.assertFalse(authority.observe_progress(reservation["reservationId"], 2, 1_900, fencing_epoch=2))
        self.assertEqual([reservation["reservationId"]], authority.reconcile(authority_tick_ms=1_900))
        self.assertTrue(authority.released_all_resources(reservation["reservationId"]))


class DeploymentAndLoadSemantics(unittest.TestCase):
    def test_deployment_key_known_answers_and_live_field_exclusion(self):
        vectors = load_json("conformance/deployment-key-vectors.json")
        base = vectors["cases"][0]
        self.assertEqual(canonical_deployment_key(base["identity"]), base["expectedDeploymentKey"])
        reordered = vectors["cases"][1]
        self.assertEqual(len(base["identity"]["artifact_bindings"]), 2)
        self.assertEqual(canonical_deployment_key(reordered["identity"]), base["expectedDeploymentKey"])
        changed = vectors["cases"][2]
        self.assertNotEqual(canonical_deployment_key(changed["identity"]), base["expectedDeploymentKey"])
        unicode_case = vectors["cases"][3]
        self.assertEqual(canonical_deployment_key(unicode_case["identity"]), unicode_case["expectedDeploymentKey"])
        self.assertFalse(set(vectors["excludedLiveFields"]) & set(base["identity"]))
        invalid_numeric = json.loads(json.dumps(base["identity"]))
        invalid_numeric["quality_floor"] = 0.95
        identity_validator = validator("deployments/deployment-identity.json")
        self.assertTrue(list(identity_validator.iter_errors(invalid_numeric)))
        with self.assertRaises(ValueError):
            canonical_deployment_key(invalid_numeric)

    def test_deployment_fixture_key_is_bound_to_manifest(self):
        deployment = load_json("fixtures/valid/deployment.json")
        self.assertEqual(deployment["deployment_key"], canonical_deployment_key(deployment["manifest"]))
        mismatch = load_json("fixtures/invalid/deployment-key-mismatch.json")
        self.assertNotEqual(mismatch["deployment_key"], canonical_deployment_key(mismatch["manifest"]))

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
