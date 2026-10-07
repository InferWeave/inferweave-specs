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
runtime/     runtime instance
requests/    request metadata, deadlines, estimates, locality, workload class
events/      event envelope, metric samples
errors/      error taxonomy and codes
jobs/        async job states and progress
artifacts/   artifact descriptor and cache state
```

Every object category is populated in this repository (common, errors, topology, model,
resources, runtime, requests, events, jobs, artifacts). All schemas are validated by the
conformance runner (`conformance/runner.py`) against `fixtures/`. The schemas are frozen
machine-readable data reconciled by test (invariant 41) via `scripts/validate_specs.py`; a
vocabulary value in prose or a schema enum that disagrees with the frozen data fails validation.
