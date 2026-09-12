# 05 — Routing, Affinity and Best-Fit Placement

## Pipeline

1. Validate request and derive hard constraints.
2. Resolve model alias/intent to eligible immutable deployments.
3. Filter fresh/healthy/non-draining service instances.
4. Filter modality/capability/license/privacy/policy.
5. Filter context/resource feasibility, including each candidate deployment's hard `max_context_tokens` ceiling.
6. Apply owner/FairShare eligibility.
7. Prefer valid existing session/cache affinity.
8. Apply best-fit packing.
9. Score remaining candidates.
10. issue lease/ticket and dispatch.
11. record route explanation.

## Best-fit

Prefer the candidate with the lowest sufficient remaining context/KV/resource envelope, preserving large contiguous capacity for requests that need it.

A faster GPU with insufficient context is not a candidate.

A context-size alias expresses caller intent and never widens a candidate's ceiling.

## Score dimensions

Weights are configurable and visible:
- session affinity;
- compatible prefix-cache affinity;
- predicted post-admission headroom;
- model residency/warmth;
- queue depth;
- TTFT/prefill/decode profile;
- locality/RTT/bandwidth;
- reliability/error penalty;
- FairShare/owner priority;
- benchmark-profile match;
- cold-start cost;
- economics only when enabled and never ahead of hard constraints.

## Sticky sessions

Long sessions use strict affinity while the service remains healthy/eligible. Bounded reroute occurs on failure, drain, policy change, explicit migration or lost deployment.

Do not move large KV state over WAN by default.

## Instances of one deployment

Each GPU instance of a deployment is a separate service instance, and routing balances across them. Where a runtime requires a unique name per loaded instance, the node exposes a distinct name per (deployment, GPU) pair and routing, not the runtime, spreads load.

A draining instance is not a candidate. Requests it cancels at its drain deadline carry reason `INSTANCE_DRAINED` and are rerouted within the bounded retry budget of `06_BACKPRESSURE_RETURN_TO_SENDER.md` (`43_GPU_PLACEMENT_HOT_SWAP.md`).

## Explainability

Persist candidate rejection reason codes, score components, selected instance/deployment and any soft fallback. The public representation uses privacy-safe IDs.


## Ephemeral allocation routing

For Slurm/other revocable resources, routing includes:
- remaining reservation lifetime;
- load/warmup cost;
- preemption risk;
- stable resource reliability history;
- current allocation health;
- cached model availability.

Do not start a workload whose expected lifetime is incompatible with the reservation unless restartability/policy explicitly permits it.
