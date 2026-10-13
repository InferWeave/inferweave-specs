"""Artifact conformance and mutation guards; live acceptance IDs remain owed."""
import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
import sys
from jsonschema import Draft7Validator, FormatChecker, RefResolver
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'conformance'))
import dynamic_aliases

STORE = {s['$id']: s for p in (ROOT / 'schemas/v1').rglob('*.json') for s in [json.loads(p.read_text())]}


def load(path):
    return json.loads((ROOT / path).read_text())


def errors(kind, value):
    schema = load('schemas/v1/aliases/' + kind + '.json')
    validator = Draft7Validator(schema, resolver=RefResolver.from_schema(schema, store=STORE), format_checker=FormatChecker())
    result = list(validator.iter_errors(value))
    return result or dynamic_aliases.semantic_errors(value, kind)


class DynamicAliasContractTests(unittest.TestCase):
    def test_schemas_are_valid_and_frozen_vocabulary_reconciles(self):
        for path in (ROOT / 'schemas/v1/aliases').glob('*.json'):
            Draft7Validator.check_schema(json.loads(path.read_text()))
        self.assertEqual([], dynamic_aliases.contract_errors(ROOT))

    def test_positive_and_hostile_fixtures(self):
        kinds = ['definition', 'resolution', 'resolve-request', 'event', 'advertisement', 'capabilities']
        for fixture in (ROOT / 'fixtures/valid').glob('dynamic-alias-*.json'):
            kind = fixture.stem.removeprefix('dynamic-alias-')
            if kind == 'definition-empty-allowlists':
                kind = 'definition'
            if kind == 'advertisement-embedding':
                kind = 'advertisement'
            self.assertFalse(errors(kind, json.loads(fixture.read_text())), fixture.name)
        for path in (ROOT / 'fixtures/invalid').glob('dynamic-alias-*.json'):
            kind = next(k for k in kinds if path.stem.startswith('dynamic-alias-' + k + '-'))
            self.assertTrue(errors(kind, json.loads(path.read_text())), path.name)

    def test_selection_empty_allowlists_do_not_become_tenant_authorization(self):
        value = load('fixtures/valid/dynamic-alias-definition-empty-allowlists.json')
        self.assertFalse(errors('definition', value))
        value['selection']['type'] = 'MANAGED'
        self.assertTrue(errors('definition', value))
        # This is a representation check, not proof that runtime policy is enforced.
        value['selection']['type'] = 'DYNAMIC'
        value['selection']['required']['allowed_tenants'] = []
        self.assertFalse(errors('definition', value))
        self.assertEqual([], value['selection']['required']['allowed_tenants'])

    def test_semantic_negative_cases(self):
        definition = load('fixtures/valid/dynamic-alias-definition.json')
        for mutate in [lambda d: d['selection'].update(preferred={'latency': 0.3}),
                       lambda d: d['selection'].update(type='MANAGED'),
                       lambda d: d['selection'].update(model_ids_allow=['alias:other']),
                       lambda d: d['selection'].update(model_ids_allow=['a'], model_ids_deny=['a'])]:
            bad = copy.deepcopy(definition); mutate(bad)
            self.assertTrue(errors('definition', bad))
        resolution = load('fixtures/valid/dynamic-alias-resolution.json')
        for mutate in [lambda d: d.update(candidates=[]),
                       lambda d: d['selected'].update(instance_generation='stale'),
                       lambda d: d.update(expires_at='2026-10-12T20:00:00Z'),
                       lambda d: d.update(expires_at='2026-10-12T20:00:03Z')]:
            bad = copy.deepcopy(resolution); mutate(bad)
            self.assertTrue(errors('resolution', bad))

    def test_wrapped_definition_and_error_semantics_cannot_bypass_validation(self):
        for kind in ['draft-write', 'simulate-request']:
            value = load('fixtures/valid/dynamic-alias-' + kind + '.json')
            value['definition']['selection']['preferred'] = {'latency': 0.3}
            self.assertTrue(errors(kind, value), kind)
        value = load('fixtures/valid/dynamic-alias-error.json')
        value['retryable'] = not value['retryable']
        self.assertTrue(errors('error', value))
        value = load('fixtures/valid/dynamic-alias-resolution.json')
        value['candidates'][0]['capability_profile']['instance_generation'] = 'wrong-instance'
        self.assertTrue(errors('resolution', value))
        # Source stream epoch and runtime instance generation are deliberately independent.
        value = load('fixtures/valid/dynamic-alias-resolution.json')
        self.assertNotEqual(value['candidates'][0]['instance_generation'], value['candidates'][0]['capability_profile']['provenance']['source_generation'])
        self.assertFalse(errors('resolution', value))

    def test_qualified_profile_and_metric_evidence(self):
        value = load('fixtures/valid/dynamic-alias-resolution.json')
        candidate = value['candidates'][0]
        profile = candidate['capability_profile']
        self.assertEqual('verified', profile['confidence'])
        self.assertEqual('no-training', profile['privacy'][0])
        candidate['metric_evidence'] = {'latency_p95': {'value': 1.2, 'unit': 'seconds',
            'sample_size': 24, 'confidence': 'verified', 'provenance': profile['provenance']}}
        self.assertFalse(errors('resolution', value))
        candidate['metric_evidence']['latency_p95']['sample_size'] = 0
        self.assertTrue(errors('resolution', value))

    def test_closed_policy_unknown_field_and_unregistered_runtime(self):
        value = load('fixtures/valid/dynamic-alias-definition.json')
        value['selection']['required']['runtime_families'] = ['made-up-family']
        self.assertTrue(errors('definition', value))
        value = load('fixtures/valid/dynamic-alias-definition.json')
        value['selection']['required']['features']['tool_calling']['confidence'] = 'unknown'
        self.assertTrue(errors('definition', value))

    def test_openapi_new_operations_require_level_and_auth(self):
        api = yaml.safe_load((ROOT / 'openapi/inferweave-v1.yaml').read_text())
        self.assertTrue(all(path.startswith('/') for path in api['paths']))
        self.assertIn('post', api['paths']['/aliases'])
        self.assertEqual('createAliasDraft', api['paths']['/aliases']['post']['operationId'])
        for path, operations in api['paths'].items():
            if not (path.startswith('/aliases') or path in ['/catalog/models','/federation/alias-advertisements']):
                continue
            for method, operation in operations.items():
                self.assertEqual([{'AliasBearer': []}, {'AliasEdgeDelegation': []}], operation['security'])
                headers = {p['name']: p for p in operation['parameters'] if p['in'] == 'header'}
                if path == '/aliases' and method == 'get':
                    self.assertNotIn('required', headers['InferWeave-Alias-Level'])
                    continue
                self.assertTrue(headers['InferWeave-Alias-Level']['required'])
                if method == 'patch' or path.endswith(('/publish','/rollback')):
                    self.assertTrue(headers['If-Match']['required'])
                    self.assertTrue(headers['Idempotency-Key']['required'])
        filters = {p['name'] for p in api['paths']['/aliases']['get']['parameters'] if p['in'] == 'query'}
        self.assertTrue({'query','runtime_family','owner_scope','status','visibility','route_kind','family'} <= filters)
        legacy = api['paths']['/aliases']['get']['responses']['200']['content']['application/json']['schema']['oneOf'][0]
        self.assertEqual('array', legacy['type'])
        schema = load('schemas/v1/model/alias.json')
        self.assertTrue(Draft7Validator(schema, resolver=RefResolver.from_schema(schema, store=STORE)).is_valid(load('fixtures/valid/alias.json')))

    def test_guards_reject_mutations(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            files = ['contracts/protocol-v1/dynamic-aliases.json','schemas/v1/aliases/contract.json',
                     'specs/54_DYNAMIC_MODEL_ALIASES.md','contracts/dynamic-alias-acceptance.json',
                     'conformance/alias-edge-delegation-vectors.json','conformance/alias_edge_delegation.py','conformance/node_join.py']
            for path in files:
                dest = root / path; dest.parent.mkdir(parents=True, exist_ok=True); dest.write_bytes((ROOT / path).read_bytes())
            mutations = [
                (files[0], lambda d:d['events'].append('made.up')),
                (files[0], lambda d:d['reason_codes'][0].update(retryable=True)),
                (files[1], lambda d:d['definitions']['candidate']['required'].remove('instance_generation')),
                (files[1], lambda d:d['definitions']['capability_profile']['required'].remove('confidence')),
                (files[1], lambda d:d['definitions']['capability_profile']['required'].remove('instance_generation')),
                (files[1], lambda d:d['definitions']['resolution']['properties'].update(admission_reserved={'type':'boolean'})),
                (files[1], lambda d:d['definitions']['advertisement']['properties'].update(allocation_entitlement={'type':'boolean'})),
                (files[3], lambda d:d['acceptance'].pop()),
                (files[3], lambda d:d['acceptance'][0].update(proof_status='proven')),
            ]
            for path, mutate in mutations:
                original=(root/path).read_bytes(); value=json.loads(original); mutate(value)
                (root/path).write_text(json.dumps(value))
                self.assertTrue(dynamic_aliases.contract_errors(root),path)
                (root/path).write_bytes(original)


if __name__ == '__main__':
    unittest.main()
