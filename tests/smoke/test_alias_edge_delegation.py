"""Offline contract proof only; Rust/Go auth and PostgreSQL replay remain owed."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'conformance'))
import alias_edge_delegation as edge
import node_join


class EdgeDelegationContractTests(unittest.TestCase):
    def setUp(self):
        self.vectors = json.loads((ROOT / 'conformance/alias-edge-delegation-vectors.json').read_text())

    def test_known_answers_reproduce(self):
        self.assertEqual([], edge.check_vectors(ROOT))
        self.assertEqual(36, len(edge.DOMAIN))
        self.assertEqual(3, len(self.vectors['known_answers']))

    def test_every_signed_field_tamper_invalidates_signature(self):
        base = self.vectors['known_answers'][0]
        public = bytes.fromhex(base['public_key_hex'])
        signature = edge.decode_base64(base['envelope']['signature'])
        seen = set()
        for case in self.vectors['negative_cases']:
            if case['operation'] != 'mutate_without_resigning':
                continue
            value = copy.deepcopy(base['envelope'])
            value[case['field']] = case['replacement']
            self.assertFalse(node_join.ed25519_verify(public, edge.transcript(value), signature), case['field'])
            seen.add(case['field'])
        self.assertEqual(set(edge.FIELDS), seen)

    def test_transport_rejects_duplicates_padding_unknown_fields_and_bad_lengths(self):
        value = self.vectors['known_answers'][0]
        with self.assertRaises(ValueError):
            edge.decode_header(value['header'] + '=')
        original = json.dumps(value['envelope'], separators=(',', ':'))
        duplicate = original[:-1] + ',"subject":"attacker"}'
        with self.assertRaises(ValueError):
            edge.decode_header(edge.b64url(duplicate.encode()))
        for mutate in [lambda c:c.update(tenant='foreign'), lambda c:c.update(signature='AA'),
                       lambda c:c.update(nonce='AA'), lambda c:c.update(version=2),
                       lambda c:c.update(issued_at_unix_ms=True),
                       lambda c:c.update(issued_at_unix_ms=1.0)]:
            claim = copy.deepcopy(value['envelope']); mutate(claim)
            with self.assertRaises(ValueError):
                edge.decode_header(edge.b64url(json.dumps(claim).encode()))

    def test_json_order_is_not_part_of_signature(self):
        value = self.vectors['known_answers'][1]
        reversed_claim = dict(reversed(list(value['envelope'].items())))
        self.assertEqual(bytes.fromhex(value['transcript_hex']), edge.transcript(reversed_claim))
        self.assertEqual(reversed_claim, edge.decode_header(edge.b64url(json.dumps(reversed_claim).encode())))

    def test_document_schema_and_frozen_transcript_agree(self):
        text = (ROOT / 'specs/55_ALIAS_EDGE_DELEGATION.md').read_text()
        schema = json.loads((ROOT / 'schemas/v1/aliases/edge-assertion.json').read_text())
        for number, field in enumerate(edge.FIELDS, 1):
            self.assertIn(f'{number}. `{field}`', text)
        self.assertEqual(set(edge.FIELDS) | {'version','signature'}, set(schema['required']))
        self.assertEqual(set(schema['required']), set(schema['properties']))
        self.assertEqual(self.vectors['fields'], list(edge.FIELDS))
        self.assertEqual('owed', self.vectors['operational_proof_status'])


if __name__ == '__main__':
    unittest.main()
