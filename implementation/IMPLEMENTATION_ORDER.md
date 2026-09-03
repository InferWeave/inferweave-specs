# Implementation Order

The authoritative task-by-task order is:

- `implementation/CANONICAL_IMPLEMENTATION_SEQUENCE.md`
- machine-readable: `contracts/canonical-task-graph.json`

Do not derive a different sequence from individual specs.

## Canonical phases

0. Foundation / bootstrap CLI / schemas / dev environment.
1. Working direct GPU weave.
2. Benchmark-driven private alpha and model recommendations.
3. Persistent sites, Slurm ephemeral resources, caches, production bootstrap, MCP and operations.
4. Durable jobs, Workbench, CI history, RAG/LSP/tools, vision/images.
5. Multi-region HA, federation, verification and production release.
6. Solana remains deferred until explicitly reopened.

Every phase has a mandatory gate in `implementation/PHASE_GATES.md`.

The task graph is optimized for 50–100K-context agents using `implementation/CONTEXT_50_100K_STRATEGY.md`.
