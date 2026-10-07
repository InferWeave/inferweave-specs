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

Not every object category is populated in this repository yet. Populating a category is tracked
by a canonical task (feature `IW-PROTO-002`); until then, objects of that category remain
representable through the extension namespace.
