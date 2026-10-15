#!/usr/bin/env python3
"""InferWeave Protocol v1 conformance runner.

Validates conformance fixtures against the canonical JSON Schemas:
- every fixture under fixtures/valid/ must validate against its schema
- every fixture under fixtures/invalid/ must fail its schema
- every fixture under fixtures/federation/ must validate against its schema
- every pinned contract under contracts/gpu-memory/ must validate as a fleet snapshot
- conformance/node-join-vectors.json (spec 47) must agree with the reference model in
  conformance/node_join.py, and its enrollment known answers must be reproducible from the seed
- conformance/native-link-binding-vectors.json (specs 45/49) must reject registration/Link races
- conformance/runtime-family-vectors.json (spec 53) is run per family; each family reports PASS/FAIL

The runner is intentionally strict: a valid fixture that stops validating, or an invalid
fixture that starts validating, fails the run.

Usage: python3 conformance/runner.py
"""
from pathlib import Path
import argparse
import json
import sys
import urllib.error
import urllib.request
from jsonschema import Draft7Validator, RefResolver

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "conformance"))
import node_join  # noqa: E402
import runtime_protocol  # noqa: E402
import link_http_json  # noqa: E402
import dynamic_aliases  # noqa: E402
import alias_edge_delegation  # noqa: E402
import runtime_observations  # noqa: E402
import alias_execution  # noqa: E402
SCHEMA_DIR = ROOT / "schemas" / "v1"

# fixture basename -> schema rel path (relative to schemas/v1)
MAP = {
    "alias-link-request": "requests/link-alias-request.json",
    "alias-consume-dispatch": "requests/link-consume-dispatch.json",
    "alias-consume-dispatch-ack": "requests/link-consume-dispatch-ack.json",
    "alias-owner-execution-permit": "aliases/owner-execution-permit.json",
    "alias-execution-binding": "aliases/execution-binding.json",
    "alias-execution-permit": "aliases/execution-permit.json",
    "alias-inference-assertion": "aliases/inference-assertion.json",
    "alias-execution-identity": "aliases/execution-identity.json",
    "alias-execution-claim": "aliases/execution-claim.json",
    "runtime-observation-report": "requests/runtime-observation-report.json",
    "runtime-observation-event": "events/runtime-observation-event.json",
    "dynamic-alias-edge-assertion": "aliases/edge-assertion.json",
    "dynamic-alias-capabilities": "aliases/capabilities.json",
    "dynamic-alias-routing-trace": "aliases/routing-trace.json",
    "dynamic-alias-advertisement-page": "aliases/advertisement-page.json",
    "dynamic-alias-catalog": "aliases/catalog.json",
    "dynamic-alias-validate-request": "aliases/validate-request.json",
    "dynamic-alias-simulate-request": "aliases/simulate-request.json",
    "dynamic-alias-error": "aliases/error.json",
    "dynamic-alias-history": "aliases/history.json",
    "dynamic-alias-validation": "aliases/validation.json",
    "dynamic-alias-list": "aliases/list.json",
    "dynamic-alias-detail": "aliases/detail.json",
    "dynamic-alias-rollback": "aliases/rollback.json",
    "dynamic-alias-publish": "aliases/publish.json",
    "dynamic-alias-draft-write": "aliases/draft-write.json",
    "dynamic-alias-advertisement": "aliases/advertisement.json",
    "dynamic-alias-event": "aliases/event.json",
    "dynamic-alias-resolve-request": "aliases/resolve-request.json",
    "dynamic-alias-resolution": "aliases/resolution.json",
    "dynamic-alias-definition": "aliases/definition.json",
    "capability-request": "routing/capability-request.json",
    "routing-decision": "routing/routing-decision.json",
    "protocol": "common/protocol.json",
    "identity": "common/identity.json",
    "features": "common/features.json",
    "provenance": "common/provenance.json",
    "extensions": "common/extensions.json",
    "error": "errors/error.json",
    "gateway": "topology/gateway.json",
    "node": "topology/node.json",
    "device": "topology/device.json",
    "allocation": "topology/allocation.json",
    "model": "model/model.json",
    "model-variant": "model/model-variant.json",
    "capabilities": "model/capabilities.json",
    "requirements": "model/requirements.json",
    "placement": "model/placement.json",
    "residency": "model/residency.json",
    "alias": "model/alias.json",
    "capacity": "resources/capacity.json",
    "seat": "resources/seat.json",
    "memory": "resources/memory.json",
    "runtime-instance": "runtime/runtime-instance.json",
    "runtime-load-request": "runtime/load-request.json",
    "node-register-response": "requests/node-register-response.json",
    "node-register": "requests/node-register.json",
    "link-hello-ack": "requests/link-hello-ack.json",
    "link-hello": "requests/link-hello.json",
    "link-http-meta": "requests/link-http-meta.json",
    "link-http-request": "requests/link-http-request.json",
    "link-http-response-head": "requests/link-http-response-head.json",
    "link-http-token": "requests/link-http-token.json",
    "link-http-failure": "requests/link-http-failure.json",
    "link-http-end": "requests/link-http-end.json",
    "link-request-meta": "requests/link-request-meta.json",
    "link-end": "requests/link-end.json",
    "link-response-meta": "requests/link-response-meta.json",
    "deployment": "deployments/deployment.json",
    "request": "requests/request.json",
    "registration": "requests/registration.json",
    "heartbeat": "requests/heartbeat.json",
    "node-hardware": "requests/node-hardware.json",
    "node-hardware-report": "requests/node-hardware-report.json",
    "event": "events/event.json",
    "metric": "events/metric.json",
    "job": "jobs/job.json",
    "progress": "jobs/progress.json",
    "artifact": "artifacts/artifact.json",
    "cache-state": "artifacts/cache-state.json",
    "federation-path": "topology/node.json",
    "quantity": "resources/quantity.json",
    "pressure": "resources/pressure.json",
    "reservation": "resources/reservation.json",
    "gpu-memory-report": "resources/gpu-memory-report.json",
    "gpu-memory-fleet": "resources/gpu-memory-fleet.json",
    "gpu-memory-postmortem": "resources/gpu-memory-postmortem.json",
    "gpu-memory-event": "events/gpu-memory-event.json",
    "rebalance-decision": "resources/rebalance-decision.json",
    "placement-simulation-request": "resources/placement-simulation-request.json",
    "placement-simulation-response": "resources/placement-simulation-response.json",
}

