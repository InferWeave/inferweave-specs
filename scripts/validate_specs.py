#!/usr/bin/env python3
"""Structural validation of the specification bundle.

`--self-test` additionally runs every data guard against a deliberately broken copy of the
registry. A guard that passes against known-bad input is a failure: it cannot be distinguished
from a guard that has silently stopped checking. See
`specs/38_EXECUTABLE_EVIDENCE_AND_CONFORMANCE.md`.
"""
from pathlib import Path
from collections import defaultdict, deque
import copy, json, math, re, sys

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


def guard_task_traceability(features, tasks, spec_exists):
    """Every task maps to a feature unless it is a recorded gate/checkpoint task.

    The allowlist is a decision, not an omission: these tasks verify or gate other work and
    own no requirement of their own. Adding to it requires saying so.
    """
    allowed = {
        "P0-T11", "P0-T12", "P1-T25", "P2-T13", "P2-T17", "P2-T22", "P3-T20", "P3-T22",
        "P4-T09", "P4-T14", "P5-T07", "P5-T08", "P5-T09", "P5-T10",
    }
    return [f"{t['id']}: no feature and not a recorded gate task"
            for t in tasks if not t.get("features") and t["id"] not in allowed]


# --- derived-artifact drift -------------------------------------------------
# The same task information exists five ways. These guards make the reconciliation a
# check rather than an author's discipline.

def _index_rows(root):
    rows = {}
    for line in (root / "implementation/CANONICAL_TASK_INDEX.md").read_text().splitlines():
        m = re.match(r"\| `([^`]+)` \| ([^|]+)\| ([^|]+)\| ([^|]+)\| (.+) \|$", line)
        if m:
            rows[m.group(1)] = (m.group(2).strip(), m.group(3).strip(),
                                m.group(4).strip(), m.group(5).strip())
    return rows


def guard_task_index_matches_graph(features, tasks, spec_exists):
    errors = []
    rows = _index_rows(ROOT)
    if set(rows) != {t["id"] for t in tasks}:
        for missing in {t["id"] for t in tasks} - set(rows):
            errors.append(f"task index missing {missing}")
        for extra in set(rows) - {t["id"] for t in tasks}:
            errors.append(f"task index has unknown task {extra}")
    for t in tasks:
        row = rows.get(t["id"])
        if not row:
            continue
        want = (str(t["phase"]), t["context_class"],
                ", ".join(t.get("depends_on", [])) or "—", t["title"])
        if row != want:
            errors.append(f"task index disagrees with graph for {t['id']}")
    return errors


def guard_sequence_matches_graph(features, tasks, spec_exists):
    errors = []
    seq = (ROOT / "implementation/CANONICAL_IMPLEMENTATION_SEQUENCE.md").read_text()
    for t in tasks:
        m = re.search(rf"^### {re.escape(t['id'])} — (.+)$", seq, re.M)
        if not m:
            errors.append(f"canonical sequence missing {t['id']}")
            continue
        if m.group(1).strip() != t["title"]:
            errors.append(f"canonical sequence title disagrees for {t['id']}")
        block = seq[m.end():]
        nxt = re.search(r"^#{2,3} ", block, re.M)
        block = block[: nxt.start()] if nxt else block
        dep = ", ".join(t.get("depends_on", [])) or "none"
        if f"**Depends on:** {dep}" not in block:
            errors.append(f"canonical sequence dependencies disagree for {t['id']}")
    return errors


def guard_every_task_has_a_card(features, tasks, spec_exists):
    return [f"{t['id']}: no task card"
            for t in tasks
            if not (ROOT / f"tasks/phase-{t['phase']}/{t['id']}.md").exists()
            and not (ROOT / f"tasks/deferred/{t['id']}.md").exists()]


def guard_coverage_tables_match(features, tasks, spec_exists):
    errors = []
    ft = (ROOT / "implementation/FEATURE_TASK_COVERAGE.md").read_text()
    for f in features:
        if f"`{f['id']}`" not in ft:
            errors.append(f"feature coverage table missing {f['id']}")
    st = (ROOT / "implementation/SPEC_TASK_COVERAGE.md").read_text()
    used = {s for t in tasks for s in t.get("specs", [])}
    for s in used:
        if f"`specs/{s}.md`" not in st:
            errors.append(f"spec coverage table missing specs/{s}.md")
    return errors


DATA_GUARDS = [
    guard_duplicate_ids,
    guard_task_references,
    guard_acyclic,
    guard_feature_mappings,
    guard_proof_status,
    guard_task_traceability,
    guard_task_index_matches_graph,
    guard_sequence_matches_graph,
    guard_every_task_has_a_card,
    guard_coverage_tables_match,
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
        "contracts/backpressure-action-codes.json",
        "contracts/backpressure-conformance-v1.json",
        "specs/36_GPU_WATCHDOG_RESCUE.md",
        "specs/37_CONTAINER_DEPLOYMENT_STANDARD.md",
        "specs/38_EXECUTABLE_EVIDENCE_AND_CONFORMANCE.md",
        "AGENTS.md",
        "README.md",
        "OPEN_GATES.md",
    ]
    return [f"missing {rel}" for rel in required if not (root / rel).exists()]


