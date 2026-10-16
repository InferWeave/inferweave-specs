"""System One capacity wire (specs 44/47/59): schema-level checks; production proof remains owed."""
import json
import sys
import unittest
from pathlib import Path

from jsonschema import Draft7Validator, RefResolver

ROOT = Path(__file__).resolve().parents[2]
STORE = {}
for path in (ROOT / 'schemas/v1').rglob('*.json'):
    schema = json.loads(path.read_text())
    STORE[schema['$id']] = schema


def check(name, value):
    schema = STORE[f'https://inferweave.dev/schemas/v1/requests/{name}.json']
    Draft7Validator(schema, resolver=RefResolver.from_schema(schema, store=STORE)).validate(value)


def valid(name, value):
    try:
        check(name, value)
        return True
    except Exception:
        return False


def semantic_advert_ok(advert):
    """The rule JSON Schema cannot express: max_concurrency >= slots when present."""
    return valid('node-systemone-advert', advert) and advert.get('max_concurrency', advert['slots']) >= advert['slots']


class SystemOneWire(unittest.TestCase):
    def test_advert_optional_members_and_semantic_bound(self):
        self.assertTrue(semantic_advert_ok({'model': 'laya-x', 'slots': 4}))
        self.assertTrue(semantic_advert_ok({'model': 'laya-x', 'slots': 4, 'device': 'cpu', 'max_concurrency': 16}))
        self.assertFalse(semantic_advert_ok({'model': 'laya-x', 'slots': 4, 'max_concurrency': 3}))
        for bad in ({'model': 'x', 'slots': 0}, {'model': '', 'slots': 1}, {'model': 'x', 'slots': 1, 'device': 'CPU'},
                    {'model': 'x', 'slots': 1, 'device': ''}, {'model': 'x', 'slots': 1, 'device': 'cpu\n'}):
            with self.subTest(bad=bad):
                self.assertFalse(valid('node-systemone-advert', bad))

    def test_status_is_camel_case_and_snake_case_is_not_it(self):
        good = {'inflight': 1, 'queueDepth': 0, 'maxConcurrency': 16, 'readyProcesses': 4, 'processes': 4}
        self.assertTrue(valid('node-systemone-status', good))
        snake = {'inflight': 1, 'queue_depth': 0, 'max_concurrency': 16, 'ready_processes': 4, 'processes': 4}
        self.assertFalse(valid('node-systemone-status', snake))

    def test_register_and_link_meta_carry_the_new_members(self):
        body = {'nodeId': 'n', 'role': 'node', 'credential': 'c', 'endpoint': '', 'models': [], 'deployment': '',
                'systemone': [{'model': 'm', 'slots': 2, 'device': 'cpu', 'max_concurrency': 8}],
                'hardware': {'version': 1, 'gpus': []}}
        self.assertTrue(valid('node-register', body))
        body['systemone'] = [{'model': 'm', 'slots': 0}]
        self.assertFalse(valid('node-register', body))
        self.assertTrue(valid('link-request-meta', {'systemone_batch': True}))
        self.assertFalse(valid('link-request-meta', {'systemone_batch': 'yes'}))

    def test_cpu_is_a_frozen_device_type(self):
        self.assertIn('cpu', json.loads((ROOT / 'contracts/protocol-v1/device-types.json').read_text())['values'])


if __name__ == '__main__':
    unittest.main()
