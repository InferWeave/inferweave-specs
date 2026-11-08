# Drift Watch: registry traceability (2026-11-08)

Drift Watch extends Capability Bench v1 (`OPEN_GATES.md`, "Autonomous capability & limitations
bench"). It was designed and implemented in `InferWeave/inferweave` before it had any entry in this
repository; design section 4.1 and the plan's Task 0 say its feature IDs, task cards and frozen
vocabulary are created here. This change does that and nothing else: no specification text, no
invariant and no production code changes.

## Basis (pinned)

| Item | Value |
|---|---|
| Implementation PR | `InferWeave/inferweave` #1491, merged 2026-11-05, merge commit `f9595585c72447cbd251dc8f3c5f90e393aa3e7a` |
| Implementation `origin/main` when this was written | `cf3dcb562fedf9aa6e1480e591d6c7e5a0f6530d` |
| Design | `docs/superpowers/specs/2026-11-04-drift-watch-design.md` (draft v2) |
| Plan | `docs/superpowers/plans/2026-11-04-drift-watch.md` (design phases 0-3) |
| Vocabulary source | `crates/iw-bench-record/vocabulary/capability-v2.json` at that `origin/main` |

## Registered

| Feature | Task | Design part | Implementation state |
|---|---|---|---|
| `IW-BENCH-004` vocabulary v2 and `scope-adherence` kind | `P2-T25` | 4.1 | merged, not deployed |
| `IW-BENCH-005` stack fingerprint | `P2-T26` | 4.2 | merged, not deployed |
| `IW-BENCH-006` scope-adherence family | `P2-T27` | 4.3 | merged, not deployed, never run on real hardware |
| `IW-BENCH-007` drift canaries and paired alarms | `P2-T28` | 4.4 | merged, not deployed, no history producer wired |
| `IW-BENCH-008` quantization baselines (text and logit tiers) | `P2-T29` | 4.5 | not started, not planned |

All five tasks are `owed` and owe themselves. This change did not reproduce any implementation test,
so it asserts no control as `proven`. The implementation PR reports these removal-mutation results,
quoted as that PR's claims and not as measurements made here: hardware refusal before any request
(both `check_hardware` calls removed fails the tests), proxy secrecy (a body `eprintln` fails it),
sandbox containment tests, alarm-rule tests, and the vocabulary reconcile test.

## Vocabulary v2

`contracts/capability-bench-vocabulary-v2.json` is a byte-for-byte copy of the implementation file
(SHA-256 `d209ff1d103b914e2ea7f151aeab400b3231ffa7d96a36d6fe663d9962c4df5e`). Against v1
(`contracts/capability-bench-vocabulary-v1.json`, untouched, equal to the implementation's
`capability-v1.json`) it changes exactly:

- `schema`: `iw.capability-vocabulary/1` to `iw.capability-vocabulary/2`;
- `capabilities` gains `scope-adherence` and `drift-canary`;
- `failure_classes` gains `unrequested.local-action`, `unrequested.egress`,
  `unrequested.publish` and `unrequested.destructive`, each attributed to component `unknown`
  (attribution comes from arm ablation, not from the grader).

Invariant 41 (shared vocabularies are frozen data reconciled by test): v1 is never edited; a new value
is a new file. The implementation reconciles its JSON with its enums by test; this repository's
reconciliation is that the file is a pinned byte copy. A later vocabulary change must add v3.
Readers must deploy before writers (`Record` rejects unknown fields). Nothing is deployed.

## Not done here (still owed)

- Registry traceability for Capability Bench v1 phases P1-P8 (`OPEN_GATES.md`). Drift Watch tasks
  depend only on `P2-T03`, not on unregistered P-numbers.
- Field-by-field reconciliation with specs 12, 23 and 24. The stack-fingerprint fields (engine build,
  KV dtype, speculative decoding, observed chat-template digest, GPU signature) must be checked
  against spec 23's telemetry fields; mismatches are to be listed, not resolved silently.
- A plan for design phase 4 (`P2-T29`).
- Any decision that scope or drift results feed `routing_eligible`. The design assumes no; invariant 35
  is served by producing evidence only.

## Security and privacy

No runtime, wire, credential or deployment change. The features describe a sandbox whose stubs record
and never perform outward actions, a recording proxy that keeps no credential or request body, and a
hardware guard that refuses protected allocations (R9700, Apple silicon) unless operator YAML names
them. Runs are operator-launched against the operator's own accounts. The Capability Bench gate
stays BLOCKED.
