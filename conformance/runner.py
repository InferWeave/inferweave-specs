#!/usr/bin/env python3
"""InferWeave Protocol v1 conformance runner.

Validates conformance fixtures against the canonical JSON Schemas:
- every fixture under fixtures/valid/ must validate against its schema
- every fixture under fixtures/invalid/ must fail its schema
- every fixture under fixtures/federation/ must validate against its schema
- every pinned contract under contracts/gpu-memory/ must validate as a fleet snapshot
- conformance/node-join-vectors.json (spec 47) must agree with the reference model in
  conformance/node_join.py, and its enrollment known answers must be reproducible from the seed
- conformance/runtime-family-vectors.json (spec 53) is run per family; each family reports PASS/FAIL

The runner is intentionally strict: a valid fixture that stops validating, or an invalid
fixture that starts validating, fails the run.

Usage: python3 conformance/runner.py
"""
from pathlib import Path
import json, sys
from jsonschema import Draft7Validator, RefResolver

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "conformance"))
import node_join  # noqa: E402
SCHEMA_DIR = ROOT / "schemas" / "v1"

# fixture basename -> schema rel path (relative to schemas/v1)
MAP = {
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
    fixture = json.loads(path.read_text())
    errors = list(validator(schema_rel).iter_errors(fixture))
    ok = not errors
    if ok == must_pass:
        return True
    print(f"FAIL  {rel}: expected {'valid' if must_pass else 'invalid'} against {schema_rel}")
    for e in errors[:5]:
        print(f"        {list(e.path)}: {e.message}")
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


def check_runtime_family_vectors():
    """Spec 53: per-family advertisement/admission round-trips and native-endpoint smoke vectors.

    Returns {family: [error, ...]}; an empty list means the family passes.
    """
    import yaml
    doc = json.loads((ROOT / "conformance" / "runtime-family-vectors.json").read_text())
    paths = yaml.safe_load((ROOT / "openapi" / "inferweave-v1.yaml").read_text())["paths"]
    registry = set(doc["registry"])
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
        if json.loads(json.dumps(ad)) != ad:
            errs.append("advertisement does not round-trip")
        if not vec.get("rejections"):
            errs.append("no rejection vectors")
        for rej in vec.get("rejections", []):
            bad = {k: v for k, v in ad.items() if k not in rej.get("omit", [])}
            bad.update(rej.get("override", {}))
            if admit_advertisement(bad, registry) != rej["expect"]["admitted"]:
                errs.append(f"rejection {rej['id']}: admission disagrees with reference")
        smoke = vec.get("nativeSmoke")
        if not smoke:
            errs.append("native smoke vector missing")
        elif smoke["method"].lower() not in paths.get(smoke["path"], {}):
            errs.append(f"native smoke {smoke['method']} {smoke['path']} not in OpenAPI")
    return results


def report_runtime_family_vectors():
    ok = True
    for fam, errs in check_runtime_family_vectors().items():
        if errs:
            ok = False
            print(f"FAIL  runtime-family {fam}")
            for e in errs:
                print(f"        {e}")
        else:
            print(f"PASS  runtime-family {fam}")
    return ok


def main():
    failures = 0
    failures += 0 if check_node_join_vectors() else 1
    failures += 0 if report_runtime_family_vectors() else 1
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
