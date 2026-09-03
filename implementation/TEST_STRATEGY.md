# Test Strategy

## Layers

### Pure/unit
- policy evaluation;
- hard-vs-soft constraints;
- capacity prediction;
- best-fit routing;
- FairShare score/deficit;
- error mapping;
- state machines;
- schema validation.

### Property tests
Prove:
- selected node always passes every hard filter;
- more API keys/sessions do not increase parent FairShare entitlement;
- idempotency keys cannot duplicate terminal job accounting;
- capacity never becomes negative;
- hard fallback constraints never relax.

### Simulation
Thousands of synthetic requests across heterogeneous nodes:
- context distributions;
- owner bursts;
- user contention;
- node failure;
- regional latency;
- model residency;
- cache affinity.

Measure wait, fairness, utilization, preserved long-context capacity and starvation.

### Contract
Generated clients against current OpenAPI/JSON Schema; backward compatibility fixtures.

### Integration
Real PostgreSQL and real gateway/node processes. Use mock OpenAI backend for deterministic failures, plus real inference backend smoke tests where hardware exists.

### E2E
At least two nodes:
- one R9700-class AMD;
- one NVIDIA or simulated heterogeneous profile.
Exercise OpenAI client, Workbench/AutoSpec metadata, disconnect, overload and failover.

### Failure/chaos
Kill node/backend/gateway mid-stream; stale heartbeat; packet loss/latency; DB restart; disk pressure simulation; revoked credentials; malformed advertisement; duplicate events; cancellation races.

### Soak
M1: 30 minutes.
Private alpha: 4+ hours mixed workload.
Production-candidate deployment/profile: 24–72 hours depending on risk.

## Coverage
80%+ new logic is a useful target, but acceptance/property/failure coverage has priority over line-count gaming.

## Test evidence
Every implementation task reports exact commands/results and skips optional hardware tests explicitly when unavailable.


## Direct-path proof
For healthy direct-capable routes, instrument the gateway and assert it sees control/ticket/accounting bytes but **zero response stream payload bytes**. Repeat with regional-relay fallback and verify only the selected relay carries stream payload.

## Prompt-ledger proof
For every submitted request fixture:
- exactly one authoritative prompt record exists;
- retry/failover lineage is preserved;
- prompt text never appears in logs/metrics/public snapshot fixtures;
- direct-node route still records prompt durably;
- prompt-content reads require authorization and create audit records.

## GPU telemetry proof
For every registered GPU fixture:
- static hardware/software fingerprint is complete;
- required supported live fields are emitted;
- unsupported sensors are explicit `unsupported`, never silently zero;
- request performance facts reference exact deployment/GPU/software fingerprints;
- version/config change forces a new fingerprint and qualification state.
