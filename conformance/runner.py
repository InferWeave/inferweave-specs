#!/usr/bin/env python3
"""InferWeave Protocol v1 conformance runner.

Validates conformance fixtures against the canonical JSON Schemas:
- every fixture under fixtures/valid/ must validate against its schema
- every fixture under fixtures/invalid/ must fail its schema
- every fixture under fixtures/federation/ must validate against its schema

The runner is intentionally strict: a valid fixture that stops validating, or an invalid
fixture that starts validating, fails the run.

Usage: python3 conformance/runner.py
"""
from pathlib import Path
import json, sys
from jsonschema import Draft7Validator, RefResolver

ROOT = Path(__file__).resolve().parents[1]
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
    "event": "events/event.json",
    "metric": "events/metric.json",
    "job": "jobs/job.json",
    "progress": "jobs/progress.json",
    "artifact": "artifacts/artifact.json",
    "cache-state": "artifacts/cache-state.json",
    "federation-path": "topology/node.json",
}

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
    # exact basename match first; otherwise map invalid fixtures by prefix before the first "-"
    if stem in MAP:
        return MAP[stem]
    prefix = stem.split("-")[0]
    return MAP.get(prefix)


def validate_fixture(path, must_pass):
    rel = path.relative_to(ROOT).as_posix()
    stem = path.stem
    schema_rel = schema_for(stem)
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


def main():
    failures = 0
    for d in ("valid", "federation", "invalid"):
        fixtures = sorted((ROOT / "fixtures" / d).glob("*.json"))
        if not fixtures:
            print(f"FAIL  fixtures/{d}/: directory is empty")
            failures += 1
            continue
        for p in fixtures:
            failures += 0 if validate_fixture(p, d != "invalid") else 1
    failures += 0 if check_openapi_refs() else 1
    if failures:
        print(f"CONFORMANCE FAILED: {failures} check(s) did not behave as expected")
        sys.exit(1)
    print("OK: conformance fixtures validate and OpenAPI refs resolve")


if __name__ == "__main__":
    main()