# Pinned iw.gpu-memory/1 contract fixtures (spec 46), shared byte-for-byte with the reference
# implementation; each is a fleet snapshot and must validate as one.
CONTRACT_DIRS = {"contracts/gpu-memory": "resources/gpu-memory-fleet.json"}

# Load every schema once and register it under its absolute $id so relative $refs resolve.
_STORE = {}
for _p in SCHEMA_DIR.rglob("*.json"):
    _s = json.loads(_p.read_text())
    _STORE[_s["$id"]] = _s
_cached = {}


def validator(schema_rel):
    if schema_rel not in _cached:
        schema = json.loads((SCHEMA_DIR / schema_rel).read_text())
        resolver = RefResolver(base_uri=schema["$id"], referrer=schema, store=_STORE)
        _cached[schema_rel] = Draft7Validator(schema, resolver=resolver)
    return _cached[schema_rel]


def schema_for(stem):
    # exact basename match first; otherwise map invalid fixtures by the longest MAP key that is
    # a "-"-delimited prefix of the name ("gpu-memory-report-zero-unknown" -> "gpu-memory-report")
    if stem in MAP:
        return MAP[stem]
    prefixes = [k for k in MAP if stem.startswith(k + "-")]
    return MAP[max(prefixes, key=len)] if prefixes else None


