"""Offline tool contract guards; no model, gateway or production qualification proof."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "conformance"))
import node_join
import runner

FIXTURE = json.loads((ROOT / "fixtures/tool-compatibility/known-answer.json").read_text())
CONTRACT = json.loads((ROOT / "contracts/tool-call-compatibility.json").read_text())


def field(value):
    raw = value.encode("utf-8")
    return struct.pack(">I", len(raw)) + raw


def number(value):
    return struct.pack(">Q", value)


def strings(values):
    values = sorted(set(values))
    return struct.pack(">I", len(values)) + b"".join(map(field, values))


def binding_transcript(binding):
    result = b"".join(field(binding[k]) for k in (
        "ownerGatewayId", "registrationIncarnation", "nodeId", "instanceId",
        "deploymentFingerprint", "generation", "sourceEpoch"))
    result += strings(binding["requiredGpuIds"])
    cohort = binding["cohort"]
    result += b"".join(field(cohort[k]) for k in (
        "model", "modelRevision", "tokenizerRevision", "quantization",
        "runtimeImplementationId", "runtimeVersion", "hardwareFingerprint"))
    result += b"".join(number(cohort[k]) for k in (
        "contextTokens", "concurrency", "outputTokens"))
    result += field(cohort["cacheRegime"])
    return result + b"".join(field(binding[k]) for k in (
        "profileSha256", "imageDigest", "artifactsSha256", "templateSha256",
        "parserFamily", "backend"))


def report_transcript(report):
    result = field("inferweave.tool-suite-report/v1") + number(report["schemaVersion"])
    result += field(report["suiteVersion"]) + number(report["repetitions"])
    binding = report.get("binding")
    result += b"\x00" if binding is None else b"\x01" + binding_transcript(binding)
    result += struct.pack(">I", len(report["attempts"]))
    for attempt in report["attempts"]:
        result += field(attempt["caseId"]) + number(attempt["repetition"])
        result += b"".join(field(attempt[k]) for k in ("path", "scope", "outcome"))
        reason = attempt.get("reason")
        result += b"\x00" if reason is None else b"\x01" + field(reason)
    return result


def qualification_transcript(body):
    result = field("inferweave.tool-qualification/v1") + number(body["schemaVersion"])
    result += b"".join(field(body[k]) for k in ("verifierId", "keyId", "purpose"))
    result += b"".join(number(body[k]) for k in (
        "policyRevision", "issuedAtMs", "notBeforeMs", "expiresAtMs"))
    result += binding_transcript(body["binding"])
    result += b"".join(field(body[k]) for k in ("suiteVersion", "reportId", "reportSha256"))
    return result + strings(body["operations"]) + number(body["repetitions"])


def protocol_subset(report, minimum=3):
    """Offline model of the minimum subset; never a qualification issuer."""
    if list(runner.validator("runtime/tool-suite-report.json").iter_errors(report)):
        return False
    if report.get("binding") is None or report["repetitions"] < minimum:
        return False
    attempts = report["attempts"]
    keys = {(a["caseId"], a["path"], a["repetition"]) for a in attempts}
    if len(keys) != len(attempts) or any(
        a["repetition"] > report["repetitions"] or a["outcome"] == "fail" for a in attempts
    ):
        return False
    required = CONTRACT["qualification"]["requiredCases"]
    for repetition in range(1, report["repetitions"] + 1):
        for path, cases in required.items():
            for case in cases:
                if not any(a["caseId"] == case and a["path"] == path
                           and a["repetition"] == repetition and a["scope"] == "actualModel"
                           and a["outcome"] == "pass" and a.get("reason") is None
                           for a in attempts):
                    return False
    return True


class ToolCompatibilityContract(unittest.TestCase):
    def check_schema(self, name, value, valid=True):
        errors = list(runner.validator("runtime/" + name + ".json").iter_errors(value))
        self.assertEqual(not errors, valid, [e.message for e in errors])

    def test_known_shapes_and_all_nested_objects_are_closed(self):
        pairs = [
            ("tool-calling", FIXTURE["profile"]),
            ("tool-execution-binding", FIXTURE["report"]["binding"]),
            ("tool-suite-report", FIXTURE["report"]),
            ("tool-qualification", FIXTURE["record"]),
            ("tool-trust-policy", FIXTURE["policy"]),
            ("tool-qualification-snapshot", FIXTURE["snapshot"]),
        ]
        for schema, value in pairs:
            with self.subTest(schema=schema):
                self.check_schema(schema, value)
                mutant = deepcopy(value)
                mutant["futureAuthority"] = True
                self.check_schema(schema, mutant, False)
        mutant = deepcopy(FIXTURE["report"])
        mutant["binding"]["cohort"]["verified"] = True
        self.check_schema("tool-suite-report", mutant, False)

    def test_transcripts_match_rust_known_answers_and_signature(self):
        report = report_transcript(FIXTURE["report"])
        self.assertEqual(sha256(report).hexdigest(), FIXTURE["expected"]["reportSha256"])
        transcript = qualification_transcript(FIXTURE["record"]["body"])
        self.assertEqual(len(transcript), 800)
        self.assertEqual("tq1-" + sha256(transcript).hexdigest(), FIXTURE["expected"]["qualificationId"])
        public = bytes.fromhex(FIXTURE["policy"]["keys"][0]["publicKey"])
        signature = bytes.fromhex(FIXTURE["record"]["signature"])
        self.assertTrue(node_join.ed25519_verify(public, transcript, signature))
        self.assertFalse(node_join.ed25519_verify(public, transcript + b"x", signature))

    def test_signature_covers_each_identity_time_and_operation(self):
        original = qualification_transcript(FIXTURE["record"]["body"])
        for key in FIXTURE["record"]["body"]["binding"]:
            mutant = deepcopy(FIXTURE["record"]["body"])
            value = mutant["binding"][key]
            if isinstance(value, str):
                mutant["binding"][key] += "x"
            elif isinstance(value, list):
                mutant["binding"][key].append("gpu-c")
            else:
                mutant["binding"][key]["runtimeVersion"] += "x"
            self.assertNotEqual(qualification_transcript(mutant), original, key)
        for key in ("issuedAtMs", "notBeforeMs", "expiresAtMs", "policyRevision", "repetitions"):
            mutant = deepcopy(FIXTURE["record"]["body"])
            mutant[key] += 1
            self.assertNotEqual(qualification_transcript(mutant), original, key)
        mutant = deepcopy(FIXTURE["record"]["body"])
        mutant["operations"].append("parallel")
        self.assertNotEqual(qualification_transcript(mutant), original)

    def test_semantic_hash_ignores_json_order_but_binds_attempt_order_and_presence(self):
        report = FIXTURE["report"]
        original = report_transcript(report)
        self.assertEqual(original, report_transcript(json.loads(json.dumps(report, sort_keys=True))))
        mutant = deepcopy(report)
        mutant["attempts"].reverse()
        self.assertNotEqual(original, report_transcript(mutant))
        mutant = deepcopy(report)
        mutant["binding"] = None
        self.assertNotEqual(original, report_transcript(mutant))
        mutant = deepcopy(report)
        mutant["attempts"][0]["reason"] = "pending"
        self.assertNotEqual(original, report_transcript(mutant))

    def test_sets_sort_wire_tokens_and_utf8_uses_byte_length(self):
        body = deepcopy(FIXTURE["record"]["body"])
        original = qualification_transcript(body)
        body["operations"].reverse()
        body["binding"]["requiredGpuIds"].reverse()
        self.assertEqual(original, qualification_transcript(body))
        self.assertEqual(field("工具")[:4], struct.pack(">I", 6))

    def test_actual_model_subset_rejects_missing_failed_synthetic_and_duplicate_evidence(self):
        good = FIXTURE["report"]
        self.assertTrue(protocol_subset(good))
        for scope in ("syntheticTransport", "physicalLifecycle"):
            mutant = deepcopy(good)
            mutant["attempts"][0]["scope"] = scope
            self.assertFalse(protocol_subset(mutant))
        for index in range(len(good["attempts"])):
            mutant = deepcopy(good)
            del mutant["attempts"][index]
            self.assertFalse(protocol_subset(mutant), index)
        for outcome, reason in (("fail", "nativeMarkupLeak"), ("unsupported", "unsupportedCapability"), ("owed", "pending")):
            mutant = deepcopy(good)
            mutant["attempts"][0].update(outcome=outcome, reason=reason)
            self.assertFalse(protocol_subset(mutant))
        mutant = deepcopy(good)
        mutant["attempts"].append(deepcopy(mutant["attempts"][0]))
        self.assertFalse(protocol_subset(mutant))
        mutant = deepcopy(good)
        mutant["binding"] = None
        self.assertFalse(protocol_subset(mutant))
        self.assertFalse(protocol_subset(good, 4))

    def test_forced_choice_and_future_vocabulary_cannot_qualify(self):
        mutant = deepcopy(FIXTURE["record"])
        mutant["body"]["operations"].append("forcedChoice")
        self.check_schema("tool-qualification", mutant, False)
        for field_name, value in (("scope", "reported"), ("outcome", "verified"), ("reason", "qualified")):
            mutant = deepcopy(FIXTURE["report"])
            mutant["attempts"][0][field_name] = value
            self.check_schema("tool-suite-report", mutant, False)

    def test_bounds_versions_and_unsupported_profile(self):
        for field_name, value in (("repetitions", 0), ("repetitions", 33), ("schemaVersion", 2), ("suiteVersion", "2")):
            mutant = deepcopy(FIXTURE["report"])
            mutant[field_name] = value
            self.check_schema("tool-suite-report", mutant, False)
        unsupported = {"schemaVersion": 1, "mode": "unsupported", "engineRevision": "other"}
        self.check_schema("tool-calling", unsupported)
        unsupported["support"] = ["streaming"]
        self.check_schema("tool-calling", unsupported, False)
        mutant = deepcopy(FIXTURE["profile"])
        mutant["engineRevision"] = "unknown-engine"
        self.check_schema("tool-calling", mutant, False)
        mutant["engineRevision"] = CONTRACT["nativeConfiguration"]["backportBase"]
        self.check_schema("tool-calling", mutant, False)
        mutant["parserPatchSha256"] = CONTRACT["nativeConfiguration"]["backportPatchSha256"]
        self.check_schema("tool-calling", mutant)
        mutant["template"]["sha256"] = "e" * 64
        self.check_schema("tool-calling", mutant, False)

    def test_existing_admin_urls_and_strict_tool_trust_authority_are_frozen(self):
        self.assertEqual(CONTRACT["admin"]["reload"],
                         "POST /v1/admin/routes/reload?tool_qualifications=true")
        self.assertEqual(CONTRACT["admin"]["context"],
                         "GET /iw/v1/routes/explain?model=<id>&tool_qualification_context=true")
        self.assertIn("Caller::Admin only", CONTRACT["admin"]["authentication"])
        spec = (ROOT / "specs/56_RUNTIME_INSTANCE_OBSERVATIONS.md").read_text()
        self.assertIn("`POST /v1/admin/routes/reload?tool_qualifications=true`", spec)
        self.assertNotIn("POST /iw/v1/routes/reload?tool_qualifications=true", spec)

    def test_admission_refusal_is_separate_from_diagnostic_vocabulary(self):
        admission = CONTRACT["admissionError"]
        self.assertEqual(admission["httpStatus"], 503)
        self.assertEqual(admission["code"], "tool_capability_unavailable")
        self.assertNotIn(admission["code"], CONTRACT["vocabulary"]["reason"])
        self.assertIn("before indefinite queueing or automatic acquisition", admission["behavior"])

    def test_dynamic_fingerprint_has_distinct_domain_and_legacy_u64_string_framing(self):
        extension = CONTRACT["dynamicFingerprintExtension"]
        self.assertEqual(extension["domain"], "iw.runtime-tool-calling/1")
        self.assertEqual(extension["order"], [
            "S(domain)", "N(schemaVersion)", "S(modeWire)", "S(engineRevision)",
            "optional parserPatchSha256:S", "optional parser:S(wireToken)",
            "optional reasoning:S(wireToken)", "optional template:S(path)+S(sha256)",
            "N(supportCount)", "S(eachSortedSupportWireToken)",
        ])
        self.assertTrue(extension["encoding"]["S"].startswith("u64 big-endian"))
        self.assertTrue(CONTRACT["transcript"]["encoding"]["string"].startswith("u32 big-endian"))
        self.assertIn("Absent toolCalling appends zero bytes", extension["presence"])

    def test_snapshot_default_is_off_and_on_requires_explicit_models(self):
        schema = json.loads((ROOT / "schemas/v1/runtime/tool-compatibility.json").read_text())
        self.assertEqual(schema["definitions"]["policy"]["properties"]["mode"]["default"], "off")
        mutant = deepcopy(FIXTURE["snapshot"])
        del mutant["policy"]["mode"]
        self.check_schema("tool-qualification-snapshot", mutant)
        mutant["policy"].update(mode="on", models=[])
        self.check_schema("tool-qualification-snapshot", mutant, False)
        mutant = deepcopy(FIXTURE["snapshot"])
        mutant["expectedBindings"] *= 257
        self.check_schema("tool-qualification-snapshot", mutant, False)


if __name__ == "__main__":
    unittest.main()
