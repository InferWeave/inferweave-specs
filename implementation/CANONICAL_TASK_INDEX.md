# Canonical Task Index

Total tasks: **124**

| Task | Phase | Context | Depends | Title |
|---|---:|---:|---|---|
| `P0-T01` | 0 | C50 | — | Bootstrap clean Rust/Next.js monorepo |
| `P0-T01A` | 0 | C65 | P0-T01 | Machine-checked registry pattern and anti-vacuous guards |
| `P0-T02` | 0 | C55 | P0-T01 | Canonical protocol versioning, typed IDs and error envelope |
| `P0-T03` | 0 | C55 | P0-T01, P0-T02 | Bootstrap CLI command framework and versioned JSON output |
| `P0-T04` | 0 | C65 | P0-T03 | Read-only doctor and host probe |
| `P0-T05` | 0 | C60 | P0-T01, P0-T02 | PostgreSQL development storage foundation |
| `P0-T06` | 0 | C65 | P0-T02 | Canonical schemas and generated Rust/TypeScript bindings |
| `P0-T06A` | 0 | C70 | P0-T06 | Conformance vectors and hostile vectors |
| `P0-T07` | 0 | C70 | P0-T03, P0-T04, P0-T05 | Container stack renderer and init plan |
| `P0-T08` | 0 | C65 | P0-T07 | Local development stack generator |
| `P0-T09` | 0 | C55 | P0-T01, P0-T06 | Next.js shell and generated API client |
| `P0-T10` | 0 | C55 | P0-T03, P0-T04 | Bootstrap CLI support bundle and config model |
| `P0-T11` | 0 | C70 | P0-T03, P0-T05, P0-T07 | Foundation security and secrets policy |
| `P0-T11A` | 0 | C70 | P0-T04, P0-T07, P0-T11 | Docker/Apptainer deployment substrate contract |
| `P0-T12` | 0 | C90 | P0-T01, P0-T02, P0-T03, P0-T04, P0-T05, P0-T06, P0-T07, P0-T08, P0-T09, P0-T10, P0-T11, P0-T11A | Phase-0 architecture and bootstrap review |
| `P1-T01` | 1 | C65 | P0-T12 | Stable provider/node/GPU identity primitives |
| `P1-T02` | 1 | C70 | P1-T01, P0-T11 | One-time enrollment and node credentials |
| `P1-T02A` | 1 | C75 | P1-T02 | Token-free proof enrollment |
| `P1-T03` | 1 | C65 | P1-T02 | Outbound node control connection and heartbeat |
| `P1-T04` | 1 | C70 | P1-T01, P0-T04 | Full hardware/software/GPU discovery fingerprint |
| `P1-T05` | 1 | C65 | P1-T04, P0-T05 | Live GPU/host telemetry collection |
| `P1-T06` | 1 | C65 | P1-T03, P1-T04, P0-T06 | Immutable deployment manifest and node advertisement |
| `P1-T06A` | 1 | C75 | P1-T06 | Publish a deployment context ceiling sized to the envelope |
| `P1-T06B` | 1 | C75 | P1-T06A | Capability precedence: declared, measured, persisted |
| `P1-T06C` | 1 | C70 | P1-T06A | Record measured runtime tuning per deployment |
| `P1-T07` | 1 | C75 | P0-T05, P0-T11 | Prompt ledger metadata and encrypted payload storage |
| `P1-T08` | 1 | C65 | P1-T07, P0-T06 | Prompt ingest API and submission ordering |
| `P1-T08A` | 1 | C75 | P1-T08 | Read-side ledger integrity |
| `P1-T09` | 1 | C60 | P1-T03, P1-T06 | Gateway registry and `/v1/models` |
| `P1-T10` | 1 | C70 | P1-T08, P1-T09 | OpenAI streaming ingress against deterministic backend |
| `P1-T11` | 1 | C75 | P1-T06, P1-T10 | Seat/session/context/KV capacity model |
| `P1-T11A` | 1 | C75 | P1-T11, P1-T06A | Enforce the context ceiling as a hard admission bound |
| `P1-T11B` | 1 | C75 | P1-T11 | Reservation liveness and stale reclamation |
| `P1-T12` | 1 | C70 | P1-T11, P1-T03 | Node authoritative admission and leases |
| `P1-T12A` | 1 | C75 | P1-T12, P1-T11B | Single-source queue observability |
| `P1-T12B` | 1 | C75 | P1-T12 | Node serviceability gate and shipped default policy |
| `P1-T13` | 1 | C70 | P1-T09, P1-T11 | Routing hard constraints |
| `P1-T13A` | 1 | C50 | P1-T13, P1-T09 | Context-size alias semantics |
| `P1-T14` | 1 | C70 | P1-T13, P1-T12 | Best-fit capacity placement |
| `P1-T15` | 1 | C65 | P1-T14 | Sticky sessions and cache affinity |
| `P1-T16` | 1 | C80 | P1-T12, P1-T15, P0-T11 | Route tickets and rendezvous protocol |
| `P1-T17` | 1 | C80 | P1-T16, P1-T10 | Local proxy direct node streaming |
| `P1-T18` | 1 | C75 | P1-T17 | Regional/gateway relay fallback |
| `P1-T19` | 1 | C65 | P1-T12, P1-T18 | Canonical 503/429 backpressure and bounded retries |
| `P1-T20` | 1 | C75 | P1-T05, P1-T10, P1-T12 | Per-request performance/resource telemetry |
| `P1-T20A` | 1 | C75 | P1-T05, P1-T06, P1-T20 | GPU/runtime watchdog detection and incident classification |
| `P1-T20B` | 1 | C85 | P1-T20A, P1-T12 | Bounded rescue ladder and automatic profile rollback |
| `P1-T20C` | 1 | C75 | P1-T20A, P1-T04 | Discovered device inventory and requalification on change |
| `P1-T21` | 1 | C75 | P0-T09, P1-T09, P1-T20 | Live Next.js cluster/GPU/request dashboard |
| `P1-T21A` | 1 | C65 | P1-T21 | Machine-checked presentation policy |
| `P1-T22` | 1 | C85 | P0-T07, P1-T02, P1-T21 | `init gateway` production container flow |
| `P1-T23` | 1 | C85 | P0-T07, P1-T02, P1-T04, P1-T17 | `init node` production container flow |
| `P1-T24` | 1 | C95 | P1-T19, P1-T20, P1-T21, P1-T22, P1-T23, P1-T20B | Two heterogeneous real-node vertical-slice E2E |
| `P1-T25` | 1 | C100 | P1-T24, P1-T20B | Phase-1 soak, failure injection and independent review |
| `P2-T01` | 2 | C75 | P1-T25 | Benchmark campaign/sample schemas and workload contracts |
| `P2-T02` | 2 | C80 | P2-T01, P1-T06, P1-T20 | Node benchmark runner and profile capture |
| `P2-T03` | 2 | C75 | P2-T02 | Global benchmark warehouse and rollups |
| `P2-T04` | 2 | C70 | P2-T03 | Model candidate registry and feasibility filter |
| `P2-T05` | 2 | C75 | P2-T04 | Quality evaluation adapters |
| `P2-T06` | 2 | C90 | P2-T05 | Pi/AutoSpec real-workflow replay benchmark |
| `P2-T07` | 2 | C85 | P2-T03, P2-T05, P2-T06 | Recommendation engine and evidence classes |
| `P2-T08` | 2 | C75 | P2-T07 | Pareto frontier and next-experiment selection |
| `P2-T09` | 2 | C75 | P2-T07, P1-T04 | Requalification and regression gates |
| `P2-T10` | 2 | C65 | P2-T01, P1-T20 | Resource lifecycle event log |
| `P2-T11` | 2 | C80 | P2-T01, P1-T12, P2-T10 | Owner priority/reclaim/preemption |
| `P2-T12` | 2 | C85 | P2-T11 | Hierarchical FairShare and anti-gaming |
| `P2-T13` | 2 | C70 | P0-T11, P2-T12 | API keys and routing preference policy |
| `P2-T14` | 2 | C70 | P2-T13, P1-T15, P2-T07 | Route preview and explainability |
| `P2-T15` | 2 | C80 | P2-T13, P1-T17, P2-T06 | Thin AutoSpec/Pi client integration |
| `P2-T16` | 2 | C70 | P1-T20, P2-T12 | Internal deterministic contribution/usage ledger |
| `P2-T17` | 2 | C70 | P2-T03, P2-T16 | Public-safe signed snapshot builder |
| `P2-T18` | 2 | C80 | P2-T03, P2-T07, P2-T09 | Next.js GPU/benchmark/recommendation explorer |
| `P2-T19` | 2 | C75 | P2-T02, P2-T08 | Resumable benchmark DAG core |
| `P2-T20` | 2 | C85 | P1-T25, P2-T10 | Cluster simulator protocol skeleton |
| `P2-T21` | 2 | C95 | P2-T20, P2-T12, P2-T19 | 10k churn/chaos scenarios and invariant checks |
| `P2-T22` | 2 | C100 | P2-T07, P2-T12, P2-T15, P2-T18, P2-T19, P2-T21 | Phase-2 private-alpha review and qualification |
| `P3-T01` | 3 | C75 | P2-T22, P1-T03 | Persistent site connector identity and control channel |
| `P3-T02` | 3 | C85 | P3-T01, P1-T06 | Hierarchical content-addressed artifact cache |
| `P3-T03` | 3 | C80 | P3-T02, P2-T07 | Gateway desired-deployment assignment negotiation |
| `P3-T04` | 3 | C70 | P3-T01 | Generic external scheduler adapter |
| `P3-T05` | 3 | C85 | P3-T04, P1-T01, P3-T01 | Slurm allocation identity and worker registration |
| `P3-T06` | 3 | C75 | P3-T05, P3-T03, P2-T01 | Slurm deadline/preemption drain |
| `P3-T07` | 3 | C75 | P3-T06, P2-T19, P2-T08 | Slurm opportunistic benchmark execution |
| `P3-T08` | 3 | C80 | P3-T01, P1-T18 | Site relay and direct-connect integration |
| `P3-T09` | 3 | C85 | P0-T07, P3-T01, P3-T04 | `init site` and Slurm discovery |
| `P3-T10` | 3 | C80 | P3-T05, P3-T06, P3-T09 | `init slurm-worker` allocation-scoped flow |
| `P3-T11` | 3 | C75 | P1-T18, P3-T02, P0-T07 | Edge node role and container init |
| `P3-T12` | 3 | C75 | P1-T07, P2-T22 | PromptStore object-storage tiering |
| `P3-T13` | 3 | C80 | P2-T03, P2-T10 | Resource health baseline and degradation detector |
| `P3-T14` | 3 | C75 | P3-T13, P2-T09 | Quarantine, diagnostics and recovery canaries |
| `P3-T15` | 3 | C75 | P2-T07, P3-T02, P3-T03 | Demand forecasting and explainable pre-staging |
| `P3-T16` | 3 | C80 | P2-T14, P2-T18, P0-T11 | Control-plane MCP read server |
| `P3-T17` | 3 | C75 | P3-T16, P0-T04, P3-T01 | Local node/site diagnostic MCP |
| `P3-T18` | 3 | C75 | P3-T16, P3-T17 | MCP controlled operations and audit |
| `P3-T18A` | 3 | C80 | P1-T20B, P3-T14, P3-T18 | Watchdog operator rescue via CLI/dashboard/MCP |
| `P3-T19` | 3 | C90 | P1-T22, P1-T23, P3-T09, P3-T11, P3-T16, P3-T18A | AI copy/paste installer acceptance flow |
| `P3-T20` | 3 | C80 | P3-T19, P3-T12 | Update/backup/restore operational lifecycle |
| `P3-T21` | 3 | C95 | P3-T07, P3-T08, P3-T10, P3-T14 | Production Slurm/site E2E and reconnect history |
| `P3-T22` | 3 | C100 | P3-T21, P3-T19, P3-T20, P3-T18A | Phase-3 operational/security review |
| `P4-T01` | 4 | C75 | P3-T22 | Durable async job/event/lease state machine |
| `P4-T02` | 4 | C75 | P4-T01, P3-T02 | Artifact metadata/grants and direct transfer |
| `P4-T03` | 4 | C80 | P4-T01, P2-T15 | Workbench session/history core |
| `P4-T04` | 4 | C80 | P4-T03, P4-T02 | Workbench fork/split/files/rendering |
| `P4-T05` | 4 | C85 | P4-T04, P3-T16 | Workbench coding/review and tool UX |
| `P4-T06` | 4 | C80 | P2-T15, P4-T03 | CI/build history and Pi review records |
| `P4-T07` | 4 | C85 | P4-T01, P2-T15 | Agentic RAG retrieval contracts and provenance |
| `P4-T08` | 4 | C80 | P4-T07, P3-T16 | LSP/MCP/tool capability broker |
| `P4-T09` | 4 | C80 | P1-T06, P4-T07 | Embeddings/rerank/vision deployment capabilities |
| `P4-T10` | 4 | C85 | P4-T01, P4-T09 | Image deployment manifests and compatible/native APIs |
| `P4-T11` | 4 | C80 | P4-T10, P4-T02 | Image direct artifact data plane and resource accounting |
| `P4-T12` | 4 | C85 | P4-T11 | Deterministic technical annotation + vision QA |
| `P4-T13` | 4 | C70 | P4-T05, P4-T12 | Optional bounded public playground behind decision gate |
| `P4-T14` | 4 | C100 | P4-T06, P4-T08, P4-T12 | Phase-4 capability/UX review |
| `P5-T01` | 5 | C85 | P4-T14 | Multi-gateway stateless control services |
| `P5-T02` | 5 | C85 | P5-T01, P2-T03 | Regional presence/sharded telemetry ingestion |
| `P5-T03` | 5 | C80 | P5-T02, P3-T08 | Regional relay failover and routing locality |
| `P5-T04` | 5 | C85 | P5-T02 | Federation/coordinator hierarchy |
| `P5-T05` | 5 | C80 | P2-T09, P5-T04 | Node/deployment challenge and verification bands |
| `P5-T06` | 5 | C95 | P5-T02, P2-T21 | Million-node public snapshot/query scale simulation |
| `P5-T07` | 5 | C95 | P5-T03, P5-T05 | Cross-region security/privacy review |
| `P5-T08` | 5 | C100 | P5-T04, P5-T06, P5-T07 | Federated production soak and chaos |
| `P5-T09` | 5 | C100 | P5-T08 | Final requirements/spec conformance audit |
| `P5-T10` | 5 | C100 | P5-T09 | Production-readiness release gate |
| `D-T01` | deferred | C70 | P5-T10 | Optional development settlement adapter |
| `P2-T23` | 2 | C80 | P0-T06, P1-T04, P1-T05 | Topology graph model and local gateway export |
| `P2-T24` | 2 | C75 | P2-T23 | Per-viewer topology redaction |
| `P5-T11` | 5 | C85 | P2-T23, P5-T04 | Federated topology composition |
| `P5-T12` | 5 | C80 | P5-T11 | Topology scale aggregation |
| `P5-T13` | 5 | C80 | P5-T11 | Whole-network topology visualization surface |
| `P5-T14` | 5 | C85 | P5-T04, P1-T12 | Inter-gateway capacity request protocol |
| `P5-T15` | 5 | C85 | P5-T14, P1-T11B | Standby slot grants and lifecycle |
| `P5-T16` | 5 | C75 | P5-T14 | Capacity request loop and amplification control |
| `P5-T17` | 5 | C80 | P5-T15 | Capacity grant receipts and forecast signals |
