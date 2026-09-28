# Historical Requirements Audit

Historical conversations/specifications were used only to recover desired product capabilities.

## Clean-slate decision

All existing InferWeave repository contents are discarded as implementation constraints.

This bundle does not require:
- preserving or porting old code;
- auditing old code for reuse;
- compatibility with old internal APIs/schemas;
- database migration from old prototypes;
- preserving old repository boundaries;
- preserving old deployment manifests.

The only authoritative implementation source is the new `InferWeave/inferweave` monorepo.

## Features recovered from history

These remain because they are desired product requirements:
- direct-first heterogeneous GPU routing;
- outbound/NAT-safe nodes;
- session/seat + context/KV capacity;
- best-fit routing and sticky/cache affinity;
- explicit 503/429 backpressure;
- absolute owner GPU priority;
- hierarchical FairShare;
- bounded encrypted prompt recording independent of gateway admission, with explicit durable ingest;
- full per-GPU hardware/software/runtime/model/settings/temp/power telemetry;
- global benchmark and contribution warehouse;
- immutable deployment fingerprints;
- node tuning/qualification;
- Next.js dashboard/portal/Workbench;
- AutoSpec/Pi integration;
- RAG, LSP/MCP/tools;
- image generation and deterministic annotations;
- durable jobs/events/artifacts;
- privacy-safe snapshots/receipts;
- federation/scale concepts;
- deferred settlement concepts.

They are reimplemented from first principles.