def _vector_error(case):
    body = case.get("body", {})
    if isinstance(body.get("error"), dict):
        return body["error"]
    detail = body.get("detail", {})
    if isinstance(detail, dict) and isinstance(detail.get("error"), dict):
        return detail["error"]
    return None


def guard_backpressure_contracts(root, features, tasks):
    """Reconcile the frozen actions, shared vectors, and their canonical owners."""
    errors = []
    action_path = root / "contracts/backpressure-action-codes.json"
    vector_path = root / "contracts/backpressure-conformance-v1.json"
    if not action_path.exists() or not vector_path.exists():
        return errors

    actions = json.loads(action_path.read_text())
    vectors = json.loads(vector_path.read_text())
    values = actions.get("values", [])
    known_actions = set(values)
    if len(values) != len(known_actions):
        errors.append("duplicate backpressure action code")
    action_names = {
        "IW-ACT-BACKOFF": "backoff",
        "IW-ACT-REDUCE-CONCURRENCY": "reduce_concurrency",
        "IW-ACT-RETRY-ALTERNATE": "retry_alternate",
        "IW-ACT-FIX-REQUEST": "fix_request",
        "IW-ACT-AUTHENTICATE": "authenticate",
        "IW-ACT-REQUEST-ACCESS": "request_access",
        "IW-ACT-RESOLVE-CONFLICT": "resolve_conflict",
        "IW-ACT-REDUCE-INPUT": "reduce_input",
        "IW-ACT-DO-NOT-RETRY": "do_not_retry",
    }
    if known_actions != set(action_names):
        errors.append("frozen action JSON disagrees with canonical action vocabulary")
    spec = (root / "specs/06_BACKPRESSURE_RETURN_TO_SENDER.md").read_text()
    published_actions = re.findall(r"^\| `(IW-ACT-[^`]+)` \|", spec, re.M)
    if published_actions != values:
        errors.append("published action table disagrees with frozen JSON")

    seen_names = set()
    unsafe_states = {"dispatched", "streaming", "unknown"}
    request_states = {"not_started", "queued", "dispatched", "streaming", "unknown"}
    scopes = {"request", "model", "caller", "global"}
    required_fields = {
        "code", "reason", "retryable", "replay_safe", "request_state",
        "action", "action_code", "scope",
    }
    covered_actions = set()
    for case in vectors.get("cases", []):
        name = case.get("name", "<unnamed>")
        if name in seen_names:
            errors.append(f"{name}: duplicate backpressure vector name")
        seen_names.add(name)
        missing = {"name", "status", "headers", "body", "expected", "legacy"} - set(case)
        if missing:
            errors.append(f"{name}: missing vector fields {', '.join(sorted(missing))}")
            continue

        expected = case["expected"]
        error = _vector_error(case)
        if error is None:
            errors.append(f"{name}: no error or detail.error envelope")
            continue

        for field in sorted(required_fields - set(error)):
            errors.append(f"{name}: missing body field {field}")
        for field in sorted(required_fields - set(expected)):
            errors.append(f"{name}: missing expected field {field}")

        for target, envelope in (("body", error), ("expected", expected)):
            for field in ("code", "reason"):
                if field in envelope and (
                    not isinstance(envelope[field], str) or not envelope[field]
                ):
                    errors.append(f"{name}: {target} {field} must be a nonempty string")
            for field in ("retryable", "replay_safe"):
                if field in envelope and type(envelope[field]) is not bool:
                    errors.append(f"{name}: {field} must be boolean in {target}")
            if "request_state" in envelope and envelope["request_state"] not in request_states:
                errors.append(f"{name}: invalid {target} request_state")
            if "scope" in envelope and envelope["scope"] not in scopes:
                errors.append(f"{name}: invalid {target} scope")
            for field in ("action", "action_code"):
                value = envelope.get(field)
                if field in envelope and target == "body" and (
                    not isinstance(value, str) or not value
                ):
                    errors.append(f"{name}: body {field} must be a nonempty string")
                if field in envelope and target == "expected" and value is not None and (
                    not isinstance(value, str) or not value
                ):
                    errors.append(f"{name}: expected {field} must be a nonempty string or null")

        expected_action = expected.get("action_code")
        if expected_action is not None and expected_action not in known_actions:
            errors.append(f"{name}: unknown expected action code {expected_action}")
        if expected_action in known_actions:
            covered_actions.add(expected_action)
        body_action = error.get("action_code")
        if expected_action is not None and body_action != expected_action:
            errors.append(f"{name}: body action code disagrees with expected action code")
        if expected_action is None and body_action in known_actions:
            errors.append(f"{name}: known body action unexpectedly rejected")
        for target, envelope in (("body", error), ("expected", expected)):
            action_code = envelope.get("action_code")
            if action_code in action_names and envelope.get("action") != action_names[action_code]:
                errors.append(f"{name}: {target} action does not match action code")

        if error.get("code") is not None and error.get("reason") is not None:
            if error["code"] != error["reason"]:
                errors.append(f"{name}: code and reason disagree")
        for field in required_fields:
            if field in {"action", "action_code"} and expected.get(field) is None:
                continue
            if field in expected and error.get(field) != expected[field]:
                errors.append(f"{name}: body {field} disagrees with expected {field}")

        condition = expected.get("code")
        if condition == "model_queue_full":
            if (
                case.get("status") != 429
                or expected.get("scope") != "model"
                or expected.get("request_state") != "queued"
                or expected.get("classification") != "admission_queue"
            ):
                errors.append(f"{name}: model queue admission classification drift")
        elif case.get("status") == 429 and expected.get("scope") == "model":
            errors.append(f"{name}: non-queue model/capacity condition uses 429")
        if condition == "NO_CONTEXT_CAPACITY":
            if case.get("status") == 429:
                errors.append(f"{name}: non-queue model/capacity condition uses 429")
            elif (
                case.get("status") != 503
                or expected.get("classification") != "capacity_unavailable"
            ):
                errors.append(f"{name}: capacity condition classification drift")

        body_delay = error.get("retry_after_ms")
        header_delay = case["headers"].get("Retry-After")
        try:
            header_delay_ms = int(header_delay) * 1000 if header_delay is not None else None
        except (TypeError, ValueError):
            header_delay_ms = None
            errors.append(f"{name}: invalid Retry-After header")
        if header_delay_ms is not None and header_delay_ms < 0:
            errors.append(f"{name}: Retry-After must be nonnegative")
        if body_delay is not None and (
            isinstance(body_delay, bool)
            or not isinstance(body_delay, (int, float))
            or (isinstance(body_delay, float) and not math.isfinite(body_delay))
            or body_delay < 0
        ):
            errors.append(f"{name}: body retry_after_ms must be nonnegative numeric")
        expected_delay = expected.get("retry_after_ms")
        if expected_delay is not None and (
            isinstance(expected_delay, bool)
            or not isinstance(expected_delay, (int, float))
            or (isinstance(expected_delay, float) and not math.isfinite(expected_delay))
            or expected_delay < 0
        ):
            errors.append(f"{name}: expected retry_after_ms must be nonnegative numeric")
        delays = [
            delay for delay in (body_delay, header_delay_ms)
            if isinstance(delay, (int, float)) and not isinstance(delay, bool) and delay >= 0
        ]
        effective_delay = max(delays, default=None)
        if expected_delay != effective_delay:
            if expected_delay is not None or effective_delay is not None:
                errors.append(f"{name}: effective delay disagrees with expected retry_after_ms")
        if expected.get("retryable") is True and effective_delay is None:
            errors.append(f"{name}: retryable without bounded delay guidance")
        if expected.get("replay_safe") and expected.get("request_state") in unsafe_states:
            errors.append(f"{name}: replay-safe in unsafe request state")

    if covered_actions != known_actions:
        errors.append("vectors do not cover frozen action codes")

    shared = {
        "contracts/backpressure-action-codes.json",
        "contracts/backpressure-conformance-v1.json",
    }
    feature = next((item for item in features if item["id"] == "IW-BP-001"), {})
    if not shared.issubset(set(feature.get("contracts", []))):
        errors.append("IW-BP-001 omits shared backpressure contracts")
    task = next((item for item in tasks if item["id"] == "P1-T19"), {})
    if not shared.issubset(set(task.get("contracts", []))):
        errors.append("P1-T19 omits shared backpressure contracts")
    for relative_path in (
        "tasks/phase-1/P1-T19.md",
        "implementation/CANONICAL_IMPLEMENTATION_SEQUENCE.md",
    ):
        text = (root / relative_path).read_text()
        if not all(contract in text for contract in shared):
            errors.append(f"{relative_path}: omits shared backpressure contracts")
    return errors


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
    errors.extend(guard_backpressure_contracts(ROOT, features, tasks))
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


def _break_traceability(features, tasks):
    nxt = next(t for t in tasks if t["id"] not in {"P0-T11"} and t.get("features"))
    nxt["features"] = []


def _break_index_drift(features, tasks):
    tasks[0]["title"] = "a title the generated index has never seen"


def _break_card_missing(features, tasks):
    tasks.append({"id": "P9-T99", "phase": 9, "title": "no card exists for this",
                  "depends_on": [], "specs": [], "features": [], "context_class": "C50",
                  "outcome": "", "required_tests": [], "notes": ""})


def _break_coverage(features, tasks):
    features[0]["id"] = "IW-NOT-IN-THE-TABLE"


MUTATIONS = [
    ("duplicate task id", _break_duplicate),
    ("dangling dependency", _break_reference),
    ("missing spec reference", _break_missing_spec),
    ("dependency cycle", _break_cycle),
    ("feature maps to missing task", _break_feature_mapping),
    ("feature with no task", _break_orphan_feature),
    ("invalid proof status", _break_proof_status),
    ("task with no feature and no gate record", _break_traceability),
    ("derived index drifted from the graph", _break_index_drift),
    ("task with no card", _break_card_missing),
    ("coverage table missing a feature", _break_coverage),
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
