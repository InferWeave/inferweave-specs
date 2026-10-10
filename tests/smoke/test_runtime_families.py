"""Smoke: canonical runtime-family registry and typed capability descriptor (spec 48, B-T01)."""

import copy
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
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
        assert admit(advert) == []
        assert json.loads(json.dumps(advert)) == EMBEDDINGS

    def test_name_derived_rejection(self):
        advert = {"model_id": "text-embedding-3-large", "chat": False}
        errors = admit(advert)
        assert "required:family" in errors
        assert "required:input_modalities" in errors

    def test_registry_closure(self):
        advert = dict(EMBEDDINGS, family="quantum")
        assert any(e.startswith("family.enum") for e in admit(advert))
        model = check({"model_id": "m", "type": "other", "family": "quantum"}, MODEL)
        assert any(e.startswith("family.enum") for e in model)

    def test_registry_closure_fails_without_control(self):
        weakened = copy.deepcopy(SCHEMA)
        del weakened["properties"]["family"]["enum"]
        assert admit(dict(EMBEDDINGS, family="quantum"), weakened) == []

    def test_quality_requires_basis(self):
        advert = dict(EMBEDDINGS, quality={"metric": "wer", "value": 0.1})
        assert "quality.required:basis" in admit(advert)

    def test_registries_agree(self):
        families = SCHEMA["properties"]["family"]["enum"]
        assert families == MODEL["properties"]["family"]["enum"]
        for family in families:
            assert f"| `{family}`" in SPEC
        assert "TypedCapabilities" in OPENAPI
        assert f"enum: [{', '.join(families)}]" in OPENAPI


if __name__ == "__main__":
    unittest.main()
