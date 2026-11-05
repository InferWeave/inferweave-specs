#!/usr/bin/env python3
"""Offline vocabulary and half-open overlap vectors; not implementation proof."""
import copy
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = json.loads((ROOT / 'contracts/benchmark-speed-execution.json').read_text())
SCHEMA = json.loads((ROOT / 'schemas/v1/benchmark-speed-execution-contract.json').read_text())
VECTORS = json.loads((ROOT / 'conformance/benchmark-speed/overlap-vectors.json').read_text())


def positive_overlap(intervals, requested):
    events = []
    for start, end in intervals:
        if end <= start:
            raise ValueError('interval must have positive duration')
        events.extend(((start, 1), (end, -1)))
    active = 0
    previous = None
    for time, change in sorted(events):  # -1 ends precede +1 starts on ties
        if previous is not None and time > previous and active >= requested:
            return True
        active += change
        previous = time
    return False


class ContractTests(unittest.TestCase):
    def test_frozen_shape_and_mutations(self):
        Draft202012Validator.check_schema(SCHEMA)
        validator = Draft202012Validator(SCHEMA)
        self.assertFalse(list(validator.iter_errors(CONTRACT)))
        for field, value in [('coverage_version', 1), ('calibration_max_calls', 5),
                             ('backend_generating_concurrency', 'measured')]:
            mutated = copy.deepcopy(CONTRACT)
            mutated[field] = value
            self.assertTrue(list(validator.iter_errors(mutated)), field)
        mutated = copy.deepcopy(CONTRACT)
        mutated['acceptance'][0]['proof_status'] = 'proven'
        self.assertTrue(list(validator.iter_errors(mutated)))
        mutated = copy.deepcopy(CONTRACT)
        mutated['authority_override'] = True
        self.assertTrue(list(validator.iter_errors(mutated)))

    def test_every_wave_and_tie_vectors(self):
        for vector in VECTORS['vectors']:
            with self.subTest(vector=vector['id']):
                result = all(positive_overlap(w, vector['requested']) for w in vector['waves'])
                self.assertEqual(vector['expected'], result)
        with self.assertRaises(ValueError):
            positive_overlap([[2, 2]], 1)


if __name__ == '__main__':
    unittest.main()
