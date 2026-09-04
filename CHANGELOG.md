# Changelog

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
