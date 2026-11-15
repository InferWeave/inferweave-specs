#!/usr/bin/env python3
"""Offline descriptor and binding projections; no complete Lease or runtime proof."""
import copy
import json
from pathlib import Path
import re
import unittest

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = json.loads((ROOT / 'contracts/benchmark-continuation-policy.json').read_text())
SCHEMA = json.loads((ROOT / 'schemas/v1/benchmark-continuation-policy-contract.json').read_text())
VECTORS = json.loads((ROOT / 'conformance/benchmark-continuation-policy/vectors.json').read_text())
VERSION = 'iw.benchmark-continuation-policy/1'


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate field')
        result[key] = value
    return result


def projection_positive(request, response, authority='owned_current'):
    """Validate projected binding only; actual Lease validity is an implementation obligation."""
    if authority != 'owned_current' or not isinstance(request, dict) or not isinstance(response, dict):
        return False
    if set(request) != {'schema', 'nonce', 'lease'} or set(response) != {
        'schema', 'nonce', 'lease_id', 'node_id', 'hard_deadline', 'policy_allows'
    }:
        return False
    lease = request['lease']
    if not isinstance(lease, dict) or set(lease) != {'lease_id', 'node_id', 'hard_deadline'}:
        return False  # projection fixture only, not a definition of a complete Lease
    nonce = request['nonce']
    return (request['schema'] == response['schema'] == VERSION
            and isinstance(nonce, str) and re.fullmatch(r'[0-9a-f]{32}', nonce) is not None
            and response['nonce'] == nonce and response['policy_allows'] is True
            and all(isinstance(lease[k], str) and bool(lease[k]) and response[k] == lease[k]
                    for k in ('lease_id', 'node_id', 'hard_deadline')))


class ContinuationContractTests(unittest.TestCase):
    def test_descriptor_and_mutations(self):
        Draft202012Validator.check_schema(SCHEMA)
        validator = Draft202012Validator(SCHEMA)
        self.assertFalse(list(validator.iter_errors(CONTRACT)))
        for field, value in [('version', 'wrong'), ('meaning', 'execution_grant'),
                             ('max_request_bytes', 1), ('start_gates', 'relaxed')]:
            mutated = copy.deepcopy(CONTRACT)
            mutated[field] = value
            self.assertTrue(list(validator.iter_errors(mutated)), field)
        mutated = copy.deepcopy(CONTRACT)
        mutated['extra'] = True
        self.assertTrue(list(validator.iter_errors(mutated)))

    def test_vectors_and_mutations(self):
        self.assertEqual(VECTORS['scope'], 'binding_projection_only_not_complete_lease_or_runtime_authority')
        for vector in VECTORS['vectors']:
            with self.subTest(vector=vector['id']):
                self.assertEqual(vector['expected'], projection_positive(
                    vector['request'], vector['response'], vector.get('authority', 'owned_current')))
        good = VECTORS['vectors'][0]
        for field, value in [('schema', 'wrong'), ('nonce', 'A' * 32), ('lease', {})]:
            request = copy.deepcopy(good['request'])
            request[field] = value
            self.assertFalse(projection_positive(request, good['response']))
        for field in ('schema', 'nonce', 'lease_id', 'node_id', 'hard_deadline'):
            response = copy.deepcopy(good['response'])
            response[field] = 'wrong'
            self.assertFalse(projection_positive(good['request'], response))
        response = copy.deepcopy(good['response'])
        response['extra'] = True
        self.assertFalse(projection_positive(good['request'], response))
        request = copy.deepcopy(good['request'])
        request['extra'] = True
        self.assertFalse(projection_positive(request, good['response']))

    def test_duplicate_json_fields_are_rejected(self):
        with self.assertRaises(ValueError):
            json.loads('{"schema":"a","schema":"b"}', object_pairs_hook=unique_object)
        with self.assertRaises(ValueError):
            json.loads('{"lease":{"node_id":"a","node_id":"b"}}', object_pairs_hook=unique_object)


if __name__ == '__main__':
    unittest.main()
