"""Canonical contract checks, not proof that a deployed backend stopped."""
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "contracts/systemone-native-admission-v1.json"


class NativePhysicalLifetime(unittest.TestCase):
    def setUp(self):
        self.contract = json.loads(CONTRACT.read_text())

    def policy(self):
        policy = self.contract.get("physicalLifetime")
        self.assertIsInstance(policy, dict, "physical completion authority is unspecified")
        return policy

    def test_only_execution_completion_or_verified_termination_can_retire_dispatched_work(self):
        self.assertEqual(self.policy()["dispatchedWorkRetirementEvidence"], [
            "authoritative_backend_completion_response_for_exact_work",
            "successful_os_wait_for_exact_owned_process_incarnation",
        ])

    def test_caller_transport_and_health_signals_are_not_physical_completion(self):
        rejected = self.policy()["notCompletionEvidence"]
        for signal in ["caller_cancellation", "caller_deadline", "transport_timeout",
                       "connection_eof", "partial_or_malformed_response", "healthy_runtime_probe",
                       "elapsed_time", "signal_sent_without_wait_receipt",
                       "missing_child_handle_without_verified_exit"]:
            self.assertIn(signal, rejected)
        self.assertEqual(self.policy()["unconfirmedWork"], "retain_debt_and_quarantine")
        self.assertEqual(self.policy()["ambiguousInferenceReplay"], "forbidden")
        self.assertEqual(self.policy()["runtimeProofStatus"], "owed")

    def test_existing_wire_fields_units_cost_and_clipped_routing_formula_are_unchanged(self):
        self.assertEqual(self.contract["registrationPoolFields"], [
            "poolId", "generation", "envelope", "models", "maxConcurrency"])
        self.assertEqual(self.contract["reportPoolFields"], [
            "poolId", "generation", "envelope", "models", "maxConcurrency",
            "inflight", "gatewayHeld", "occupancyBasis"])
        self.assertEqual(self.contract["optionalReportPoolFields"], ["queued", "reportedInflight"])
        self.assertEqual(self.contract["poolConcurrencyUnit"], "state_admission_units")
        self.assertEqual(self.contract["requestCost"], {
            "single": 1, "batch": "min(number of states, selected pool maxConcurrency)"})
        self.assertEqual(self.contract["occupancySemantics"]["inflight"],
                         "min(maxConcurrency, reportedInflight + gatewayHeld)")

    def test_required_runtime_proofs_remain_explicitly_owed(self):
        required = self.contract["requiredTests"]
        for proof in ["caller-timeout-retains-physical-work-permit",
                      "queued-cancellation-retires-only-undispatched-work",
                      "ambiguous-backend-failure-no-replay",
                      "checked-owned-process-exit-before-physical-reuse",
                      "old-incarnation-completion-cannot-release-new-work"]:
            self.assertIn(proof, required)
        self.assertEqual(self.contract["proofStatus"], "owed")

    def test_original_red_and_bounded_green_receipts_have_distinct_honest_scopes(self):
        evidence = ROOT / "evidence/systemone-native-physical-lifetime-2026-11-12"
        red = json.loads((evidence / "red-receipts.json").read_text())
        baseline = next(run for run in red["runs"] if run["run_id"] == "9921")
        observed = next(event for event in baseline["events"]
                        if event["event"] == "RED_unacknowledged_work_reported_free")
        self.assertEqual(baseline["classification"], "RED")
        self.assertEqual(observed["reported_units"], 0)
        self.assertEqual(observed["child_held"], 0)
        self.assertGreater(observed["cpu_ticks_delta"], 0)
        green = json.loads((evidence / "bounded-green-receipt.json").read_text())
        self.assertEqual(green["classification"], "GREEN")
        self.assertEqual(green["proof_scope"], "private_15_second_timeout_physical_retirement_only")
        self.assertEqual(green["production_qualification"], "owed")
        events = {event["event"]: event for event in green["events"]}
        self.assertGreater(events["old_owned_process_exited"]["elapsed_seconds"],
                           events["caller_ended_before_physical_proof"]["elapsed_seconds"])
        self.assertNotEqual(events["GREEN_physical_lifetime"]["replacement_pid"],
                            events["physical_probe_started"]["old_pid"])
        self.assertEqual(events["GREEN_physical_lifetime"]["normal_route_status"], 200)
        self.assertTrue(green["checked_exit_receipts"])
        self.assertTrue(all(receipt["termination_signal"] == 9
                            and receipt["status_kind"] == "SIGKILL"
                            for receipt in green["checked_exit_receipts"]))


if __name__ == "__main__":
    unittest.main()
