#!/usr/bin/env python3
"""Negative contract tests for the mission-event schema (specs/60, R-EVENT, T27).

Three independent proofs per invalid fixture in fixtures/invalid/mission-event-*.json:

1. the fixture is its valid base with exactly ONE defect applied (so a rejection cannot come from a typo);
2. the schema rejects it for the intended reason only: the distinct (keyword, path, message) findings equal
   the expected set. mission-event.json also inherits event.json through allOf, so a defect on a shared
   field is legitimately reported once per schema; the set removes that duplication, not the check;
3. removing the constraint (from every schema that states it) in an isolated copy of the repository makes
   conformance/runner.py fail on that fixture, so the fixture is `proven`: it fails if the control is removed.
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

MISSION = "events/mission-event.json"
ENVELOPE = "events/event.json"

FULL = "fixtures/valid/mission-event-progress.json"
HEARTBEAT = "fixtures/valid/mission-event-heartbeat-only.json"


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


def put_nested(key, inner, value):
    return lambda doc: doc[key].__setitem__(inner, value)


def remove_from(schema_rel, path, entry):
    """Schema break: delete `entry` from the list or dict at `path` inside `schema_rel`."""
    def apply(root):
        node = json.loads((root / "schemas" / "v1" / schema_rel).read_text())
        target = node
        for step in path:
            target = target[step]
        target.remove(entry) if isinstance(target, list) else target.pop(entry)
        (root / "schemas" / "v1" / schema_rel).write_text(json.dumps(node))
    return apply


def required_in_both(field):
    return [remove_from(MISSION, ["required"], field), remove_from(ENVELOPE, ["required"], field)]


SEQUENCE = ["properties", "sequence"]


def forbidden_field_breaks(field):
    """causation_id and payload are forbidden twice over: by `"<field>": false` and, independently, by the
    closed object (`additionalProperties: false`) because the field is not listed. event.json allows both
    fields, so the control is only really gone when BOTH are removed; removing either alone must not pass."""
    return [remove_from(MISSION, ["properties"], field), remove_from(MISSION, [], "additionalProperties")]

# name -> (valid base, change, {(keyword, path, message fragment)}, [schema breaks that remove the constraint])
CASES = {
    "mission-event-missing-mission-id": (
        FULL, drop("mission_id"),
        {("required", (), "'mission_id' is a required property")},
        [remove_from(MISSION, ["required"], "mission_id")]),
    "mission-event-missing-state": (
        FULL, drop("state"),
        {("required", (), "'state' is a required property")},
        [remove_from(MISSION, ["required"], "state")]),
    "mission-event-missing-event-id": (
        FULL, drop("event_id"),
        {("required", (), "'event_id' is a required property")},
        required_in_both("event_id")),
    "mission-event-negative-sequence": (
        FULL, put("sequence", -1),
        {("minimum", ("sequence",), "-1 is less than the minimum of 1")},
        [remove_from(MISSION, SEQUENCE, "minimum"), remove_from(ENVELOPE, SEQUENCE, "minimum")]),
    "mission-event-zero-sequence": (
        FULL, put("sequence", 0),
        {("minimum", ("sequence",), "0 is less than the minimum of 1")},
        [remove_from(MISSION, SEQUENCE, "minimum"), remove_from(ENVELOPE, SEQUENCE, "minimum")]),
    "mission-event-string-sequence": (
        FULL, put("sequence", "124"),
        {("type", ("sequence",), "'124' is not of type 'integer'")},
        [remove_from(MISSION, SEQUENCE, "type"), remove_from(ENVELOPE, SEQUENCE, "type")]),
    "mission-event-fractional-sequence": (
        FULL, put("sequence", 1.5),
        {("type", ("sequence",), "1.5 is not of type 'integer'")},
        [remove_from(MISSION, SEQUENCE, "type")]),
    "mission-event-unknown-progress-kind": (
        FULL, put("progress_kind", "deploy"),
        {("enum", ("progress_kind",), "'deploy' is not one of")},
        [remove_from(MISSION, ["properties", "progress_kind"], "enum")]),
    "mission-event-unknown-field": (
        FULL, put("priority", 1),
        {("additionalProperties", (), "'priority' was unexpected")},
        [remove_from(MISSION, [], "additionalProperties")]),
    "mission-event-causation-id": (
        FULL, put("causation_id", "evt-000123"),
        {(None, ("causation_id",), FALSE_SCHEMA)},
        forbidden_field_breaks("causation_id")),
    "mission-event-payload": (
        FULL, put("payload", {"prompt": "redacted"}),
        {(None, ("payload",), FALSE_SCHEMA)},
        forbidden_field_breaks("payload")),
    "mission-event-short-commit-sha": (
        FULL, put("commit_sha", "b97c777"),
        {("pattern", ("commit_sha",), "does not match")},
        [remove_from(MISSION, ["properties", "commit_sha"], "pattern")]),
    "mission-event-summary-too-long": (
        FULL, put("human_summary", "x" * 281),
        {("maxLength", ("human_summary",), "is too long")},
        [remove_from(MISSION, ["properties", "human_summary"], "maxLength")]),
    "mission-event-negative-resource-usage": (
        FULL, put_nested("resource_usage", "cpu_seconds", -0.5),
        {("minimum", ("resource_usage", "cpu_seconds"), "-0.5 is less than the minimum of 0")},
        [remove_from(MISSION, ["properties", "resource_usage", "additionalProperties"], "minimum")]),
}


def findings(value):
    schema = json.loads((SCHEMA_DIR / MISSION).read_text())
    validator = Draft7Validator(schema, resolver=RefResolver(base_uri=schema["$id"], referrer=schema, store=STORE))
    return {(e.validator, tuple(e.path), e.message) for e in validator.iter_errors(value)}


def run_runner(root):
    return subprocess.run([sys.executable, str(root / "conformance" / "runner.py")],
                          capture_output=True, text=True, cwd=root)


def run_runner_with_broken_schema(breaks):
    """Run conformance/runner.py in an isolated copy of the repo whose schemas lost one constraint."""
    with tempfile.TemporaryDirectory() as directory:
        copy_root = Path(directory) / "repo"
        shutil.copytree(ROOT, copy_root, ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"))
        for apply in breaks:
            apply(copy_root)
        return run_runner(copy_root)


class MissionEventContract(unittest.TestCase):
    def test_at_least_four_mission_event_fixtures_exist_and_all_are_covered(self):
        on_disk = {p.stem for p in (ROOT / "fixtures/invalid").glob("mission-event-*.json")}
        self.assertEqual(set(CASES), on_disk)
        self.assertGreaterEqual(len(on_disk), 4)

    def test_valid_bases_are_valid(self):
        for base in (FULL, HEARTBEAT):
            self.assertEqual(set(), findings(load(base)), base)

    def test_each_invalid_fixture_is_its_base_plus_one_defect(self):
        for name, (base, change, _expected, _breaks) in CASES.items():
            with self.subTest(name):
                self.assertEqual(mutated(base, change), load(f"fixtures/invalid/{name}.json"))

    def test_each_invalid_fixture_is_rejected_for_the_intended_reason(self):
        for name, (_base, _change, expected, _breaks) in CASES.items():
            with self.subTest(name):
                found = findings(load(f"fixtures/invalid/{name}.json"))
                self.assertEqual({(k, p) for k, p, _ in expected}, {(k, p) for k, p, _ in found})
                for keyword, path, fragment in expected:
                    self.assertTrue(any(k == keyword and p == path and fragment in m for k, p, m in found),
                                    f"{(keyword, path, fragment)} not in {found}")

    def test_forbidden_fields_stay_rejected_when_one_of_the_two_controls_is_removed(self):
        for name in ("mission-event-causation-id", "mission-event-payload"):
            with self.subTest(name):
                field = name.removeprefix("mission-event-").replace("-", "_")
                for apply in (remove_from(MISSION, ["properties"], field), remove_from(MISSION, [], "additionalProperties")):
                    result = run_runner_with_broken_schema([apply])
                    self.assertNotIn(f"FAIL  fixtures/invalid/{name}.json", result.stdout)

    def test_runner_accepts_the_repository_as_committed(self):
        result = run_runner(ROOT)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_runner_fails_when_the_intended_schema_constraint_is_removed(self):
        for name, (_base, _change, _expected, breaks) in CASES.items():
            with self.subTest(name):
                result = run_runner_with_broken_schema(breaks)
                self.assertNotEqual(0, result.returncode, "runner still passes without the constraint")
                self.assertIn(f"FAIL  fixtures/invalid/{name}.json", result.stdout)


if __name__ == "__main__":
    unittest.main()
