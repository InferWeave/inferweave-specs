# Independent E0 canonical contract review — 2026-11-05

Reviewed worktree: `/home/wohlgemuth/IdeaProjects/inferweave-specs-speed-contract-20261105`

Frozen HEAD: `9b83fb0641051bdc1675b08609989de9634cdf63`

Base: `9b1ff54a1895ff3616c0400941964e032b4c2c28`

## Verdicts

- **Contract compliance: PASS.** The frozen normative contract satisfies the E0 safety, authority, recovery, identity, compatibility and honest-proof requirements examined below. This verdict approves specification content only, not runtime execution or production qualification.
- **Quality: REQUEST CHANGES — one P2 finding.** The new offline regression suite is disconnected from the repository's normal validation/test entry points. Connect it before treating this delivery's anti-drift coverage as complete.

## Finding

### P2 — Run the new contract tests through standard gates

Location: `scripts/test_benchmark_speed_contract.py:32–59` (new standalone suite).

The schema mutation checks and per-wave overlap vectors are meaningful, but only the explicitly invoked standalone command runs them. The repository's CI runs `scripts/validate_specs.py`, its `--self-test`, and `conformance/runner.py` (`.github/workflows/protocol-ci.yml:20–25`); none imports or invokes this new suite. Likewise, `make check` / `make test` discover only `tests/smoke/` (`Makefile:7–15`). A focused search for `benchmark-speed`, `test_benchmark_speed` and `positive_overlap` across these runners and tests finds only the new script itself. The explicit driver/self-test and conformance call lists confirm the absence.

