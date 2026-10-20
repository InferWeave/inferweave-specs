"""Offline contract regressions; no operational warehouse claim."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'conformance'))
import request_observations as observations


class RequestObservationTests(unittest.TestCase):
    def setUp(self):
        self.contract = json.loads((ROOT / 'contracts/request-observation.json').read_text())
        self.event = json.loads((ROOT / 'fixtures/valid/request-observation-ingress.json').read_text())
        self.rollup = json.loads((ROOT / 'fixtures/valid/request-observation-rollup.json').read_text())

    def test_failure_rollup_companion_is_available_without_changing_v1(self):
        self.assertTrue((ROOT / 'schemas/v1/events/request-observation-failure-rollup.json').is_file(),
                        'bounded additive failure-rollup schema is missing')
        self.assertIn('failure_rollup_schema', self.contract)

    def test_fixtures_and_identity_vectors(self):
        self.assertEqual([], observations.contract_errors(ROOT))

    def test_missing_is_not_zero_and_200_is_not_success(self):
        zero = self.event['tokens']['input_total']
        missing = self.event['tokens']['context_consumed']
        self.assertEqual(0, zero['value'])
        self.assertNotIn('value', missing)
        bad = copy.deepcopy(self.event)
        bad['outcome']['completion'] = 'protocol_failure'
        self.assertTrue(observations.event_errors(bad))

    def test_weighted_histograms_merge_and_provenance_does_not(self):
        one = self.rollup['metrics'][0]
        two = copy.deepcopy(one)
        two.update(eligible_count=2, known_count=2, sum=2000)
        two['histogram']['counts'][8] = 2
        merged = observations.merge_metrics(one, two)
        self.assertEqual((3, 3000, 3), (merged['known_count'], merged['sum'], sum(merged['histogram']['counts'])))
        two['source'] = 'http_first_token_proxy'
        with self.assertRaises(ValueError):
            observations.merge_metrics(one, two)

    def test_dataset_overlap_and_rollup_replay_are_not_additive(self):
        second = copy.deepcopy(self.rollup)
        second.update(rollup_id='next', window_start='2026-10-20T00:05:00Z', window_end='2026-10-20T00:10:00Z')
        observations.require_mergeable(self.rollup, second)
        second['dataset'] = 'controlled'
        with self.assertRaises(ValueError):
            observations.require_mergeable(self.rollup, second)
        with self.assertRaises(ValueError):
            observations.require_mergeable(self.rollup, self.rollup)
        self.assertEqual(1, len(observations.replace_rollups([self.rollup, self.rollup])))
        revised = copy.deepcopy(self.rollup)
        revised['revision'] += 1
        with self.assertRaises(ValueError):
            observations.replace_rollups([self.rollup, revised])

    def test_semantic_mutations(self):
        for field, value in [('source_gateway_id', 'other-owner'), ('dataset', 'controlled')]:
            event = copy.deepcopy(self.event)
            event[field] = value
            self.assertTrue(observations.event_errors(event))
        for change in [lambda r:r['counts'].update(total=2), lambda r:r['coverage'].update(dropped_events=None), lambda r:r['metrics'][0].update(sum=1)]:
            row = copy.deepcopy(self.rollup)
            change(row)
            self.assertTrue(observations.rollup_errors(row, self.contract))

    def test_second_event_identity_cannot_recount_terminal_fact(self):
        second = copy.deepcopy(self.event)
        second['event_id'] = 'second-event-same-ingress'
        with self.assertRaises(ValueError):
            observations.deduplicate([self.event, second])
        second['lineage']['logical_request_id'] = 'independent-ingress'
        self.assertEqual(2, len(observations.deduplicate([self.event, second])[0]))

    def test_revision_cannot_move_cohort_and_reset_cannot_be_hidden(self):
        first = copy.deepcopy(self.rollup)
        first['sealed'] = False
        second = copy.deepcopy(first)
        second['revision'] += 1
        second['dataset'] = 'controlled'
        with self.assertRaises(ValueError):
            observations.replace_rollups([first, second])
        second = copy.deepcopy(first)
        second.update(window_start='2026-10-20T00:05:00Z', window_end='2026-10-20T00:10:00Z')
        second['coverage']['counter_epoch'] = 'reset'
        with self.assertRaises(ValueError):
            observations.require_mergeable(first, second)

    def test_phase_semantics_are_part_of_metric_definition(self):
        changed = copy.deepcopy(self.event)
        changed['timings'][0]['semantics'] = 'interval'
        self.assertTrue(observations.event_errors(changed))

    def test_counter_epoch_is_immutable_across_revisions(self):
        first = copy.deepcopy(self.rollup)
        first['sealed'] = False
        second = copy.deepcopy(first)
        second['revision'] += 1
        second['coverage']['counter_epoch'] = 'reset'
        with self.assertRaises(ValueError):
            observations.replace_rollups([first, second])

    def test_rollup_attribution_matches_event_rules(self):
        changed = copy.deepcopy(self.rollup)
        changed['attribution'].update(gpu_count=42, gpu_resource_ids=[])
        self.assertTrue(observations.rollup_errors(changed, self.contract))

    def test_submillisecond_window_drift_is_rejected(self):
        changed = copy.deepcopy(self.rollup)
        for end in ('2026-10-20T00:05:00.000999Z', '2026-10-20T00:05:00.0000009Z'):
            changed['window_end'] = end
            self.assertTrue(observations.rollup_errors(changed, self.contract))

    def test_nonfinite_json_literals_are_rejected_by_decoder(self):
        for literal in ('NaN', 'Infinity', '-Infinity'):
            with self.subTest(literal=literal), self.assertRaises(ValueError):
                observations.decode('{"value":' + literal + '}')

    def test_bounded_recursive_strict_decoder(self):
        with self.assertRaises(ValueError):
            observations.decode('{"outcome":{"status":"success","status":"unknown"}}')
        with self.assertRaises(ValueError):
            observations.decode(' ' * 65537)


if __name__ == '__main__':
    unittest.main()
