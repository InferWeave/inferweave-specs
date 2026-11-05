# E0 canonical speed contract delivery

Worktree: /home/wohlgemuth/IdeaProjects/inferweave-specs-speed-contract-20261105
Branch: feat/benchmark-speed-execution-contract-20261105
Base: 9b1ff54a1895ff3616c0400941964e032b4c2c28
Commit: 9b83fb0641051bdc1675b08609989de9634cdf63

Inherited draft provenance: applied the exact /tmp/iw-existing-benchmark-spec-draft-20261105.patch, SHA-256 5020511946b1a88ef1099fef943cd7d00a7bae92eae933b7619b40c2d79bfd50, after apply-check, solely in the clean isolated worktree. Its three files (OPEN_GATES and specs 23/33) are included in the same commit as the subsequent contract. Original dirty checkout was not touched. No push or implementation repository edits.

Feature/task links: IW-BENCH-003/P2-T19 and IW-BENCH-002/P2-T03, with existing IW-GPUMEM-001 independent safety dependency. AC-SPEED-01–08 are all owed. Contract/schema are closed vocabulary and offline shape checks, not executable authority or a runtime payload schema.

Changed files: specs/23_GLOBAL_TELEMETRY_BENCHMARKS.md, specs/33_RESUMABLE_BENCHMARK_DAG.md, OPEN_GATES.md, contracts/benchmark-speed-execution.json, schemas/v1/benchmark-speed-execution-contract.json, conformance/benchmark-speed/overlap-vectors.json, scripts/test_benchmark_speed_contract.py, tasks/phase-2/P2-T03.md, tasks/phase-2/P2-T19.md, implementation/ACCEPTANCE_TEST_MATRIX.md, implementation/FEATURE_TASK_COVERAGE.md, generated BUNDLE_INDEX.md and checksums.json. Total 13 files, 512 additions and 15 deletions. Existing registry/graph/sequence mappings were not changed because no new feature/task/dependency is introduced; explicit links are in task cards and coverage/acceptance matrix.

Validation, final tree:
- python3 scripts/generate_bundle_metadata.py — completed, refreshed bundle indexes/digests.
- python3 scripts/test_benchmark_speed_contract.py — 2 tests OK; /tmp/iw-e0-contract-test.log. Closed vocabulary mutations and half-open per-wave overlap vectors only; these do not establish runtime behavior.
- python3 scripts/validate_specs.py — OK: 106 features, 172 canonical tasks, DAG valid; /tmp/iw-e0-validate.log.
- git diff --check 9b1ff54a1895ff3616c0400941964e032b4c2c28 HEAD — exit 0; /tmp/iw-e0-final-diff-check.log.
- git status --porcelain — empty after commit.

An intermediate sequence edit failed the graph/sequence consistency guard; it was removed before the final successful run and commit. No RED runtime claim is made.

Limitations: no production, runtime, GPU, live cancellation, owned-child, or qualification proof; all remain owed. E7–E9 authenticated producer/observed payload/exact coverage and Slurm resident attestation are future engineering dependencies. No independent review has yet taken place; releasing source slot for independent review now.

## Fix round 1 — standard gate coverage

Commit 5f1befc71e0170235e024d29a2b9dcf59348f174 (base 9b83fb0641051bdc1675b08609989de9634cdf63). CI's `python3 scripts/validate_specs.py --self-test` invokes the existing standalone offline suite through `tests/smoke/test_speed_contract_smoke.py`; the same wrapper is discovered by `make test` and `make check`. Original standalone tests remain unchanged. Regenerated BUNDLE_INDEX.md and checksums.json. Offline checks remain shape/arithmetic proof only; all runtime and production gates remain owed.

- `/tmp/ci585-venv/bin/python -m pytest tests/smoke/test_speed_contract_smoke.py -q`: 2 passed, 4 subtests passed; /tmp/iw-e0-fix-smoke.log.
- `/tmp/ci585-venv/bin/python scripts/validate_specs.py --self-test`: passed, 106 features, 172 tasks, 12 registry and 7 file mutations; /tmp/iw-e0-fix-selftest.log.
- Isolated temporary copy: changed `calibration_max_calls` to 5 and regenerated metadata, then ran the same `--self-test` entry using the venv Python. Before wiring it exited 0; after wiring it exited 1 in `test_frozen_shape_and_mutations`, reporting `4 was expected`. Test harness asserted that exact failure; /tmp/iw-e0-fix-invalid.log. No live source was mutated for this proof.
- `PATH=/tmp/ci585-venv/bin:$PATH PYTEST_ADDOPTS='-k test_speed_contract_smoke' make test`: 2 passed, 244 deselected, 4 subtests passed; /tmp/iw-e0-fix-make-focused.log. A full `make test` run was deliberately interrupted while still progressing, so no full-suite result is claimed. An earlier focused selection matched no tests and exited 5; corrected selection above passed.
- `python3 scripts/validate_specs.py`: passed; /tmp/iw-e0-fix-validate.log. `git diff --cached --check`: passed before commit. Worktree clean after commit.

Environment: system jsonschema 4.10.3 cannot run existing self-tests using the newer `registry` argument, so CI-equivalent tests used existing /tmp/ci585-venv with jsonschema 4.26.0; no dependencies installed or network used. Original checkout untouched, no push. Source slot released for independent review.
