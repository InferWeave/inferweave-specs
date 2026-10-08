# End-to-End Acceptance Matrix

| ID | Scenario | Expected |
|---|---|---|
| AC-001 | Node behind NAT, no inbound port | outbound registration and inference succeed |
| AC-002 | Heartbeat expires | node becomes ineligible before new lease |
| AC-003 | Request model absent | node rejected with `MODEL_MISMATCH` |
| AC-004 | Faster node lacks context | sufficient slower node selected |
| AC-005 | Two sufficient nodes | best-fit preserves larger headroom |
| AC-006 | Existing healthy session | same eligible node/deployment retained |
| AC-007 | Context grows | additional capacity estimate decreases |
| AC-008 | No safe capacity | 503 + retryable capacity error |
| AC-009 | User policy exhausted | 429, not 503 |
| AC-010 | Hard privacy constraint | no fallback to weaker privacy |
| AC-011 | Soft region preference | may relax only if allowed, disclosed |
| AC-012 | Client disconnect stream | upstream cancelled/lease released |
| AC-013 | Node crashes after lease | bounded failure/failover; no duplicate accounting |
| AC-014 | Owner begins local work | network admissions stop/reclaim per policy |
| AC-015 | API-key fan-out | no extra parent FairShare entitlement |
| AC-016 | Deployment runtime changes | new fingerprint/requalification required |
| AC-017 | Public snapshot stale | UI shows stale/unknown, not live-ready |
| AC-018 | Public node page | no private address/session/wallet/home location |
| AC-019 | Benchmark incorrect output | run invalidated and profile not activated |
| AC-020 | Experimental profile | ordinary production route cannot select it |
| AC-021 | Durable job duplicate submit | one logical job/accounting result |
| AC-022 | Gateway restarts during durable job | events/state resume |
| AC-023 | Large image artifact | bulk bytes bypass central gateway normally |
| AC-024 | Solana dev adapter unavailable | inference continues |
| AC-025 | Workbench fork | distinct conversation branch, execution ownership unchanged |

| AC-026 | Accepted direct request while recorder sink is blocked | route succeeds within the admission bound; buffer/drop state is visible; serving health stays healthy |
| AC-027 | Direct route healthy | gateway carries control only, not inference stream bytes |
| AC-028 | Direct route impossible | nearest regional relay selected before gateway relay |
| AC-029 | Every GPU online | complete hardware/software/runtime/model fingerprint present |
| AC-030 | GPU telemetry stream | temp/power/clocks/utilization/VRAM recorded where supported |
| AC-031 | Deployment version changes | new fingerprint + qualification required |
| AC-032 | Global benchmark query | results dimensioned by GPU/model/runtime/context/concurrency/settings |
| AC-033 | Owner starts work | shared work yields/reclaims until owner target restored |
| AC-034 | Prompt read by admin | audited access record created |
| AC-035 | Public benchmark | contains no prompt body/user/private node address |
| AC-036 | Solana service absent | working GPU weave unaffected |

| AC-037 | New GPU fingerprint | recommender ranks only feasible model/deployment candidates |
| AC-038 | Recommendation query | result includes workload, exact fingerprint, suite versions, evidence class and confidence |
| AC-039 | Predicted recommendation | UI/API never labels it measured |
| AC-040 | Driver/runtime/model change | old recommendation downgrades/requalifies |
| AC-041 | Coding-agent recommendation | real Pi/AutoSpec workflow replay contributes to ranking |
| AC-042 | Slurm allocation starts | worker registers only allocation-visible GPUs |
| AC-043 | Same host/GPU returns later | gateway resolves same stable host_id/gpu_id but creates new allocation/worker records |
| AC-044 | Same Slurm hostname with replaced GPU | new host generation/GPU identity created; old GPU performance not misapplied |
| AC-045 | Gateway assigns model | worker receives immutable desired deployment based on resources/cache/lifetime/demand |
| AC-046 | Short reservation | gateway avoids deployment whose load/work duration cannot fit |
| AC-047 | Slurm preemption | worker drains, stops admissions, flushes facts and disconnects |
| AC-048 | Requeue/restart | new worker_instance_id created without duplicate live resource lease |
| AC-049 | Direct path blocked on HPC | site/regional relay is used without public inbound compute port |
| AC-050 | Returned known GPU exact fingerprint | prior recommendation reused with defined confidence/smoke policy |
| AC-051 | Returned known GPU software changed | fresh fingerprint captured and requalification scheduled |
| AC-052 | Duplicate worker advertises same GPU/allocation | gateway detects conflict and prevents duplicate authoritative lease |

