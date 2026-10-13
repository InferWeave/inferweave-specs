# InferWeave Protocol v1 — OpenAPI

This directory holds the OpenAPI definition (`inferweave-v1.yaml`) for the Protocol v1 HTTP
surfaces (control, observability, and data planes). It is tracked by canonical task `P5-T27`
(feature `IW-PROTO-002`); the file is not yet published. HTTP + JSON is the normative v1
transport; schemas remain transport-independent per `specs/45_PROTOCOL_V1.md`.

## Implemented read-contract evidence

`openapi/model-intelligence.yaml` and `openapi/model-intelligence.md` document the
additive operator read API and typed response/unsupported branches. Evidence and
remaining requirements are in `evidence/model-intelligence-2026-10-12/README.md`.
Current Go access is operator-only through its existing middleware; normative
shared operational and verified private tenant/user grants remain owed.
