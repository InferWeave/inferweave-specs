"""Fixture/conformance semantics for runtime contracts; never a production allocator."""

from copy import deepcopy
import hashlib
import json
import re


class IdempotencyConflict(ValueError):
    pass


class PhysicalResourceConflict(ValueError):
    pass


def _canonical_json(value):
    """RFC 8785 encoding for the deployment identity's string/digest-only domain."""
    def reject_number(item):
        if isinstance(item, (int, float)) and not isinstance(item, bool):
            raise ValueError("deployment identity numbers must be represented by a versioned digest")
        if isinstance(item, dict):
            for child in item.values():
                reject_number(child)
        elif isinstance(item, list):
            for child in item:
                reject_number(child)

    reject_number(value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def canonical_deployment_key(identity):
    digest = re.compile(r"^sha256:[0-9a-f]{64}$")
    required = {
        "schema_version", "modality", "model_id", "artifact_bindings", "runtime_identity",
        "effective_profile_digest", "policy_digest", "resource_contract_digest",
    }
    runtime_required = {"adapter", "version", "config_digest"}
    runtime = identity.get("runtime_identity") if isinstance(identity, dict) else None
    valid = (
        isinstance(identity, dict) and set(identity) == required
        and identity.get("schema_version") == "inferweave.deployment-identity/v1"
        and all(isinstance(identity.get(name), str) and identity[name] for name in ("modality", "model_id"))
        and isinstance(identity.get("artifact_bindings"), dict) and identity["artifact_bindings"]
        and all(re.fullmatch(r"[a-z][a-z0-9_.-]{0,63}", role)
                and isinstance(item, str) and digest.fullmatch(item)
                for role, item in identity["artifact_bindings"].items())
        and isinstance(runtime, dict) and set(runtime) == runtime_required
        and all(isinstance(runtime.get(name), str) and runtime[name] for name in ("adapter", "version"))
        and isinstance(runtime.get("config_digest"), str) and digest.fullmatch(runtime["config_digest"])
        and all(isinstance(identity.get(name), str) and digest.fullmatch(identity[name]) for name in
                ("effective_profile_digest", "policy_digest", "resource_contract_digest"))
    )
    if not valid:
        raise ValueError("deployment identity is outside the canonical string/digest-only schema")
    encoded = _canonical_json(identity).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def canonical_reservation_request_digest(identity):
    required = {
        "schema_version", "deployment_key", "owner_component", "owner_gateway_id", "kind",
        "physical_resource_key", "resource_domain_key", "placement_group_id", "requested_bytes_decimal",
    }
    digest = re.compile(r"^sha256:[0-9a-f]{64}$")
    valid = (
        isinstance(identity, dict) and set(identity) == required
        and identity.get("schema_version") == "inferweave.reservation-request/v1"
        and isinstance(identity.get("deployment_key"), str) and digest.fullmatch(identity["deployment_key"])
        and identity.get("kind") in {"placement", "primary-restart", "kv-growth", "runtime-growth", "restore"}
        and all(isinstance(identity.get(name), str) and identity[name] for name in
                ("owner_component", "owner_gateway_id", "physical_resource_key", "resource_domain_key", "placement_group_id"))
        and isinstance(identity.get("requested_bytes_decimal"), str)
        and re.fullmatch(r"0|[1-9][0-9]{0,15}", identity["requested_bytes_decimal"])
        and int(identity["requested_bytes_decimal"]) <= 9007199254740991
    )
    if not valid:
        raise ValueError("reservation request identity is outside its canonical string-only schema")
    return "sha256:" + hashlib.sha256(_canonical_json(identity).encode("utf-8")).hexdigest()


class SingleFlightLoads:
    def __init__(self):
        self._waiters = {}

    def attach(self, deployment_key, waiter_id):
        created = deployment_key not in self._waiters
        self._waiters.setdefault(deployment_key, set()).add(waiter_id)
        return created

    def cancel(self, deployment_key, waiter_id):
        waiters = self._waiters.get(deployment_key, set())
        waiters.discard(waiter_id)
        cancel_underlying = not waiters
        if cancel_underlying:
            self._waiters.pop(deployment_key, None)
        return {"cancel_underlying": cancel_underlying}

    def waiters(self, deployment_key):
        return set(self._waiters.get(deployment_key, set()))


def _evidenced_bytes(quantity):
    if not isinstance(quantity, dict):
        return None
    if quantity.get("basis") not in {"measured", "derived", "estimated", "declared"}:
        return None
    if not isinstance(quantity.get("bytes"), int) or quantity["bytes"] < 0:
        return None
    if not quantity.get("source") or quantity.get("confidence") not in {"high", "medium", "low"}:
        return None
    return quantity["bytes"]


def safe_peak_admissible(envelope, available_bytes, available_cpu_ram_bytes=None, available_disk_bytes=None):
    contributors = envelope.get("gpuContributors", {})
    names = {"weights", "kvCache", "activations", "runtimeWorkspace", "auxiliaryModels", "loadingPeak"}
    if set(contributors) != names:
        return False
    values = [_evidenced_bytes(contributors[name]) for name in sorted(names)]
    headroom = _evidenced_bytes(envelope.get("gpuHeadroom"))
    peak = _evidenced_bytes(envelope.get("gpuSafePeak"))
    if any(value is None for value in values) or headroom is None or peak is None:
        return False
    inputs = [contributors[name] for name in names] + [envelope["gpuHeadroom"]]
    any_non_derived_input = any(quantity["basis"] in {"estimated", "declared"} for quantity in inputs)
    expected_basis = "estimated" if any_non_derived_input else "derived"
    confidence_rank = {"low": 0, "medium": 1, "high": 2}
    weakest = min((quantity["confidence"] for quantity in inputs), key=confidence_rank.get)
    expected_confidence = "low" if any_non_derived_input else ("low" if weakest == "low" else "medium")
    if envelope["gpuSafePeak"].get("basis") != expected_basis:
        return False
    if envelope["gpuSafePeak"].get("confidence") != expected_confidence:
        return False
    cpu_peak = _evidenced_bytes(envelope.get("cpuRamSafePeak"))
    disk_peak = _evidenced_bytes(envelope.get("diskSafePeak"))
    if cpu_peak is None or disk_peak is None:
        return False
    if available_cpu_ram_bytes is not None and cpu_peak > available_cpu_ram_bytes:
        return False
    if available_disk_bytes is not None and disk_peak > available_disk_bytes:
        return False
    return peak >= sum(values) + headroom and peak <= available_bytes


class ReservationAuthority:
    def __init__(self, progress_timeout_ms, authority_id="rebalancer"):
        self.progress_timeout_ms = progress_timeout_ms
        self.authority_id = authority_id
        self._by_idempotency = {}
        self._by_physical = {}
        self._by_domain = {}
        self._reservations = {}
        self._next = 1

    def reserve(self, idempotency_key, payload_digest, request_identity, fencing_epoch, physical_key, resource_domain_key,
                envelope, authority_tick_ms, requested_bytes, effective_bytes, gpu_capacity_bytes,
                cpu_ram_capacity_bytes, disk_capacity_bytes, owner_component, owner_gateway_id,
                placement_group_id, kind, caller="rebalancer"):
        if caller != self.authority_id:
            raise PermissionError("only the configured reservation authority may reserve")
        if payload_digest != canonical_reservation_request_digest(request_identity):
            raise ValueError("payload digest does not match canonical reservation request identity")
        duplicated = {
            "owner_component": owner_component,
            "owner_gateway_id": owner_gateway_id,
            "kind": kind,
            "physical_resource_key": physical_key,
            "resource_domain_key": resource_domain_key,
            "placement_group_id": placement_group_id,
            "requested_bytes_decimal": str(requested_bytes),
        }
        if any(request_identity.get(name) != value for name, value in duplicated.items()):
            raise ValueError("reservation request identity disagrees with admission fields")
        accelerator = envelope.get("accelerator")
        device_ids = envelope.get("deviceIds", [])
        if accelerator == "gpu":
            if envelope.get("gpuCount") != 1 or len(device_ids) != 1:
                raise ValueError("each GPU grant must identify exactly one physical device")
            if physical_key != f"{resource_domain_key}/{device_ids[0]}":
                raise ValueError("physical resource key must derive from host domain and device id")
        elif accelerator == "cpu" and not physical_key.startswith(resource_domain_key + "/"):
            raise ValueError("CPU physical resource key must belong to its host domain")
        peak = _evidenced_bytes(envelope.get("gpuSafePeak"))
        if (not safe_peak_admissible(envelope, gpu_capacity_bytes, cpu_ram_capacity_bytes, disk_capacity_bytes)
                or requested_bytes < peak or effective_bytes < peak):
            raise ValueError("reservation does not cover the evidenced safe peak")
        claim = (
            payload_digest, fencing_epoch, physical_key, resource_domain_key, owner_component, owner_gateway_id, placement_group_id,
            requested_bytes, effective_bytes,
            json.dumps(envelope, sort_keys=True, separators=(",", ":")),
        )
        previous = self._by_idempotency.get(idempotency_key)
        if previous:
            if previous[0] != claim:
                raise IdempotencyConflict(idempotency_key)
            return deepcopy(self._reservations[previous[1]])
        reservation_id = None
        active_ids = self._by_physical.get(physical_key, set())
        for existing_id in active_ids:
            existing = self._reservations[existing_id]
            if existing["claim"] == claim:
                reservation_id = existing_id
                break
        if reservation_id is None:
            domain_ids = self._by_domain.get(resource_domain_key, set())
            # The fixture model covers initial grants, where effective == requested. Production
            # authorities shrink effective holds as allocations become physically observed.
            aggregate_gpu = sum(self._reservations[item]["effectiveBytes"] for item in active_ids) + effective_bytes
            groups = {}
            for item in domain_ids:
                existing = self._reservations[item]
                values = (
                    _evidenced_bytes(existing["resourceEnvelope"]["cpuRamSafePeak"]),
                    _evidenced_bytes(existing["resourceEnvelope"]["diskSafePeak"]),
                )
                group_claim = (existing["deploymentKey"], existing["ownerComponent"], existing["ownerGatewayId"], existing["kind"], existing["fencingEpoch"], values)
                prior = groups.setdefault(existing["placementGroupId"], group_claim)
                if prior != group_claim:
                    raise PhysicalResourceConflict(resource_domain_key)
            incoming = (_evidenced_bytes(envelope["cpuRamSafePeak"]), _evidenced_bytes(envelope["diskSafePeak"]))
            incoming_claim = (request_identity["deployment_key"], owner_component, owner_gateway_id, kind, fencing_epoch, incoming)
            if placement_group_id in groups and groups[placement_group_id] != incoming_claim:
                raise PhysicalResourceConflict(resource_domain_key)
            groups.setdefault(placement_group_id, incoming_claim)
            aggregate_cpu = sum(group_claim[5][0] for group_claim in groups.values())
            aggregate_disk = sum(group_claim[5][1] for group_claim in groups.values())
            if aggregate_gpu > gpu_capacity_bytes or aggregate_cpu > cpu_ram_capacity_bytes or aggregate_disk > disk_capacity_bytes:
                raise PhysicalResourceConflict(physical_key)
            reservation_id = f"reservation-{self._next}"
            self._next += 1
            self._reservations[reservation_id] = {
                "reservationId": reservation_id,
                "fencingEpoch": fencing_epoch,
                "payloadDigest": payload_digest,
                "deploymentKey": request_identity["deployment_key"],
                "ownerComponent": owner_component,
                "ownerGatewayId": owner_gateway_id,
                "placementGroupId": placement_group_id,
                "kind": kind,
                "claim": claim,
                "physicalResourceKey": physical_key,
                "resourceDomainKey": resource_domain_key,
                "resourceEnvelope": deepcopy(envelope),
                "requestedBytes": requested_bytes,
                "effectiveBytes": effective_bytes,
                "progressSequence": 0,
                "lastProgressAuthorityTick": authority_tick_ms,
                "leaseDeadlineAuthorityTick": authority_tick_ms + self.progress_timeout_ms,
                "state": "loading",
                "released": False,
            }
            self._by_physical.setdefault(physical_key, set()).add(reservation_id)
            self._by_domain.setdefault(resource_domain_key, set()).add(reservation_id)
        self._by_idempotency[idempotency_key] = (claim, reservation_id)
        return deepcopy(self._reservations[reservation_id])

    def authorize(self, reservation_id, fencing_epoch):
        current = self._reservations[reservation_id]
        return not current["released"] and fencing_epoch == current["fencingEpoch"]

    def observe_progress(self, reservation_id, sequence, authority_tick_ms, fencing_epoch):
        current = self._reservations[reservation_id]
        if (current["released"] or fencing_epoch != current["fencingEpoch"]
                or sequence <= current["progressSequence"]
                or authority_tick_ms <= current["lastProgressAuthorityTick"]
                or authority_tick_ms >= current["leaseDeadlineAuthorityTick"]):
            return False
        current["progressSequence"] = sequence
        current["lastProgressAuthorityTick"] = authority_tick_ms
        current["leaseDeadlineAuthorityTick"] = authority_tick_ms + self.progress_timeout_ms
        return True

    def reconcile(self, authority_tick_ms):
        expired = []
        for reservation_id, current in self._reservations.items():
            if not current["released"] and authority_tick_ms >= current["leaseDeadlineAuthorityTick"]:
                current["released"] = True
                current["state"] = "expired"
                physical = self._by_physical.get(current["physicalResourceKey"], set())
                physical.discard(reservation_id)
                if not physical:
                    self._by_physical.pop(current["physicalResourceKey"], None)
                domain = self._by_domain.get(current["resourceDomainKey"], set())
                domain.discard(reservation_id)
                if not domain:
                    self._by_domain.pop(current["resourceDomainKey"], None)
                expired.append(reservation_id)
        return expired

    def released_all_resources(self, reservation_id):
        current = self._reservations[reservation_id]
        return (current["released"]
                and reservation_id not in self._by_physical.get(current["physicalResourceKey"], set())
                and reservation_id not in self._by_domain.get(current["resourceDomainKey"], set()))


_NATIVE_ENDPOINTS = {
    "embeddings": "/embeddings",
    "reranking": "/rerank",
    "prediction": "/predictions",
    "llm": "/jobs",
    "reasoning": "/jobs",
    "stt": "/jobs",
    "tts": "/jobs",
    "audio": "/jobs",
    "image": "/jobs",
    "video": "/jobs",
    "multimodal": "/jobs",
    "scientific": "/jobs",
    "rag": "/jobs",
}


def link_dispatch_decision(meta, features):
    native = meta.get("native")
    if native is None:
        return {"allowed": True}
    if features.get("native_link_requests") != "1":
        return {"allowed": False, "code": "FEATURE_UNSUPPORTED"}
    allowed = (
        native.get("endpoint") == _NATIVE_ENDPOINTS.get(native.get("family"))
        and native.get("method") == "POST"
        and native.get("content_type") == "application/json"
        and isinstance(native.get("payload_bytes"), int)
        and 0 <= native["payload_bytes"] <= 16_777_216
        and isinstance(native.get("artifact_refs"), list)
    )
    return {"allowed": True} if allowed else {"allowed": False, "code": "INVALID_NATIVE_DISPATCH"}
