# 53 — Runtime-Family Conformance and Traceability

## Relationship to existing conformance

[`specs/38_EXECUTABLE_EVIDENCE_AND_CONFORMANCE.md`](38_EXECUTABLE_EVIDENCE_AND_CONFORMANCE.md),
[`conformance/`](../conformance/) (`runner.py`, `compatibility.yaml`,
`manifest.yaml`), and the feature registry (`contracts/feature-registry.json`)
define executable conformance and traceability for the protocol. This
specification extends those so the new runtime-family surface
([`specs/48`](48_RUNTIME_FAMILIES_AND_CAPABILITIES.md)) and native endpoints
([`specs/49`](49_NATIVE_CONTROL_PLANE_ENDPOINTS.md)) are covered by
machine-checkable conformance, and every new capability is traceable to a
feature id and a canonical task.

## Extensions

- **Conformance vectors.** Add runtime-family conformance fixtures to
  `conformance/` covering at least `embeddings`, `reranking`, `prediction`,
  `stt`, and `rag` advertisement/admission round-trips, plus a native-endpoint
  smoke vector for each family-specific endpoint in
  [`specs/49`](49_NATIVE_CONTROL_PLANE_ENDPOINTS.md).
- **Runner coverage.** Extend `conformance/runner.py` to run the new vectors and
  report per-family pass/fail, wired into the same exit-code and evidence
  discipline as existing conformance.
- **Feature registry.** Register one feature id per new capability (e.g.
  `IW-RT-001` runtime-family registry, `IW-RT-002` native endpoints, `IW-RT-003`
  transactional lifecycle, `IW-RT-004` pipelines, `IW-RT-005` durable jobs) in
  `contracts/feature-registry.json`, each mapped to its canonical task id.
- **Canonical task graph.** Add the new workstream-B tasks
  (`B-T01`…`B-T06`) to `contracts/canonical-task-graph.json` with their
  dependency edges, and keep `implementation/CANONICAL_IMPLEMENTATION_SEQUENCE.md`
  consistent.
- **Validation script.** Ensure `scripts/validate_specs.py --self-test` passes
  with the new specs and that every new feature id is referenced.

## Invariants

1. **Every capability is traceable.** A runtime-family capability is not
   conformance-covered unless its feature id is registered and its conformance
   vector exists.
2. **Self-test green.** `validate_specs.py --self-test` and `runner.py` pass
   after the extension; a red conformance run is a blocked change.
3. **No untested surface.** A native endpoint in
   [`specs/49`](49_NATIVE_CONTROL_PLANE_ENDPOINTS.md) without a conformance
   vector is reported, not silently merged.

## Required tests

- conformance-runs: `conformance/runner.py` reports the new family vectors and
  exits per the existing evidence discipline.
- registry-traceable: every feature id added is present in
  `contracts/feature-registry.json` and referenced by a conformance vector or
  canonical task.
- self-test-green: `scripts/validate_specs.py --self-test` passes.
