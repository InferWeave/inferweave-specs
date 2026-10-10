"""B-T06B: workstream-B feature ids are registered and traceable to canonical tasks (specs/53)."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FEATURE_IDS = [f"IW-RT-00{i}" for i in range(1, 7)]
TASK_IDS = [f"B-T0{i}" for i in range(1, 7)]


def _load(rel):
    return json.loads((ROOT / rel).read_text())


def unmapped_features(features, tasks):
    """Return registered IW-RT ids with no mapping to an existing canonical task."""
    task_ids = {t["id"] for t in tasks}
    bad = []
    for fid in FEATURE_IDS:
        entry = next((f for f in features if f["id"] == fid), None)
        mapped = entry.get("canonical_tasks", []) if entry else []
        if not mapped or any(t not in task_ids for t in mapped):
            bad.append(fid)
    return bad


class RegistryTraceableTest(unittest.TestCase):
    def setUp(self):
        self.features = _load("contracts/feature-registry.json")["features"]
        self.tasks = _load("contracts/canonical-task-graph.json")["tasks"]

    def test_every_feature_mapped_to_existing_task(self):
        bad = unmapped_features(self.features, self.tasks)
        assert bad == [], f"unmapped or dangling workstream-B features: {bad}"

    def test_task_graph_has_dependency_edges(self):
        by_id = {t["id"]: t for t in self.tasks}
        for tid in TASK_IDS:
            assert tid in by_id, f"{tid} missing from task graph"
        assert by_id["B-T01"]["depends_on"] == []
        for tid in TASK_IDS[1:]:
            assert by_id[tid]["depends_on"], f"{tid} has no dependency edge"
            assert all(d in by_id for d in by_id[tid]["depends_on"])

    def test_sequence_lists_workstream_b_tasks(self):
        seq = (ROOT / "implementation/CANONICAL_IMPLEMENTATION_SEQUENCE.md").read_text()
        by_id = {t["id"]: t for t in self.tasks}
        for tid in TASK_IDS:
            assert f"### {tid} — {by_id[tid]['title']}" in seq, f"{tid} missing from sequence"
            dep = ", ".join(by_id[tid]["depends_on"]) or "none"
            assert f"**Depends on:** {dep}" in seq

    def test_unmapped_feature_is_detected(self):
        features = [dict(f) for f in self.features]
        for f in features:
            if f["id"] == "IW-RT-003":
                f["canonical_tasks"] = []
        assert unmapped_features(features, self.tasks) == ["IW-RT-003"]
        dangling = [dict(f) for f in self.features]
        for f in dangling:
            if f["id"] == "IW-RT-005":
                f["canonical_tasks"] = ["B-T99"]
        assert unmapped_features(dangling, self.tasks) == ["IW-RT-005"]


if __name__ == "__main__":
    unittest.main()
