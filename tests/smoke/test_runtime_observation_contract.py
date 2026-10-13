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
        for guard in ['semantic_errors', 'disposition']:
            with self.subTest(guard=guard):
                replacement = [] if guard == 'semantic_errors' else {'accepted': True, 'producer_ready': ['instance-a']}
                with patch.object(contract, guard, return_value=replacement):
                    self.assertTrue(contract.check_vectors(ROOT), 'removed guard went undetected')

    def test_tombstone_and_generation_are_distinct(self):
        vectors = json.loads((ROOT / 'conformance/runtime-observation-vectors.json').read_text())['vectors']
        tombstone = next(x for x in vectors if x['id'] == 'resurrection-denied')
        self.assertFalse(contract.disposition(tombstone['report'], tombstone['context'])['accepted'])
        report = deepcopy(tombstone['report'])
        report['instances'][0]['observation']['generation'] = 'new-load'
        self.assertEqual(contract.disposition(report, tombstone['context'])['producer_ready'], ['instance-a'])


if __name__ == '__main__':
    unittest.main()
