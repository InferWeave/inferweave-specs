# 58 — Model Intelligence and Existing UI Cohesion

Status: required implementation; runtime, tenant, hardware and rollout proof **owed**.
Feature IDs: IW-OBS-001, IW-TEL-001, IW-BENCH-002, IW-ECON-001, IW-EVENT-001,
IW-REC-001, IW-REC-002, IW-UI-001.

## Source and authority

The operator supplied the full v1.0 kit on 2026-10-12 and explicitly requested
preservation of the current `metabolomics-us/inferweave-gateway` embedded UI
through full analytics implementation and merge. The unchanged source is
[`MASTER_SPEC.md`](../docs/specs/model-intelligence-kit/MASTER_SPEC.md)
(SHA-256: d2f8c9a01d3e0149d7e74f950973c161ed93a4c81dbb324cc7db49a346649275). Its singular `inferweave/inferweave-spec` repository
hint resolves to this canonical `InferWeave/inferweave-specs` repository.
This document normalizes the kit against binding invariants and the scoped
[D-002 amendment](../decisions/2026-10-12-model-intelligence-ui-cohesion.md).
Concept images are hierarchy references, never evidence of existing UI or data.
The kit's entire product scope remains required; unsupported measurements must be
visible as unsupported until implemented and qualified, not silently dropped.

## Ownership and integration boundary

Rust owns normalization, outcomes, aggregates, cost, evaluations, capacity,
recommendations and policy. Reuse PgStore, RequestFact, existing request-fact /
prompt-record relations, resource lifecycle events and benchmark warehouse.
Extend records additively with nullable fields and versioned semantics; old
records retain unknown fields. No new analytics service or storage silo, no
historical cache/token/cost backfill inferred from totals. Retention/rollups use
existing bounded storage policy; object artifacts use existing supported stores.
Recording stays bounded and cannot block admission. Analytics needs no prompt
or response content. Retain raw provider usage only under existing restricted
retention/privacy policy; never return it in shared reports.

The Go gateway is an authorized read adapter. TypeScript renders Rust results,
filters and formats them without recomputing domain measures. Preserve current
routes, controls, role restrictions, settings, live-update/pause/focus behavior,
preferences and existing source/dist delivery. Extend existing overview, models,
model details, usage, cluster/GPU, routing and traffic/events pages. Introduce a
comparison route only when existing affordances cannot support comparison.
No second frontend, parallel menu, new scheduler or automatic resource command.

## MI-01 — Measurement envelope and reliability

Every scalar, series, cohort and comparison carries metric_definition_version,
time window and as_of, aggregation dimensions, units, source, measurement status,
numerator/denominator, sample count, coverage and explicit exclusions. Pagination,
maximum query windows, bucket resolution and grouping cardinality are bounded.
Expose missing, unsupported, stale and zero distinctly: null with a reason for
an unknown value; zero only for a measured zero. Ratios with no denominator are
unknown. Coverage describes both present and eligible observations; a truncated
query discloses its covered window/count and cannot claim complete coverage.

Keep logical_request_id, attempt_id and trace correlation distinct. Tenant/user,
mission, gateway, worker, stable node/GPU, allocation, deployment/model revision,
quantization, runtime/profile, hardware class and region are scoped dimensions;
unique identifiers never become Prometheus labels. Hashed user IDs remain private.
Retry/fallback attempts are physical work, not new logical requests or users.
Transport success, attempt success, logical success after retry, feedback-based
task success and model-serving availability have independent denominators.
A transport success is not proof of inference or task success. Cancellation
exclusions require a named policy and tooltip. Preserve original reason and
attempt cause chain for preemption, scheduler reclaim, world-size mismatch, OOM,
crash, timeout, rejection, queue expiry, unload, network, cancellation, invalid
output, failed task, other and unknown; reuse frozen protocol reason registries
or add documented/test-reconciled vocabulary rather than inventing local enums.

Distinguish replica up, advertised availability, serviceable within SLO and
logical request served. Time-weighted availability uses eligible requested time,
explicit maintenance exclusions and observed state intervals. Unknown intervals
remain unknown; no traffic does not prove demand was served. Link Slurm/worker
preemption and recovery to GPU/allocation and affected logical requests/failovers.
Report interrupted requests and events per replica-hour/GPU-hour separately.

