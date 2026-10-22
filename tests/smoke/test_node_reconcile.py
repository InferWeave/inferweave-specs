"""Offline managed-onboarding controls; never substitutes for host/runtime proof."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'conformance'))


class NodeReconcileContractTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.find_spec('node_reconcile')
        self.assertIsNotNone(spec, 'managed onboarding conformance checker is absent')
        import node_reconcile
        self.model = node_reconcile

    def case(self, name='ready', kind='valid'):
        return json.loads((ROOT / f'fixtures/node-reconcile/{kind}/{name}.json').read_text())

    def test_contract_fixtures_and_frozen_vocabularies(self):
        self.assertEqual([], self.model.contract_errors(ROOT))

    def test_managed_proof_has_its_own_registered_feature_and_task(self):
        contract = json.loads((ROOT / 'contracts/node-reconcile.json').read_text())
        self.assertEqual(['IW-DYNNODE-002'], contract['features'])
        self.assertEqual(['P5-T38'], contract['canonical_tasks'])
        graph = json.loads((ROOT / 'contracts/canonical-task-graph.json').read_text())
        task = next(item for item in graph['tasks'] if item['id'] == 'P5-T38')
        self.assertEqual('owed', task['proof_status'])
        self.assertEqual(['IW-DYNNODE-002'], task['features'])

    def test_ready_requires_independent_owner_evidence(self):
        case = self.case()
        self.assertEqual([case['assignments'][0]['deployment']], self.model.evaluate(ROOT, case)['ready'])
        case['context']['evidence'] = []
        result = self.model.evaluate(ROOT, case)
        self.assertEqual([], result['ready'])
        self.assertIn('qualification_missing', result['reasons'])

    def test_health_success_does_not_clear_expiry_or_quarantine(self):
        for filename, reason in [('stale-qualification', 'qualification_stale'),
                                 ('quarantined-health-success', 'quarantined'),
                                 ('missing-attestation', 'attestation_missing')]:
            with self.subTest(filename=filename):
                result = self.model.evaluate(ROOT, self.case(filename, 'invalid'))
                self.assertEqual([], result['ready'])
                self.assertIn(reason, result['reasons'])

    def test_negotiation_and_enrollment_precede_execution(self):
        for member, value in [('accepted', []), ('offered', []), ('enrolled', False),
                              ('ownerAuthenticated', False)]:
            case = self.case()
            case['context'][member] = value
            result = self.model.evaluate(ROOT, case)
            self.assertEqual([], result['execute'])
            self.assertEqual([], result['ready'])
            self.assertTrue(result['reasons'])

    def test_duplicate_deployment_is_not_an_implicit_span(self):
        result = self.model.evaluate(ROOT, self.case('duplicate-deployment', 'invalid'))
        self.assertIn('duplicate_deployment', result['reasons'])
        self.assertEqual([], result['execute'])
        explicit = self.case('explicit-span')
        self.assertEqual([], self.model.evaluate(ROOT, explicit)['reasons'])

    def test_disjoint_distinct_deployments_and_repeated_desired_state(self):
        case = self.case('distinct-deployments')
        first = self.model.evaluate(ROOT, case)
        second = self.model.evaluate(ROOT, copy.deepcopy(case))
        self.assertEqual([], first['reasons'])
        self.assertEqual(first, second)
        self.assertEqual(2, len(first['execute']))

    def test_scope_and_permit_cannot_be_forged_or_replayed(self):
        case = self.case('qualification-permit')
        result = self.model.evaluate(ROOT, case)
        self.assertEqual([], result['reasons'])
        self.assertEqual([], result['ready'])
        for edit in [lambda c: c['context']['permits'].clear(),
                     lambda c: c['context']['permits'][0].update(usedRequests=1),
                     lambda c: c['context'].update(now=1300),
                     lambda c: c['control']['permits'][0].update(nodeId='another-node')]:
            changed = copy.deepcopy(case)
            edit(changed)
            with self.subTest(changed=changed):
                rejected = self.model.evaluate(ROOT, changed)
                self.assertIn('permit_denied', rejected['reasons'])
                self.assertEqual([], rejected['ready'])

    def test_duplicate_keys_nonfinite_utf8_and_bounds_are_rejected(self):
        for raw in [b'{"version":1,"version":1}', b'{"a":{"x":1,"x":2}}',
                    b'{"x":NaN}', b'{"x":Infinity}', b'{"x":1e999}', b'\xff', b' ' * 65537]:
            with self.subTest(raw=raw[:40]), self.assertRaises(ValueError):
                self.model.decode(raw)

    def test_removing_readiness_guard_changes_result(self):
        case = self.case()
        for change in [lambda c: c['context'].update(reportAgeMs=300000),
                       lambda c: c['status']['records'][0]['watchdog'].update(state='inactive'),
                       lambda c: c['context']['evidence'][0]['checks'].remove('cancellation_reuse'),
                       lambda c: c['context'].update(servingScopes=[]),
                       lambda c: c['status']['records'][0]['attestation'].update(environmentFingerprint='sha256:' + 'f' * 64)]:
            changed = copy.deepcopy(case)
            change(changed)
            with self.subTest(changed=changed):
                result = self.model.evaluate(ROOT, changed)
                self.assertTrue(result['reasons'])
                self.assertEqual([], result['ready'])

    def test_booleans_are_not_wire_integers(self):
        case = self.case()
        case['facts']['version'] = True
        self.assertIn('malformed', self.model.evaluate(ROOT, case)['reasons'])

    def test_reordered_same_generation_cannot_replace_claims(self):
        case = self.case()
        case['context']['previousGeneration'] = 2
        self.assertIn('assignment_mismatch', self.model.evaluate(ROOT, case)['reasons'])
        case['context']['previousGeneration'] = 1
        case['context']['previousClaims'] = []
        self.assertIn('assignment_mismatch', self.model.evaluate(ROOT, case)['reasons'])

    def test_quarantined_or_exhausted_desired_state_cannot_execute_again(self):
        for name in ['quarantined-health-success', 'recovery-exhausted']:
            with self.subTest(name=name):
                self.assertEqual([], self.model.evaluate(ROOT, self.case(name, 'invalid'))['execute'])

    def test_owner_evidence_watchdog_generation_must_match_grant(self):
        case = self.case()
        case['context']['evidence'][0]['watchdogGeneration'] = 0
        result = self.model.evaluate(ROOT, case)
        self.assertIn('qualification_missing', result['reasons'])
        self.assertEqual([], result['ready'])

    def test_failed_record_retains_exhausted_recovery_budget(self):
        case = self.case()
        case['status']['records'][0].update(phase='failed')
        case['status']['records'][0]['recovery']['attempts'] = 2
        result = self.model.evaluate(ROOT, case)
        self.assertIn('recovery_exhausted', result['reasons'])
        self.assertEqual([], result['execute'])

    def test_frozen_vocabulary_drift_fails_validation(self):
        original = Path.read_text
        def read(path, *args, **kwargs):
            value = original(path, *args, **kwargs)
            if path == ROOT / 'contracts/node-reconcile.json':
                contract = json.loads(value)
                contract['reason_codes'].append('invented')
                return json.dumps(contract)
            return value
        with patch.object(Path, 'read_text', read):
            self.assertTrue(self.model.contract_errors(ROOT))


if __name__ == '__main__':
    unittest.main()
