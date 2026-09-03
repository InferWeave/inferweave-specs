# Changelog

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
