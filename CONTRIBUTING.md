# Contributing

## Purpose

This repository accepts:
- new specifications;
- corrections;
- ADRs;
- task-graph improvements;
- acceptance tests;
- benchmark methodology;
- operational/security requirements;
- traceability fixes.

Production implementation code belongs in `InferWeave/inferweave`.

## Branch / PR shape

Recommended branch:

```text
spec/<feature-id>-short-description
```

PR title:

```text
[IW-XXXX-NNN] concise change
```

## Required PR content

Describe:
- problem;
- affected feature IDs;
- specs changed;
- decisions/invariants affected;
- task-graph impact;
- acceptance criteria;
- security/privacy/deployment impact;
- whether existing implementation work must be revisited.

## Validation

Run:

```bash
python3 scripts/validate_specs.py
```

No PR should leave:
- duplicate feature IDs;
- unmapped required features;
- task dependency cycles;
- missing task dependencies;
- task references to missing specs;
- Podman/Kubernetes production guidance;
- active Solana work.

## Architecture changes

A resolved decision changes only through an ADR.

Use:
- `decisions/ADR_TEMPLATE.md`.

## Agent-generated changes

Agent-generated PRs are welcome but must follow `AGENTS.md`.

Agents should include deterministic evidence rather than asserting that traceability is correct.

## Review

Changes to:
- invariants;
- security/privacy;
- prompt retention;
- direct-data-plane rules;
- owner priority;
- watchdog/rescue;
- container substrate;
- stable identity;
- FairShare;
- Solana deferral

require especially careful independent review.
