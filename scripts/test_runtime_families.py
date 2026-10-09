import copy
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "schemas/v1/model/capabilities.json").read_text())
MODEL = json.loads((ROOT / "schemas/v1/model/model.json").read_text())
SPEC = (ROOT / "specs/48_RUNTIME_FAMILIES_AND_CAPABILITIES.md").read_text()
OPENAPI = (ROOT / "openapi/inferweave-v1.yaml").read_text()


def check(value, schema):
    """Minimal draft-07 subset: type, enum, required, items, min/uniqueItems."""
    errors = []
    types = schema.get("type")
    if types is not None:
        names = types if isinstance(types, list) else [types]
        pytypes = {"object": dict, "array": list, "string": str, "number": (int, float), "boolean": bool, "null": type(None)}
        if not any(isinstance(value, pytypes[n]) for n in names):
            return ["type"]
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"enum:{value!r}")
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"required:{key}")
        for key, sub in schema.get("properties", {}).items():
            if key in value:
                errors += [f"{key}.{e}" for e in check(value[key], sub)]
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            errors.append("minItems")
        if schema.get("uniqueItems") and len(set(map(json.dumps, value))) != len(value):
            errors.append("uniqueItems")
        for item in value:
            errors += check(item, schema.get("items", {}))
    return errors


def admit(advert, schema=SCHEMA):
    """Admission = base schema plus the typed_admission requirement."""
    return check(advert, schema) + check(advert, schema["$defs"]["typed_admission"])


EMBEDDINGS = {
    "family": "embeddings",
    "input_modalities": ["text", "image"],
    "output_modalities": ["vector"],
    "quality": {"metric": "embedding_dimension", "value": 1024, "basis": "self-reported"},
    "context": None,
    "runtime_preference": ["vllm", "llama.cpp"],
}


class RuntimeFamilyTests(unittest.TestCase):
    def test_typed_capability_round_trip(self):
        advert = copy.deepcopy(EMBEDDINGS)
        self.assertEqual(admit(advert), [])
        self.assertEqual(json.loads(json.dumps(advert)), EMBEDDINGS)

    def test_name_derived_rejection(self):
        advert = {"model_id": "text-embedding-3-large", "chat": False}
        errors = admit(advert)
        self.assertIn("required:family", errors)
        self.assertIn("required:input_modalities", errors)

    def test_registry_closure(self):
        advert = dict(EMBEDDINGS, family="quantum")
        self.assertTrue(any(e.startswith("family.enum") for e in admit(advert)))
        model = check({"model_id": "m", "type": "other", "family": "quantum"}, MODEL)
        self.assertTrue(any(e.startswith("family.enum") for e in model))

    def test_registry_closure_fails_without_control(self):
        weakened = copy.deepcopy(SCHEMA)
        del weakened["properties"]["family"]["enum"]
        self.assertEqual(admit(dict(EMBEDDINGS, family="quantum"), weakened), [])

    def test_quality_requires_basis(self):
        advert = dict(EMBEDDINGS, quality={"metric": "wer", "value": 0.1})
        self.assertIn("quality.required:basis", admit(advert))

    def test_registries_agree(self):
        families = SCHEMA["properties"]["family"]["enum"]
        self.assertEqual(families, MODEL["properties"]["family"]["enum"])
        for family in families:
            self.assertIn(f"| `{family}`", SPEC)
        self.assertIn("TypedCapabilities", OPENAPI)
        self.assertIn(f"enum: [{', '.join(families)}]", OPENAPI)


if __name__ == "__main__":
    unittest.main()
