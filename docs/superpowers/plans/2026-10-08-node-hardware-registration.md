# Hardware-only node registration and tokenless enrollment Implementation Plan

**Goal:** Publish one wire contract that the Rust gateway (`InferWeave/inferweave`) and the in-house
Go gateway (`metabolomics-us/inferweave-gateway`) implement concurrently: an optional versioned
`hardware` report on `POST /v1/node/register`, a valid hardware-only registration that is recorded
but never routable or dialled, an always-present `assignments` array in the response, and the
tokenless enrollment endpoints (`/v1/node/key`, `/challenge`, `/proof`) with their exact signed
transcript.

**Architecture:** The specs repository owns the contract (spec 47), a minimal gateway-acceptance
schema for `hardware`, a producer schema, schema fixtures, and a language-neutral vector file with
HTTP-level register cases and Ed25519 known answers. Both gateways replay the vectors in their own
suites. The runner proves the vectors are self-consistent and recomputes the known answers from the
seed with a dependency-free reference model. Nothing here changes an existing Protocol v1 object.

**Spec:** `specs/47_NODE_JOIN_AND_HARDWARE_REGISTRATION.md`
**Decision record:** `decisions/2026-10-08-open-proof-enrollment-and-hardware-registration.md`

## Global constraints

- Additive and backwards compatible: an older node that sends no `hardware` keeps joining, and an
  older gateway ignores an unknown member.
- `hardware` is informational. It never feeds routing, admission, trust or authentication.
- A registration with a non-empty `endpoint` or non-empty `models` keeps every existing check.
- Cover only what the repository can prove: the known answers are cross-checked with OpenSSL and
  with the reference implementation; both gateway implementations stay `owed`.

## Tasks

### Task 1: Contract text
- [ ] `specs/47_NODE_JOIN_AND_HARDWARE_REGISTRATION.md`: normative sections 3 to 7 (hardware field,
      hardware-only registration, `assignments`, enrollment wire and transcript, open policy).
- [ ] Cross-reference from `specs/03_NODE_BOOTSTRAP_DEPLOYMENTS.md` (enrollment prose stays there)
      and `specs/45_PROTOCOL_V1.md` (Registration, Conformance levels).
- [ ] ADR (Proposed) for the open enrollment policy and the hardware-only state.

### Task 2: Schemas, fixtures, vectors
- [ ] `schemas/v1/requests/node-hardware.json` (acceptance) and `node-hardware-report.json`
      (producer); valid and invalid schema fixtures; runner mapping.
- [ ] `conformance/node-join-vectors.json`: cases (a) to (f) plus boundaries, and two enrollment
      known answers (role claim, model claim) from the RFC 8032 section 7.1 test 1 seed.
- [ ] `conformance/node_join.py` reference model; `conformance/runner.py` runs it.
- [ ] `conformance/manifest.yaml`: scenarios `node_enrollment`, `hardware_registration`.

### Task 3: Traceability
- [ ] Feature `IW-NODEHW-001`; tasks `P5-T33` (Rust gateway) and `P5-T34` (Go gateway), both
      `owed`; task cards, sequence, indices, coverage tables, acceptance matrix.
- [ ] `OPEN_GATES.md` entry, `CHANGELOG.md` entry, `docs/compatibility.md` note.

### Task 4: Validation
- [ ] `python3 scripts/generate_bundle_metadata.py`, then `python3 scripts/validate_specs.py`,
      `--self-test`, `python3 scripts/test_validate_specs.py`, `python3 conformance/runner.py`.
- [ ] Re-verify the known answers with OpenSSL and record the commands in the vector file.

## Review focus

- The 65536-byte limit is measured on the compact serialization; vectors avoid the band where raw
  and compact differ.
- A hardware-only body still carries the baseline numeric members as `0` / `[]`.
- The Rust reference registers a proof-earned credential in a store `/v1/node/register` does not
  consult; spec 47 states the required behavior and `OPEN_GATES.md` records the gap.
