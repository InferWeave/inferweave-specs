#!/usr/bin/env python3
"""Regression test for runtime-family conformance vectors and runner coverage (specs/53, B-T06A)."""
import json
import threading
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VECTORS = ROOT / "conformance" / "runtime-family-vectors.json"
FAMILIES = ["embeddings", "reranking", "prediction", "stt", "rag"]


def run_runner(vectors_text=None):
    """Run the runner against an isolated vector copy so mutation tests cannot race."""
    with tempfile.TemporaryDirectory() as directory:
        vector_copy = Path(directory) / "runtime-family-vectors.json"
        vector_copy.write_text(vectors_text if vectors_text is not None else VECTORS.read_text())
        return subprocess.run(
            [
                sys.executable,
                str(ROOT / "conformance" / "runner.py"),
                "--runtime-family-vectors",
                str(vector_copy),
            ],
            capture_output=True,
            text=True,
            cwd=ROOT,
        )


class Conformance(unittest.TestCase):
    def test_sibling_schema_references_resolve_without_network(self):
        from conformance import runner
        fixture = json.loads((ROOT / "fixtures/valid/alias-link-request.json").read_text())
        try:
            with patch("jsonschema.validators.urlopen", side_effect=AssertionError("offline validation attempted network")):
                errors = list(runner.validator("requests/link-alias-request.json").iter_errors(fixture))
        except Exception as error:
            self.fail(f"bundled sibling references must resolve offline: {error}")
        self.assertEqual(errors, [])

    def test_root_reference_keeps_its_registered_retrieval_uri(self):
        from conformance import runner
        fixture = json.loads((ROOT / "fixtures/valid/dynamic-alias-adhoc-resolution.json").read_text())
        try:
            errors = list(runner.validator("aliases/adhoc-resolution.json").iter_errors(fixture))
        except Exception as error:
            self.fail(f"root $ref must resolve relative to its registered document URI: {error}")
        self.assertEqual(errors, [])

    def test_sibling_schema_validation_still_rejects_unknown_fields(self):
        from conformance import runner
        fixture = json.loads((ROOT / "fixtures/valid/alias-link-request.json").read_text())
        fixture["meta"]["executable"]["unrecognized"] = True
        with patch("jsonschema.validators.urlopen", side_effect=AssertionError("offline validation attempted network")):
            errors = list(runner.validator("requests/link-alias-request.json").iter_errors(fixture))
        self.assertTrue(errors, "local reference resolution must retain closed-schema validation")

    def test_family_vectors_present(self):
        doc = json.loads(VECTORS.read_text())
        for fam in FAMILIES:
            assert fam in doc["families"], fam
            assert doc["families"][fam]["advertisement"]["family"] == fam

    def test_native_smoke_vectors_present(self):
        doc = json.loads(VECTORS.read_text())
        for fam in FAMILIES:
            cases = doc["families"][fam]["nativeCases"]
            assert any(case["expectStatus"] < 400 for case in cases)
            assert any(case["expectStatus"] >= 400 for case in cases)

    def test_quality_uses_schema_basis_and_runner_rejects_source(self):
        doc = json.loads(VECTORS.read_text())
        quality = doc["families"]["embeddings"]["advertisement"]["quality"]
        assert set(quality) >= {"metric", "value", "basis"}
        quality.pop("basis")
        quality["source"] = "self-reported"
        res = run_runner(json.dumps(doc))
        assert res.returncode != 0
        assert "quality" in res.stdout

    def test_runner_reports_per_family(self):
        res = run_runner()
        assert res.returncode == 0, res.stdout + res.stderr
        for fam in FAMILIES:
            assert f"PASS  runtime-family {fam}" in res.stdout

    def test_runner_fails_when_family_vector_removed(self):
        doc = json.loads(VECTORS.read_text())
        del doc["families"]["rag"]
        res = run_runner(json.dumps(doc))
        assert res.returncode != 0
        assert "FAIL  runtime-family rag" in res.stdout

    def test_runner_fails_when_smoke_removed(self):
        doc = json.loads(VECTORS.read_text())
        del doc["families"]["stt"]["nativeCases"]
        res = run_runner(json.dumps(doc))
        assert res.returncode != 0
        assert "FAIL  runtime-family stt" in res.stdout

    def test_offline_runner_labels_native_cases_contract_only(self):
        res = run_runner()
        assert res.returncode == 0, res.stdout + res.stderr
        assert "native HTTP: NOT RUN" in res.stdout

    def test_optional_live_runner_executes_native_http_cases(self):
        vectors = json.loads(VECTORS.read_text())
        expected = {}
        for family in FAMILIES:
            for case in vectors["families"][family]["nativeCases"]:
                expected[(case["method"], case["path"], case["id"])] = case["expectStatus"]

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers.get("Content-Length", "0"))
                body = json.loads(self.rfile.read(length))
                case_id = self.headers["X-InferWeave-Conformance-Case"]
                status = expected[("POST", self.path, case_id)]
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"family": body.get("family"), "case": case_id}).encode())

            def log_message(self, _format, *_args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            base = f"http://127.0.0.1:{server.server_port}"
            res = subprocess.run(
                [sys.executable, str(ROOT / "conformance" / "runner.py"), "--live-base-url", base],
                capture_output=True,
                text=True,
                cwd=ROOT,
            )
        finally:
            server.shutdown()
            server.server_close()
            thread.join()
        assert res.returncode == 0, res.stdout + res.stderr
        assert "PASS  native HTTP" in res.stdout


if __name__ == "__main__":
    unittest.main()
