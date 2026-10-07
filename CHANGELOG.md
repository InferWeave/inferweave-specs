# InferWeave Protocol changelog

This file records the InferWeave Protocol release history and compatibility-relevant changes.
Version numbers are semantic and match the `VERSION` file. See `specs/45_PROTOCOL_V1.md` for the
versioning rules and the protocol change workflow.

## 1.0.0 — initial protocol (in progress)

The first Protocol v1 wire contract. Formalizes the scheduler-neutral vocabulary of
`specs/44_CORE_PROTOCOL.md` into a versioned, machine-readable, language-neutral contract:

- protocol versioning and feature negotiation
- three planes (data, control, observability)
- stable identity model and request/trace identity
- canonical objects and JSON Schemas under `schemas/v1/`
- events, state machines, canonical enums, and error taxonomy
- aliases, routing, affinity, jobs, streaming, and async jobs
- conformance levels and compatibility matrix

Status: specification only, BLOCKED for production. All required tests are `owed` by canonical
tasks `P5-T24`–`P5-T29` (feature `IW-PROTO-002`).
