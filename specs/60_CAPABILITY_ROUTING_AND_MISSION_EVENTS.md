# 60 — Capability Request, Routing Decision and Mission Event Contracts

## Purpose

Feature ID: `IW-ROUTE-001`; task `P2-T14`; delivery task `T27` of
`docs/specs/2026-10-14-pi-autospec-autonomous-delivery-design.md` in
`berlinguyinca/autospec` (requirements R-MODEL and R-EVENT, umbrella
`berlinguyinca/autospec#4742`).

Three delivery sources asked for overlapping client-visible behaviour and each one stated a
different subset: client-side fallback only, a request/response exchange that returns an
eligible model and an estimated wait, and an event field list. The source design resolved the
conflict by requiring the gateway-side answer (estimated wait and route reasons), so the
contract lives here. This specification is the single reconciled text of:

1. the **capability request** a client sends to ask which model and slot can serve a task;
2. the **routing decision** InferWeave returns for it;
3. the **mission event** a client-side orchestrator emits so progress is observable.

This document defines wire contracts only. It adds no scheduler, no gateway role and no new
deployment substrate. `05_ROUTING_AFFINITY.md` remains the authority on how a candidate is
chosen; `06_BACKPRESSURE_RETURN_TO_SENDER.md` remains the authority on bounded retry. Where this
text and those specifications disagree, those specifications win.

JSON Schemas, fixtures and contract tests are separate, later changes. Until they exist,
nothing in this text is `proven`; see Proof status.

## Capability request

A capability request is a closed object. Version 1 carries `schema_version: "1"`.

| Field | Type | Meaning |
|---|---|---|
| `schema_version` | const `"1"` | contract version; a reader that does not know the version rejects the request |
| `capability` | capability id | task capability the model must hold, a namespaced extensible string id from `44_CORE_PROTOCOL.md` (for example `llm.tool_use`, `llm.code`); client-side names are mapped to these ids by the client |
| `quality_floor` | object `{metric_id, minimum}` | minimum acceptable value of one generic quality metric of `44_CORE_PROTOCOL.md` (for example `metric_id: llm.tool_use_quality`); `minimum` is a number in the unit of that metric |
| `min_context_tokens` | integer >= 1 | smallest acceptable hard context ceiling of the chosen deployment |
| `modality` | token | input modality such as `text`, `image`, `audio` |
| `deadline` | RFC 3339 date-time | latest time by which the work must have started being served |
| `affinity` | object | optional; `session_id` binds the request to a session for sticky routing (`05_ROUTING_AFFINITY.md`, Sticky sessions) |
| `open_weight_only` | boolean | when true only self-hosted open-weight deployments are eligible |
| `extensions` | object | namespaced optional growth (`schemas/v1/common/extensions.json`) |

Required: `schema_version`, `capability`, `quality_floor`, `min_context_tokens`, `modality`,
`deadline`, `open_weight_only`. `affinity` is optional.

`44_CORE_PROTOCOL.md` transports quality measurements per metric and defines no universal
intelligence score, so the floor names its metric instead of inventing a shared scale. A
deployment with no sample for `metric_id` does not meet the floor.

Unknown top-level fields are rejected, not ignored: a field a sender believes is a hard
constraint must never be silently dropped. New constraints arrive by a new `schema_version` or,
for non-binding hints, inside `extensions`. A sender must not place a hard constraint in
`extensions`; a receiver ignores unknown extension namespaces.

## Routing decision

A routing decision is a closed object with `schema_version: "1"` and a `status` of `ROUTED` or
`BLOCKED`. There is no third status and no "maybe".

### ROUTED

Required: `schema_version`, `status`, `model`, `slot`, `estimated_wait_ms`, `route_reasons`.

- `model` is a canonical model id of an eligible deployment (invariant 5: a request is never
  routed to a node that lacks the required model, deployment or capability).
- `slot` is an opaque identifier of the serving slot.
- `estimated_wait_ms` is an integer in [0, `MAX_WAIT_BOUND_MS`].
- `route_reasons` has at least one entry.
- `retry_after_ms` is absent.

### BLOCKED

Required: `schema_version`, `status`, `retry_after_ms`, `route_reasons`.