def validate_fixture(path, must_pass, schema_rel=None):
    rel = path.relative_to(ROOT).as_posix()
    stem = path.stem
    schema_rel = schema_rel or schema_for(stem)
    if schema_rel is None:
        print(f"FAIL  {rel}: no schema mapped for fixture name '{stem}'")
        return False
    wire = path.read_bytes()
    if schema_rel == "requests/runtime-observation-report.json":
        try:
            fixture = runtime_observations.decode_report(wire)
        except (ValueError, UnicodeDecodeError) as error:
            if must_pass:
                print(f"FAIL  {rel}: {error}")
            return not must_pass
    else:
        fixture = json.loads(wire)
    errors = list(validator(schema_rel).iter_errors(fixture))
    semantic_errors = []
    if schema_rel == "deployments/deployment.json" and not errors:
        try:
            expected = runtime_protocol.canonical_deployment_key(fixture["manifest"])
            if fixture["deployment_key"] != expected:
                semantic_errors.append("deployment_key does not match canonical manifest digest")
        except (KeyError, TypeError, ValueError) as error:
            semantic_errors.append(f"deployment identity binding failed: {error}")
    if schema_rel == "resources/reservation.json" and fixture.get("contractVersion") == 1 and not errors:
        try:
            expected = runtime_protocol.canonical_reservation_request_digest(fixture["requestIdentity"])
            if fixture["payloadDigest"] != expected:
                semantic_errors.append("payloadDigest does not match canonical requestIdentity digest")
            identity = fixture["requestIdentity"]
            duplicated = {
                "owner_component": fixture["owner"]["component"],
                "owner_gateway_id": fixture["owner"]["gatewayId"],
                "kind": fixture["kind"],
                "physical_resource_key": fixture["physicalResourceKey"],
                "resource_domain_key": fixture["resourceDomainKey"],
                "placement_group_id": fixture["placementGroupId"],
                "requested_bytes_decimal": str(fixture["requestedBytes"]),
            }
            if any(identity.get(name) != value for name, value in duplicated.items()):
                semantic_errors.append("requestIdentity disagrees with duplicated reservation fields")
        except (KeyError, TypeError, ValueError) as error:
            semantic_errors.append(f"reservation request identity binding failed: {error}")
    if schema_rel == "requests/runtime-observation-report.json" and not errors:
        semantic_errors.extend(runtime_observations.semantic_errors(fixture))
    if schema_rel == "events/runtime-observation-event.json" and not errors:
        semantic_errors.extend(runtime_observations.semantic_errors(fixture["report"]))
    if schema_rel.startswith("aliases/") and not errors:
        semantic_errors.extend(dynamic_aliases.semantic_errors(fixture, Path(schema_rel).stem))
    ok = not errors and not semantic_errors
    if ok == must_pass:
        return True
    print(f"FAIL  {rel}: expected {'valid' if must_pass else 'invalid'} against {schema_rel}")
    for e in errors[:5]:
        print(f"        {list(e.path)}: {e.message}")
    for error in semantic_errors[:5]:
        print(f"        semantic: {error}")
    return False


def check_openapi_refs():
    """Every local $ref in the OpenAPI must resolve within components.schemas."""
    try:
        import yaml
    except ImportError:
        print("FAIL  openapi: pyyaml not installed; cannot validate refs")
        return False
    spec = yaml.safe_load((ROOT / "openapi" / "inferweave-v1.yaml").read_text())
    names = set(spec.get("components", {}).get("schemas", {}).keys())
    bad = []

    def walk(node):
        if isinstance(node, dict):
            if isinstance(node.get("$ref"), str):
                ref = node["$ref"]
                if ref.startswith("#/components/schemas/"):
                    name = ref.rsplit("/", 1)[-1]
                    if name not in names:
                        bad.append(ref)
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(spec)
    if bad:
        print(f"FAIL  openapi: unresolvable $refs {sorted(set(bad))}")
        return False
    return True


def check_deployment_key_vectors():
    """Recompute immutable deployment-key known answers and equality relations."""
    doc = json.loads((ROOT / "conformance" / "deployment-key-vectors.json").read_text())
    cases = doc["cases"]
    base = runtime_protocol.canonical_deployment_key(cases[0]["identity"])
    ok = all(
        runtime_protocol.canonical_deployment_key(case["identity"]) == case["expectedDeploymentKey"]
        for case in cases
    )
    ok = ok and cases[1]["expectedDeploymentKey"] == base
    ok = ok and cases[2]["expectedDeploymentKey"] != base
    if not ok:
        print("FAIL  deployment-key vectors disagree with canonical JCS/SHA-256 reference")
    return ok


