# ADR — Configuration is one YAML file per service, never the environment

**Status:** Accepted for implementation  
**Decision owner:** Operator (berlinguyinca)  
**Date:** 2026-10-21  
**Authorizes:** Building and rolling out YAML-only configuration for the gateway (done: InferWeave/inferweave#1140, #1145); converting the remaining binaries. It does **not** authorize any deployment beyond the gateway's already-performed hive and zapp rollouts.  
**Relationship:** discloses invariant 44 of `specs/00_INVARIANTS.md`; amends no earlier record.  

## Measured basis

The stream-reliability limits that prompted this decision were idle 180 s and request 1800 s, as read from `crates/iw-gateway/src/inference_stream.rs` in `InferWeave/inferweave` before the change. No count of environment read sites is claimed here; the enforcement is the gateway's startup refusal, covered by `crates/iw-gateway/tests/config_startup.rs`.

## Context

The 2026-10-20 stream-reliability work shipped its inference timeouts as `IW_INFERENCE_IDLE_TIMEOUT_SECS` and `IW_INFERENCE_REQUEST_TIMEOUT_SECS`. An operator seeing "Inference stream exceeded its configured time limit" could not tell what the limit was: an environment is set at restart, is not auditable from the running process, and differs between launchers (hive, farm, whiteale, lab, fry, zapp).

## Options

1. Keep environment variables, document them.
2. Environment variables with a YAML file as an optional override.
3. One YAML file per service; no environment variable is ever read for configuration.

## Decision

Option 3. Invariant 44 states the rule. The gateway implements it: one `--config <path>` file; precedence flag, then YAML, then default; secrets are `*_file` paths; unknown keys, wrong types and out-of-range values fail startup naming the key; `GET /internal/config` reports the effective configuration with secrets redacted behind the metrics bearer token; a set `IW_*` or `INFERWEAVE_*` variable stops startup. Launchers write the file; the autoscaler and cluster tunnel scrub the variables from the processes they start.

## Consequences

- Positive: every limit is visible and auditable; launchers cannot silently differ.
- Negative: test harnesses that export `IW_*` variables for other binaries must start the gateway without them (main was red for one pipeline after #1140 for exactly this reason; fixed in #1145).
- Operational: the gateway launchers on hive, farm, whiteale, lab, fry and zapp now write `gateway.yaml`.
- Migration, still open: `inferweave` node/join/probe/cluster-init, relay, workers, drain, store and schema-gen still read `IW_*`; `deploy/farm/ops/gateway-peer.sh` depends on `inferweave join` environment. Each converts under this decision.

## Requirements affected

- Invariant 44 (`specs/00_INVARIANTS.md`)
- OPEN_GATES: the environment-variable gate is "partially satisfied" until the remaining binaries convert.

## Rollback/revisit trigger

A platform that can only pass a setting through the environment (not a file) and for which a launcher-written file is demonstrably impractical. Absent that, no revisit.
