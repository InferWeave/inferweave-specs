# Feature Preservation Matrix

This matrix exists specifically to prevent consolidation from deleting desired behavior.

| Area | Preserved target | Canonical spec | Phase |
|---|---|---|---:|
| OpenAI API | `/v1/models`, chat, responses, embeddings; images later | 02 | 1 |
| Native API | `/api/v1` nodes, capacity, routes, jobs, policy, tuning | 02 | 1+ |
| Seats | one active session = seat; unequal resource cost | 04 | 1 |
| Context/KV | measured/predicted admission, growth reserve, headroom | 04 | 1 |
| Routing | model/capability/policy hard filters | 05 | 1 |
| Packing | lowest sufficient remaining context/KV | 05 | 1 |
| Affinity | sticky sessions + prefix/cache locality | 05 | 1 |
| Preferences | GPU/model/context/privacy/perf/region + soft fallbacks | 02/05 | 2 |
| Backpressure | 503 infra, 429 policy, bounded retry/queues | 06 | 1 |
| Return-to-sender | hierarchical rejection propagation | 06 | 2 |
| NAT | outbound node connectivity | 08 | 1 |
| Direct-first data plane | direct client/local-proxy↔node, nearest relay fallback, gateway last resort | 08 | 1 |
| Prompt ledger | every submitted prompt persisted encrypted in shared DB | 22 | 1 |
| Full GPU telemetry | hardware/software/model/settings/temp/power/utilization for every GPU | 23 | 1 |
| Global benchmarks | cluster-wide exact-fingerprint performance/contribution warehouse | 23 | 2 |
| Relays/direct | regional relays + route-scoped direct paths | 08 | 3 |
| Local proxy/cache | connection/routing/prefix optimization | 08/11 | 3 |
| FairShare | hierarchy, min/max, burst, aging, anti-fanout | 07 | 2 |
| Owner priority | local owner reserve/reclaim/preemption policy | 07 | 2 |
| Immutable deployments | exact model/runtime/config fingerprints | 03 | 1 |
| Model lifecycle | fetch/verify/warm/drain/update/rollback/quarantine | 03 | 2 |
| Benchmarking | TTFT/prefill/decode/concurrency/correctness/fingerprint | 12 | 2 |
| R9700 optimization | ROCm/Vulkan/AITER/MTP/MXFP4 evidence gates | 12 | 2 |
| Route explainability | rejected candidates, scores, fallbacks | 09 | 1 |
| Signed snapshots | freshness + privacy-safe aggregate public data | 09/10 | 2 |
| Receipts | content-free signed work/accounting evidence | 09 | 3 |
| Dashboard | capacity/routes/sessions/errors/benchmarks | 10 | 1-2 |
| CI dashboard | current/past builds, logs, Pi reviews, artifacts | 19 | 3 |
| Public trial | anonymous bounded `/play` with circuit breaker | 10 | decision |
| API keys/OIDC | scoped keys; OIDC before public multi-user | 16 | 1-2 |
| Workbench | sessions, fork/split, files, rendering, coding UX | 11 | 3 |
| AutoSpec/Pi | stable IDs/workload hints/prefix reuse | 11 | 2 |
| Agentic RAG | semantic/lexical/AST/LSP/git/docs provenance | 13 | 4 |
| LSP/tools | capability-brokered self-hosted services | 13 | 4 |
| Image generation | immutable pipelines, async jobs, direct artifacts | 14/15 | 4 |
| Annotated images | grounding + deterministic annotations + vision QA | 14 | 4 |
| Scale | regional gateways, sharded snapshots, million-node-safe UI | 17 | 5 |
| Internal ledger | deterministic accounting independent of chain | 18 | 2 |
| ASPEC concepts | fixed cap, accepted-work, donor/community ideas | 18 | experimental |
| Solana | local validator/devnet adapter only | 18 | 5 |
| Local node admin | local-only config/secrets/install/update by default | 03/16 | 1 |
| Privacy | no prompts/outputs/keys/private addresses in public data | 09/16 | 1 |

## Explicitly superseded older designs

- Fixed inference slots as capacity.
- Workbench directly spawning/managing Pi.
- Workbench owning Docker/worktrees.
- `autospec-inferweave` implementing its own inference scheduler/server.
- Public dashboard remotely administering provider nodes by default.
- Silent provider/model/policy fallback.
- Mainnet-dependent routing/accounting.
- One universal TPS number used to compare every model/runtime.
