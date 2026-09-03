# First 15 Pi Tasks — Clean Monorepo

1. Bootstrap Rust workspace + CI/workspace lint policy and create the `inferweave` CLI binary.
2. Implement read-only `inferweave doctor --json` / `probe --json`, then bootstrap `apps/web` as Next.js + TypeScript.
3. Create canonical protocol IDs/errors/versioning/schema generation.
4. Create PostgreSQL storage crate + local Compose stack.
5. Create encrypted prompt-ledger schema + idempotent ingest API.
6. Create node hardware/GPU/software discovery.
7. Create GPU telemetry schema + collector fixture.
8. Create node identity/enrollment + outbound control connection.
9. Create immutable deployment manifest/fingerprint.
10. Create gateway registry/freshness + `/v1/models`.
11. Create session/seat/context/KV capacity model.
12. Create hard-filter + best-fit routing property tests.
13. Create direct route ticket/rendezvous contract.
14. Create local-proxy direct-node transport against mock backend.
15. Complete vertical slice: prompt persisted → gateway routes → proxy connects directly to node → response streams → request/GPU telemetry persists.

Historical repos are not read for implementation reuse.


## After the core GPU-weave vertical slice

Implement:
1. stable provider/cluster/host/GPU identity;
2. worker/allocation identities;
3. rediscovery/reconciliation tests;
4. model recommendation candidate registry;
5. Slurm scheduler adapter;
6. allocation-scoped node mode;
7. gateway desired-deployment assignment;
8. reservation-aware drain;
9. Slurm benchmark jobs.


## Bootstrap/MCP follow-on tasks
- `init plan gateway`;
- container stack renderer;
- one-time enrollment;
- `init gateway`;
- `init node`;
- `init edge`;
- `init site`;
- `verify/status/support-bundle`;
- control-plane MCP read resources/tools;
- local MCP diagnostics;
- AI install prompt acceptance test.