def check_native_link_binding_vectors():
    """Exercise negotiation and revocation against hostile registration/Link races."""
    doc = json.loads((ROOT / "conformance" / "native-link-binding-vectors.json").read_text())
    capability = doc["capability"]
    failures = []
    for case in doc["registrationCases"]:
        got = runtime_protocol.negotiate_registration_capabilities(case.get("offered"), case["supported"])
        if got != case["expect"]:
            failures.append(case["id"])
    for case in doc["negotiationCases"]:
        registration = dict(doc["registration"])
        hello = dict(doc["hello"])
        local = {capability}
        if case["mutation"] == "registration_connection_id":
            registration["connection_id"] = "c-fedcba9876543210"
        elif case["mutation"] == "registration_fresh":
            registration["fresh"] = False
        elif case["mutation"] == "credential_valid":
            registration["credential_valid"] = False
        elif case["mutation"] == "registration_capability":
            registration["capabilities"] = []
        elif case["mutation"] == "local_feature":
            local.clear()
        ack = runtime_protocol.negotiate_native_link(registration, hello, local)
        if ack["binding_status"] != case["expectStatus"] or ack.get("reason") != case.get("expectReason"):
            failures.append(case["id"])

    hello = dict(doc["hello"])
    exact_ack = runtime_protocol.negotiate_native_link(doc["registration"], hello, {capability})
    for case in doc["acknowledgementCases"]:
        ack = dict(exact_ack)
        if case["mutation"] == "registration_connection_id":
            ack["registration_connection_id"] = "c-fedcba9876543210"
        elif case["mutation"] == "link_incarnation_id":
            ack["link_incarnation_id"] = "link-incarnation-second-0002"
        if runtime_protocol.accept_native_link_ack(hello, ack) != case["expectAccepted"]:
            failures.append(case["id"])

    native = json.loads((ROOT / "fixtures" / "valid" / "link-request-meta-native.json").read_text())
    for case in doc["stateCases"]:
        state = runtime_protocol.NativeLinkState({capability})
        state.register("node-a", doc["registration"]["connection_id"], {capability})
        first = dict(doc["hello"])
        state.accept("node-a", first)
        if case["transition"] == "reregister":
            state.register("node-a", "c-fedcba9876543210", {capability})
        elif case["transition"] == "replace_link":
            state.accept("node-a", dict(first, link_incarnation_id="link-incarnation-second-0002"))
        elif case["transition"] == "withdraw":
            state.withdraw("node-a")
        elif case["transition"] == "expire":
            state.expire("node-a")
        elif case["transition"] == "expire_credential":
            state.expire_credential("node-a")
        elif case["transition"] == "close":
            state.close("node-a")
        allowed = state.dispatch("node-a", first["link_incarnation_id"], native)["allowed"]
        if allowed != case["expectNative"]:
            failures.append(case["id"])
    register_request = json.loads((ROOT / "fixtures" / "valid" / "node-register-native.json").read_text())
    register_response = json.loads((ROOT / "fixtures" / "valid" / "node-register-response-native.json").read_text())
    negotiated = runtime_protocol.negotiate_registration_capabilities(
        register_request.get("capabilities"), [capability]
    )
    if negotiated != register_response["capabilities"]:
        failures.append("node-register-negotiated-response")
    legacy = json.loads((ROOT / "fixtures" / "valid" / "node-register-legacy.json").read_text())
    if runtime_protocol.negotiate_registration_capabilities(legacy.get("capabilities"), [capability]):
        failures.append("legacy-register-negotiates-none")
    if failures:
        print("FAIL  native-link binding vectors: " + ", ".join(failures))
        return False
    print("PASS  native-link binding vectors (exact registration and Link incarnation)")
    return True


