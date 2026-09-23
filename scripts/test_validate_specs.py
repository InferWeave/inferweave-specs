import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
ACTION_CONTRACT = "contracts/backpressure-action-codes.json"
VECTOR_CONTRACT = "contracts/backpressure-conformance-v1.json"
FROZEN_ACTIONS = {
    "IW-ACT-BACKOFF",
    "IW-ACT-REDUCE-CONCURRENCY",
    "IW-ACT-RETRY-ALTERNATE",
    "IW-ACT-FIX-REQUEST",
    "IW-ACT-AUTHENTICATE",
    "IW-ACT-REQUEST-ACCESS",
    "IW-ACT-RESOLVE-CONFLICT",
    "IW-ACT-REDUCE-INPUT",
    "IW-ACT-DO-NOT-RETRY",
}
ACTION_NAMES = {
    "IW-ACT-BACKOFF": "backoff",
    "IW-ACT-REDUCE-CONCURRENCY": "reduce_concurrency",
    "IW-ACT-RETRY-ALTERNATE": "retry_alternate",
    "IW-ACT-FIX-REQUEST": "fix_request",
    "IW-ACT-AUTHENTICATE": "authenticate",
    "IW-ACT-REQUEST-ACCESS": "request_access",
    "IW-ACT-RESOLVE-CONFLICT": "resolve_conflict",
    "IW-ACT-REDUCE-INPUT": "reduce_input",
    "IW-ACT-DO-NOT-RETRY": "do_not_retry",
}


def copy_repo(destination: Path) -> Path:
    repo = destination / "repo"
    shutil.copytree(
        ROOT,
        repo,
        ignore=shutil.ignore_patterns(".git", ".superpowers", "__pycache__"),
    )
    return repo


