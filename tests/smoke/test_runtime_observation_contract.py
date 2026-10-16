"""Anti-vacuous checks for spec56 offline reference guards."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'conformance'))
import runtime_observations as contract


class RuntimeObservationContract(unittest.TestCase):
    def test_vectors_and_guard_mutations(self):
        self.assertEqual(contract.check_vectors(ROOT), [])
        with patch.object(contract.Draft7Validator, 'iter_errors', return_value=[]):
            self.assertTrue(contract.check_vectors(ROOT), 'removed schema guard went undetected')
        with patch.object(contract, 'decode_report', side_effect=json.loads):
            self.assertTrue(contract.check_vectors(ROOT), 'removed encoded-byte cap went undetected')
        for guard in ['semantic_errors', 'item_fence_errors', 'disposition']:
            with self.subTest(guard=guard):
                replacement = [] if guard != 'disposition' else {'accepted': True, 'producer_ready': ['instance-a']}
                with patch.object(contract, guard, return_value=replacement):
                    self.assertTrue(contract.check_vectors(ROOT), 'removed guard went undetected')

    def test_wire_size_bounds_use_actual_bytes(self):
        raw = (ROOT / 'fixtures/valid/runtime-observation-report.json').read_bytes()
        at_limit = raw + b' ' * (contract.MAX_REPORT_BYTES - len(raw))
        self.assertEqual(contract.decode_report(at_limit), json.loads(raw))
        with self.assertRaisesRegex(ValueError, '256 KiB'):
            contract.decode_report(at_limit + b' ')
        oversized = (ROOT / 'fixtures/invalid/runtime-observation-report-oversized.json').read_bytes()
        self.assertEqual(len(oversized), 334441)
        import runner
        self.assertEqual(list(runner.validator('requests/runtime-observation-report.json').iter_errors(json.loads(oversized))), [])
        with self.assertRaisesRegex(ValueError, '256 KiB'):
            contract.decode_report(oversized)

    def test_stale_instance_ready_does_not_override_draining(self):
        vectors = json.loads((ROOT / 'conformance/runtime-observation-vectors.json').read_text())['vectors']
        for name in ['old-ready-item-after-draining', 'same-item-sequence-changed-content', 'item-fence-survives-omission']:
            with self.subTest(vector=name):
                vector = next(v for v in vectors if v['id'] == name)
                self.assertFalse(contract.disposition(vector['report'], vector['context'])['accepted'])

    def test_tombstone_and_generation_are_distinct(self):
        vectors = json.loads((ROOT / 'conformance/runtime-observation-vectors.json').read_text())['vectors']
        tombstone = next(x for x in vectors if x['id'] == 'resurrection-denied')
        self.assertFalse(contract.disposition(tombstone['report'], tombstone['context'])['accepted'])
        report = deepcopy(tombstone['report'])
        report['instances'][0]['observation']['generation'] = 'new-load'
        self.assertEqual(contract.disposition(report, tombstone['context'])['producer_ready'], ['instance-a'])


class ResyncDiagnosticAmendment(unittest.TestCase):
    """The heartbeat-answer member the Rust producer and ingester use must stay specified."""

    def test_spec_defines_the_resync_diagnostic_and_its_limits(self):
        text = (ROOT / 'specs/56_RUNTIME_INSTANCE_OBSERVATIONS.md').read_text()
        for needle in [
            '`runtimeObservations.resync`', 'diagnostic only', 'never a refusal',
            'RetiredEpoch', 'N consecutive', '5 minutes', '1 hour',
            'MUST start a\nnew epoch', 'Nothing is forgotten within an epoch',
        ]:
            if needle == 'RetiredEpoch':
                needle = 'retired source epoch'
            self.assertIn(needle, text)


if __name__ == '__main__':
    unittest.main()