Consequently, a subsequent change to this frozen vocabulary/schema or overlap examples can pass ordinary gates after normal bundle-metadata regeneration without running their dedicated negative checks. That is a concrete regression-coverage gap for canonical frozen data (invariant 41 and P0-T01A's anti-drift model), despite the successful one-off invocation.

Requested repair: wire the existing suite into the canonical validation/conformance or self-test path used by CI, and expose it to the standard smoke/test target (a small smoke wrapper is sufficient). Preserve the explicit offline-only proof label. Verify the affected entry point invokes it and rejects a representative in-memory or isolated invalid contract/vector; no runtime, GPU, network or production exercise is needed.

No other actionable findings identified in the frozen diff.

## Compliance examination

- **Canonical authority and scope:** Read the task brief first, then AGENTS, README, START_HERE, resolved decisions, invariants, contribution rules, relevant specs 23/33 and spec46's status/authority definitions, selected implementation sequence/coverage/task entries, and OPEN_GATES. No decision, invariant, registry or deployment-substrate change was introduced. No second scheduler, registry, database or fixed-slot scheme is added.
- **Private authority:** Spec33:156–189 requires an actual privately constructed capability bound to resident supervisor, owned unreaped Child, exact saved leaf, live held lease, NodeOwned acquisition, gateway/node authority, restoration fingerprint and verified endpoint/deployment. Queue JSON, flags, durable PIDs, copied policy and serialized leases grant no authority. Release-channel loss, uncertain reap, floors and independent memory admission retain fail-closed fences. TaskSerial, ordinary constrained CLI, FakeEnv, Mac/protected/unknown resources remain refused/excluded.
- **Recovery ordering:** Spec33:166–174 places committed-capsule loading and held-journal import before current policy, manifest, readiness, corpus or catalogue checks. Original canonical RecordID must match capsule and imported record. Expired deadlines and policy absence/off do not disable completed recovery. Absence is separated from corruption/conflict/unsupported version; ambiguous starts cannot cause reruns. Import failure retains capsule and fence.
- **Time and cleanup:** Spec33:191–198 preserves one original expiration through preflight to commit, monotonic parent enforcement and once-derived child deadline, no serialized Instant or inference extension through cleanup grace. Parent kill/reap bounds stuck fsync. Spec33:142–148, 187–189 and inherited background text retain independent Stop/Scratch/Restore/Verify/Release and recovery-required fencing; elapsed deadline is not successful restoration.
- **Workload and measurement:** Spec33:200–207 limits actual generated corpus to 4 MiB, bounded streaming and terminal/provider-usage validation, at most four calibration calls plus C×R measured requests, and forbids separate hidden readiness/model-list/warmup/retry calls. Spec23:440–459 separates per-request admission ceiling from final provider-reported prompt-depth window, excludes calibration from measurement, and separates requested C, observed HTTP overlap and unknown backend generating concurrency. Every measured wave requires positive-duration overlap at C with half-open intervals; requested load and declarations cannot become physical observations.
- **Identity and compatibility:** Spec23:442–469 binds saved-leaf/suite/spec/corpus/input/load/output/sampling/seed/cache identity and preserves v1 semantics rather than reinterpreting old concurrency. Legacy v1 capsules lack observed runtime/GPU/deployment facts and cannot satisfy those exact axes. Valid workload evidence, exact-known-axis matching and qualification remain distinct. Unknown is neither zero nor wildcard.
- **Dependencies and production gates:** E7–E9 authenticated owner observations, additive payload v2 and producer receipts remain later engineering dependencies; no premature producer schema is added. Slurm resident attestation remains absent and unsupported execution refused. OPEN_GATES:3–20 and 1422–1433 keep owning-gateway composition, live memory safety, cancellation, canary, restoration, soak and qualification unsatisfied. Existing IW-GPUMEM-001 / P5-T30..32 remains an independent safety gate, not an implied runtime capability.
- **Traceability:** Existing IW-BENCH-003/P2-T19 and IW-BENCH-002/P2-T03 own AC-SPEED-01..08 with explicit owed status. Task cards, acceptance matrix and FEATURE_TASK_COVERAGE agree. Feature registry, graph and canonical sequence retain existing mappings and ordering; no duplicate registry or new task graph appears. The phase-5 safety dependency is explicitly retained as a gate rather than falsely represented as already implemented by phase-2 tasks.
- **Contract and tests:** The closed schema freezes contract metadata and acceptance ownership/status; it is not an execution payload or permission token. Mutations reject coverage-version drift, calibration-cap drift, fabricated backend measurement, a proven-status claim and extra authority fields. Vectors cover positive overlap in each wave, touching-only intervals, one failing wave, C=1 and nonpositive intervals. Their scope is correctly limited to offline vocabulary/arithmetic, with the integration gap above.

## Evidence inspected and limits

- Read the exact review package `.superpowers/sdd/iw-speed-contract-e0-plan-20261105/review-9b1ff54..9b83fb0.diff`, changed normative/contract/schema/test/task files, and `/tmp/iw-speed-contract-e0-report-20261105.md` as an evidence inventory, not as authority for conclusions.
- Read `/tmp/iw-e0-contract-test.log`: recorded **2 tests OK**. Read `/tmp/iw-e0-validate.log`: recorded **106 features, 172 canonical tasks, DAG valid**. The recorded final diff-check log is empty; its claimed exit code 0 comes from the delivery report. These successful suites were not rerun.
- Independently read `git rev-parse HEAD`: matches frozen HEAD. `git status --porcelain` produced no entries.
- Independently hashed the inherited patch: SHA-256 `5020511946b1a88ef1099fef943cd7d00a7bae92eae933b7619b40c2d79bfd50`. Its three-file background/gate/co-residency additions are present in the reviewed diff. The original dirty checkout was neither read nor changed by this review; historical non-mutation of that checkout is a delivery assertion, not independently attested here.
- No author reasoning was solicited. No subagents, source edits, git mutations, Cargo, network, GPU, Slurm/ops actions or production tests were used. The only written artifact is this requested review report.
- This is an independent specification review. It proves neither actual owned-child permissions nor cancellation, runtime measurement, live recovery, observation authenticity or production qualification. All AC-SPEED runtime proofs remain owed.
