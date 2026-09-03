# Getting Started — One Empty Monorepo

## Canonical source repository

```text
InferWeave/inferweave
```

Existing contents are not authoritative. The implementation plan assumes a fresh implementation baseline.

## Safe repository setup

If the repository does not exist:

```bash
mkdir -p ~/src/InferWeave
cd ~/src/InferWeave
gh repo create InferWeave/inferweave --private --clone
cd inferweave
```

If it already exists, establish a fresh implementation root/branch according to your Git policy. Pi MUST NOT rewrite Git history or destroy existing branches unless explicitly authorized.

## Bootstrap

Create:
- Rust workspace;
- `apps/web` Next.js + TypeScript application;
- schema/generated-binding directories;
- PostgreSQL local stack;
- CI;
- docs/spec/ADR structure.

## Stack

- Rust: every production backend/control/node/relay/proxy service.
- Next.js + TypeScript: all browser surfaces.
- PostgreSQL: control state, prompt ledger, telemetry/benchmark warehouse initially.
- OpenTelemetry + Prometheus-compatible metrics.
- Docker Compose: local integration.
- Solana: no implementation work.

## Initial dependency spine

```text
protocol / IDs / errors
      ↓
storage + prompt-ledger + telemetry
      ↓
node + gateway
      ↓
capacity + routing + leases
      ↓
direct connectivity + local proxy
      ↓
OpenAI-compatible streaming
      ↓
Next.js live dashboard
```

## First working GPU weave

The first real milestone requires:

- one gateway/control process;
- two heterogeneous outbound-connected GPU nodes;
- complete GPU/runtime/model fingerprints;
- live temperature/power/utilization telemetry;
- every submitted prompt persisted;
- `/v1/models`;
- streaming `/v1/chat/completions`;
- model/context hard filtering;
- dynamic seat/context/KV capacity;
- sticky sessions;
- direct client/local-proxy ↔ node streaming;
- regional relay fallback;
- 503 infrastructure capacity semantics;
- 429 user/FairShare semantics;
- owner GPU priority/reclaim;
- Next.js GPU/model/request/telemetry dashboard;
- gateway carrying control traffic, not normal response-stream bytes.

## Pi rule

Do not inspect historical InferWeave repositories for code reuse.

Only inspect the current clean monorepo and this bundle.
