# Feature → Canonical Task Coverage

Features: **92**

| Feature | Priority | Phase | Owner component | Canonical tasks |
|---|---|---|---|---|
| `IW-CORE-001` OpenAI-compatible text inference | P0 | 1 | control-plane | `P0-T02`, `P0-T06`, `P1-T09`, `P1-T10`, `P1-T24` |
| `IW-NODE-001` Outbound-only node enrollment and heartbeat | P0 | 1 | node | `P1-T01`, `P1-T02`, `P1-T03` |
| `IW-CAP-001` Seat/session + context/KV capacity accounting | P0 | 1 | control-plane+node | `P1-T11`, `P1-T12` |
| `IW-ROUTE-001` Model/capability hard filtering | P0 | 1 | control-plane | `P1-T13`, `P2-T14` |
| `IW-ROUTE-002` Best-fit context packing | P0 | 1 | control-plane | `P1-T14` |
| `IW-ROUTE-003` Sticky session/cache affinity | P0 | 1 | control-plane | `P1-T15` |
| `IW-BP-001` Bounded backpressure 503/429 semantics | P0 | 1 | control-plane | `P1-T12`, `P1-T19` |
| `IW-DP-001` NAT-safe persistent relay | P0 | 1 | control-plane+node | `P1-T03`, `P1-T18` |
| `IW-OBS-001` Route/capacity/request telemetry | P0 | 1 | control-plane+node | `P1-T05`, `P1-T20` |
| `IW-UI-001` Live node/model/capacity/session dashboard | P0 | 1 | control-plane | `P0-T09`, `P1-T21` |
| `IW-TUNE-001` Node benchmark/tuning and qualified profiles | P0 | 2 | node | `P2-T02`, `P2-T09` |
| `IW-QOS-001` Hierarchical FairShare and anti-gaming | P1 | 2 | control-plane | `P2-T12` |
| `IW-QOS-002` Owner reserve/reclaim | P1 | 2 | control-plane+node | `P2-T11` |
| `IW-DP-002` Regional relay/direct path/rendezvous (link upstream role: spec 63) | P1 | 3 | control-plane+node | `P1-T16`, `P1-T18`, `P3-T08`, `P5-T03` |
| `IW-PROXY-001` Local edge proxy/cache | P1 | 3 | autospec-client | `P1-T17` |
| `IW-WB-001` Workbench persistent sessions/fork/files/rendering | P1 | 3 | web/workbench | `P4-T03`, `P4-T04`, `P4-T05` |
| `IW-PUBLIC-001` Anonymous bounded playground | P2 | 4 | control-plane | `P4-T13` |
| `IW-RAG-001` Agentic RAG/provenance | P1 | 4 | node | `P4-T07` |
| `IW-LSP-001` LSP/tool capability brokering | P2 | 4 | node | `P4-T08` |
| `IW-IMG-001` Distributed image generation/editing | P1 | 4 | control-plane+node | `P4-T10`, `P4-T11` |
| `IW-IMG-002` Deterministic annotated technical images + vision QA | P2 | 4 | node | `P4-T12` |
| `IW-JOB-001` Durable async jobs/events/artifacts | P1 | 3 | control-plane | `P4-T01`, `P4-T02` |
| `IW-CI-001` Build history/logs/Pi review dashboard | P1 | 3 | control-plane | `P4-T06` |
| `IW-SCALE-001` Regional/multi-gateway HA | P1 | 5 | control-plane | `P5-T01`, `P5-T02`, `P5-T03`, `P5-T06` |
| `IW-ECON-001` Internal deterministic usage ledger | P1 | 2 | control-plane | `P2-T16` |
| `IW-ECON-002` Solana local/devnet settlement adapter | P2 | deferred | control-plane | `D-T01` |
| `IW-AUTOSPEC-001` Thin AutoSpec/Pi InferWeave integration | P0 | 2 | autospec-client | `P2-T06`, `P2-T15` |
| `IW-NODE-002` Node hardware/runtime/model self-discovery and safe config proposal | P1 | 2 | node | `P0-T04`, `P1-T04`, `P1-T06`, `P1-T23` |
| `IW-FED-001` Intermediate coordinator/federation roles | P1 | 5 | control-plane | `P5-T04` |
| `IW-TOOL-001` Workbench MCP/tool catalog and permission-aware invocation | P2 | 4 | web/workbench | `P4-T05`, `P4-T08` |
| `IW-VERIFY-001` Node/deployment challenge and verification bands | P2 | 5 | control-plane+node | `P5-T05` |
| `IW-PROMPT-001` Record encrypted prompts without coupling gateway admission to sink availability | P0 | 1 | control-plane | `P0-T05`, `P1-T07`, `P1-T08`, `P1-T24` |
| `IW-DP-003` Direct-first client/local-proxy to node data path | P0 | 1 | control-plane+node | `P1-T16`, `P1-T17`, `P1-T24` |
| `IW-TEL-001` Per-GPU full hardware/software/runtime/model telemetry | P0 | 1 | node | `P0-T04`, `P0-T05`, `P1-T04`, `P1-T05`, `P1-T20` |
| `IW-BENCH-002` Global cluster benchmark and contribution warehouse | P0 | 2 | control-plane | `P2-T01`, `P2-T03` |
| `IW-UI-002` Next.js benchmark/GPU/contribution explorer | P1 | 2 | control-plane | `P2-T18` |
| `IW-REC-001` Hardware/workload-specific model recommendation engine | P0 | 2 | benchmarks | `P2-T04`, `P2-T05`, `P2-T07`, `P2-T14` |
| `IW-REC-002` Measured/predicted recommendation evidence and Pareto frontier | P0 | 2 | benchmarks | `P2-T07`, `P2-T08`, `P2-T09` |
| `IW-REC-003` Real Pi/AutoSpec workflow replay for coding-agent recommendations | P0 | 2 | benchmarks+autospec-client | `P2-T06` |
| `IW-SCHED-001` Generic external resource scheduler adapter | P1 | 3 | control-plane | `P3-T04` |
| `IW-SLURM-001` Slurm allocation-scoped ephemeral provider workers | P0 | 3 | node+control-plane | `P3-T05`, `P3-T10`, `P3-T21` |
| `IW-SLURM-002` Stable host/GPU identity across ephemeral Slurm allocations | P0 | 3 | identity+node | `P1-T01`, `P3-T05`, `P3-T21` |
| `IW-SLURM-003` Gateway desired-deployment assignment for ephemeral workers | P0 | 3 | deployments+routing | `P3-T03`, `P3-T21` |
| `IW-SLURM-004` Reservation deadline/preemption-aware draining and routing | P0 | 3 | node+routing | `P3-T06`, `P3-T21` |
| `IW-SLURM-005` Opportunistic resumable benchmarking on Slurm capacity | P1 | 3 | benchmarks | `P3-T07`, `P3-T21` |
| `IW-SITE-001` Persistent HPC/Slurm site connector | P0 | 3 | site | `P3-T01`, `P3-T08`, `P3-T09` |
| `IW-CACHE-001` Hierarchical content-addressed artifact/model cache | P0 | 3 | site+deployments | `P3-T02` |
| `IW-BOOT-001` Single AI-friendly InferWeave bootstrap/init CLI | P0 | 0 | bootstrap | `P0-T01`, `P0-T03`, `P3-T19` |
| `IW-BOOT-002` Containerized gateway/node/edge/site/proxy initialization | P0 | 0 | bootstrap | `P0-T07`, `P0-T08`, `P1-T22`, `P1-T23`, `P3-T09`, `P3-T10`, `P3-T11`, `P3-T19` |
| `IW-BOOT-003` Idempotent one-time enrollment and verification | P0 | 1 | bootstrap+auth | `P1-T02`, `P1-T22`, `P1-T23` |
| `IW-BOOT-004` Versioned JSON doctor/probe/plan/status for AI automation | P0 | 0 | bootstrap | `P0-T03`, `P0-T04`, `P0-T07`, `P0-T10`, `P3-T19` |
| `IW-MCP-001` Authenticated control-plane MCP information server | P1 | 3 | mcp | `P3-T16`, `P3-T18` |
| `IW-MCP-002` Local node/site diagnostic MCP server | P1 | 3 | mcp+node | `P3-T17`, `P3-T18` |
| `IW-WORK-001` Explicit workload scheduling contracts | P0 | 2 | routing | `P2-T01` |
| `IW-EVENT-001` Persistent resource lifecycle event log | P0 | 2 | telemetry | `P2-T10` |
| `IW-HEALTH-001` Automatic resource degradation/quarantine/recovery | P0 | 3 | health | `P3-T13`, `P3-T14` |
| `IW-FORECAST-001` Demand forecasting and model artifact pre-staging | P1 | 3 | deployments+routing | `P3-T15` |
| `IW-BENCH-003` Resumable preemption-safe benchmark DAG | P0 | 2 | benchmarks | `P2-T19` |
| `IW-PROMPT-002` Backend-independent PromptStore with encrypted object tiering | P0 | 3 | prompt-ledger | `P3-T12` |
| `IW-SIM-001` Large-scale protocol-accurate cluster/churn simulator | P0 | 2 | simulator | `P2-T20`, `P2-T21`, `P5-T06` |
| `IW-WATCH-001` Per-GPU watchdog detects runtime/GPU correctness and liveness failures | P0 | 1 | node+health | `P1-T20A` |
| `IW-WATCH-002` Bounded automatic rescue ladder with known-good profile rollback | P0 | 1 | node+deployments | `P1-T20B` |
| `IW-WATCH-003` Watchdog CLI/dashboard/MCP diagnostics and operator rescue | P0 | 3 | health+mcp+web | `P3-T18A` |
| `IW-DEPLOY-001` Docker Compose is mandatory persistent deployment substrate | P0 | 0 | bootstrap | `P0-T11A`, `P1-T22`, `P1-T23`, `P3-T09`, `P3-T11` |
| `IW-DEPLOY-002` Apptainer is mandatory Slurm allocation deployment substrate | P0 | 3 | bootstrap+slurm | `P3-T10` |
| `IW-CAP-002` Deployment context ceiling as a hard admission bound | P0 | 1 | control-plane+node | `P1-T06A`, `P1-T11A` |
| `IW-CAP-003` Reservation liveness and stale reclamation | P0 | 1 | control-plane+node | `P1-T11B` |
| `IW-NODE-003` Capability precedence, persistence and cold-start admissibility | P0 | 1 | node | `P1-T06B` |
| `IW-DEPLOY-003` Maximum-context deployment sizing | P0 | 1 | node | `P1-T06A` |
| `IW-ROUTE-004` Context-size alias semantics | P0 | 1 | control-plane | `P1-T13A` |
| `IW-BOOT-005` Node serviceability gate and shipped default policy | P0 | 1 | node | `P1-T12B` |
| `IW-WATCH-004` Discovered device inventory and requalification on change | P0 | 1 | node | `P1-T20C` |
| `IW-OBS-002` Single-source queue observability | P0 | 1 | control-plane | `P1-T12A` |
| `IW-EVID-001` Conformance and hostile vectors | P0 | 0 | protocol+control-plane | `P0-T06A` |
| `IW-EVID-002` Machine-checked registries with anti-vacuous guards | P0 | 0 | bootstrap | `P0-T01A` |
| `IW-NODE-004` Token-free proof enrollment | P0 | 1 | node+control-plane | `P1-T02A` |
| `IW-OBS-003` Read-side ledger integrity | P0 | 1 | control-plane | `P1-T08A` |
| `IW-UI-003` Machine-checked presentation policy | P0 | 1 | web | `P1-T21A` |
| `IW-TOPO-001` Local topology graph export | P1 | 2 | control-plane | `P2-T23` |
| `IW-TOPO-002` Topology horizon and completeness semantics | P0 | 2 | control-plane | `P2-T23` |
| `IW-TOPO-003` Federated topology composition | P1 | 5 | control-plane | `P5-T11` |
| `IW-TOPO-004` Per-viewer topology redaction | P0 | 2 | control-plane | `P2-T24` |
| `IW-TOPO-005` Topology scale aggregation | P2 | 5 | control-plane | `P5-T12` |
| `IW-TOPO-006` Whole-network visualization surface | P2 | 5 | web | `P5-T13` |
| `IW-GRANT-004` Capacity grant receipts and forecast signals (provisioning hosting requests: spec 62) | P2 | 5 | control-plane | `P5-T17` |
| `IW-GRANT-001` Inter-gateway capacity request protocol | P1 | 5 | control-plane | `P5-T14` |
| `IW-GRANT-002` Standby slot grants and lifecycle | P1 | 5 | control-plane | `P5-T15` |
| `IW-GRANT-003` Capacity request loop and amplification control | P0 | 5 | control-plane | `P5-T16` |
| `IW-TUNE-002` Measured runtime tuning record | P0 | 1 | node | `P1-T06C` |
| `IW-SCHED-002` Per-GPU placement and hot-swap with availability floor | P1 | 3 | control-plane+node | `P3-T23`, `P3-T24`, `P3-T25` |
| `IW-PROTO-001` Scheduler-neutral core protocol: model, artifact, capability, resource, capacity, lifecycle, metric, and federation description | P1 | 5 | control-plane+gateway+node | `P5-T18`, `P5-T19`, `P5-T20`, `P5-T21`, `P5-T22`, `P5-T23` |
| `IW-PROTO-002` InferWeave Protocol v1: versioned, machine-readable, language-neutral wire contract (planes, identity, objects, events, state machines, enums, errors, aliases, routing, jobs, conformance) formalizing the scheduler-neutral core protocol | P1 | 5 | control-plane+gateway+node+consumer | `P5-T24`, `P5-T25`, `P5-T26`, `P5-T27`, `P5-T28`, `P5-T29` |
| `IW-GPUMEM-001` GPU memory accounting, reservations, pressure, decision records, OOM postmortem and placement simulation on the capability-gated iw.gpu-memory family (Protocol 1.1.0) | P1 | 5 | control-plane+gateway+node+consumer | `P5-T30`, `P5-T31`, `P5-T32` |
| `IW-NODEHW-001` Hardware-only node registration, the optional versioned hardware report, the always-present assignments array and tokenless proof enrollment as one wire contract for the Rust and Go gateways (Protocol 1.1.0) | P1 | 5 | gateway+node | `P5-T33`, `P5-T34` |
| `IW-DYNNODE-001` Dynamic nodes: gateway-driven provisioning over the register and heartbeat responses (`iw.dynamic-node/1`), measured-profile selection, one node per engine, drafted profiles from measurements (Protocol 1.1.0) | P1 | 5 | gateway+node | `P5-T35` |
| `IW-DYNNODE-002` Managed persistent node onboarding, qualification and durable reconciliation (`iw.node-reconcile/1`; new proof owed) | P1 | 5 | gateway+node | `P5-T38` |
| `IW-STORE-001` InferWeave Storage Phase 1: content-addressed model store, signed iwg1 grants, native and S3 read-only front ends, digest index, quarantine and multi-source stager (`iw.store/1`, Protocol 1.1.0) | P1 | 5 | gateway+node | `P5-T36` |
| `IW-STORE-002` InferWeave Storage Phase 2: TLS, federated grant forwarding, per-range hashes, ingest leases, replication, write path, rendezvous | P2 | 5 | gateway+node | `P5-T37` |
| `IW-RT-001` Runtime families, typed capabilities, isolated adapters and feature negotiation | P1 | B | control-plane | `B-T01` |
| `IW-RT-002` Native `/inferweave/v1` endpoints, standalone schema parity and exact-incarnation bounded request plus HTTP response-proof negotiation | P1 | B | control-plane | `B-T02` |
| `IW-RT-003` Transactional lifecycle, single-flight loads, reservations, caches and rollback | P1 | B | control-plane | `B-T03` |
| `IW-RT-004` Typed inference pipelines | P1 | B | control-plane | `B-T04` |
| `IW-RT-005` Durable inference jobs with additive legacy compatibility | P1 | B | control-plane | `B-T05` |
| `IW-RT-006` Runtime-family contract/live conformance and traceability | P1 | B | control-plane | `B-T06` |
| `IW-ALIAS-001` Dynamic model aliases (specs 54–57, 61 and 62; inference identity, claims and node execution fence) | P0 | A | control-plane+gateway | `A-T01`, `A-T02`, `A-T03`, `A-T04`, `A-T05`, `A-T06`, `A-T07`, `A-T08` |


