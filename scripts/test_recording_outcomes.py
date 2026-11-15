"""Frozen recording vocabulary: document parity and deliberately bad data."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "conformance"))
import recording_outcomes

class RecordingOutcomesTests(unittest.TestCase):
    def test_repository_contract_matches_published_document(self):
        self.assertEqual(recording_outcomes.contract_errors(ROOT), [])

    def broken(self, mutate):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative in ["contracts/recording-outcomes-v1.json", "docs/contracts/recording-outcomes-v1.md"]:
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((ROOT / relative).read_bytes())
            mutate(root)
            return recording_outcomes.contract_errors(root)

    def test_undeclared_unknown_reason_is_rejected(self):
        def mutate(root):
            path = root / "contracts/recording-outcomes-v1.json"
            data = json.loads(path.read_text())
            data["unknown_outcome_reasons"].append("invented_unknown_reason")
            path.write_text(json.dumps(data))
        self.assertTrue(any("not published" in e for e in self.broken(mutate)))

    def test_duplicate_reason_is_rejected(self):
        def mutate(root):
            path = root / "contracts/recording-outcomes-v1.json"
            data = json.loads(path.read_text())
            data["known_loss_reasons"].append(data["known_loss_reasons"][0])
            path.write_text(json.dumps(data))
        self.assertTrue(any("duplicate" in e for e in self.broken(mutate)))

    def test_document_cannot_invent_a_reason_outside_frozen_data(self):
        def mutate(root):
            path = root / "docs/contracts/recording-outcomes-v1.md"
            path.write_text(path.read_text().replace("| `worker_termination` |", "| `invented_unknown_reason` |"))
        self.assertTrue(any("disagrees" in e for e in self.broken(mutate)))

    def test_zero_and_inconsistent_policy_vectors_are_required(self):
        def mutate(root):
            path = root / "contracts/recording-outcomes-v1.json"
            data = json.loads(path.read_text())
            data["invalid_policy_vectors"] = []
            path.write_text(json.dumps(data))
        self.assertTrue(any("policy vectors" in e for e in self.broken(mutate)))

    def test_wrong_entropy_type_is_a_closed_validation_error(self):
        def mutate(root):
            path = root / "contracts/recording-outcomes-v1.json"
            data = json.loads(path.read_text())
            data["entropy_policy"]["queued_objects"] = "8191"
            path.write_text(json.dumps(data))
        self.assertTrue(any("entropy" in e for e in self.broken(mutate)))

    def test_missing_metric_family_binding_is_rejected(self):
        def mutate(root):
            path = root / "contracts/recording-outcomes-v1.json"
            data = json.loads(path.read_text())
            data["metrics"] = {}
            path.write_text(json.dumps(data))
        self.assertTrue(any("metric" in e for e in self.broken(mutate)))

    def test_unknown_top_level_fields_are_rejected(self):
        def mutate(root):
            path = root / "contracts/recording-outcomes-v1.json"
            data = json.loads(path.read_text())
            data["undeclared_field"] = True
            path.write_text(json.dumps(data))
        self.assertTrue(any("closed object" in e for e in self.broken(mutate)))

if __name__ == "__main__":
    unittest.main()
