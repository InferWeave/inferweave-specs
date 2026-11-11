#!/usr/bin/env python3
"""Negative contract tests for the capability-request and routing-decision schemas (specs/60, T27).

Three independent proofs per invalid fixture in fixtures/invalid/:

1. the fixture is its valid base with exactly ONE defect applied (so a rejection cannot come from a typo);
2. the schema rejects it with exactly one error, raised by the intended keyword at the intended path;
3. removing that one constraint from an isolated copy of the schema makes conformance/runner.py fail
   on that fixture, so the fixture is `proven`: it fails if the control is removed.
"""
import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft7Validator, RefResolver

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = ROOT / "schemas" / "v1"
STORE = {s["$id"]: s for p in SCHEMA_DIR.rglob("*.json") for s in [json.loads(p.read_text())]}
FALSE_SCHEMA = "False schema does not allow"

DECISION = "routing/routing-decision.json"
REQUEST = "routing/capability-request.json"


def load(path):
    return json.loads((ROOT / path).read_text())


def mutated(base, change):
    value = copy.deepcopy(load(base))
    change(value)
    return value


def drop(*names):
    return lambda doc: [doc.pop(n) for n in names]


def put(key, value):
    return lambda doc: doc.__setitem__(key, value)


def remove_from(path, entry):
    """Schema break: delete `entry` from the list at `path`, or from the dict at `path`."""
    def apply(schema):
        node = schema
        for step in path:
            node = node[step]
        node.remove(entry) if isinstance(node, list) else node.pop(entry)
    return apply


ROUTED = "fixtures/valid/routing-decision-routed.json"
BLOCKED = "fixtures/valid/routing-decision-blocked.json"
REQ = "fixtures/valid/capability-request-basic.json"

# name -> (valid base, change, schema, [(keyword, path, message fragment)], break the constraint)
CASES = {
    "routing-decision-routed-missing-wait": (
        ROUTED, drop("estimated_wait_ms"), DECISION,
        [("required", [], "'estimated_wait_ms' is a required property")],
        remove_from(["then", "required"], "estimated_wait_ms")),
    "routing-decision-routed-empty-reasons": (
        ROUTED, put("route_reasons", []), DECISION,
        [("minItems", ["route_reasons"], "should be non-empty")],
        remove_from(["properties", "route_reasons"], "minItems")),
    "routing-decision-routed-wait-over-bound": (
        ROUTED, put("estimated_wait_ms", 300001), DECISION,
        [("maximum", ["estimated_wait_ms"], "is greater than the maximum of 300000")],
        remove_from(["properties", "estimated_wait_ms"], "maximum")),
    "routing-decision-routed-with-retry-after": (
        ROUTED, put("retry_after_ms", 1000), DECISION,
        [(None, [], FALSE_SCHEMA)],
        remove_from(["then", "properties"], "retry_after_ms")),
    "routing-decision-blocked-missing-retry-after": (
        BLOCKED, drop("retry_after_ms"), DECISION,
        [("required", [], "'retry_after_ms' is a required property")],
        remove_from(["else", "required"], "retry_after_ms")),
    "routing-decision-blocked-wait-over-bound": (
        BLOCKED, put("retry_after_ms", 300001), DECISION,
        [("maximum", ["retry_after_ms"], "is greater than the maximum of 300000")],
        remove_from(["properties", "retry_after_ms"], "maximum")),
    "routing-decision-blocked-with-model": (
        BLOCKED, put("model", "glm-5.3-flash"), DECISION,
        [(None, [], FALSE_SCHEMA)],
        remove_from(["else", "properties"], "model")),
    "routing-decision-unknown-field": (
        ROUTED, put("priority", 1), DECISION,
        [("additionalProperties", [], "'priority' was unexpected")],
        remove_from([], "additionalProperties")),
    "capability-request-unknown-field": (
        REQ, put("fallback_model", "any"), REQUEST,
        [("additionalProperties", [], "'fallback_model' was unexpected")],
        remove_from([], "additionalProperties")),
    "capability-request-missing-deadline": (
        REQ, drop("deadline"), REQUEST,
        [("required", [], "'deadline' is a required property")],
        remove_from(["required"], "deadline")),
    "capability-request-missing-quality-floor": (
        REQ, drop("quality_floor"), REQUEST,
        [("required", [], "'quality_floor' is a required property")],
        remove_from(["required"], "quality_floor")),
    "capability-request-zero-context": (
        REQ, put("min_context_tokens", 0), REQUEST,
        [("minimum", ["min_context_tokens"], "is less than the minimum of 1")],
        remove_from(["properties", "min_context_tokens"], "minimum")),
}


def errors_for(schema_rel, value):
    schema = STORE[json.loads((SCHEMA_DIR / schema_rel).read_text())["$id"]]
    validator = Draft7Validator(schema, resolver=RefResolver(base_uri=schema["$id"], referrer=schema, store=STORE))
    return list(validator.iter_errors(value))


def run_runner_with_broken_schema(schema_rel, break_constraint):
    """Run conformance/runner.py in an isolated copy of the repo whose schema lost one constraint."""
    with tempfile.TemporaryDirectory() as directory:
        copy_root = Path(directory) / "repo"
        shutil.copytree(ROOT, copy_root, ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"))
        target = copy_root / "schemas" / "v1" / schema_rel
        schema = json.loads(target.read_text())
        break_constraint(schema)
        target.write_text(json.dumps(schema))
        return run_runner(copy_root)


def run_runner(root):
    return subprocess.run([sys.executable, str(root / "conformance" / "runner.py")],
                          capture_output=True, text=True, cwd=root)


class CapabilityRoutingContract(unittest.TestCase):
    def test_at_least_five_routing_fixtures_exist_and_all_are_covered(self):
        on_disk = {p.stem for p in (ROOT / "fixtures/invalid").glob("*.json")
                   if p.stem.startswith(("routing-decision-", "capability-request-"))}
        self.assertEqual(set(CASES), on_disk)
        self.assertGreaterEqual(len(on_disk), 5)

    def test_valid_bases_are_valid(self):
        for base, schema_rel in ((ROUTED, DECISION), (BLOCKED, DECISION), (REQ, REQUEST)):
            self.assertEqual([], errors_for(schema_rel, load(base)), base)

    def test_each_invalid_fixture_is_its_base_plus_one_defect(self):
        for name, (base, change, _schema, _expected, _break) in CASES.items():
            with self.subTest(name):
                self.assertEqual(mutated(base, change), load(f"fixtures/invalid/{name}.json"))

    def test_each_invalid_fixture_is_rejected_for_the_intended_reason(self):
        for name, (_base, _change, schema_rel, expected, _break) in CASES.items():
            with self.subTest(name):
                found = errors_for(schema_rel, load(f"fixtures/invalid/{name}.json"))
                self.assertEqual(len(expected), len(found), [e.message for e in found])
                for (keyword, path, fragment), error in zip(expected, found):
                    self.assertEqual(keyword, error.validator)
                    self.assertEqual(path, list(error.path))
                    self.assertIn(fragment, error.message)

    def test_runner_accepts_the_repository_as_committed(self):
        result = run_runner(ROOT)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_runner_fails_when_the_intended_schema_constraint_is_removed(self):
        for name, (_base, _change, schema_rel, _expected, break_constraint) in CASES.items():
            with self.subTest(name):
                result = run_runner_with_broken_schema(schema_rel, break_constraint)
                self.assertNotEqual(0, result.returncode, "runner still passes without the constraint")
                self.assertIn(f"FAIL  fixtures/invalid/{name}.json", result.stdout)


if __name__ == "__main__":
    unittest.main()
