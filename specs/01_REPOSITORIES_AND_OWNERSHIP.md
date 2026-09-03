# 01 — Clean-Slate Monorepo Architecture

## Canonical repository

```text
InferWeave/inferweave
```

No historical InferWeave repository is an implementation dependency.

## Clean-slate rule

Existing code, schemas, migrations, binaries, APIs, package layouts and repository boundaries are ignored unless a requirement in this bundle explicitly reintroduces the concept.

There is no legacy migration/compatibility phase.

## Recommended layout

```text
inferweave/
├── Cargo.toml
├── rust-toolchain.toml
├── crates/
│   ├── iw-protocol/
│   ├── iw-core/
│   ├── iw-storage/
│   ├── iw-prompt-ledger/
│   ├── iw-telemetry/
│   ├── iw-benchmarks/
│   ├── iw-deployments/
│   ├── iw-capacity/
│   ├── iw-routing/
│   ├── iw-fairshare/
│   ├── iw-connectivity/
│   ├── iw-site/
│   ├── iw-bootstrap/
│   ├── iw-mcp/
│   ├── iw-health/
│   ├── iw-simulator/
│   ├── iw-auth/
│   ├── iw-jobs/
│   ├── iw-artifacts/
│   ├── iw-rag/
│   ├── iw-tools/
│   └── iw-images/
├── bins/
│   ├── inferweave-gateway/
│   ├── inferweave-node/
│   ├── inferweave-relay/
│   ├── inferweave-proxy/
│   ├── inferweave-bench/
│   ├── inferweave-site/
│   ├── inferweave-sim/
│   └── inferweave-cli/
├── apps/
│   └── web/                  # Next.js
├── schemas/
│   ├── openapi/
│   └── json-schema/
├── generated/
│   ├── rust/
│   └── typescript/
├── deploy/
├── tests/
│   ├── contract/
│   ├── integration/
│   ├── e2e/
│   ├── simulation/
│   └── chaos/
├── benchmarks/
├── docs/
│   ├── architecture/
│   ├── adr/
│   ├── specs/
│   └── operations/
└── scripts/
```

Do not pre-create dozens of empty crates. Create boundaries when implementation requires them.

## Language policy

Production services: Rust.

Web/dashboard/portal/Workbench: Next.js + TypeScript.

## Monorepo is not a runtime monolith

Independently deployable processes remain:
- gateway/control plane;
- node;
- relay;
- local proxy;
- benchmark/tuner;
- Next.js web.

They communicate using versioned contracts and can scale independently.

## Shared contracts

Canonical protocol/domain types live once.

OpenAPI/JSON Schema produce generated TypeScript/Rust bindings. CI rejects schema/binding drift.

## AutoSpec/Pi integration

AutoSpec/Pi integration is a thin module/client inside the monorepo unless a future distribution need justifies splitting it out.

It owns:
- session/project/task/workload metadata;
- routing preferences;
- local-proxy integration;
- diagnostics;
- prompt/request correlation.

It does not own physical inference scheduling.