def check_native_link_response_vectors():
    """Exercise exact HTTP response proof without deriving status from response JSON fields."""
    doc = json.loads((ROOT / "conformance" / "native-link-response-vectors.json").read_text())
    failures = []
    negotiated = runtime_protocol.negotiate_native_link(
        doc["registration"], doc["hello"], set(doc["capabilities"])
    )
    if negotiated != doc["ack"]:
        failures.append("response-capability-negotiation")
    if not runtime_protocol.accept_native_link_response_ack(doc["hello"], doc["ack"]):
        failures.append("response-capability-acknowledgement")
    for case in doc["cases"]:
        response = None
        if case.get("responseFixture"):
            response = json.loads((ROOT / case["responseFixture"]).read_text())
        got = runtime_protocol.validate_native_link_response(
            case["body"].encode("utf-8"), response, case.get("negotiatedFeatures", [])
        )
        if got["allowed"] != case["expectAllowed"]:
            failures.append(case["id"])
        elif got["allowed"] and got["status"] != case["expectStatus"]:
            failures.append(case["id"])
        elif not got["allowed"] and got["code"] != case["expectCode"]:
            failures.append(case["id"])
    if failures:
        print("FAIL  native-link response vectors: " + ", ".join(failures))
        return False
    print("PASS  native-link response vectors (status and exact body proof)")
    return True


def check_node_join_vectors():
    """Spec 47: the register vectors agree with the reference model; the known answers recompute."""
    doc = json.loads((ROOT / "conformance" / "node-join-vectors.json").read_text())
    ok = True
    seen = set()
    for case in doc["registerCases"]:
        if case["id"] in seen:
            print(f"FAIL  node-join vector {case['id']}: duplicate id")
            ok = False
        seen.add(case["id"])
        got = node_join.register_decision(doc["baselineRegister"], case)
        for key, want in case["expect"].items():
            if key in ("nodeAdmitted", "storedEqualsSent"):
                continue  # asserted by the gateway's own HTTP-level replay, not modelled here
            if got.get(key) != want:
                print(f"FAIL  node-join vector {case['id']}: {key} expected {want!r}, reference model gives {got.get(key)!r}")
                ok = False
    required = {
        "hw-only-with-hardware", "hw-oversize", "hw-not-object-array", "hw-version-missing",
        "older-node-no-hardware",
    }
    for missing in sorted(required - seen):
        print(f"FAIL  node-join vectors: required case {missing} is missing")
        ok = False
    roles = doc["enrollmentRoleCases"]["cases"]
    if {c["expect"]["status"] for c in roles} != {200, 400}:
        print("FAIL  node-join role cases must cover both 200 and 400")
        ok = False
    for c in roles:
        if node_join.challenge_decision(c["challenge"]) != c["expect"]:
            print(f"FAIL  node-join role case {c['id']}: reference model disagrees")
            ok = False
    trust = doc["enrollmentTrustCases"]["cases"]
    for c in trust:
        if node_join.trust_decision(c) != c["expect"]:
            print(f"FAIL  node-join trust case {c['id']}: reference model disagrees")
            ok = False
    if len(trust) < 5:
        print("FAIL  node-join trust cases: the five required cases are missing")
        ok = False
    id_doc = doc["enrollmentIdCases"]
    if node_join.derived_node_id(id_doc["publicKeyHex"]) != id_doc["derivedNodeId"] or id_doc["publicKeyHex"] != doc["enrollmentKnownAnswers"]["publicKeyHex"]:
        print("FAIL  node-join derived node id does not follow from the known-answer public key")
        ok = False
    for c in id_doc["cases"]:
        if node_join.id_decision(c) != c["expect"]:
            print(f"FAIL  node-join id case {c['id']}: reference model disagrees")
            ok = False
    for c in doc["enrollmentLifecycleCases"]["cases"]:
        got = node_join.lifecycle_decisions(c)
        for i, (step, g) in enumerate(zip(c["steps"], got)):
            if g != step["expect"]:
                print(f"FAIL  node-join lifecycle {c['id']} step {i} ({step['op']}): expected {step['expect']}, model gives {g}")
                ok = False
    for c in doc["requestSizeCases"]["cases"]:
        if node_join.size_decision(c) != c["expect"]:
            print(f"FAIL  node-join size case {c['id']}: reference model disagrees")
            ok = False
    hw_errors = node_join.check_hardware(doc["hardwareSample"])
    if hw_errors:
        print(f"FAIL  node-join hardwareSample: {hw_errors}")
        ok = False
    for error in node_join.check_known_answers(doc["enrollmentKnownAnswers"]):
        print(f"FAIL  node-join known answer: {error}")
        ok = False
    return ok


