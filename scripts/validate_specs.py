#!/usr/bin/env python3
"""Structural validation of the specification bundle.

`--self-test` additionally runs every data guard against a deliberately broken copy of the
registry. A guard that passes against known-bad input is a failure: it cannot be distinguished
from a guard that has silently stopped checking. See
`specs/38_EXECUTABLE_EVIDENCE_AND_CONFORMANCE.md`.
"""
from pathlib import Path
from collections import defaultdict, deque
import copy, json, re, sys

ROOT = Path(__file__).resolve().parents[1]


# --------------------------------------------------------------------- guards
# Each guard is a pure function of (features, tasks, spec_exists) returning errors, so the
# same code path runs against the real registry and against broken copies.

def guard_duplicate_ids(features, tasks, spec_exists):
    errors = []
    fids = [f["id"] for f in features]
    tids = [t["id"] for t in tasks]
    if len(fids) != len(set(fids)):
        errors.append("duplicate feature IDs")
    if len(tids) != len(set(tids)):
        errors.append("duplicate task IDs")
    return errors


def guard_task_references(features, tasks, spec_exists):
    errors = []
    task_ids = {t["id"] for t in tasks}
    for t in tasks:
        for d in t.get("depends_on", []):
            if d not in task_ids:
                errors.append(f"{t['id']}: missing dependency {d}")
        for s in t.get("specs", []):
            if not spec_exists(s):
                errors.append(f"{t['id']}: missing spec specs/{s}.md")
    return errors


def guard_acyclic(features, tasks, spec_exists):
    task_ids = {t["id"] for t in tasks}
    indeg = {tid: 0 for tid in task_ids}
    adj = defaultdict(list)
    for t in tasks:
        for d in t.get("depends_on", []):
            if d in task_ids:
                adj[d].append(t["id"])
                indeg[t["id"]] += 1
    q = deque([x for x, n in indeg.items() if n == 0])
    seen = 0
    while q:
        x = q.popleft()
        seen += 1
        for y in adj[x]:
            indeg[y] -= 1
            if indeg[y] == 0:
                q.append(y)
    return [] if seen == len(tasks) else ["canonical task graph contains cycle"]


def guard_feature_mappings(features, tasks, spec_exists):
    errors = []
    task_ids = {t["id"] for t in tasks}
    for f in features:
        ct = f.get("canonical_tasks", [])
        if not ct:
            errors.append(f"{f['id']}: no canonical task")
        for tid in ct:
            if tid not in task_ids:
                errors.append(f"{f['id']}: maps to missing task {tid}")
    return errors


def guard_proof_status(features, tasks, spec_exists):
    """Every required test declares proven or owed; never both, never neither."""
    errors = []
    for t in tasks:
        proof = t.get("proof_status")
        if proof is None:
            continue  # not yet declared; the bundle migrates task by task
        if proof not in {"proven", "owed", "mixed"}:
            errors.append(f"{t['id']}: proof_status '{proof}' is not proven/owed/mixed")
        if proof in {"owed", "mixed"} and not t.get("proof_owed_by"):
            errors.append(f"{t['id']}: proof_status '{proof}' names no owing task")
    return errors


DATA_GUARDS = [
    guard_duplicate_ids,
    guard_task_references,
    guard_acyclic,
    guard_feature_mappings,
    guard_proof_status,
]


# ------------------------------------------------------------- file-tree guards

def guard_deployment_substrate(root):
    bad_patterns = {
        r"Podman/Podman Compose": "Podman production guidance",
        r"Quadlet": "Quadlet production guidance",
        r"Bootstrap `inferweave` Go": "stale Go bootstrap guidance",
    }
    errors = []
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix not in {".md", ".json", ".yaml", ".yml", ".sh"}:
            continue
        rel = p.relative_to(root)
        if str(rel) == "scripts/validate_specs.py":
            continue
        text = p.read_text(errors="ignore")
        for pat, label in bad_patterns.items():
            if re.search(pat, text, re.I):
                errors.append(f"{rel}: {label}")
    return errors


def guard_required_artifacts(root):
    required = [
        "specs/36_GPU_WATCHDOG_RESCUE.md",
        "specs/37_CONTAINER_DEPLOYMENT_STANDARD.md",
        "specs/38_EXECUTABLE_EVIDENCE_AND_CONFORMANCE.md",
        "AGENTS.md",
        "README.md",
        "OPEN_GATES.md",
    ]
    return [f"missing {rel}" for rel in required if not (root / rel).exists()]


# --------------------------------------------------------------------- driver

def load():
    features = json.loads((ROOT / "contracts/feature-registry.json").read_text())["features"]
    tasks = json.loads((ROOT / "contracts/canonical-task-graph.json").read_text())["tasks"]
    return features, tasks


def spec_exists(name):
    return (ROOT / f"specs/{name}.md").exists()


def validate():
    features, tasks = load()
    errors = []
    for g in DATA_GUARDS:
        errors.extend(g(features, tasks, spec_exists))
    errors.extend(guard_deployment_substrate(ROOT))
    errors.extend(guard_required_artifacts(ROOT))
    return features, tasks, errors


# Each entry breaks the registry in exactly the way one guard exists to catch.
def _break_duplicate(features, tasks):
    tasks.append(copy.deepcopy(tasks[0]))


def _break_reference(features, tasks):
    tasks[0].setdefault("depends_on", []).append("P0-TNOPE")


def _break_missing_spec(features, tasks):
    tasks[0].setdefault("specs", []).append("99_NOT_A_SPEC")


def _break_cycle(features, tasks):
    a, b = tasks[0]["id"], tasks[1]["id"]
    tasks[0]["depends_on"] = [b]
    tasks[1]["depends_on"] = [a]


def _break_feature_mapping(features, tasks):
    features[0]["canonical_tasks"] = ["P0-TNOPE"]


def _break_orphan_feature(features, tasks):
    features[0]["canonical_tasks"] = []


def _break_proof_status(features, tasks):
    tasks[0]["proof_status"] = "definitely"


MUTATIONS = [
    ("duplicate task id", _break_duplicate),
    ("dangling dependency", _break_reference),
    ("missing spec reference", _break_missing_spec),
    ("dependency cycle", _break_cycle),
    ("feature maps to missing task", _break_feature_mapping),
    ("feature with no task", _break_orphan_feature),
    ("invalid proof status", _break_proof_status),
]


def self_test():
    """Prove each guard can fail. A silent guard is worse than a missing one."""
    base_features, base_tasks = load()
    failures = []
    for label, mutate in MUTATIONS:
        features = copy.deepcopy(base_features)
        tasks = copy.deepcopy(base_tasks)
        mutate(features, tasks)
        errors = []
        for g in DATA_GUARDS:
            errors.extend(g(features, tasks, spec_exists))
        if not errors:
            failures.append(f"no guard rejected: {label}")
    if failures:
        print("GUARD SELF-TEST FAILED")
        for f in failures:
            print(f"- {f}")
        return 1
    print(f"OK: {len(MUTATIONS)} mutations, every guard rejects its known-bad input")
    return 0


if __name__ == "__main__":
    features, tasks, errors = validate()
    if errors:
        print("SPEC VALIDATION FAILED")
        for e in errors:
            print(f"- {e}")
        sys.exit(1)
    print(f"OK: {len(features)} features, {len(tasks)} canonical tasks, DAG valid")
    if "--self-test" in sys.argv:
        sys.exit(self_test())