## MI-02 — Exclusive token and exact cost accounting

Normalize attempt input_total, uncached, cache_read, cache_write, output_total,
visible/reasoning, tokenizer revision, cache source, reported/estimated status,
provider billed categories and coverage through runtime capabilities. Never add
a total to its nested subset. Reasoning included in output_total is not additional
output. Only derive input_total = uncached + cache_read + exclusive_cache_write +
unknown_input when the adapter proves those buckets are exclusive; otherwise
retain overlap annotations and unknown composition. Unknown historical breakdown
cannot be invented from a total. Keep logical tokens, billed tokens and physical
attempt work separate, including retry costs and partial/missing usage.

Use exact checked integer/fixed-point monetary arithmetic with currency, scale,
rounding policy and effective dated rate-card version. Rates distinguish provider,
region, input/output/cache read/write, reasoning billing and context tiers. Missing
rates are unknown, not free. Self-hosted GPU reservations/active slices use a unique
allocation identity and versioned attribution policy; attributed plus explicitly
unallocated GPU time/cost conserves each physical allocation and cannot be charged
twice to colocated models. Do not combine currencies or measured and estimated
costs silently. Configured compute/power/storage/transfer components identify their
sources. Cost per successful task includes failed/retried physical work in the
same cohort and feedback-confirmed successes in the denominator. Per-million
logical/input/output/cache figures identify their token mix and denominator.
Simulations are estimates with uncertainty, not measured billing.

## MI-03 — Speed and observed capacity

Distinguish queue/scheduler wait, TTFT, inter-token latency, prefill, request decode,
aggregate throughput, end-to-end latency and completed requests per time. Report
p50/p95/p99 with samples, units, estimator and confidence where defensible. Preserve
missing timing data. Connections, in-flight requests, attempts, decode sequences,
slots, sessions, agents and distinct active identities are separate measures.

Safe sustainable request concurrency is limited to observed SLO-compliant bins
for exact model/profile/hardware/workload, with minimum samples, evidence window,
coverage, confidence and last observation. Match prompt/output lengths, cache mix,
batching and latency targets; show saturation/queue/preemption effects and gaps.
Do not extrapolate above tested load or imply sustained service from a short bin.
User-equivalent capacity requires an explicit requests-per-user workload scenario;
otherwise it is unsupported. Measured request concurrency is not active humans.

## MI-04 — Task evaluations, fair candidates and safety

Version task-family suites (coding, tools/agent completion, reasoning/math,
summarization, embeddings/reranking, speech/TTS, vision and prediction) with dataset
provenance, scorer/direction, sample count/confidence, model/tokenizer revision,
resource profile and latency. Keep production feedback separate from benchmark
quality; protect private datasets and do not invent a global intelligence score.
An explicitly configured composite exposes weights and missing dimensions.

Compare equivalent task, workload/token mix, quality threshold, latency SLO and
hardware. Compute Pareto candidates only after hard eligibility: tools, context,
modality/schema, policy/license, quality, confidence, exact profile/quantization,
VRAM/KV/topology and current owned hardware availability. Unknown feasibility is
not eligible. Preserve availability/preemption constraints and lower-confidence
external evidence; a published benchmark is not measured local performance.
Show evidence window/sample size, provenance, savings uncertainty and rejection
reasons. A fingerprint change invalidates or downgrades evidence.

Recommendation is read-only by default. Use the existing qualification/routing
policy boundary for discovery -> eligibility -> offline benchmark -> privacy-safe
shadow/replay -> bounded canary -> explicit opt-in promotion -> rollback. Transitions
require stage evidence, downstream owner authorization, limits and known-good
rollback; skipped stages, automatic promotion, stale evidence and failed canaries
cannot activate routing. Preserve watchdog, owner priority, scheduler authority,
drain, bounded recovery and quarantine. Offline proof does not authorize deployment.

## MI-05 — Authorized read API

Add versioned GET resources under `/iw/v1/model-intelligence/`:
`summary`, `timeseries`, `incidents`, `tokens`, `capacity`, `evaluations`,
`candidates`, `costs`. Reuse existing transport, generated schemas and error
envelopes. Each resource authenticates an explicitly authorized operator principal
before reading private analytics; being under `/iw` is no authorization exemption.
A tenant filter narrows an existing grant; it never creates one.
`x-inferweave-tenant` is untrusted input, not verified tenant or user authority.
Private tenant/user scopes are unsupported until verified grants and isolation
are demonstrated. Never substitute a global report for an unsupported private query.
Audit privileged reads using existing content-free audit paths.