def validate(repo: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", "scripts/validate_specs.py"],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )


def load_json(repo: Path, relative_path: str):
    return json.loads((repo / relative_path).read_text())


def write_json(repo: Path, relative_path: str, value) -> None:
    (repo / relative_path).write_text(json.dumps(value, indent=2) + "\n")


def vector_error(case):
    return case["body"].get("error") or case["body"]["detail"]["error"]


class BackpressureContractTests(unittest.TestCase):
    def copied_repo(self, temporary_directory: str) -> Path:
        return copy_repo(Path(temporary_directory))

    def test_backpressure_actions_match_vectors_and_required_coverage(self):
        actions = load_json(ROOT, ACTION_CONTRACT)
        vectors = load_json(ROOT, VECTOR_CONTRACT)

        self.assertEqual(actions["name"], "backpressure_action_code")
        self.assertEqual(set(actions["values"]), FROZEN_ACTIONS)
        expected_actions = {
            case["expected"]["action_code"]
            for case in vectors["cases"]
            if case["expected"].get("action_code")
        }
        self.assertEqual(expected_actions, set(actions["values"]))
        for case in vectors["cases"]:
            action_code = case["expected"].get("action_code")
            if action_code:
                self.assertEqual(case["expected"]["action"], ACTION_NAMES[action_code])
        self.assertEqual(
            {400, 401, 403, 404, 408, 409, 413, 422, 429, 500, 502, 503, 504},
            {case["status"] for case in vectors["cases"]},
        )
        self.assertEqual(
            {"not_started", "queued", "dispatched", "streaming", "unknown"},
            {case["expected"].get("request_state") for case in vectors["cases"]},
        )
        self.assertTrue(any(case["legacy"] for case in vectors["cases"]))
        self.assertTrue(any("detail" in case["body"] for case in vectors["cases"]))
        self.assertTrue(
            any(
                case["headers"].get("Retry-After")
                and case["body"].get("error", {}).get("retry_after_ms")
                != int(case["headers"]["Retry-After"]) * 1000
                for case in vectors["cases"]
            )
        )
        self.assertTrue(
            any(
                case["expected"].get("retryable") is False
                and case["expected"].get("replay_safe") is False
                for case in vectors["cases"]
            )
        )
        self.assertTrue(
            any(
                case["expected"].get("action_code") is None
                and "IW-ACT-UNKNOWN" in json.dumps(case["body"])
                for case in vectors["cases"]
            )
        )
        self.assertTrue(any("</script>" in json.dumps(case["body"]) for case in vectors["cases"]))

    def test_undocumented_action_fails_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = self.copied_repo(directory)
            vectors = load_json(repo, VECTOR_CONTRACT)
            vectors["cases"][0]["expected"]["action_code"] = "IW-ACT-NOT-DOCUMENTED"
            write_json(repo, VECTOR_CONTRACT, vectors)

            result = validate(repo)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unknown expected action code", result.stdout)

    def test_duplicate_action_fails_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = self.copied_repo(directory)
            actions = load_json(repo, ACTION_CONTRACT)
            actions["values"].append(actions["values"][0])
            write_json(repo, ACTION_CONTRACT, actions)

            result = validate(repo)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("duplicate backpressure action code", result.stdout)

    def test_mismatched_code_and_reason_fails_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = self.copied_repo(directory)
            vectors = load_json(repo, VECTOR_CONTRACT)
            vectors["cases"][0]["body"]["error"]["reason"] = "different_condition"
            write_json(repo, VECTOR_CONTRACT, vectors)

            result = validate(repo)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("code and reason disagree", result.stdout)

    def test_retryable_without_bounded_guidance_fails_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = self.copied_repo(directory)
            vectors = load_json(repo, VECTOR_CONTRACT)
            case = next(case for case in vectors["cases"] if case["expected"].get("retryable"))
            case["headers"].pop("Retry-After", None)
            case["body"]["error"].pop("retry_after_ms", None)
            case["expected"].pop("retry_after_ms", None)
            write_json(repo, VECTOR_CONTRACT, vectors)

            result = validate(repo)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("retryable without bounded delay guidance", result.stdout)

    def test_replay_safe_unsafe_state_fails_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = self.copied_repo(directory)
            vectors = load_json(repo, VECTOR_CONTRACT)
            case = next(
                case
                for case in vectors["cases"]
                if case["expected"].get("request_state") == "dispatched"
            )
            case["body"]["error"]["replay_safe"] = True
            case["expected"]["replay_safe"] = True
            write_json(repo, VECTOR_CONTRACT, vectors)

            result = validate(repo)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("replay-safe in unsafe request state", result.stdout)

    def test_feature_and_task_must_reference_shared_contracts(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = self.copied_repo(directory)
            features = load_json(repo, "contracts/feature-registry.json")
            feature = next(feature for feature in features["features"] if feature["id"] == "IW-BP-001")
            feature["contracts"].remove(VECTOR_CONTRACT)
            write_json(repo, "contracts/feature-registry.json", features)

            result = validate(repo)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("IW-BP-001 omits shared backpressure contracts", result.stdout)

        with tempfile.TemporaryDirectory() as directory:
            repo = self.copied_repo(directory)
            tasks = load_json(repo, "contracts/canonical-task-graph.json")
            task = next(task for task in tasks["tasks"] if task["id"] == "P1-T19")
            task["contracts"].remove(ACTION_CONTRACT)
            write_json(repo, "contracts/canonical-task-graph.json", tasks)

            result = validate(repo)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("P1-T19 omits shared backpressure contracts", result.stdout)

    def test_model_capacity_condition_cannot_be_canonical_429(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = self.copied_repo(directory)
            vectors = load_json(repo, VECTOR_CONTRACT)
            case = next(case for case in vectors["cases"] if case["name"] == "known model has no usable capacity")
            case["status"] = 429
            write_json(repo, VECTOR_CONTRACT, vectors)

            result = validate(repo)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("non-queue model/capacity condition uses 429", result.stdout)

    def test_published_action_table_must_match_frozen_json(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = self.copied_repo(directory)
            spec = repo / "specs/06_BACKPRESSURE_RETURN_TO_SENDER.md"
            text = spec.read_text()
            spec.write_text(text.replace("| `IW-ACT-BACKOFF` |", "| `IW-ACT-NOT-FROZEN` |", 1))

            result = validate(repo)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("published action table disagrees with frozen JSON", result.stdout)

    def test_vectors_must_cover_every_frozen_action(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = self.copied_repo(directory)
            vectors = load_json(repo, VECTOR_CONTRACT)
            for case in vectors["cases"]:
                if case["expected"].get("action_code") == "IW-ACT-AUTHENTICATE":
                    case["expected"]["action_code"] = "IW-ACT-FIX-REQUEST"
                    case["expected"]["action"] = "fix_request"
                    error = vector_error(case)
                    error["action_code"] = "IW-ACT-FIX-REQUEST"
                    error["action"] = "fix_request"
            write_json(repo, VECTOR_CONTRACT, vectors)

            result = validate(repo)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("vectors do not cover frozen action codes", result.stdout)

    def test_canonical_body_and_expected_fields_are_required(self):
        fields = (
            "code", "reason", "retryable", "replay_safe", "request_state",
            "action", "action_code", "scope",
        )
        for target, field in ((target, field) for target in ("body", "expected") for field in fields):
            with self.subTest(target=target, field=field), tempfile.TemporaryDirectory() as directory:
                repo = self.copied_repo(directory)
                vectors = load_json(repo, VECTOR_CONTRACT)
                case = vectors["cases"][0]
                container = vector_error(case) if target == "body" else case["expected"]
                container.pop(field, None)
                write_json(repo, VECTOR_CONTRACT, vectors)

                result = validate(repo)

                self.assertNotEqual(result.returncode, 0)
                self.assertIn(f"missing {target} field {field}", result.stdout)

    def test_canonical_field_types_are_checked(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = self.copied_repo(directory)
            vectors = load_json(repo, VECTOR_CONTRACT)
            case = vectors["cases"][0]
            vector_error(case)["retryable"] = "false"
            case["expected"]["retryable"] = "false"
            write_json(repo, VECTOR_CONTRACT, vectors)

            result = validate(repo)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("retryable must be boolean", result.stdout)

    def test_readable_action_must_match_action_code(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = self.copied_repo(directory)
            vectors = load_json(repo, VECTOR_CONTRACT)
            case = vectors["cases"][0]
            vector_error(case)["action"] = "authenticate"
            case["expected"]["action"] = "authenticate"
            write_json(repo, VECTOR_CONTRACT, vectors)

            result = validate(repo)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("action does not match action code", result.stdout)

    def test_large_nonnegative_retry_delay_is_valid(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = self.copied_repo(directory)
            vectors = load_json(repo, VECTOR_CONTRACT)
            case = next(case for case in vectors["cases"] if case["expected"].get("retryable"))
            vector_error(case)["retry_after_ms"] = 172_800_000
            case["headers"]["Retry-After"] = "172800"
            case["expected"]["retry_after_ms"] = 172_800_000
            write_json(repo, VECTOR_CONTRACT, vectors)

            result = validate(repo)

            self.assertEqual(result.returncode, 0, result.stdout)

    def test_negative_retry_delay_fails_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = self.copied_repo(directory)
            vectors = load_json(repo, VECTOR_CONTRACT)
            case = next(case for case in vectors["cases"] if case["expected"].get("retryable"))
            vector_error(case)["retry_after_ms"] = -1
            case["headers"].pop("Retry-After", None)
            case["expected"]["retry_after_ms"] = -1
            write_json(repo, VECTOR_CONTRACT, vectors)

            result = validate(repo)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("retry_after_ms must be nonnegative numeric", result.stdout)


if __name__ == "__main__":
    unittest.main()
