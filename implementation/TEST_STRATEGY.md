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

## Conformance vectors
Every protocol-level contract is proven against hash-pinned vectors rather than against a
reading of the document. Two implementations agreeing with the same prose is not evidence;
both agreeing with the same vector is. See `specs/38_EXECUTABLE_EVIDENCE_AND_CONFORMANCE.md`.

Every vector set ships hostile cases beside valid ones — malformed, replayed, truncated,
reordered, over-large, wrongly signed, boundary-value — each with its expected refusal. A
vector set of valid inputs only proves an implementation can succeed and says nothing about
how it fails.

## Guards are tested against known-bad input
Every structural guard runs additionally against a deliberately broken copy of the data it
guards, and a guard that passes there is a test failure.

A guard that silently stops checking reports success indefinitely and cannot be distinguished
from one that works. `scripts/validate_specs.py --self-test` applies this rule to this
repository's own validator.

## Coverage measures coverage, not truth
A scanner reports which code the suite reaches. It cannot report whether the reachable
behaviour is correct, and it cannot see a data state no test constructs.

Do not delete a guard because a coverage signal says no test reaches it. Remove a guard only
once the condition it detects is unreachable at the point of writing, and assert that
unreachability by test.

Where a proof depends on a storage-engine property — integrality, uniqueness, a constraint —
assert that premise against the live engine by attempting the write that would violate it. A
declared type is not always an enforced type.

## Whole-object integrity
Verification of an ordered, gapless record proves the property over the whole object, never
over the page in hand. A gap below a reader's cursor is invisible to a page-shaped check while
the stream replays as complete.

## Coverage
80%+ new logic is a useful target, but acceptance/property/failure coverage has priority over line-count gaming.

## Test evidence
Every implementation task reports exact commands/results and skips optional hardware tests explicitly when unavailable.


## Direct-path proof
For healthy direct-capable routes, instrument the gateway and assert it sees control/ticket/accounting bytes but **zero response stream payload bytes**. Repeat with regional-relay fallback and verify only the selected relay carries stream payload.

## Prompt-ledger proof
For ordinary gateway request fixtures:
- identity derivation and non-blocking record offer occur before route dispatch;
- a blocked or unavailable sink does not delay or refuse an otherwise valid route;
- the bounded buffer drops deterministically and exposes depth, loss, and degraded state;
- retry/failover events retain stable identities and lineage;
- prompt text never appears in logs/metrics/public snapshot fixtures;
- records that reach a durable sink remain idempotent, authorized, and audited.

For explicit durable-ingest fixtures:
- exactly one authoritative prompt record exists before acknowledgement;
- unavailable storage withholds acknowledgement or fails closed;
- prompt-content reads require authorization and create audit records.

## GPU telemetry proof
For every registered GPU fixture:
- static hardware/software fingerprint is complete;
- required supported live fields are emitted;
- unsupported sensors are explicit `unsupported`, never silently zero;
- request performance facts reference exact deployment/GPU/software fingerprints;
- version/config change forces a new fingerprint and qualification state.