The Go adapter exposes GET `/console/api/model-intelligence/report` using existing
console access control and configured authenticated Rust credentials. Its shared
operational mode returns only allowlisted redacted aggregates; operator mode
requires explicit operator authorization. No raw provider usage, prompts/outputs,
request/user/session identities, private addresses or credentials reach shared
responses, errors, browser caches or exports. Do not forward browser-provided
identity headers as grants. Verify redaction and query bounds at both boundaries;
errors and unsupported resources are visible, never replaced by fixture metrics.

## MI-06 — UI cohesion and acceptance evidence

Inventory actual routes/state/providers/styles/charts/permissions/API contracts
and capture non-sensitive baseline fixtures before modifying screens. Retain
existing default light styling. Optional system/light/dark parity uses one shared
preference and semantic token source; do not assert a pre-existing dark theme.
Reuse shared charts/tables/filters, accessible status text/legends, unit tooltips,
timezone-aware axes and precision. Preserve keyboard focus, screenreader names,
forced colors/reduced motion, pause/focus settings and responsive table behavior.
All surfaces need loading/empty/error/unsupported/stale states, time/model/scope
filters, visible provenance and authorized exports when the existing pattern allows.
Fixture values are clearly DEMO and never enter live aggregates.

Required acceptance includes desktop/tablet/mobile and browser/theme comparisons
against actual baselines, all existing routes/actions/permissions, source/dist
parity, accessibility, query/performance limits, explicit unknown decomposition
of historical totals (including the kit's illustrative 100M case), linked incidents,
request/attempt distinction, fair comparisons and no implicit recommendation
activation. Keep migration and rollback notes and flags for risky features.
Final requirement-to-code/test/screenshot evidence must identify unsupported live
sources. Missing measurements remain an explicit gap, not a completion claim.

## Traceability and proof

| Requirement | Existing tasks | Acceptance |
|---|---|---|
| MI-01 outcomes, provenance, availability | P1-T20, P2-T10 | AC-MI-01, AC-MI-05 |
| MI-02 exclusive tokens, exact economics | P2-T16 | AC-MI-02 |
| MI-03 speed and capacity | P1-T20 | AC-MI-03 |
| MI-04 evaluation/candidate/safety | P2-T05, P2-T07, P2-T08 | AC-MI-04 |
| MI-05 persistence and read authorization | P2-T03 | AC-MI-06 |
| MI-06 existing UI and evidence | P1-T21 | AC-MI-07 |

Machine-readable acceptance: `contracts/model-intelligence-acceptance.json`.
All new implementation tests are **owed** by these tasks; spec validation proves
artifact consistency only. Existing task dependencies/order remain in force.
P1-T21 may show honest unsupported states while phase-2 data is unavailable; full
kit integration requires all mapped tasks, not only the first dashboard task.
No production, tenant, hardware or continuous-measurement gate closes here.

## Implemented read-contract evidence

`openapi/model-intelligence.yaml` and `openapi/model-intelligence.md` document the
additive operator read API and typed response/unsupported branches. Evidence and
remaining requirements are in `evidence/model-intelligence-2026-10-12/README.md`.
Current Go access is operator-only through its existing middleware; normative
shared operational and verified private tenant/user grants remain owed.

## Scoped edge observations and public GPU profiles (2026-10-20)

The [observability ADR](../decisions/2026-10-20-observability-capacity.md) narrowly
amends the ownership paragraph: existing Go may persist its own bounded edge
observations/local rollups with local provenance and coverage. Rust continues
to own global metrics and capacity. New public GPU profiles belong in the
existing Next.js `apps/web`, while the existing embedded operator pages retain
the D-002 exception. Both render spec04 typed capacity without computing
admission or pooling per-card VRAM. Public profiles show context/workload,
fingerprint, observation window, coverage and freshness; private stable node
addresses, principal IDs, exact private workload times and content are absent.
Initial publication thresholds are 30 requests and 5 distinct principals per
cohort, with small/unknown cohorts suppressed and policy version disclosed.
Those defaults are not universal privacy proof; cross-filter differencing and
linkability require independent review before production publication.