- `retry_after_ms` is an integer in [0, `MAX_WAIT_BOUND_MS`]. The gateway never answers with an
  unbounded or unspecified wait.
- `route_reasons` has at least one entry naming why no candidate qualified.
- `model`, `slot` and `estimated_wait_ms` are absent. A BLOCKED decision names no model, so no
  caller can mistake it for an assignment.

`MAX_WAIT_BOUND_MS` is `300000` (five minutes). This is a protocol ceiling chosen by this
contract, **not** a measured value; the AGENTS.md measured-basis rule therefore applies to the
number itself, and the calibration is recorded as owed in `OPEN_GATES.md`. A deployment may
publish a lower bound; it never publishes a higher one under `schema_version` 1. A computed wait
above the bound is reported as BLOCKED, not as a long ROUTED wait.

### Rules

1. **The quality floor is never relaxed to win a slot.** If only candidates below
   `quality_floor` have capacity, the decision is BLOCKED with `QUALITY_FLOOR_UNMET`. The same
   holds for `min_context_tokens`, `modality`, `open_weight_only` and `deadline`: every field of
   the request is a hard constraint (`05_ROUTING_AFFINITY.md`: a faster GPU with insufficient
   context is not a candidate).
2. **No infinite wait and no infinite retry.** Both waits are bounded by `MAX_WAIT_BOUND_MS`. A
   client that receives BLOCKED waits at least `retry_after_ms` (with jitter) and retries inside
   the bounded budget of `06_BACKPRESSURE_RETURN_TO_SENDER.md`; it then surfaces the failure.
3. **Reasons are codes and identifiers only** (invariant 25). A reason carries a registered or
   additive upper-case `code` and, optionally, a `subject_id` identifier. It never carries prompt
   text, completion text, credentials, free-form messages or hidden reasoning.
4. **A decision is advice, not a lease.** ROUTED does not reserve the slot; admission and
   leases remain with `04_CAPACITY_ADMISSION_SEATS.md`. The slot may be gone by dispatch time and
   the client must treat the ordinary admission rejection as authoritative.
5. **A decision that disagrees with admission is a defect in the decision.** The route
   explanation persisted by `05_ROUTING_AFFINITY.md` must be able to reconstruct it.

## Route reason codes

A reason is `{ "code": <CODE>, "subject_id": <id> }`; `subject_id` is optional. `code` matches
`^[A-Z][A-Z0-9_]{2,63}$`; `subject_id` matches `^[A-Za-z0-9._:/-]{1,128}$`. Readers treat an
unregistered code as opaque and still apply the ROUTED/BLOCKED rules, so adding a code is
additive.

Registered codes for ROUTED:

| Code | Meaning |
|---|---|
| `CAPABILITY_MATCH` | the deployment holds the requested capability |
| `QUALITY_FLOOR_MET` | the metric named by `quality_floor` is at or above its minimum |
| `CONTEXT_FITS` | hard context ceiling is at least `min_context_tokens` |
| `MODALITY_MATCH` | the deployment accepts the requested modality |
| `OPEN_WEIGHT_SATISFIED` | the deployment is self-hosted open-weight |
| `SESSION_AFFINITY` | chosen to honour `affinity.session_id` |
| `WITHIN_DEADLINE` | the estimated wait ends before `deadline` |
| `BEST_FIT` | lowest sufficient remaining envelope (`05_ROUTING_AFFINITY.md`, Best-fit) |

Registered codes for BLOCKED:

| Code | Meaning |
|---|---|
| `NO_ELIGIBLE_CAPACITY` | eligible deployments exist but none has capacity inside the bound |
| `QUALITY_FLOOR_UNMET` | only deployments below `quality_floor` (or with no sample for its metric) have capacity |
| `CAPABILITY_UNSUPPORTED` | no deployment holds the capability |
| `CONTEXT_UNSATISFIABLE` | no deployment has a large enough hard context ceiling |
| `MODALITY_UNSUPPORTED` | no deployment accepts the modality |
| `OPEN_WEIGHT_UNSATISFIABLE` | no open-weight deployment qualifies |
| `DEADLINE_UNSATISFIABLE` | the earliest start is after `deadline` |
| `WAIT_EXCEEDS_BOUND` | the computed wait is above `MAX_WAIT_BOUND_MS` |

