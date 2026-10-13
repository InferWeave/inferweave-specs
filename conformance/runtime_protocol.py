"""Fixture/conformance semantics for runtime contracts; never a production allocator."""

from copy import deepcopy
import hashlib
import json
import math
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

_NATIVE_LINK_CAPABILITY = "iw.link-native-request/1"
_NATIVE_LINK_RESPONSE_CAPABILITY = "iw.link-native-response/1"


def _draft7_integer(value):
    """Return the canonical int for a finite Draft 7 integer-valued JSON number."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if isinstance(value, float) and (not math.isfinite(value) or not value.is_integer()):
        return None
    return int(value)


def _reject_non_json_constant(value):
    raise ValueError(f"non-JSON numeric constant: {value}")


def validate_native_link_response(body, response, negotiated_features):
    """Validate one buffered native Link response without inferring HTTP semantics from its body."""
    features = set(negotiated_features or ())
    if not {_NATIVE_LINK_CAPABILITY, _NATIVE_LINK_RESPONSE_CAPABILITY} <= features:
        return {"allowed": False, "code": "FEATURE_UNSUPPORTED"}
    if not isinstance(body, bytes) or not isinstance(response, dict):
        return {"allowed": False, "code": "INVALID_NATIVE_RESPONSE"}
    if set(response) != {"status", "headers", "body_bytes", "body_sha256"}:
        return {"allowed": False, "code": "INVALID_NATIVE_RESPONSE"}
    status = _draft7_integer(response.get("status"))
    headers = response.get("headers")
    body_bytes = _draft7_integer(response.get("body_bytes"))
    digest = response.get("body_sha256")
    valid_status = (
        status is not None
        and (200 <= status <= 299 or 400 <= status <= 599)
    )
    valid_headers = isinstance(headers, dict) and set(headers) <= {
        "content-type", "retry-after", "location"
    }
    if not valid_status or not valid_headers:
        return {"allowed": False, "code": "INVALID_NATIVE_RESPONSE"}
    if "content-type" in headers and headers["content-type"] != "application/json":
        return {"allowed": False, "code": "INVALID_NATIVE_RESPONSE"}
    if body_bytes is None or not 0 <= body_bytes <= 16_777_216:
        return {"allowed": False, "code": "INVALID_NATIVE_RESPONSE"}
    if len(body) > 16_777_216:
        return {"allowed": False, "code": "INVALID_NATIVE_RESPONSE"}
    actual_digest = "sha256:" + hashlib.sha256(body).hexdigest()
    if body_bytes != len(body) or digest != actual_digest:
        return {"allowed": False, "code": "INVALID_NATIVE_RESPONSE"}
    if body:
        if headers.get("content-type") != "application/json":
            return {"allowed": False, "code": "INVALID_NATIVE_RESPONSE"}
        try:
            json.loads(body.decode("utf-8"), parse_constant=_reject_non_json_constant)
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError, RecursionError):
            return {"allowed": False, "code": "INVALID_NATIVE_RESPONSE"}
    if status == 204 and body:
        return {"allowed": False, "code": "INVALID_NATIVE_RESPONSE"}
    retry_after = headers.get("retry-after")
    if retry_after is not None and (
        status not in {429, 503}
        or not isinstance(retry_after, str)
        or re.fullmatch(r"0|[1-9][0-9]{0,9}", retry_after) is None
    ):
        return {"allowed": False, "code": "INVALID_NATIVE_RESPONSE"}
    location = headers.get("location")
    if location is not None and (
        status not in {201, 202}
        or not isinstance(location, str)
        or re.fullmatch(r"/inferweave/v1/jobs/[A-Za-z0-9._:-]{1,256}", location) is None
    ):
        return {"allowed": False, "code": "INVALID_NATIVE_RESPONSE"}
    return {"allowed": True, "status": status, "headers": deepcopy(headers), "body": body}


def negotiate_registration_capabilities(offered, supported):
    """Exact, bounded intersection for POST /v1/node/register capabilities arrays."""
    if not isinstance(offered, list):
        return []
    grammar = re.compile(r"^iw\.[a-z0-9-]+/(0|[1-9][0-9]*)$")
    offered = {
        item for item in offered[:32]
        if isinstance(item, str) and len(item) <= 128 and grammar.fullmatch(item)
    }
    negotiated = []
    seen = set()
    for item in supported:
        if item in offered and item not in seen:
            negotiated.append(item)
            seen.add(item)
    return negotiated


def _native_link_ack(hello, status, negotiated_features=None, reason=None):
    ack = {
        "kind": "hello_ack",
        "native_link_version": 1,
        "registration_connection_id": hello.get("registration_connection_id", ""),
        "link_incarnation_id": hello.get("link_incarnation_id", ""),
        "binding_status": status,
        "negotiated_features": list(negotiated_features or ()) if status == "bound" else [],
    }
    if reason is not None:
        ack["reason"] = reason
    return ack


def negotiate_native_link(registration, hello, local_features):
    """Return the v1 acknowledgement bound to one current registration and Link socket."""
    if hello.get("native_link_version") != 1:
        return None
    if not registration or not registration.get("fresh"):
        return _native_link_ack(hello, "unbound", reason="registration_not_current")
    if not registration.get("credential_valid"):
        return _native_link_ack(hello, "unbound", reason="credential_invalid")
    if hello.get("registration_connection_id") != registration.get("connection_id"):
        return _native_link_ack(hello, "unbound", reason="registration_mismatch")
    if _NATIVE_LINK_CAPABILITY not in registration.get("capabilities", set()):
        return _native_link_ack(hello, "unbound", reason="feature_not_registered")
    if _NATIVE_LINK_CAPABILITY not in hello.get("native_link_features", []):
        return _native_link_ack(hello, "unbound", reason="feature_not_offered")
    if _NATIVE_LINK_CAPABILITY not in local_features:
        return _native_link_ack(hello, "unbound", reason="feature_not_supported")
    registration_features = set(registration.get("capabilities", ()))
    hello_features = set(hello.get("native_link_features", ()))
    local_features = set(local_features)
    negotiated = [
        capability
        for capability in (_NATIVE_LINK_CAPABILITY, _NATIVE_LINK_RESPONSE_CAPABILITY)
        if capability in registration_features
        and capability in hello_features
        and capability in local_features
    ]
    return _native_link_ack(hello, "bound", negotiated)


def accept_native_link_ack(hello, ack):
    """A node enables native dispatch only for the acknowledgement of its exact Hello."""
    return bool(
        ack
        and ack.get("kind") == "hello_ack"
        and ack.get("native_link_version") == 1
        and ack.get("binding_status") == "bound"
        and ack.get("registration_connection_id") == hello.get("registration_connection_id")
        and ack.get("link_incarnation_id") == hello.get("link_incarnation_id")
        and _NATIVE_LINK_CAPABILITY in hello.get("native_link_features", [])
        and _NATIVE_LINK_CAPABILITY in ack.get("negotiated_features", [])
    )


def accept_native_link_response_ack(hello, ack):
    """Response proof is usable only when its separate capability is in the exact accepted ack."""
    return bool(
        accept_native_link_ack(hello, ack)
        and _NATIVE_LINK_RESPONSE_CAPABILITY in hello.get("native_link_features", [])
        and _NATIVE_LINK_RESPONSE_CAPABILITY in ack.get("negotiated_features", [])
    )


class NativeLinkState:
    """Implementation-neutral fixture model; production must provide equivalent atomicity."""

    def __init__(self, local_features):
        self.local_features = set(local_features)
        self.registrations = {}
        self.links = {}

    def register(self, node_id, connection_id, capabilities):
        self.registrations[node_id] = {
            "connection_id": connection_id,
            "capabilities": set(capabilities),
            "fresh": True,
            "credential_valid": True,
        }

    def accept(self, node_id, hello):
        previous = self.links.get(node_id)
        if previous:
            previous["current"] = False
        ack = negotiate_native_link(self.registrations.get(node_id), hello, self.local_features)
        self.links[node_id] = {
            "incarnation_id": hello.get("link_incarnation_id"),
            "registration_connection_id": hello.get("registration_connection_id"),
            "ack": deepcopy(ack),
            "current": True,
            "live": True,
        }
        return deepcopy(ack)

    def withdraw(self, node_id):
        registration = self.registrations.get(node_id)
        if registration:
            registration["fresh"] = False

    def expire(self, node_id):
        self.withdraw(node_id)

    def expire_credential(self, node_id):
        registration = self.registrations.get(node_id)
        if registration:
            registration["credential_valid"] = False

    def close(self, node_id):
        link = self.links.get(node_id)
        if link:
            link["live"] = False
            link["current"] = False

    def dispatch(self, node_id, link_incarnation_id, meta):
        # This lookup-and-check is one transition in the reference model. Production performs
        # selection, binding validation, and frame enqueue under one manager synchronization scope.
        link = self.links.get(node_id)
        if meta.get("native") is None:
            return {"allowed": bool(link and link["live"] and link["incarnation_id"] == link_incarnation_id)}
        registration = self.registrations.get(node_id)
        binding_valid = bool(
            link
            and link["live"]
            and link["current"]
            and link["incarnation_id"] == link_incarnation_id
            and accept_native_link_ack(
                {
                    "registration_connection_id": link["registration_connection_id"],
                    "link_incarnation_id": link["incarnation_id"],
                    "native_link_features": [_NATIVE_LINK_CAPABILITY],
                },
                link["ack"],
            )
            and registration
            and registration["fresh"]
            and registration["credential_valid"]
            and registration["connection_id"] == link["registration_connection_id"]
            and _NATIVE_LINK_CAPABILITY in registration["capabilities"]
        )
        if not binding_valid:
            return {"allowed": False, "code": "FEATURE_UNSUPPORTED"}
        return link_dispatch_decision(meta, {"native_link_requests": "1"})


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