def admit_advertisement(ad, registry):
    """Reference admission for a typed capability advertisement (spec 48)."""
    if not isinstance(ad.get("family"), str) or ad["family"] not in registry:
        return False
    return all(isinstance(ad.get(k), list) and ad[k] for k in ("input_modalities", "output_modalities"))


def check_runtime_family_vectors(vector_path=None):
    """Spec 53: per-family advertisements and executable native request contract cases.

    Returns {family: [error, ...]}; an empty list means the family passes.
    """
    import yaml
    vector_path = vector_path or ROOT / "conformance" / "runtime-family-vectors.json"
    doc = json.loads(Path(vector_path).read_text())
    openapi = yaml.safe_load((ROOT / "openapi" / "inferweave-v1.yaml").read_text())
    paths = openapi["paths"]
    registry = set(doc["registry"])
    capability_validator = validator("model/capabilities.json")
    openapi_resolver = RefResolver(base_uri="", referrer=openapi)
    results = {}
    for fam in doc["requiredFamilies"]:
        errs = results.setdefault(fam, [])
        vec = doc["families"].get(fam)
        if vec is None:
            errs.append("vector missing")
            continue
        ad = vec["advertisement"]
        if ad.get("family") != fam:
            errs.append("advertisement names a different family")
        if admit_advertisement(ad, registry) != vec["expect"]["admitted"]:
            errs.append("advertisement admission disagrees with reference")
        quality_errors = list(capability_validator.iter_errors(ad))
        if quality_errors:
            errs.append(f"quality/capability schema invalid: {quality_errors[0].message}")
        if json.loads(json.dumps(ad)) != ad:
            errs.append("advertisement does not round-trip")
        if not vec.get("rejections"):
            errs.append("no rejection vectors")
        for rej in vec.get("rejections", []):
            bad = {k: v for k, v in ad.items() if k not in rej.get("omit", [])}
            bad.update(rej.get("override", {}))
            if admit_advertisement(bad, registry) != rej["expect"]["admitted"]:
                errs.append(f"rejection {rej['id']}: admission disagrees with reference")
        cases = vec.get("nativeCases")
        if not cases:
            errs.append("native executable cases missing")
            continue
        if not any(case["expectStatus"] < 400 for case in cases):
            errs.append("native success case missing")
        if not any(case["expectStatus"] >= 400 for case in cases):
            errs.append("native negative case missing")
        for case in cases:
            operation = paths.get(case["path"], {}).get(case["method"].lower())
            if operation is None:
                errs.append(f"native case {case['id']}: {case['method']} {case['path']} not in OpenAPI")
                continue
            request_schema = operation.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema")
            if request_schema is None:
                errs.append(f"native case {case['id']}: OpenAPI operation has no JSON request schema")
                continue
            request_errors = list(Draft7Validator(request_schema, resolver=openapi_resolver).iter_errors(case["body"]))
            if case["expectStatus"] < 400 and request_errors:
                errs.append(f"native case {case['id']}: valid body rejected: {request_errors[0].message}")
            if case["expectStatus"] >= 400 and not request_errors:
                errs.append(f"native case {case['id']}: negative body is accepted by the request contract")
    return results


def report_runtime_family_vectors(vector_path=None):
    ok = True
    for fam, errs in check_runtime_family_vectors(vector_path).items():
        if errs:
            ok = False
            print(f"FAIL  runtime-family {fam}")
            for e in errs:
                print(f"        {e}")
        else:
            print(f"PASS  runtime-family {fam}")
    return ok


