# 10 — Next.js Dashboard, Portal and Public Proxy

All web surfaces use **Next.js + TypeScript** and shared generated InferWeave API types.

## Public/read-only dashboard

Routes may include:
- `/`
- `/capacity`
- `/models`
- `/gpus`
- `/nodes`
- `/benchmarks`
- `/contributions`
- `/status`
- `/docs`
- `/about`
- `/connect`
- optional `/play`
- later `/economics`

Show useful ready capacity first.

Capacity views read waiting work from the structure that orders admission
(`04_CAPACITY_ADMISSION_SEATS.md`), never from a separate collector that observes only
executing requests.

A per-resource capacity view shows context occupied, the sessions holding it, context
remaining, and how many further clients fit at common context sizes before requests begin to
queue.

## GPU explorer

For each privacy-safe GPU/service view display appropriate public-safe fields:
- GPU model/architecture/VRAM;
- region band;
- active deployment/model;
- context envelope;
- TTFT/prefill/decode/aggregate benchmark ranges;
- utilization/power/temperature bands;
- reliability/qualification band;
- contribution totals/accepted work aggregates;
- exact benchmark fingerprint details that do not reveal secrets/private addresses.

Operators with authorization can view deeper telemetry, settings and historical charts.

## Global benchmark explorer

Filter/compare:
- GPU;
- model/revision;
- runtime/backend/version;
- quantization/precision/KV precision;
- context;
- concurrency;
- batching/attention/speculative settings;
- workload class;
- cache hit/miss;
- power/thermal envelope;
- software/container fingerprint.

Never display ambiguous cross-model universal TPS rankings without dimensions.

## Authenticated portal

- API keys;
- usage;
- prompt/session/request history where authorized;
- saved routing policies;
- provider contribution history;
- node/GPU telemetry and benchmark history;
- CI/build/Pi-review history;
- operator policy/routing/queue views.

## Prompt history

Because every submitted prompt is stored, authorized users can inspect their own prompt/session history. Access control comes from the prompt ledger and every privileged content read is audited.

## Node administration

Hosted dashboard is not the authoritative node secret/config/install/update surface. Local node administration remains authoritative unless a later ADR defines secure remote management.

## Live updates

Use server components/static rendering for stable catalog pages and SSE/WebSocket or efficient polling for live capacity/telemetry. Browser update strategy must not force inference traffic through Next.js or gateway servers.


## Ephemeral-resource views

Authorized cluster views show:
- stable host/GPU identity;
- currently connected worker/allocation;
- reservation time remaining;
- historical allocations;
- cumulative serving/benchmark contribution;
- performance history;
- runtime/model history;
- temperature/power/health trends;
- current gateway-assigned desired deployment;
- cached artifacts;
- reconnect/rediscovery events.

A returned known node should visibly continue the same resource history rather than appearing as an unrelated new GPU.
