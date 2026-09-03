# Feature Gaps and Conflict Resolutions

## Conflicts resolved

### Fixed slots vs dynamic seats
**Resolution:** dynamic seat/session + resource capacity wins. Compatibility fields may exist only at external legacy boundaries and must be deprecated.

### 429 vs 503 overload
**Resolution:** 503 for infrastructure/model/context capacity. 429 for user/API-key/rate/FairShare restriction.

### Workbench-owned Pi/runtime vs three-plane architecture
**Resolution:** preserve Workbench UX, move physical Pi/worktree/container lifecycle to autospec-orchestrator.

### autospec-inferweave as server vs thin integration client
**Resolution:** thin integration wins. Inference gateway/node code lives in InferWeave repos.

### Gateway as all-byte proxy vs gateway as coordinator
**Resolution:** direct client/local-proxy↔node is the default from the first real deployment. Regional relay is fallback; gateway byte proxying is last resort only.

### Mutable model name vs reproducible deployment
**Resolution:** aliases are mutable policy mappings; scheduled deployment identity is immutable/fingerprinted.

### Public dashboard node management vs provider privacy
**Resolution:** public/hosted dashboard is read-only/public-safe for provider nodes. Local admin is authoritative.

### Universal TPS comparison vs workload profiles
**Resolution:** benchmark profile includes model/runtime/precision/context/concurrency/workload. No universal cross-model TPS ranking.

### Blockchain-first incentives vs reliable inference
**Resolution:** deterministic internal accounting first. Solana implementation is deferred entirely until the working deployed GPU weave and global telemetry/benchmark system are stable.

## Features intentionally deferred, not removed

- anonymous trial playground;
- direct node/client data paths;
- million-provider sharding;
- challenge/reputation;
- RAG/LSP/tools;
- image generation/editing;
- visual annotation QA;
- federation rewards;
- public economics page;
- production blockchain of any kind.

They remain in `contracts/feature-registry.json` or the canonical specs.

## Open product decisions

See `decisions/DECISIONS_REQUIRED.md`. Pi must not silently choose a different product policy.


### Historical multi-repo design vs clean monorepo
**Resolution:** one clean monorepo wins. Historical repository boundaries are not preserved.

### Legacy compatibility vs direct implementation
**Resolution:** direct clean implementation wins. No migration/compatibility work exists unless a future external contract explicitly requires it.
