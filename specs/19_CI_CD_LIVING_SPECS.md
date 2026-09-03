# 19 — CI/CD, Historical Builds, Pi Reviews and Living Specifications

Every repository exposes current and historical delivery evidence.

## CI required

- format;
- lint/static analysis;
- unit tests;
- integration tests;
- contract/schema drift tests;
- security/dependency scan;
- builds/packages/images;
- targeted E2E where relevant.

Infrastructure-bound tests use real local services/containers when practical; if a required optional runtime is unavailable, skip explicitly rather than silently passing.

## Dashboard integration

Show:
- running builds;
- past builds;
- branch/commit;
- stage/status/duration;
- live and retained logs;
- test results/coverage;
- artifacts;
- Pi-generated implementation/review summaries;
- links to related requirement/task/PR.

## Pi review provenance

Store model/provider, role, prompt-template/spec version, commit SHA, result and evidence refs. AI review never substitutes deterministic tests.

## Changelog/spec evolution

Every architecture-affecting PR updates:
- CHANGELOG;
- relevant spec/ADR;
- feature registry/requirement IDs;
- API/schema docs;
- generated current-system map where applicable.

Do not regenerate an entire canonical spec from a model after every commit. Specs are version-controlled reviewed artifacts.
