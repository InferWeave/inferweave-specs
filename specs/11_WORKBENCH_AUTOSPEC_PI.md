# 11 — Workbench, AutoSpec and Pi Integration

## Workbench features to preserve

- persistent user-facing sessions/history;
- chat and agentic task views;
- conversation split/fork;
- files/artifacts;
- Markdown/HTML/YAML/XML/JSON/code rendering and downloads;
- coding workspace and diff/review inspection;
- MCP/tool catalog and permission-aware tool invocation UX;
- context/token/capacity visibility;
- actual selected deployment/region/privacy/fallback visibility;
- image job progress/artifacts;
- favorites/saved sessions;
- attach/resume to durable orchestrator execution where authorized.

## Ownership correction

Workbench does **not**:
- directly spawn Pi;
- own Pi session storage;
- create/manage worktrees;
- provision Docker environments;
- schedule GPU inference.

Those capabilities belong to AutoSpec/autospec-orchestrator/InferWeave respectively.

## `autospec-inferweave`

This repository is a thin integration layer. It passes:
- stable session ID;
- project/repository/initiative/task IDs;
- workload/role hints;
- privacy/context/model constraints;
- fallback preferences where policy permits.

It consumes route/result metadata and exposes diagnostics to AutoSpec/Pi.

## Prefix reuse

AutoSpec/Pi should structure reusable system/tool/AGENTS/spec/repository context deterministically. InferWeave reports prefix cache behavior and retains compatible session affinity. The network does not assume WAN KV migration.

## Separation of duties

InferWeave may route models but does not decide which model role may review the same implementation. AutoSpec policy enforces independent planning/review/test roles.
