# Release review and rollout authorization

The operator explicitly authorized PR creation, review, merge, and deployment to
`llm.metabolomics.us`, Farm, Hive and Whiteale on 2026-10-20. This is deployment
authority, not evidence of successful activation or recovery.

PRs: [Rust #1132](https://github.com/InferWeave/inferweave/pull/1132),
[Go #604](https://github.com/metabolomics-us/inferweave-gateway/pull/604), and
[specifications #309](https://github.com/InferWeave/inferweave-specs/pull/309).

Two independent review lanes examined all three changesets. The code reviewer
reviewed 65 changed files and found two medium issues; both were repaired. Final
recommendation: **APPROVE**. Architectural status after repair: **CLEAR**. These
are automated source reviews, not a claim of independent human approval.

- Rust now releases the control mutex before constructing or writing either
  statistics response. Real TCP-backpressure regressions cover authorized and
  unauthorized requests. The original method failed both tests; the repaired
  method passed both (0.47 s). Configuration help and parser-format/64 KiB
  bounds are documented. Follow-up implementation commit: `81e55e04`.
- UI and operational documentation no longer infer committed headers from a
  recorded HTTP 200. The new browser assertion failed against the earlier copy;
  Traffic and attention-diagnosis browser checks passed after the repair. Fresh
  TypeScript/build and complete Go formatting/vet/test/build gates passed.
  Follow-up implementation commit: `86cd57d`.

The two optional persistence checks remain unresolved as executable tests. A
bounded independent investigation compared production `c673fad2`, upstream
`de7619b6`, and the candidate. The entire persistence test file, post-stream
persistence sequence, `finish`, and deterministic request-ID helper are
byte-identical across those revisions. The fixtures stop reading at `[DONE]`
before post-stream facts necessarily persist and reuse one derived request ID
for distinct logical requests; one global-count assertion also races two
successful executions. This supports pre-existing fixture/identity assumptions,
not evidence of a new production change. No passing baseline execution or fix
for same-ID retry semantics is claimed, and no assertions were weakened.

Rollout preserves the deployed site-specific launchers and rollback releases.
Farm's installed drain/successor wrapper differs from the repository wrapper and
must not be overwritten. Whiteale's gateway owner watcher restarts dependent Laya
workers after a gateway-job replacement; activation is permitted only in a quiet
window, with the existing worker SIF, weights, identities and unrelated CDN/S3
services preserved. New gateways must report the merged revision and independent
timeout settings, restore their parent routes, and pass serving probes before
the rollout is reported successful.

## Persistence fixture gap closed

Test-only commit `efe0d866` drains bounded EOF, explicitly waits for the mock
node to hold its seat, supplies distinct logical request IDs and asserts exact
per-prompt facts. The repaired tests passed 2/2 against the candidate and 2/2
against unchanged `de7619b6` production code. Targeted strict Clippy and formatting
passed, and independent source review approved the stronger assertions.

The original baseline fixtures happened to pass while logging the same duplicate
attempt error, so a deterministic baseline failure was not reproduced. The
corrected fixtures close the timing/identity test gap; true repeated-ID attempt
accounting remains a separate pre-existing behavior, not a hidden product fix.
