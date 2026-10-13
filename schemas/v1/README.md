# InferWeave Protocol v1 — JSON Schema

The JSON Schema under this directory is **authoritative** for Protocol v1 wire objects. See
`specs/45_PROTOCOL_V1.md` ("Schema layout and rules") for the schema rules.

Layout:

```text
common/      shared envelopes: protocol version, identity, features, provenance,
             extensions
errors/      protocol error envelope and error taxonomy
topology/    gateway, node, device, allocation, residency hierarchy
model/       model, model variant, capabilities, requirements, placement, residency,
             alias
resources/   capacity, seats, memory
runtime/     runtime instance, isolated adapter contract, single-flight load request
deployments/ standalone deployment manifest/live projection
requests/    request metadata, deadlines, estimates, locality, workload class, family requests
events/      event envelope, metric samples
errors/      error taxonomy and codes
jobs/        async job states and progress
artifacts/   artifact descriptor and cache state
```

Protocol 1.1.0 adds the `iw.gpu-memory` schemas of `specs/46_GPU_MEMORY_INTELLIGENCE.md`:
`resources/quantity.json`, `pressure.json`, `reservation.json`, `gpu-memory-*.json`,
`rebalance-decision.json`, `placement-simulation-*.json`, and `events/gpu-memory-event.json`. They
are camelCase and keep `additionalProperties: true`, so a newer producer's fields never break an
older reader.

Protocol 1.1.0 also adds `requests/node-hardware.json` (what a gateway accepts in the optional
`hardware` member of `POST /v1/node/register`) and `requests/node-hardware-report.json` (the
version 1 layout a node should send) of `specs/47_NODE_JOIN_AND_HARDWARE_REGISTRATION.md`.

The specs/48–53 additive runtime protocol adds `runtime/adapter.json`,
`runtime/load-request.json`, `deployments/deployment.json`, and the standalone family request
schemas. Legacy job and reservation documents remain valid; new runtime behavior is selected only
through feature negotiation and versioned additive members.

Every object category is populated in this repository (common, errors, topology, model,
resources, runtime, requests, events, jobs, artifacts). All schemas are validated by the
conformance runner (`conformance/runner.py`) against `fixtures/`. The schemas are frozen
machine-readable data reconciled by test (invariant 41) via `scripts/validate_specs.py`; a
vocabulary value in prose or a schema enum that disagrees with the frozen data fails validation.
