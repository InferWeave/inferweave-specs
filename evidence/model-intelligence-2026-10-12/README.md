# Model intelligence evidence handoff — 2026-10-12

Status: **implementation evidence recorded; full kit/P5 acceptance owed**.
Rust snapshot: `35ac81e7b0a0c3cba23390c1adae092ea392ca0d`.
Go snapshot: `613c78187af0719b7dc91eda06b677b58f06a2b8`.
These records are bounded local evidence, not a production deployment approval.

## Artifact scope

- `backend-integration-report.md` preserves the integration owner's detailed
  source/transport/storage/rollback report. Its runtime assertions remain scoped
  to disposable PostgreSQL and synthetic streams; no live fleet importer is implied.
- `reported-test-results.json` captures inspected source-log hashes and result
  lines. These are execution evidence, not proof that every control fails when
  removed. No acceptance record is promoted to proven on the strength of a log.
- `report.demo.json` is a compact copy of the actual sanitized PostgreSQL HTTP
  fixture, retaining its explicit DEMO/fixture marker. The backend's full-window
  default fixture hashes and schema check outcomes are in `schema-validation.json`.
- `ui-before-report.json` is the original synthetic UI inventory/baseline, source
  `6ccf2bdb0983e6fc5b7ddb1e49a4ed5172d05416`. Dark OS preference still rendered light.
- `theme-after-report.json` records the bounded shared-theme checks and exact-light
  regression results. Its screenshot paths refer to the coordinating workspace
  audit captures; this snapshot does not supply final integrated P5 screenshots.
  Final browser/route/dist parity and screenshot publication remain owed.

## Requirement → implementation → test mapping

Paths below are relative to the named implementation repository. Test symbols are
real source controls at the handoff; they are not a claim of unbounded live data.
All AC-MI records retain `proof_status: owed` until their full evidence closes.

| Acceptance | Rust implementation / regression controls | Go/UI or remaining evidence |
|---|---|---|
| AC-MI-01 outcomes/cohorts | `crates/iw-core/src/model_intelligence.rs`; `crates/iw-core/tests/model_intelligence.rs::retries_are_physical_attempts_but_one_logical_request_and_replay_is_idempotent`; `crates/iw-gateway/tests/model_intelligence_live.rs::filtered_http_success_is_a_failed_inference_incident` | Live stream success does not establish task success; historical logical/task identity remains absent. |
| AC-MI-02 accounting | `crates/iw-core/src/token_accounting.rs`, `token_economics.rs`; `crates/iw-core/tests/token_accounting.rs::nested_cache_and_reasoning_are_exclusive_not_additive_totals`; `crates/iw-core/tests/token_economics.rs::shared_gpu_allocations_conserve_physical_cost_with_unattributed_remainder`; `crates/iw-gateway/src/server_intelligence.rs::tests::monetary_wire_values_preserve_all_u64_digits` | Typed supplied billing/GPU evidence is tested through HTTP. Real bills, configured rates and physical intervals are not derived from the live generic stream. |
| AC-MI-03 capacity | `crates/iw-core/src/model_capacity.rs`; `crates/iw-core/tests/model_capacity.rs::capacity_requires_sample_floor_and_observed_slo_compliance_without_extrapolation`; `repeated_capacity_samples_do_not_manufacture_sample_floor_and_demo_is_excluded` | No sustained current hardware/workload qualification or active-human measurement is claimed. |
| AC-MI-04 qualification | `crates/iw-core/src/model_intelligence_recommendations.rs`; corresponding tests `latest_failure_cannot_be_hidden_by_older_success`, `every_hard_constraint_is_checked_before_ranking`, `rollout_defaults_deny_and_promotion_cannot_skip_qualification`; `crates/iw-gateway/tests/model_intelligence_http.rs::postgres_evidence_reaches_authenticated_http_tokens_costs_capacity_and_qualification` | Report-only policy evaluation; no routing executor, production canary or promotion is authorized. |
| AC-MI-05 availability/events | `crates/iw-core/src/model_capacity.rs`; corresponding tests `availability_is_time_weighted_and_distinct_from_advertisement_and_slo`, `shared_gpus_are_unioned_and_unknown_preemption_correlations_stay_unknown` | Live complete serving-state intervals and scheduler/preemption correlations remain unavailable until authoritative producers exist. |
| AC-MI-06 API/storage/auth | `crates/iw-gateway/src/server_intelligence.rs`, `crates/iw-storage/src/model_intelligence.rs`; `crates/iw-gateway/tests/model_intelligence_http.rs::model_intelligence_refuses_scope_injection_and_body`; `crates/iw-storage/tests/model_intelligence.rs::persisted_observations_deduplicate_reject_conflicts_and_filter` | `cmd/gateway/model_intelligence_core_test.go`: `TestIntelligenceCoreReadRequiresOperator`, `TestIntelligenceCoreNoRedirectOrOversizedReply`, `TestIntelligenceCoreRealDefaultWirePayloads`; real tenant/user grant projection and ordinary shared viewer report remain unsupported. |
| AC-MI-07 UI | Shared theme and existing page integration; `web/tools/theme-check.mjs`, `web/tools/intelligence-kit-check.mjs` in gateway repo | Before/after reports above are bounded slices. Final retained-route/cross-browser/responsive screenshots, all controls/permissions and final source/dist parity remain P5 obligations. |

