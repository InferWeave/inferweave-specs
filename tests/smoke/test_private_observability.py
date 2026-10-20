"""Private HTTP contract proof only; runtime carrier and persistence remain owed."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'conformance'))


class PrivateObservabilityTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('private_observability'), 'private HTTP contract validator missing')
        import private_observability
        self.api = private_observability
        self.event = json.loads((ROOT / 'fixtures/valid/request-observation-ingress.json').read_text())

    def test_transport_is_bounded_strict_utf8_recursive_json(self):
        wire = json.dumps(self.event).encode()
        self.assertEqual(self.event, self.api.decode_event(wire))
        for bad in (wire.decode().encode('utf-16'), wire.decode().encode('utf-32'), b'\xff',
                    b'{"x":{"a":1,"a":2}}', b'{"x":NaN}', b'{"x":"\\ud800"}',
                    b'{"\\ud800":1}', b'{"nested":{"\\udfff":0}}', b' ' * 65537):
            with self.subTest(wire=bad[:20]), self.assertRaises(ValueError):
                self.api.decode_event(bad)
        self.assertEqual({}, self.api.decode_event(b'{}' + b' ' * 65534))

    def test_producer_binding_is_separate_from_claims(self):
        event = self.event
        trusted = {'authenticated': True, 'registered': True, 'role': 'gateway',
                   'node_id': event['source_gateway_id'], 'source_gateway_id': event['source_gateway_id'],
                   'producer_epochs': [event['producer_epoch']], 'lineage_authorized': True}
        self.assertEqual([], self.api.producer_errors(event, trusted))
        for key, value in [('authenticated', False), ('registered', False), ('role', 'upstream'),
                           ('node_id', 'other'), ('node_id', None), ('source_gateway_id', 'other'),
                           ('producer_epochs', []), ('lineage_authorized', False)]:
            with self.subTest(key=key):
                context = {**trusted, key: value}
                self.assertTrue(self.api.producer_errors(event, context))
        self.assertTrue(self.api.producer_errors(event, event))

    def test_duplicate_security_headers_are_case_insensitive(self):
        for name in self.api.CONTRACT['authentication']['singleton_headers']:
            with self.subTest(name=name):
                self.assertTrue(self.api.header_errors([(name, 'same'), (name.upper(), 'same')]))
        self.assertEqual([], self.api.header_errors([('Authorization', 'Bearer opaque')]))

    def test_ingest_cannot_supply_coverage_clocks_or_public_grants(self):
        import runner
        for key in ('server_now', 'received_at', 'coverage', 'principal_count', 'public_eligible', 'prompt', 'body'):
            event = {**self.event, key: 1}
            self.assertTrue(list(runner.validator('events/request-observation.json').iter_errors(event)))

    def test_pages_validate_nested_dtos_and_failure_parent(self):
        import runner
        for kind in ('valid', 'invalid'):
            for path in sorted((ROOT / 'fixtures' / kind).glob('private-observability-*.json')):
                with self.subTest(path=path.name):
                    self.assertTrue(runner.validate_fixture(path, kind == 'valid'))
        page = json.loads((ROOT / 'fixtures/valid/private-observability-rollups.json').read_text())
        self.assertEqual([], self.api.page_errors(page, 'rollups', ROOT))
        page['items'][0]['parent']['revision'] += 1
        self.assertTrue(self.api.page_errors(page, 'rollups', ROOT))

    def test_query_bounds_and_no_unknown_or_duplicate_scalar(self):
        base = [('start', '2026-10-20T00:00:00Z'), ('end', '2026-10-20T01:00:00Z')]
        self.assertEqual([], self.api.query_errors(base, 'diagnostics'))
        self.assertEqual([], self.api.query_errors(base + [('resolution_seconds', '300')], 'rollups'))
        for extra in ([('limit', '101')], [('limit', '0')], [('limit', '1.0')], [('limit', '1'), ('limit', '1')],
                      [('server_now', 'x')], [('cursor', 'x' * 1025)], [('source_gateway_id', 'x' * 129)],
                      [('resolution_seconds', '300')]):
            self.assertTrue(self.api.query_errors(base + extra, 'diagnostics'))
        self.assertTrue(self.api.query_errors(base[::-1] + [('start', base[0][1])], 'rollups'))
        self.assertTrue(self.api.query_errors([('start', '2026-01-01T00:00:00Z'), ('end', base[1][1])], 'diagnostics'))
        self.assertTrue(self.api.query_errors([('start', 'junk'), ('end', base[1][1])], 'diagnostics'))

    def test_snapshot_cursor_binds_authority_query_endpoint_and_expiry(self):
        query = {'start': '2026-10-20T00:00:00Z', 'end': '2026-10-20T01:00:00Z', 'limit': 25}
        claims = {'operator': 'operator-one', 'endpoint': 'rollups', 'query': query,
                  'snapshot_id': 'snapshot-one', 'last_sort_key': ['window', 'source', 'epoch', 'row'],
                  'expires_at': '2026-10-20T01:05:00Z'}
        args = ['operator-one', 'rollups', query, '2026-10-20T01:04:59Z', True]
        self.assertEqual([], self.api.cursor_errors(claims, *args))
        for index, value in [(0, 'other'), (1, 'diagnostics'), (2, {**query, 'limit': 26}),
                             (3, claims['expires_at']), (4, False)]:
            changed = args.copy()
            changed[index] = value
            self.assertTrue(self.api.cursor_errors(claims, *changed))

    def test_read_health_filters_and_row_bounds_are_enforced(self):
        page = json.loads((ROOT / 'fixtures/valid/private-observability-diagnostics.json').read_text())
        mutations = [lambda p: p['query'].update(model_id='different'),
                     lambda p: p['query'].update(gpu_resource_id='different'),
                     lambda p: p['query'].update(end=p['query']['start']),
                     lambda p: p.update(expires_at='2026-10-20T01:05:01Z'),
                     lambda p: p['query_health'].update(status='unavailable'),
                     lambda p: p['items'].append(copy.deepcopy(p['items'][0]))]
        for mutate in mutations:
            changed = copy.deepcopy(page)
            mutate(changed)
            self.assertTrue(self.api.page_errors(changed, 'diagnostics', ROOT))
        self.assertTrue(self.api.query_errors([('start', '2026-10-20T00:00:00Z'),
                                              ('end', '2026-10-20T01:00:00Z'),
                                              ('limit', '9' * 8000)], 'diagnostics'))

    def test_extreme_exponents_are_controlled_decode_errors(self):
        for exponent in ('9999999999999999999', '-9999999999999999999'):
            with self.subTest(exponent=exponent), self.assertRaises(ValueError):
                self.api.decode_event(('{"value":1e' + exponent + '}').encode())

    def test_ambiguous_framing_and_comma_credentials_are_refused(self):
        with self.subTest(framing='content-length plus transfer-encoding'):
            self.assertTrue(self.api.header_errors([('Content-Length', '10'), ('Transfer-Encoding', 'chunked')]))
        for name in ('Authorization', 'X-InferWeave-Admin', 'X-InferWeave-Node'):
            with self.subTest(name=name):
                self.assertTrue(self.api.header_errors([(name, 'one,two')]))

    def test_pages_are_strictly_sorted_including_identity_ties(self):
        for kind in ('diagnostics', 'rollups'):
            page = json.loads((ROOT / f'fixtures/valid/private-observability-{kind}.json').read_text())
            item = page['items'][0]
            row = item if kind == 'diagnostics' else item['parent']
            if kind == 'rollups':
                item.update(failure=None, failure_availability='unavailable')
            id_field = 'event_id' if kind == 'diagnostics' else 'rollup_id'
            row[id_field] = 'a'
            second = copy.deepcopy(item)
            second_row = second if kind == 'diagnostics' else second['parent']
            second_row[id_field] = 'z'
            page['items'] = [item, second]
            self.assertEqual([], self.api.page_errors(page, kind, ROOT))
            page['items'].reverse()
            with self.subTest(kind=kind, order='identity tie'):
                self.assertTrue(self.api.page_errors(page, kind, ROOT))
            if kind == 'diagnostics':
                second_row['observed_at'] = '2026-10-20T00:10:00Z'
            else:
                second_row.update(window_start='2026-10-20T00:05:00Z', window_end='2026-10-20T00:10:00Z',
                                  as_of='2026-10-20T00:10:01Z')
            page['items'] = [item, second]
            self.assertEqual([], self.api.page_errors(page, kind, ROOT))
            page['items'].reverse()
            with self.subTest(kind=kind, order='chronological'):
                self.assertTrue(self.api.page_errors(page, kind, ROOT))

    def test_retention_uses_server_snapshot_clock_not_query_width(self):
        from datetime import timedelta
        for kind, days in [('diagnostics', 7), ('rollups', 90)]:
            page = json.loads((ROOT / f'fixtures/valid/private-observability-{kind}.json').read_text())
            item = page['items'][0]
            row = item if kind == 'diagnostics' else item['parent']
            if kind == 'rollups':
                item.update(failure=None, failure_availability='unavailable')
                row['as_of'] = row['window_end']
            point = self.api.utc(row['observed_at'] if kind == 'diagnostics' else row['window_end'])
            for age, valid in [(0, True), (days * 86400 - 1, True), (days * 86400, False),
                               (days * 86400 + 1, False), (-1, False)]:
                changed = copy.deepcopy(page)
                now = point + timedelta(seconds=age)
                changed['as_of'] = now.strftime('%Y-%m-%dT%H:%M:%SZ')
                changed['expires_at'] = (now + timedelta(seconds=300)).strftime('%Y-%m-%dT%H:%M:%SZ')
                errors = self.api.page_errors(changed, kind, ROOT)
                with self.subTest(kind=kind, age=age):
                    self.assertEqual(valid, not errors, errors)

    def test_reliability_selectors_are_exact_frozen_enums(self):
        base = [('start', '2026-10-20T00:00:00Z'), ('end', '2026-10-20T01:00:00Z')]
        selectors = [('dataset', 'production'), ('observation_kind', 'ingress_terminal'), ('lineage_scope', 'trusted')]
        self.assertEqual([], self.api.query_errors(base + selectors, 'diagnostics'))
        for name, _ in selectors:
            self.assertTrue(self.api.query_errors(base + [(name, 'invented')], 'diagnostics'))
        for kind in ('diagnostics', 'rollups'):
            page = json.loads((ROOT / f'fixtures/valid/private-observability-{kind}.json').read_text())
            page['query'].update(selectors)
            self.assertEqual([], self.api.page_errors(page, kind, ROOT))
            for field, value in [('dataset', 'controlled'), ('observation_kind', 'attempt_terminal'),
                                 ('observation_kind', 'hop_terminal'), ('lineage_scope', 'local_unlinked')]:
                changed = copy.deepcopy(page)
                changed['query'][field] = value
                self.assertTrue(self.api.page_errors(changed, kind, ROOT))

    def test_contract_guard_and_mutations(self):
        self.assertEqual([], self.api.contract_errors(ROOT))
        for section, key, value in [('limits', 'event_bytes', 16777216), ('defaults', 'enabled', True),
                                    ('retention', 'diagnostic_days', 90), ('authentication', 'ingest_role', 'user')]:
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                (root / 'contracts').mkdir()
                altered = copy.deepcopy(self.api.CONTRACT)
                altered[section][key] = value
                (root / 'contracts/private-observability.json').write_text(json.dumps(altered))
                self.assertTrue(self.api.contract_errors(root))


if __name__ == '__main__':
    unittest.main()
