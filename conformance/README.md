# InferWeave Protocol v1 — conformance suite

Defines conformance profiles (`IW-DATA`, `IW-NODE`, `IW-GATEWAY`, `IW-FEDERATION`,
`IW-OBSERVABILITY`, `IW-ADMIN`, `IW-FULL`) and reusable scenarios: schema validation, protocol
discovery, feature negotiation, registration, heartbeat, topology, events, retries, errors,
aliases, federation, capability advertisement, snapshot consistency, and backwards
compatibility. `manifest.yaml` declares profiles; `scenarios/` holds the tests. The reference
conformance suite is tracked by canonical task `P5-T28`; the compatibility matrix by `P5-T29`
(feature `IW-PROTO-002`).
