"""Implementation-neutral reference semantics for runtime protocol contracts."""

from copy import deepcopy
import hashlib
import json


class IdempotencyConflict(ValueError):
    pass


def _canonical_json(value):
    """RFC 8785-compatible encoding for the integer/string deployment identity domain."""
    def reject_float(item):
        if isinstance(item, float):
            raise ValueError("deployment identities must not contain floating-point values")
        if isinstance(item, dict):
            for child in item.values():
                reject_float(child)
        elif isinstance(item, list):
            for child in item:
                reject_float(child)

    reject_float(value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def canonical_deployment_key(identity):
    encoded = _canonical_json(identity).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


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


def safe_peak_admissible(envelope, available_bytes):
    contributors = envelope.get("gpuContributors", {})
    names = {"weights", "kvCache", "activations", "runtimeWorkspace", "auxiliaryModels", "loadingPeak"}
    if set(contributors) != names:
        return False
    values = [_evidenced_bytes(contributors[name]) for name in sorted(names)]
    headroom = _evidenced_bytes(envelope.get("gpuHeadroom"))
    peak = _evidenced_bytes(envelope.get("gpuSafePeak"))
    if any(value is None for value in values) or headroom is None or peak is None:
        return False
    return peak >= sum(values) + headroom and peak <= available_bytes


class ReservationAuthority:
    def __init__(self, progress_timeout_ms, authority_id="rebalancer"):
        self.progress_timeout_ms = progress_timeout_ms
        self.authority_id = authority_id
        self._by_idempotency = {}
        self._by_physical = {}
        self._reservations = {}
        self._next = 1

    def reserve(self, idempotency_key, payload_digest, fencing_epoch, physical_key, envelope, authority_tick_ms, caller="rebalancer"):
        if caller != self.authority_id:
            raise PermissionError("only the configured reservation authority may reserve")
        previous = self._by_idempotency.get(idempotency_key)
        if previous:
            if previous[0] != payload_digest:
                raise IdempotencyConflict(idempotency_key)
            return deepcopy(self._reservations[previous[1]])
        if physical_key in self._by_physical:
            reservation_id = self._by_physical[physical_key]
        else:
            reservation_id = f"reservation-{self._next}"
            self._next += 1
            self._reservations[reservation_id] = {
                "reservationId": reservation_id,
                "fencingEpoch": fencing_epoch,
                "physicalResourceKey": physical_key,
                "resourceEnvelope": deepcopy(envelope),
                "progressSequence": 0,
                "lastProgressAuthorityTick": authority_tick_ms,
                "leaseDeadlineAuthorityTick": authority_tick_ms + self.progress_timeout_ms,
                "state": "loading",
                "released": False,
            }
            self._by_physical[physical_key] = reservation_id
        self._by_idempotency[idempotency_key] = (payload_digest, reservation_id)
        return deepcopy(self._reservations[reservation_id])

    def authorize(self, reservation_id, fencing_epoch):
        current = self._reservations[reservation_id]
        return not current["released"] and fencing_epoch >= current["fencingEpoch"]

    def observe_progress(self, reservation_id, sequence, authority_tick_ms):
        current = self._reservations[reservation_id]
        if current["released"] or sequence <= current["progressSequence"]:
            return False
        current["progressSequence"] = sequence
        current["lastProgressAuthorityTick"] = authority_tick_ms
        current["leaseDeadlineAuthorityTick"] = authority_tick_ms + self.progress_timeout_ms
        return True

    def reconcile(self, authority_tick_ms):
        expired = []
        for reservation_id, current in self._reservations.items():
            if not current["released"] and authority_tick_ms > current["leaseDeadlineAuthorityTick"]:
                current["released"] = True
                current["state"] = "expired"
                self._by_physical.pop(current["physicalResourceKey"], None)
                expired.append(reservation_id)
        return expired

    def released_all_resources(self, reservation_id):
        current = self._reservations[reservation_id]
        return current["released"] and current["physicalResourceKey"] not in self._by_physical


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
