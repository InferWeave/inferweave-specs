"""Anti-vacuous checks for capacity provenance, policy bounds and vocabulary."""
import copy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'conformance'))
import observability_capacity as capacity


class CapacityContractTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = json.loads((ROOT / 'fixtures/valid/observability-capacity-fresh.json').read_text())

    def test_contract_and_fixtures(self):
        self.assertEqual([], capacity.contract_errors(ROOT))

    def test_semantic_mutations_are_rejected(self):
        edits = [
            lambda x: x.update(received_age_ms=x['validity_ms']),
            lambda x: x.update(validity_ms=0, received_age_ms=0),
            lambda x: x['serving_offers'][0].update(valid_for_ms=0),
            lambda x: x['cpu']['owner_budget_millicores'].update(value=9000),
            lambda x: x['cpu']['available_millicores'].update(value=4999),
            lambda x: x['cpu']['quota_millicores'].pop('value'),
            lambda x: x['serving_offers'][0].update(max_output_tokens=8193),
            lambda x: x['serving_offers'][0].update(valid_for_ms=30000),
            lambda x: x['serving_offers'].append(copy.deepcopy(x['serving_offers'][0])),
            lambda x: x['serving_offers'][0].update(basis='measured'),
            lambda x: x['serving_offers'][0].update(exclusion_reasons=['unqualified']),
        ]
        for edit in edits:
            changed = copy.deepcopy(self.snapshot)
            edit(changed)
            with self.subTest(changed=changed):
                self.assertTrue(capacity.semantic_errors(changed))

    def test_duplicate_keys_rejected_at_all_depths(self):
        for wire in ('{"status":"stale","status":"fresh"}',
                     '{"nodes":[{"status":"stale","status":"fresh"}]}'):
            with self.subTest(wire=wire), self.assertRaises(ValueError):
                capacity.decode(wire)

    def test_pool_allows_alternatives_but_rejects_mixed_authority(self):
        alternative = json.loads((ROOT / 'fixtures/valid/observability-capacity-alternative-profiles.json').read_text())
        self.assertEqual([], capacity.semantic_errors(alternative))
        for name in ('mixed-owner', 'mixed-epoch'):
            bad = json.loads((ROOT / ('fixtures/invalid/observability-capacity-fleet-pool-' + name + '.json')).read_text())
            self.assertTrue(capacity.fleet_errors(bad))

    def test_vocabulary_drift_is_rejected(self):
        original = Path.read_text
        def read(path, *args, **kwargs):
            result = original(path, *args, **kwargs)
            if path.name == 'observability-capacity.json' and path.parent.name == 'contracts':
                contract = json.loads(result)
                contract['basis'].append('invented')
                return json.dumps(contract)
            return result
        with patch.object(Path, 'read_text', read):
            self.assertTrue(capacity.contract_errors(ROOT))


if __name__ == '__main__':
    unittest.main()
