"""Bounded failure companion contract proof; runtime persistence remains owed."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'conformance'))
import request_observations as observations


class FailureRollupTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('failure_rollups'), 'failure rollup validator missing')
        import failure_rollups
        self.failures = failure_rollups
        self.contract = json.loads((ROOT / 'contracts/request-observation.json').read_text())
        self.parent = json.loads((ROOT / 'fixtures/valid/request-observation-rollup-failures.json').read_text())
        self.row = json.loads((ROOT / 'fixtures/valid/request-observation-failure-rollup.json').read_text())

    def test_full_conformance_runner_routes_and_validates_failure_companions(self):
        import runner
        for stem in ('request-observation-failure-rollup', 'request-observation-failure-rollup-marginal'):
            self.assertEqual('events/request-observation-failure-rollup.json', runner.schema_for(stem))
        self.assertEqual('events/request-observation.json', runner.schema_for('request-observation-ingress'))
        self.assertEqual('events/request-observation-rollup.json', runner.schema_for('request-observation-rollup-failures'))
        for kind in ('valid', 'invalid'):
            for path in sorted((ROOT / 'fixtures' / kind).glob('request-observation-failure-rollup*.json')):
                with self.subTest(fixture=path.name):
                    self.assertTrue(runner.validate_fixture(path, kind == 'valid'))

    def test_valid_pair_and_fixed_fingerprint_vector(self):
        self.assertEqual([], self.failures.pair_errors(self.row, self.parent, ROOT))
        vector = json.loads((ROOT / 'conformance/request-observation-failure-rollup-vectors.json').read_text())
        self.assertEqual(vector['parent_fingerprint'], self.failures.parent_fingerprint(self.parent))
        for value in vector['canonical_vectors']:
            self.assertEqual(value['canonical'], self.failures.canonical_parent(value['value']))
        reordered = dict(reversed(list(self.parent.items())))
        self.assertEqual(self.failures.parent_fingerprint(self.parent), self.failures.parent_fingerprint(reordered))

    def test_parent_integer_spellings_preserve_frozen_v1_compatibility(self):
        parent = copy.deepcopy(self.parent)
        parent['revision'] = 1.0
        self.assertEqual([], observations.rollup_errors(parent, self.contract))
        self.assertEqual([], self.failures.pair_errors(self.row, parent, ROOT))
        self.assertEqual(self.row['parent']['fingerprint'], self.failures.parent_fingerprint(parent))
        self.assertTrue(hasattr(self.failures, 'decode_parent'))
        for spelling in ('1', '1.0', '1e0', '1.00e+0'):
            decoded = self.failures.decode_parent('{"revision":' + spelling + '}')
            self.assertEqual('{"revision":1}', self.failures.canonical_parent(decoded))
        for spelling in ('0', '-0', '-0.0', '0e0'):
            decoded = self.failures.decode_parent('{"revision":' + spelling + '}')
            self.assertEqual('{"revision":0}', self.failures.canonical_parent(decoded))
        for spelling in ('1.1', '1.00000000000000001', '9007199254740991.1', '9007199254740992', '1e99999', 'NaN', 'Infinity'):
            with self.subTest(spelling=spelling), self.assertRaises(ValueError):
                self.failures.decode_parent('{"revision":' + spelling + '}')
        self.assertEqual(observations.MAX_INTEGER, self.failures.decode_parent('9007199254740991.0'))
        self.assertEqual(observations.MAX_INTEGER, self.failures.decode_parent('9.007199254740991e15'))
        wire = json.dumps(self.parent)
        for encoding in ('utf-16', 'utf-32'):
            with self.assertRaises(ValueError):
                self.failures.decode_parent(wire.encode(encoding))
        with self.assertRaises(ValueError):
            self.failures.decode_parent('{"parent":{"revision":1,"revision":1}}')

    def test_parent_binding_covers_every_field_and_revision(self):
        for field, value in [('revision', 2), ('sealed', False), ('dataset', 'unknown'), ('as_of', '2026-10-20T00:05:02Z')]:
            with self.subTest(field=field):
                changed = copy.deepcopy(self.parent)
                changed[field] = value
                self.assertTrue(self.failures.pair_errors(self.row, changed, ROOT))
        changed = copy.deepcopy(self.row)
        changed['parent']['fingerprint'] = 'sha256:' + '0' * 64
        self.assertTrue(self.failures.pair_errors(changed, self.parent, ROOT))
        self.assertTrue(self.failures.pair_errors(None, self.parent, ROOT))
        self.assertTrue(self.failures.pair_errors(self.row, None, ROOT))

    def test_closed_complete_vocabularies_and_counts(self):
        for axis in ('reason_counts', 'layer_counts', 'phase_counts'):
            row = copy.deepcopy(self.row)
            key = next(iter(row['breakdowns']['service_failure'][axis]))
            del row['breakdowns']['service_failure'][axis][key]
            self.assertTrue(self.failures.pair_errors(row, self.parent, ROOT))
            row = copy.deepcopy(self.row)
            row['breakdowns']['service_failure'][axis]['invented'] = 0
            self.assertTrue(self.failures.pair_errors(row, self.parent, ROOT))
            row = copy.deepcopy(self.row)
            row['breakdowns']['service_failure'][axis]['unknown'] += 1
            self.assertTrue(self.failures.pair_errors(row, self.parent, ROOT))
        row = copy.deepcopy(self.row)
        row['breakdowns']['success'] = copy.deepcopy(row['breakdowns']['unknown'])
        self.assertTrue(self.failures.pair_errors(row, self.parent, ROOT))

    def test_timeout_cross_table_is_correlated_and_conserves_marginals(self):
        service = self.row['breakdowns']['service_failure']
        self.assertEqual(1, sum(phases['queue'] for phases in service['timeout_phase_counts'].values()))
        self.assertEqual(2, sum(service['reason_counts'][reason] for reason in service['timeout_phase_counts']))
        row = copy.deepcopy(self.row)
        row['breakdowns']['service_failure']['timeout_phase_counts']['BACKEND_TIMEOUT']['queue'] += 1
        self.assertTrue(self.failures.pair_errors(row, self.parent, ROOT))
        row = copy.deepcopy(self.row)
        phases = row['breakdowns']['service_failure']['timeout_phase_counts']['BACKEND_TIMEOUT']
        phases['queue'], phases['execution'] = 2, 0
        self.assertTrue(self.failures.pair_errors(row, self.parent, ROOT))

    def test_wire_requires_utf8_before_json_decoding(self):
        wire = json.dumps(self.row)
        self.assertEqual(self.row, self.failures.decode(wire.encode('utf-8')))
        for encoding in ('utf-16', 'utf-16-le', 'utf-16-be', 'utf-32', 'utf-32-le', 'utf-32-be'):
            with self.subTest(encoding=encoding), self.assertRaises(ValueError):
                self.failures.decode(wire.encode(encoding))

    def test_strict_wire_limits_and_checked_addition(self):
        for wire in ['{"parent":{"revision":1,"revision":2}}', ' ' * 65537,
                     '{"value":NaN}', '{"value":Infinity}', '{"value":1.0}',
                     '{"value":9007199254740992}', '{"value":"\\ud800"}']:
            with self.subTest(wire=wire[:80]), self.assertRaises(ValueError):
                self.failures.decode(wire)
        self.assertEqual(observations.MAX_INTEGER, self.failures.checked_sum([observations.MAX_INTEGER, 0]))
        for values in ([observations.MAX_INTEGER, 1], [-1], [True], [1.0]):
            with self.assertRaises(ValueError):
                self.failures.checked_sum(values)
        row = copy.deepcopy(self.row)
        row['breakdowns']['service_failure']['reason_counts']['unknown'] = observations.MAX_INTEGER
        self.assertTrue(self.failures.pair_errors(row, self.parent, ROOT))

    def test_only_deduplicated_all_terminal_facts_contribute(self):
        events = json.loads((ROOT / 'conformance/request-observation-failure-rollup-vectors.json').read_text())['events']
        self.assertEqual(self.row['breakdowns'], self.failures.count_breakdowns(events, self.contract))
        duplicate_identity = copy.deepcopy(events[0])
        duplicate_identity['outcome']['reason_code'] = 'unknown'
        with self.assertRaises(ValueError):
            self.failures.count_breakdowns(events + [duplicate_identity], self.contract)
        duplicate_terminal = copy.deepcopy(events[0])
        duplicate_terminal['event_id'] = 'new-identity-same-terminal'
        with self.assertRaises(ValueError):
            self.failures.count_breakdowns(events + [duplicate_terminal], self.contract)

    def test_none_phase_and_layer_remain_valid_and_coverage_is_parent_owned(self):
        self.assertEqual(1, self.row['breakdowns']['cancelled']['phase_counts']['none'])
        self.assertEqual(1, self.row['breakdowns']['cancelled']['layer_counts']['none'])
        self.assertNotIn('coverage', self.row)
        parent = copy.deepcopy(self.parent)
        parent['coverage'].update(status='partial', dropped_events=1)
        row = copy.deepcopy(self.row)
        row['parent']['fingerprint'] = self.failures.parent_fingerprint(parent)
        self.assertEqual([], self.failures.pair_errors(row, parent, ROOT))
        row['coverage'] = copy.deepcopy(parent['coverage'])
        self.assertTrue(self.failures.pair_errors(row, parent, ROOT))


if __name__ == '__main__':
    unittest.main()