def run_live_runtime_family_cases(base_url, vector_path=None):
    """Execute native cases over HTTP. This is optional and is the only HTTP qualification mode."""
    vector_path = vector_path or ROOT / "conformance" / "runtime-family-vectors.json"
    doc = json.loads(Path(vector_path).read_text())
    ok = True
    for family in doc["requiredFamilies"]:
        for case in doc["families"][family]["nativeCases"]:
            url = base_url.rstrip("/") + case["path"]
            request = urllib.request.Request(
                url,
                data=json.dumps(case["body"]).encode(),
                headers={
                    "Content-Type": "application/json",
                    "X-InferWeave-Conformance-Case": case["id"],
                },
                method=case["method"],
            )
            try:
                with urllib.request.urlopen(request, timeout=10) as response:
                    status = response.status
            except urllib.error.HTTPError as error:
                status = error.code
            except OSError as error:
                print(f"FAIL  native HTTP {case['id']}: {error}")
                ok = False
                continue
            if status != case["expectStatus"]:
                print(f"FAIL  native HTTP {case['id']}: expected {case['expectStatus']}, got {status}")
                ok = False
            else:
                print(f"PASS  native HTTP {case['id']} ({status})")
    return ok


def main():
    parser = argparse.ArgumentParser(description="Validate Protocol v1 fixtures and optional live runtime-family HTTP cases.")
    parser.add_argument(
        "--live-base-url",
        help="Execute native runtime-family cases against this URL (include /inferweave/v1 when the server mounts that prefix).",
    )
    parser.add_argument(
        "--runtime-family-vectors",
        type=Path,
        default=ROOT / "conformance" / "runtime-family-vectors.json",
        help=argparse.SUPPRESS,
    )
    args = parser.parse_args()
    failures = 0
    http_errors = link_http_json.check_vectors(ROOT)
    for error in http_errors:
        print("FAIL  " + error)
    failures += len(http_errors)
    if not http_errors:
        print("PASS  Link HTTP JSON vectors (offline; production proof owed)")
    execution_errors = alias_execution.check_vectors(ROOT)
    for error in execution_errors:
        print("FAIL  " + error)
    failures += len(execution_errors)
    if not execution_errors:
        print("PASS  alias execution vectors (offline only; HTTP/DB/node proof owed)")
    observation_errors = runtime_observations.check_vectors(ROOT)
    for error in observation_errors:
        print("FAIL  " + error)
    failures += len(observation_errors)
    if not observation_errors:
        print("PASS  runtime observation vectors (offline producer facts; no admission proof)")
    edge_errors = alias_edge_delegation.check_vectors(ROOT)
    for error in edge_errors:
        print("FAIL  " + error)
    failures += len(edge_errors)
    failures += 0 if check_node_join_vectors() else 1
    failures += 0 if check_deployment_key_vectors() else 1
    failures += 0 if check_native_link_binding_vectors() else 1
    failures += 0 if check_native_link_response_vectors() else 1
    failures += 0 if report_runtime_family_vectors(args.runtime_family_vectors) else 1
    if args.live_base_url:
        failures += 0 if run_live_runtime_family_cases(args.live_base_url, args.runtime_family_vectors) else 1
    else:
        print("INFO  native HTTP: NOT RUN (contract-only validation; pass --live-base-url for operational qualification)")
    for d in ("valid", "federation", "invalid"):
        fixtures = sorted((ROOT / "fixtures" / d).glob("*.json"))
        if not fixtures:
            print(f"FAIL  fixtures/{d}/: directory is empty")
            failures += 1
            continue
        for p in fixtures:
            failures += 0 if validate_fixture(p, d != "invalid") else 1
    for d, schema_rel in CONTRACT_DIRS.items():
        contracts = sorted((ROOT / d).glob("*.json"))
        if not contracts:
            print(f"FAIL  {d}/: directory is empty")
            failures += 1
        for p in contracts:
            failures += 0 if validate_fixture(p, True, schema_rel) else 1
    failures += 0 if check_openapi_refs() else 1
    if failures:
        print(f"CONFORMANCE FAILED: {failures} check(s) did not behave as expected")
        sys.exit(1)
    print("OK: conformance fixtures validate, node-join vectors agree and OpenAPI refs resolve")


if __name__ == "__main__":
    main()
