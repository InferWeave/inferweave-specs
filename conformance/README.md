# InferWeave Protocol v1 — conformance suite

Defines conformance profiles (`IW-DATA`, `IW-NODE`, `IW-GATEWAY`, `IW-FEDERATION`,
`IW-OBSERVABILITY`, `IW-ADMIN`, `IW-FULL`) and reusable scenarios: schema validation, protocol
discovery, feature negotiation, registration, heartbeat, topology, events, retries, errors,
aliases, federation, capability advertisement, snapshot consistency, and backwards
compatibility. `manifest.yaml` declares profiles and required scenarios. `runner.py` is the
language-neutral conformance harness: it validates every `fixtures/valid/` and
`fixtures/federation/` fixture against the canonical JSON Schemas and requires every
`fixtures/invalid/` fixture to fail its schema, failing the run when a fixture behaves
unexpectedly. `compatibility.yaml` is the machine-readable compatibility matrix;
`release-manifest.yaml` records the immutable artifacts published per protocol version.

Runtime-family vectors are contract-tested offline by default, including executable positive and
negative request bodies. The offline runner prints `native HTTP: NOT RUN`; it does not treat an
OpenAPI path as proof of a running endpoint. To replay those cases against a real implementation,
run `python3 conformance/runner.py --live-base-url http://host/inferweave/v1`. Only that mode sends
HTTP and checks the returned status codes.

`native-link-binding-vectors.json` adds implementation-neutral negotiation, acknowledgement, and
revocation cases for the exact registration plus Link-incarnation binding required by
`iw.link-native-request/1`. These are fixture semantics; production atomicity remains open-gated.

The conformance suite and fixtures are delivered (feature `IW-PROTO-002`, task `P5-T28`);
production conformance by a running component remains `owed` until the reference implementation
ships.