## Model-intelligence extension

Spec 58 reuses IW-OBS-001/IW-TEL-001 (P1-T20), IW-UI-001 (P1-T21),
IW-BENCH-002 (P2-T03), IW-REC-001/IW-REC-002 (P2-T05/P2-T07/P2-T08),
IW-EVENT-001 (P2-T10), and IW-ECON-001 (P2-T16). Their feature-registry
contract links and task cards trace the added acceptance. No new feature or
dependency order is introduced; new proof remains owed.

Stream incident diagnostic acceptance AC-STREAM-01..08 extends IW-OBS-001 and
IW-OBS-002 in `contracts/inference-stream-reliability.json`; P1-T20 owns stream
timeout/correlation diagnostics, and P1-T12A owns admission scope/metadata
observability. Proof and deployment status remain explicit in OPEN_GATES.

## Observability capacity extension (2026-10-20)

Existing feature/task mappings remain in force. The bounded cross-cutting
acceptance mapping for specs 04/09/23/42/43/46/58/64 and P1-T05/P1-T20/
P2-T03/P1-T21/P2-T18/P5-T30..32 is `contracts/observability-capacity.json`.
New runtime and rollout proof remains owed.

The internal request-observation extension maps IW-OBS-001/IW-TEL-001/IW-BENCH-002
to existing P1-T20/P2-T03 and specs09/23/58 through
`contracts/request-observation.json` (AC-REQOBS-01..09, runtime proof owed).

The private HTTP carrier reuses IW-OBS-001/IW-TEL-001/IW-BENCH-002 and P1-T20/P2-T03:
`contracts/private-observability.json`, AC-PRIVATEOBS-01..06. Existing request and
failure DTOs are unchanged; private ingest/read runtime proof remains owed.

## Managed-profile implementation alignment (2026-10-27)

Specs50/28 reuse IW-RT-003/B-T03 and IW-BOOT-001/IW-BOOT-004/P0-T03 for
the bounded pinned-profile owner/helper/client contract. The task graph, task cards and
canonical sequence carry the added acceptance; no feature or dependency is added.
Live-owner composition, hardware qualification and full runtime_reservations/1 proof
remain owed in OPEN_GATES.

The spec64 optional assignment-identity correction extends the same managed-profile
acceptance under B-T03 and existing IW-DYNNODE-001/P5-T35 conformance vectors.
Legacy proof is retained; new byte-encoding checks do not establish live managed-profile
or hardware qualification. No task status or phase dependency changes.