## Mission event

A mission event extends the event envelope of `schemas/v1/events/event.json` with the R-EVENT
fields. It therefore inherits every envelope requirement, including `source_id`, and adds its
own. Version 1 carries `schema_version: "1"`.

Required: `schema_version`, `event_id`, `mission_id`, `event_type`, `state`, `timestamp`,
`sequence`, plus the envelope's `source_id`.

Optional and typed (a producer omits a field it does not have; it never invents a value):
`trace_id`, `task_id`, `worker_id`, `host_id`, `repository`, `worktree_id`, `commit_sha`,
`operation_id`, `causal_parent_id`, `human_summary`, `progress_kind`, `last_heartbeat_at`,
`last_progress_at`, `deadline_at`, `resource_usage`, `artifact_refs`.

A mission event is a closed object: it lists every allowed property (the envelope's `event_id`,
`source_id`, `timestamp`, `sequence`, `trace_id`, `correlation_id`, `extensions` and the fields
above) and rejects any other, so a field a producer believes is binding is never silently dropped.

Rules:

1. `sequence` is a positive integer: the first event of a mission has `sequence` 1 (matching the
   R-PROTO evaluation-journal sequence), and it is monotonic per `mission_id`. Monotonicity across
   events is consumer behaviour: a consumer ignores an event whose `sequence` is not above its
   checkpoint for that mission and records the gap. The schema cannot check it.
2. **Liveness and progress are separate fields.** `last_heartbeat_at` records that the producer
   is alive. `last_progress_at` records the last useful progress and moves only when
   `progress_kind` names real work. A heartbeat-only event updates `last_heartbeat_at` and leaves
   `last_progress_at` untouched, so a live-but-stuck worker is distinguishable from a working one.
3. `progress_kind` is one of `edit`, `build`, `test`, `review`, `merge`, `cleanup`, `routing`,
   `none`. `none` means no useful progress.
4. Delivery is at-least-once. A consumer is idempotent on `event_id` and keeps a replay
   checkpoint per mission.
5. **No content.** A mission event carries identifiers and measurements, not prompts, completions,
   credentials or hidden reasoning (invariant 25). `human_summary` is at most 280 characters and
   must already be redacted by the producer. The envelope `payload` is not permitted on a mission
   event; the typed fields above are the whole contract.
6. `resource_usage` is a flat map of non-negative numbers. `artifact_refs` is a bounded list of
   `{kind, id}` references, never inline content.
7. `state` and `event_type` are non-empty strings whose vocabularies belong to the producing
   orchestrator; this contract fixes their shape, not their values.
8. `causal_parent_id` names the event that caused this one. The envelope also defines
   `causation_id`; a mission event carries `causal_parent_id` only and **must not** carry
   `causation_id`, so there is exactly one caused-by field.

## Compatibility

- Additive only within `schema_version` 1. Reason codes and `extensions` are the additive
  surfaces. `progress_kind` is a closed enumeration: a new kind needs a new `schema_version`.
- A reader rejects an unknown `schema_version`.
- The gateway (`metabolomics-us/inferweave-gateway`) stays a thin relay and admin UI with no
  scheduling role. This contract gives it no decision to make.
- Existing implementation work is unaffected: nothing here changes a shipped wire format.
  Producers and consumers of the new objects do not exist yet.

## Proof status

| Control | Status | Evidence |
|---|---|---|
| Closed schemas for request, decision and mission event | owed | schemas and fixtures follow in later changes |
| Invalid decisions and events are rejected | owed | contract tests follow; `proven` only once a test fails when a schema constraint is removed |
| Gateway emits `estimated_wait_ms` and `route_reasons` | owed | recorded in `OPEN_GATES.md`; unsatisfied |
| `quality_floor` metric ids and minimums comparable across deployments | owed | per-metric provenance and scale comparability unmeasured here |
| `MAX_WAIT_BOUND_MS` calibrated against measured wait distributions | owed | unmeasured; chosen by contract |
| Quality floor never relaxed at runtime | owed | a runtime property of the router; no test exists here |

Every row above is unsatisfied. This text records the contract; it does not record that anything
enforces it.