## Current limitations retained from normative spec 58

Existing operator-only Go transport is implemented; a `shared` Rust query label
is still operator-authenticated, not a shared audience grant. Private tenant/user
queries remain unsupported. Schema and negative fixture checks cannot prove runtime
authorization. Generic OpenAI-shaped usage does not establish cache/reasoning
inclusion semantics. Unknown historical categories, logical IDs, downstream task
outcomes, complete availability intervals, physical GPU allocation, billing facts,
measured workload capacity and production evaluation imports remain unknown until
authoritative producers and tests exist. No importer or fresh hardware evidence is
manufactured by the typed internal API. No numerical field is production-qualified
because a synthetic fixture has it. Final root gate was still running at handoff.

The master kit bytes are unchanged. Evidence supplements its requirements; it does
not lower acceptance, close OPEN_GATES, or claim the whole MASTER_SPEC complete.

## Final logical/task/day contract checkpoint

Approved backend implementation: `be8ce4055f57d4498218176920d13b5ed38f2c92`.
This checkpoint supersedes the initial response-shape snapshot above for the
current additive OpenAPI. Earlier `report.demo.json`/`schema-validation.json`
remain historical evidence for `35ac81e`; they are not current-schema fixtures.
`backend-final-integration-report.md` preserves the final integration handoff.

Current actual PostgreSQL HTTP DEMO captures are
`rust-report-logical-task.demo.json`,
`rust-report-logical-task-unavailable.demo.json`, and
`rust-report-token-days.demo.json`. The checked logical/task fixture keeps three
physical attempts in cost, but one authoritative logical projection in token
counts: task amount is the exact decimal string `330`; cost per million logical
tokens is `2750000` with denominator 120. These are controlled fixture facts,
not live rate, workload, capacity or billing claims. Missing logical projection
keeps its usage and per-million cost null even if task cost is separately known.

Actual response fields are `logical_tokens`, `logical_token_coverage`,
`token_days`, `token_day_coverage`, `costs.per_successful_task` and
`costs.per_million_logical_tokens`. The old always-unavailable
`successful_task_cost` placeholder is removed. Cost wrappers preserve closed
cohort counts, source, basis, feedback/attempt coverage, nullable amounts and
exact decimal-string money. Private producer identities and warehouse proof
objects are absent from responses. Optional internal UsageEvidence projections,
explicit projection timestamps and closed task evidence add no public POST API.

Physical days use actual attempt-start UTC days; logical days use explicit
projection timestamps. Windows are clipped, days sparse, historical record time
is not guessed as attempt time, and absent/estimated totals yield unknown/partial
coverage. Recorder snapshot counts and live timing provenance now accompany full
reports; loss or changing snapshots prevents complete-cohort claims.

Additional AC-MI-01/02/06 regressions map to
`crates/iw-gateway/src/server_logical_economics.rs`,
`crates/iw-storage/src/model_intelligence.rs`, and
`crates/iw-gateway/tests/model_intelligence_logical.rs`:

- `closed_task_cost_includes_two_retries_but_logical_projection_counts_once`;
- `private_projection_and_task_binding_is_rejected_on_ingest`;
- `self_hosted_task_cost_uses_explicit_attempt_allocations_once`;
- `daily_physical_buckets_are_sparse_and_logical_projection_uses_its_own_utc_time`;
- `historical_record_time_does_not_become_actual_attempt_day`;
- `contradictory_timestamps_for_one_logical_projection_fail_closed`;
- `another_model_retry_cannot_be_hidden_by_model_filter_or_pagination`;
- `dated_logical_measurements_preserve_missing_and_estimated_status`;
- `pending_recorder_suppresses_closed_costs_but_retains_physical_subtotals`.

See `logical-schema-validation.json` for exact final capture hashes and schema
negative cases. Controls retain their full acceptance status **owed**: synthetic
closed-cohort/projection producers and schema checks do not establish real
end-user grants, complete logical/task feedback, billing/GPU attribution sources,
live availability, sustained hardware qualification or production approval.
The master kit is unchanged; final broad root/P5 gates are recorded separately.
