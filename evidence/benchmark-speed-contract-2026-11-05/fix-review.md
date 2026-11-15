# E0 fix-round-1 independent re-review — 2026-11-05

Worktree: `/home/wohlgemuth/IdeaProjects/inferweave-specs-speed-contract-20261105`

Original reviewed HEAD / fix base: `9b83fb0641051bdc1675b08609989de9634cdf63`

Fix HEAD: `5f1befc71e0170235e024d29a2b9dcf59348f174`

Original branch base: `9b1ff54a1895ff3616c0400941964e032b4c2c28`

## Verdicts

- **Original P2 standard-gate wiring finding: ADDRESSED.**
- **Compliance: PASS.** Original contract compliance verdict stands; this narrow fix preserves its scope and offline-only proof semantics.
- **Quality: PASS.** No new actionable findings in the scoped fix diff.
- **Combined branch readiness: APPROVED for E0 specification integration**, based on the original full review plus this scoped fix review. No unresolved findings remain from those reviews. This is not runtime execution permission, production qualification, or a claim that the full smoke suite completed.

## Resolution evidence

`scripts/validate_specs.py:1056–1060` now invokes `tests/smoke/test_speed_contract_smoke.py` through the current Python interpreter with `-B`, captures diagnostics and propagates a nonzero status. CI already invokes this validator with `--self-test`, so the new contract suite participates in its existing canonical gate without a separate workflow.

`tests/smoke/test_speed_contract_smoke.py:1–12` imports the existing unittest `ContractTests` class without copying its assertions. The wrapper runs through unittest when invoked directly and is discoverable under `tests/smoke/` by the existing `make test` / `make check` target. The wrapper and validator comment retain explicit offline vocabulary/arithmetic scope. The underlying contract, schema, vectors and tests are unchanged.

The remaining two changed files are regenerated BUNDLE_INDEX.md and checksums.json; their changes track the validator edit and new wrapper. No normative spec, authority rule, acceptance status, task dependency or production gate changed.

## Recorded checks inspected

- `/tmp/iw-e0-fix-smoke.log`: focused wrapper pytest run, **2 passed, 4 subtests passed**.
- `/tmp/iw-e0-fix-selftest.log`: canonical `--self-test` completed, **106 features, 172 canonical tasks, DAG valid**, **12 registry and 7 file mutations**. These are the existing summary counters; the speed suite is invoked additionally by the inspected code.
- `/tmp/iw-e0-fix-invalid.log`: isolated invalid `calibration_max_calls=5` reached the speed suite through the same canonical entry point and exited **1**, with `test_frozen_shape_and_mutations` failing because **4 was expected**. The delivery report records metadata regeneration in the isolated copy; the observed failure is semantic, not a stale checksum failure. This supplies concrete rejection evidence for the wiring repair.
- `/tmp/iw-e0-fix-make-focused.log`: the standard make recipe executed `python3 -m pytest tests/smoke/ -q` with the reported focused selection; **2 passed, 244 deselected, 4 subtests passed**. Existing RefResolver deprecation warnings came from unchanged collection-time imports. They are not introduced by this fix.
- `/tmp/iw-e0-fix-validate.log`: **106 features, 172 canonical tasks, DAG valid**.
- Independently read `git rev-parse HEAD`: matches the frozen fix HEAD. `git status --porcelain` was empty.

The full `make test` run was interrupted and has no completed full-suite result. The focused make log's generic `test: all smoke tests passed` banner must be interpreted with its explicit **244 deselected** result, not as whole-suite success. The report also discloses an earlier selector matching no tests, followed by the corrected passing selection. Canonical self-test evidence used the existing venv with newer jsonschema because the system installation cannot run pre-existing registry-argument checks; no installation or network was needed. These limitations do not undermine the narrow gate-integration evidence.

## Scope and limits

Read the fix brief first, the exact `.superpowers/sdd/iw-speed-contract-e0-plan-20261105/review-9b83fb0..5f1befc.diff`, the delivery-report fix-round-1 tail, affected code and evidence logs. Original full review remains `/tmp/iw-speed-contract-e0-review-20261105.md`; unchanged source was not broadly re-reviewed. Successful suites were not rerun.

No source or git mutations, subagents, Cargo, network, GPU, runtime or operations actions were performed. Only this requested report was written. The original dirty checkout remained untouched by this review.

All runtime authority, owned-child, recovery, cancellation, measurement, authenticated observation, Slurm attestation, E7–E9 producer/payload/exact-coverage and production qualification obligations remain owed, exactly as recorded by the original contract review.
