# Private observability contract evidence — 2026-10-20

Base: specs main `149ba26` (failure-rollup contract #313). This patch adds a
private HTTP contract; it does not implement the runtime HTTP server or database.
The unchanged event/rollup/failure v1 contracts remain the nested DTO authority.

- `red.log`: the initial seven focused cases fail because the new boundary
  validator is absent. This records tests before implementation.
- `green.log`: the initial nine focused tests pass after implementation, including strict
  decoding, header/source/epoch checks, content/authority injection rejection,
  query bounds, cursor binding, nested pair validation and guard mutations.
- `review-red.log` / `review-green.log`: review regression tests first fail on
  extreme decimal exponents, ambiguous framing/credentials, page ordering,
  retention boundaries and missing exact reliability selectors, then all fourteen
  focused tests pass after the cohesive fixes.
- `unicode-red.log`: escaped lone-surrogate object keys fail the additional
  rejection test before the decoder validates all keys recursively; those cases
  are included in the final fourteen-test `review-green.log`.
- `conformance.log`: all repository fixtures, vectors and OpenAPI references pass;
  the new private OpenAPI/auth/cache contract guard runs in the same command.
- `validation.log` and `regression.log`: final spec validation/self-test and smoke
  regression command output, copied after execution, with bundle metadata then
  regenerated and the validation rerun outside the tracked evidence directory.
- `static.log`: Ruff on the two new Python files and Python AST parsing for all
  changed Python files. The available LSP tool is TypeScript-only and reports
  `tsc skipped: no tsconfig found`; no Python LSP/typecheck proof is claimed.

Commands are `python3 -B tests/smoke/test_private_observability.py`,
`python3 -B conformance/runner.py`,
`python3 -B scripts/validate_specs.py --self-test`, and
`python3 -B -m pytest tests/smoke/ -q`.

Proof scope is offline only. Real HTTP size enforcement before buffering,
credentials/revocation/registration races, durable ACK/outbox and database restart,
snapshot concurrency, complete independent capture accounting, and transactional
paired generation/sealing/pruning all remain **owed** (AC-PRIVATEOBS-01..06).
The private API and collection remain default disabled. No public release,
retention migration or deployment gate is opened by these tests.
