# Monorepo Bootstrap Blueprint

## Start small

Initial Rust crates:

```text
crates/iw-protocol
crates/iw-core
crates/iw-storage
crates/iw-prompt-ledger
crates/iw-telemetry
crates/iw-deployments
crates/iw-capacity
crates/iw-routing
crates/iw-connectivity

bins/inferweave-gateway
bins/inferweave-node
bins/inferweave-proxy
```

Initial web:

```text
apps/web
```

Do not create unused crates just to match a theoretical final tree.

## PostgreSQL

Use one PostgreSQL deployment initially with logically separate tables/schemas for:
- control/routing/session state;
- prompt ledger;
- telemetry/benchmarks;
- accounts/API keys;
- jobs/artifacts.

Split storage only after measured load/security boundaries justify it.

## Local Compose

```text
postgres
gateway
node-a
node-b
mock-backend-a
mock-backend-b
proxy
web
```

## First canonical contracts

Implement first:
- protocol version;
- typed IDs;
- error envelope;
- node registration/heartbeat;
- deployment fingerprint;
- prompt record;
- GPU hardware/software inventory;
- GPU telemetry record;
- capacity/session record;
- route ticket.

## CI

Monorepo CI:
1. Rust format/lint/test;
2. Next.js lint/typecheck/test;
3. schema validation;
4. generated binding drift;
5. builds;
6. deterministic integration tests;
7. security/dependency scans.

## Dependency policy

Select current stable library versions at implementation time. The spec governs behavior and contracts, not arbitrary library version pinning.
