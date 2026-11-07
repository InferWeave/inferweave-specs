# IW-PROMPT-001 bounded recorder repair evidence

## Why this policy exists

The operator's Farm incident investigation reported home-quota exhaustion and
large retained encrypted outbox files, followed by serving failure. The terminal
exit cause was not logged: **ENOSPC causing that exit is not proven**. This
source-only repair did not read prompt contents or operate Farm services.

At implementation baseline `379c9235763df7614e3634ae010a08d60a8a9f06`, the
ordinary gateway awaited durable ledger ingestion, sink startup opened the
outbox synchronously, and disk append had no byte or retention budget. The
4096-record queue bounded only queued records, not disk bytes. Deployed
`7e5d5cbf6152ba593b64847c8fc8a8cb83a8ab32` and that baseline had identical
`crates/iw-gateway/src/outbox.rs`: SHA256
`7058cf6bc6dffde03b133a733e0d9fc7671c9dcb3135763b055d162b47bde72d`.
Reproduce with `git show <commit>:crates/iw-gateway/src/outbox.rs | shasum -a 256`.

This was an implementation gap against the existing 2026-09-28 decision. The
specification also lacked encoded-byte/file-budget and stable-identity migration
policy; following only its event-count limit would not prevent retained file
sink growth. New numerical defaults are operator-selected policy ceilings,
**not measured GPU, filesystem or hardware capacity**.

## Source components and verification scope

- Implementation `ba5bac18ee03eff0e570928e49b626a230123e88`: managed one-use
  prepared sealing entropy. The held-RNG regression passed; replacing the
  nonblocking seal with the old blocking encrypt failed within its test
  deadline. Restored source SHA256
  `a9d27d3a9e0b63cb0c1961dc032f4a7a8a6932f0637d4b86b23f5645a9343dbe`.
- Implementation `18a1d5ef`: bounded producer/file sink and ordinary route
  separation. Focused local tests cover ciphertext-only offers, fixed memory
  policy, frozen sink factory before gateway startup, authenticated request
  success independent of durable ledger, stable tenant/request identity,
  per-event loss/unresolved retries, file byte budget/restart/partial write,
  private permissions, cooperative locks, symlink rejection and bounded scan.
  A private-copy file-budget removal control failed; the original source was
  not mutated. This proves that local private-directory fixture's budget guard,
  not remote lock semantics. Independent review identified unsafe writable-root
  and historical hardlink/permission/reference-stability gaps. Those were fixed
  in `61e504124e4fbb94df3595829d7401a6c581bb82`, independently re-reviewed LGTM,
  with14 focused Cargo tests and15 private exact-module tests. The
  [exact-source control receipt](file-namespace-control-proof.json) records8/8
  behavioral removal failures, each selecting one test. It explicitly preserves
  the earlier7/8 scan-loop survivor and the later scan-work assertion that kills
  it; the survivor is not retroactively counted as success.
- Implementation `3f96ba5e246b92226dd6d915dc0d1776fd91bfce`: atomic semantic
  receipts for supported PostgreSQL prompt/attempt/fact recording. Local
  preflight/migration-roster/error tests pass. One real isolated PostgreSQL16.15
  sequential transaction test passed under explicit Linux Rust1.91.0, using the
  existing cached image without a pull. The sanitized
  [receipt](postgres-sequential-receipt-proof.json) pins source, archive, test
  binary, image, resources and verified exact-container/password-file cleanup.
  It covers sequential identical retries, changed digests, legacy-row conflicts,
  missing parents, unrelated success and deferred/cascading parent constraints.
  **That first run is not concurrent-race or network-lost-acknowledgement proof**.
  A later [actual concurrent/ACK-loss receipt](postgres-concurrent-ack-proof.json)
  pins test-fix source `0ae0f23c7dd6d826e2594de523d96b54b7a65785` while the
  storage implementation remains `3f96ba5e`. PostgreSQL lock waits prove actual
  row/receipt contention; identical writers produce2 Ok/1 row/1 receipt, while
  mismatched digests produce1 Ok/1 conflict. The proxy observes and withholds
  backend CommandComplete(COMMIT), the caller errors, direct queries see the
  committed row+receipt, and retry keeps one of each. Exact-container/password
  cleanup was independently rechecked. Proxy limits are source-enforced, not an
  independent OS-thread census. An intermediate
  [failed fixture run](postgres-failed-fixture-run.json) is preserved: invalid
  test IDs stopped execution before any marker, proving neither property; that
  test grammar was fixed and checked locally before the successful retry.
  No response-payload storage is introduced.
- Corrected secret-file/static-identity CLI startup fixtures passed: legacy
  implicit identity fails before recorder filesystem access, and an explicitly
  provisioned stable identity serves `/health` while the recorder-only database
  is unreachable. Full affected auth/alias/cancellation regressions, unknown
  in-flight outcome negatives and independent whole-diff review remain **owed
  at this checkpoint**. Final artifact/test pins must be appended before
  claiming the repair complete. A passing component test is not deployment.

No new feature ID, task dependency, execution authority or production activation
is created. Existing P1-T08 durable ingest stays fail closed; P1-T25 owns failure
injection and integrated review. Buffer identity is not durable acknowledgement,
route authorization or an alias execution claim.

## Qualification and migration still owed

- Independent review and final source/artifact pins; target runtime startup and
  cancellation checks with the old stable identity preprovisioned independently.
- Actual target shared-filesystem locking and exclusion of older writers; no
  correctness claim is inherited from a local temporary-directory test.
- Explicit operator-authorized, audited preservation/drain/retention of existing
  acknowledged data. The source never automatically deletes it to make space.
- Production rollout and any GPU/HPC/CI changes remain separately gated.

## Frozen outcome vocabulary and current integration checkpoint

The [canonical contract](../../contracts/recording-outcomes-v1.json),
[document](../../docs/contracts/recording-outcomes-v1.md) and
[decision addendum](../../decisions/2026-11-06-recording-resource-policy.md)
freeze known-loss/unknown/health/sink classes, policy defaults, count ceilings
and the fixed entropy bound. The Python reconciler has8 passing tests including
explicitly malformed/undeclared data and document drift. Rust vendors the exact
bytes and tests emitted labels, source enum classes, defaults and invalid policy
vectors. No runtime fetch is used.

A complete source-manifest-pinned gateway run at `b373eca8` executed with actual
installed cargo/rustc/rustdoc1.91 on a new owned Mac target:40/41 passed. It exposed
a fixture assumption that a prepared-but-pending entropy send was immediately
consumable. The corrected source names the gauge `entropy_prepared`, fixes the
reservoir independently of lowered event counts, and uses a condition-variable
N+1 preparation barrier. Count/full/byte assertions are unchanged. The next
stable-source1.91 execution and before/after manifest comparison are **owed at
this checkpoint**; do not call the partially failed run fully qualified.
Unknown-outcome, encoded-byte and count-ceiling private removal controls and
whole affected auth/alias/upstream validation remain **owed** until their exact
source results are attached. Production, remote filesystem and migration gates
remain closed regardless of these component results.
