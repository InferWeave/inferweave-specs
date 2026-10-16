"""Golden and hostile offline checks of the spec 63 upstream-role frames. Production proof remains owed."""
import copy
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'conformance'))

import link_upstream  # noqa: E402
from link_upstream import (  # noqa: E402
    ABSENT, KIND_SCHEMA, decode_frame, dialer_accepts_ack, effective_class, request_with_class, semantic_errors,
    validate,
)
from link_http_json import request_valid  # noqa: E402

CONTRACT = json.loads((ROOT / 'contracts/protocol-v1/link-upstream.json').read_text())
VECTORS = json.loads((ROOT / 'conformance/link-upstream-vectors.json').read_text())


def load(rel):
    return json.loads((ROOT / rel).read_text())


def valid_fixtures():
    return sorted((ROOT / 'fixtures/valid').glob('link-upstream-*.json'))


def invalid_fixtures():
    return sorted((ROOT / 'fixtures/invalid').glob('link-upstream-*.json'))


class LinkUpstream(unittest.TestCase):
    def test_vectors_agree_and_are_not_vacuous(self):
        self.assertEqual(link_upstream.check_vectors(ROOT), [])
        self.assertGreaterEqual(len(VECTORS['wire_cases']), 20)
        self.assertTrue(any(not c['valid'] for c in VECTORS['wire_cases']))
        self.assertTrue(any(c['valid'] for c in VECTORS['wire_cases']))

    def test_duplicate_member_vectors_are_refused_by_the_strict_decoder(self):
        # json.loads keeps the LAST duplicate, so a frame whose first member is harmless and whose last is
        # not would pass a lenient decoder; each such vector must be refused before schema validation.
        names = [c['name'] for c in VECTORS['wire_cases'] if 'duplicate' in c['name'] and 'model_id' not in c['name']]
        self.assertGreaterEqual(len(names), 8)
        for case in VECTORS['wire_cases']:
            if case['name'] in names:
                with self.subTest(case=case['name']), self.assertRaises(ValueError):
                    link_upstream.strict_json(case['wire'])
                with self.subTest(case=case['name'], decoder='lenient'):
                    json.loads(case['wire'])  # the same text is well-formed JSON for a last-wins decoder

    def test_every_valid_fixture_validates_and_every_invalid_one_is_refused(self):
        self.assertGreaterEqual(len(valid_fixtures()), 10)
        self.assertGreaterEqual(len(invalid_fixtures()), 50)
        for path in valid_fixtures():
            with self.subTest(path=path.name):
                decode_frame(path.read_text())
        for path in invalid_fixtures():
            with self.subTest(path=path.name), self.assertRaises(Exception):
                decode_frame(path.read_text())

    def test_the_schema_alone_refuses_every_invalid_fixture_but_the_duplicate_model_id(self):
        # Removing the semantic rule must change exactly the one fixture it exists for.
        with patch('link_upstream.semantic_errors', return_value=[]):
            accepted = []
            for path in invalid_fixtures():
                try:
                    decode_frame(path.read_text())
                    accepted.append(path.name)
                except Exception:
                    pass
        self.assertEqual(accepted, ['link-upstream-catalog-duplicate-model-id.json'])

    def test_the_upstream_hello_is_also_a_valid_open_hello_and_legacy_hellos_still_are(self):
        hello = load('fixtures/valid/link-upstream-hello.json')
        validate('link-hello', hello)
        for name in ('link-hello-legacy', 'link-hello-native-v1', 'link-hello-native-response-v1'):
            validate('link-hello', load(f'fixtures/valid/{name}.json'))
        # An api_key Hello has no registration to bind to, and the open schema still refuses the shapes
        # the role forbids.
        for change in (
            lambda h: h.update(registration_connection_id='c-0123456789abcdef'),
            lambda h: h.update(link_roles=['serve', 'upstream']),
            lambda h: h.pop('channel_binding'),
            lambda h: h.pop('link_roles'),
            lambda h: h.update(channel_binding='AB' * 32),
        ):
            bad = copy.deepcopy(hello)
            change(bad)
            with self.subTest(change=bad), self.assertRaises(Exception):
                validate('link-hello', bad)
        # A registration Hello can never carry the upstream role or a channel binding.
        registration = load('fixtures/valid/link-hello-native-v1.json')
        for member, value in (('link_roles', ['upstream']), ('channel_binding', '0' * 64)):
            bad = copy.deepcopy(registration)
            bad[member] = value
            with self.subTest(member=member), self.assertRaises(Exception):
                validate('link-hello', bad)
        ok = copy.deepcopy(registration)
        ok['link_roles'] = ['serve']
        ok['credential_type'] = 'registration'
        validate('link-hello', ok)

    def test_the_spec59_oracle_knows_traffic_class(self):
        for declared in ('private', 'shareable', 'volunteer', '', 'x' * 32):
            frame = request_with_class(declared)
            self.assertEqual(request_valid(frame), frame['payload'].encode())
        self.assertEqual(request_valid(request_with_class(ABSENT)), request_with_class(ABSENT)['payload'].encode())
        for declared in ('x' * 33, True, 1, None, ['private']):
            with self.subTest(declared=declared), self.assertRaises(Exception):
                request_valid(request_with_class(declared))
        # The bound is the same in the open meta schema as in the closed request.
        open_meta = load('schemas/v1/requests/link-request-meta.json')['properties']['traffic_class']
        closed = load('schemas/v1/requests/link-http-request.json')['properties']['meta']['properties']['traffic_class']
        self.assertEqual(open_meta['maxLength'], closed['maxLength'])
        self.assertEqual(closed['maxLength'], CONTRACT['traffic_class_max_bytes'])

    def test_class_order_never_loosens_the_ceiling(self):
        for declared in ('private', 'shareable', None, 'volunteer', ''):
            self.assertEqual(effective_class(declared, 'private'), 'private')
        self.assertEqual(effective_class('shareable', 'shareable'), 'shareable')
        for declared in (None, 'volunteer', '', 'PRIVATE', 'Shareable'):
            self.assertEqual(effective_class(declared, 'shareable'), 'private')

    def test_ack_pairing_needs_the_same_dials_ids_and_never_grants_serve(self):
        hello = load('fixtures/valid/link-upstream-hello.json')
        ack = load('fixtures/valid/link-upstream-hello-ack.json')
        self.assertTrue(dialer_accepts_ack(hello, ack))
        for change in (
            lambda a: a.update(link_incarnation_id='link-incarnation-upstream-0002'),
            lambda a: a.update(granted_roles=['serve']),
            lambda a: a.update(granted_roles=['serve', 'upstream']),
            lambda a: a.update(upstream_binding_id='ub-1'),
            lambda a: a.pop('upstream_binding_id'),
            lambda a: a.update(kind='hello_ack'),
        ):
            bad = copy.deepcopy(ack)
            change(bad)
            with self.subTest(change=bad):
                self.assertFalse(dialer_accepts_ack(hello, bad))

    def test_contract_agrees_with_the_schemas_and_the_spec(self):
        refused = load('schemas/v1/requests/link-upstream-refused.json')['properties']['code']['enum']
        self.assertEqual(refused, CONTRACT['refusal_codes'])
        self.assertTrue(set(CONTRACT['reversible_refusal_codes']) <= set(refused))
        spec = (ROOT / 'specs/63_LINK_UPSTREAM_ROLE_AND_AUTHENTICATED_GATEWAYS.md').read_text()
        for code in refused:
            self.assertIn(f'`{code}`', spec)
        catalog = load('schemas/v1/requests/link-upstream-catalog.json')
        self.assertEqual(catalog['properties']['models']['maxItems'], CONTRACT['max_catalog_entries'])
        self.assertEqual(
            catalog['properties']['models']['items']['properties']['provenance']['const'], CONTRACT['catalog_provenance'])
        self.assertEqual(
            load('schemas/v1/requests/link-upstream-hello-ack.json')['properties']['principal_label']['maxLength'],
            CONTRACT['max_principal_label_length'])
        for name, rel in CONTRACT['frames'].items():
            self.assertTrue((ROOT / rel).is_file(), rel)
            self.assertIn(name, KIND_SCHEMA)
        self.assertIn(f"`{CONTRACT['capability']}`", spec)

    def test_a_catalog_listing_a_model_twice_is_semantically_refused_not_schema_refused(self):
        frame = load('fixtures/invalid/link-upstream-catalog-duplicate-model-id.json')
        validate('link-upstream-catalog', frame)
        self.assertEqual(semantic_errors(frame), ['catalog lists a model id twice'])


if __name__ == '__main__':
    unittest.main()
