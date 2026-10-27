"""Spec64 optional assignment identity suffixes preserve legacy known answers."""
import copy
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from conformance import dynamic_nodes

ROOT = Path(__file__).resolve().parents[2]
VECTORS = ROOT / "conformance/dynamic-node-vectors.json"
LEGACY = {
    "serve": "dep_2dbde03f1caf05686818da3ade04a6ced7853aedea6ac3021d76e27d38c94e44",
    "measure": "dep_6866ef335f03f489914a99313941c3b16b2be92b8cad743439c2f851aa26019e",
    "serve-with-env-privileges-mounts-shm": "dep_6c0ec71feede12a8789bccda8a8d345b7ec27547af8c074e5bef58987b8c615f",
}
OPTIONAL = {"serve-with-entrypoint", "serve-with-served-model", "serve-with-gpu-binding",
            "serve-with-all-optional-suffixes-in-order"}


class DynamicNodeIdentity(unittest.TestCase):
    def setUp(self):
        self.vectors = json.loads(VECTORS.read_text())
        self.base = self.vectors["base"]

    def test_known_answers_and_relations(self):
        self.assertEqual(dynamic_nodes.check_vectors(ROOT), [])
        answers = {case["id"]: case["expect"] for case in self.vectors["knownAnswers"]}
        self.assertTrue(OPTIONAL <= answers.keys())
        for name, expected in LEGACY.items():
            self.assertEqual(answers[name], expected)

    def test_absent_and_explicit_null_preserve_legacy(self):
        change = {"launch": {"entrypoint": None},
                  "profile": {"servedModel": None, "gpuBinding": None}}
        self.assertEqual(dynamic_nodes.deployment_id(*dynamic_nodes._apply(self.base, change)),
                         LEGACY["serve"])

    def test_present_empty_is_encoded_independently_of_validation(self):
        for change in ({"launch": {"entrypoint": ""}}, {"profile": {"servedModel": ""}}):
            self.assertNotEqual(dynamic_nodes.deployment_id(*dynamic_nodes._apply(self.base, change)),
                                LEGACY["serve"])

    def test_domains_do_not_alias_identical_values(self):
        entrypoint = dynamic_nodes._apply(self.base, {"launch": {"entrypoint": "same-value"}})
        model = dynamic_nodes._apply(self.base, {"profile": {"servedModel": "same-value"}})
        self.assertNotEqual(dynamic_nodes.deployment_id(*entrypoint),
                            dynamic_nodes.deployment_id(*model))

    def test_combined_order_is_independent_of_json_insertion_order(self):
        case = next(case for case in self.vectors["knownAnswers"]
                    if case["id"] == "serve-with-all-optional-suffixes-in-order")
        model, profile, artifacts, advert = dynamic_nodes._apply(self.base, case["change"])
        profile = dict(reversed(list(profile.items())))
        profile["launch"] = dict(reversed(list(profile["launch"].items())))
        self.assertEqual(dynamic_nodes.deployment_id(model, profile, artifacts, advert),
                         case["expect"])

    def test_omitting_any_suffix_is_detected_by_vectors(self):
        encode = dynamic_nodes.deployment_id
        for field, case_id in (("entrypoint", "serve-with-entrypoint"),
                               ("servedModel", "serve-with-served-model"),
                               ("gpuBinding", "serve-with-gpu-binding")):
            def stripped(model, profile, artifacts, advert):
                profile = copy.deepcopy(profile)
                target = profile["launch"] if field == "entrypoint" else profile
                target.pop(field, None)
                return encode(model, profile, artifacts, advert)
            with patch.object(dynamic_nodes, "deployment_id", side_effect=stripped):
                errors = dynamic_nodes.check_vectors(ROOT)
            self.assertTrue(any(f"vector {case_id}:" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