| AC-053 | Fresh gateway host | `doctor→plan→init→verify` produces healthy containerized gateway without hand-edited config |
| AC-054 | Fresh GPU host | node init probes exact GPUs/runtime, enrolls with one-time code and registers stable identities |
| AC-055 | Re-run init | installation is idempotent; no duplicate gateway/node identity |
| AC-056 | Edge init | selected relay/cache capabilities start without GPU requirement |
| AC-057 | Site init | Slurm cluster identity/cache/worker enrollment path established |
| AC-058 | AI install procedure | shell-capable assistant can complete supported setup using only CLI structured commands |
| AC-059 | CLI JSON mode | schemas/versioning stable and secrets redacted |
| AC-060 | MCP read request | authorized assistant retrieves GPU/benchmark/route information without log copy/paste |
| AC-061 | MCP prompt read | requires prompt-content scope and produces audit record |
| AC-062 | MCP mutation | unauthorized caller cannot drain/redeploy/enroll |
| AC-063 | Artifact cached at site | ephemeral worker uses site cache instead of gateway artifact bytes |
| AC-064 | Partial artifact | never advertised ready; resumes and verifies hash |
| AC-065 | Resource regression | repeated measured degradation transitions resource to DEGRADED/diagnostic policy |
| AC-066 | Quarantined GPU | receives no normal shared traffic |
| AC-067 | Resource recovers | bounded canary/requalification precedes HEALTHY |
| AC-068 | Forecast pre-stage | decision is explainable and cannot override hard policy/owner constraints |
| AC-069 | Benchmark preemption | completed leaf samples survive; expired leaf is rescheduled |
| AC-070 | Large prompt | PromptStore can store encrypted payload outside PostgreSQL while metadata remains queryable |
| AC-071 | Explicit durable ingest while PromptStore is unavailable | no durable acknowledgement is returned and no route claims durable submission |
| AC-072 | 10k synthetic workers | simulator maintains leases/queues/invariants under churn |
| AC-073 | Duplicate identity chaos | simulator detects/prevents two authoritative leases for same physical allocation resource |
| AC-074 | Site connector down | ephemeral workers fail over according to policy without identity corruption |
| AC-075 | Gateway byte accounting | site/regional caches/relays keep model and inference bytes off gateway normal path |
| AC-076 | Remote gateway advertises only model/capabilities/slots | upstream derives capabilities and capacity; artifact/hardware remain explicitly unknown, never inferred |
| AC-077 | Model with zero live runtimes | model lifecycle state is reported independently of runtime state, not treated as unavailable-by-identity |
| AC-078 | Self-reported 82 tok/s vs locally observed 64 tok/s | both evidence values coexist with provenance; neither overwrites the other |
| AC-079 | Downstream gateway disconnects | its capacity is marked stale/unavailable and not advertised live; historical identity is preserved |
| AC-080 | Gateway reconnects | runtime state reconciles without duplicate runtime identities or duplicate events |
| AC-081 | Capacity 8 → eviction → 0 → load → 4 → 8 | generic lifecycle events and a current-state snapshot let upstream compute recovery time |
| AC-082 | 100 health probes, 0 user requests | user demand stays 0; idle model is not kept resident unless policy says otherwise; probe failures still affect health |
| AC-083 | Topology-sensitive model requires 2×24 GB | not matched to 1×48 GB unless the profile explicitly supports that placement |
| AC-084 | Slurm-backed, Docker, manual worker, remote gateway | all present through one generic protocol; no upstream logic requires Slurm fields |
| AC-085 | Older gateway advertises model/endpoint/slots only | keeps functioning; missing fields yield unknown, not rejection |
| AC-086 | Protocol v1 version negotiation | peers negotiate `minimum_compatible_version`; a peer below it is rejected with `PROTOCOL_VERSION_UNSUPPORTED` |
| AC-087 | Protocol v1 feature negotiation | unknown features are tolerated and preserved; a feature is never assumed from a peer's release |
| AC-088 | Protocol v1 JSON Schemas | malformed enums rejected; unknown fields/enum values preserved and forwarded; extension namespace ignored by core readers |
| AC-089 | Protocol v1 state machines and enums | invalid transitions identifiable; error taxonomy, lifecycle reasons, workload classes, device types, provenance sources reconcile by test |
| AC-090 | Protocol v1 conformance profiles | a lightweight `IW-NODE` passes its declared scenarios without administrative features |
| AC-091 | Protocol v1 cross-repo CI | protocol-visible drift fails reference-implementation and gateway compatibility builds |
| AC-092 | GPU memory accounting is explainable and never invents zero | every GPU reports physical total/used/free with a basis; used + free and attributed + unattributed reconcile within tolerance or an anomaly is emitted; an unknown reading carries no bytes |
| AC-093 | GPU memory logical and physical stay separate | reservations and the placement-class view are never added to a physical total; safe-schedulable never exceeds raw free and is zero on a GPU InferWeave does not own |
