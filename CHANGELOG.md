# Changelog

## Unreleased

### Added — operational bundle `docs/specs/dynamic-context-capabilities/`

Model context capability, request-scoped weighted admission, and the Pi client
contract, delivered as a single bundle with work breakdown and acceptance
criteria. It operationalises clauses that `04_CAPACITY_ADMISSION_SEATS` and
`05_ROUTING_AFFINITY` already stated and that no implementation honoured: context
feasibility is a hard routing filter against each candidate's ceiling, and seat
count is descriptive rather than admission capacity.

The bundle adds the pieces the numbered documents left open: the three lease
types (hard request lease, session-affinity lease, soft KV lease) as distinct
objects with distinct limits; the reservation arithmetic
(`prompt + bounded output + configurable margin`, never a model window); the
capability document and its `ETag`/generation semantics, including the rule that
an alias advertises only what it can guarantee to route; the six admission failure
reasons and their retryability; and the client precedence chain ending in a
conservative 128K floor with **no** generic 260K fallback anywhere.

Canonical specifications are unchanged: `02`, `04` and `05` remain authoritative
for the contract, and `docs/specs/README.md` records where the bundle sits
relative to them.

## v12 — 2026-09-12

- Added `43_GPU_PLACEMENT_HOT_SWAP`: capacity moves between models one GPU at a time; each model has
  a configurable dwell, derived from its measured load time when not set; a catalogued model never
  falls below its healthy-instance floor; a swap drains with a bounded per-model deadline, pins every
  runtime component to the claimed GPU, and rolls back on failure. Runtime on-demand loading and
  eviction no longer decide placement.
- **The specification was the defect.** The fleet autoscaler was implemented from an issue with no
  specification. Followed literally, `03` and `05` left a runtime's least-recently-used router
  deciding placement: on one host it reloaded models 52–82 times a day, force-killed serving instances
  without a drain, and could evict the instance on the wrong GPU.
- Added invariant 43, feature `IW-SCHED-002`, tasks `P3-T23`–`P3-T25` (proof `owed`), reason code
  `INSTANCE_DRAINED`, and the GPU placement and hot-swap gate.

## v11 — 2026-09-04

- Added `39_INFERENCE_RUNTIME_TUNING`: throughput figures require a measured context depth;
  KV cache quantization is a measured choice and often a net loss; thread count is physical
  cores; accelerator memory needs working headroom; backend selection is measured; drafters
  are qualified per workload and depth with recorded acceptance; MoE placement has a hard
  ceiling when experts are not device-resident.
- Added invariant 42.

## v10 — 2026-09-03

Made the bundle enforceable rather than aspirational, from ideas recovered out of the archived
`InferWeave/*` repositories and rewritten under the clean-slate constraint.

- Added `38_EXECUTABLE_EVIDENCE_AND_CONFORMANCE`: registries as frozen data plus published
  document plus reconciling tests; hash-pinned conformance vectors with hostile cases;
  whole-object integrity; explicit proof status.
- Guards must be able to fail. `scripts/validate_specs.py --self-test` runs every data guard
  against a deliberately broken registry; removing a guard fails the self-test.
- Recorded that coverage measures coverage, not truth: a guard may not be deleted on a
  coverage signal.
- Added `OPEN_GATES.md`, a register of what is *not* approved, including that no independent
  reviewer is enrolled and every M-of-N threshold is presently 1-of-1.
- ADR template now states what a record authorizes and its exact relationship to prior
  records; measured figures must be reproduced, not quoted.
- Adopted token-free proof enrollment (`D-007`), replacing the operator bootstrap token.
- Added a machine-checked presentation policy to the dashboard specification.
- Added read-side ledger integrity to the prompt ledger.
- Added invariants 39–41.

## v9 — 2026-09-03

Aligned the bundle with operational evidence from production GPU inference.

- Made a deployment's context ceiling (`max_context_tokens`) a published manifest field and a
  hard, fail-closed admission bound evaluated before capacity arithmetic.
- Separated permanent from transient capacity failure: added non-retryable
  `CONTEXT_WINDOW_EXCEEDED` (`413`) alongside transient `NO_CONTEXT_CAPACITY` (`503`).
- Specified capability precedence — declared, measured, persisted — so an autoloading runtime
  cannot deadlock cold start on an unmeasured model.
- Required deployments to load at the largest context their measured envelope permits, making
  node-local context size derived rather than configured.
- Defined context-size aliases as request-shaping hints against one deployment rather than
  separate qualified deployments.
- Added a serviceability gate: schedulable only after a real request traverses the full
  authorization path, and every fail-closed gate ships a default policy.
- Made expected device inventory discovered and fingerprint-versioned; device-count change is
  a requalification trigger, never a permanent degraded state or silent CPU fallback.
- Required queue observability to read from the structure that orders admission.
- Specified reservation liveness: expiry on silence rather than elapsed duration.
- Added invariants 36–38 and opened D-006 on the status of `autospec-inferweave`.
- Made continuous operational feedback an explicit specification obligation.

## v8 — 2026-09-03

- Established `inferweave-specs` repository layout and agent contribution rules.
- Added canonical GPU watchdog, rescue and automatic rollback specification.
- Preserved prior GPU reset/restart-loop/rollback qualification requirements.
- Standardized persistent deployments on Docker Engine + Docker Compose.
- Standardized Slurm allocation workers on Apptainer.
- Added watchdog/operator CLI/dashboard/MCP tasking.
- Added deployment substrate feature/task traceability.
