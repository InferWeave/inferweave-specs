# 00 — System Invariants

These requirements override every feature spec.

1. **Plane ownership**
   - AutoSpec: what development work should happen.
   - autospec-orchestrator: where/how Pi agent work physically executes.
   - InferWeave: where/how model inference physically executes.
2. **One logical active inference conversation = one seat**, but seats are not equal-cost resource units.
3. Admission uses measured/predicted context, KV, VRAM/RAM, compute, bandwidth, thermal and runtime constraints where applicable.
4. New inference scheduling code never depends on fixed slots.
5. A request is never routed to a node that lacks the required model/deployment/capability.
6. Security, privacy, license, modality, context, explicit deny rules and exact-deployment requirements are hard constraints.
7. Fallback never silently weakens a hard constraint.
8. Session and compatible prefix/cache affinity are preserved unless availability/policy makes the current placement invalid.
9. Do not transfer large KV caches over WAN by default.
10. Nodes can participate from behind NAT/firewalls without inbound port forwarding.
11. Direct client/local-proxy↔node transport is the normal inference data path. Regional relay is fallback; gateway byte proxying is last resort only.
12. Infrastructure capacity exhaustion returns `503`; user/rate/FairShare restriction returns `429`.
13. Queues are bounded. No layer may hide indefinite queueing from its caller.
14. Backpressure propagates toward the sender; upstream layers must not hoard work rejected downstream.
15. Model/runtime configurations are immutable deployments identified by fingerprints.
16. Capability claims expire and must be refreshed/requalified after material configuration changes.
17. Gateway admission never waits for record-storage I/O. Prompt and response content is encrypted before entering a bounded best-effort recording buffer; loss is explicit and measured. Callers that require proof of durable submission use the separate fail-closed prompt-ingest API. Public telemetry contains no prompt bodies, outputs, API keys, stable private node addresses, stable wallet mappings or home-location data.
18. Public node identifiers are privacy-safe/pseudonymous/rotatable where practical.
19. Owner/provider local-use priority is represented explicitly; remote capacity borrowing cannot manufacture permanent entitlement.
20. FairShare is charged to stable parent identities so API-key/session/agent fan-out cannot create extra budget.
21. Gateway admission and node admission are independent safety boundaries.
22. A predictable overload must not become OOM, swap death, disk-full loops, GPU reset loops or indefinite hangs.
23. Cancellation releases leases/reservations/resources.
24. Durable asynchronous jobs are idempotent and do not double-account on retry.
25. Receipts and route explanations contain identifiers/measurements, not plaintext content.
26. Workbench is not a second execution/runtime control plane.
27. `autospec-inferweave` remains a thin integration client/operator surface.
28. Experimental inference profiles cannot be selected by ordinary production routing until qualification gates pass.
29. Solana/mainnet is never required for routing or inference.
30. Do not implement blockchain/Solana integration until the deployed GPU weave, prompt ledger, direct routing and global telemetry/benchmark warehouse are stable; any later work remains local-validator/devnet only until separate production approval.
31. Every physical GPU must have an inventory/software/deployment fingerprint and continuous operational telemetry where the hardware exposes it.
32. All production backend/control/node services use Rust; all web/dashboard/Workbench surfaces use Next.js + TypeScript unless an ADR explicitly changes the rule.

33. Production deployment uses Docker/Compose for persistent InferWeave roles and Apptainer for Slurm allocation workers; model servers are not deployed as unmanaged bare-host processes.
34. Every GPU-serving node has a bounded watchdog/rescue mechanism that drains before recovery, preserves a known-good rollback target, and quarantines after repeated failure.
35. A GPU reset, illegal-memory fault, OOM below the admitted envelope, restart loop, correctness corruption, or profile drift cannot remain silently routable.
36. No request is admitted whose total or predicted peak context exceeds the target deployment's published context ceiling. A deployment whose ceiling is unknown is not admissible; an absent capability claim is never read as an unbounded one.
37. Reservations expire on absence of observable progress, never on elapsed duration, and reclamation releases every resource the reservation held.
38. A node becomes schedulable only after a real request has traversed its full authorization and admission path. Starting successfully is not evidence of being able to serve.
39. There is no authoritative global provider registry in the request path. Discovery returns a bounded candidate set for a query and never requires enumerating the network.
40. A control is proven only by a test that fails when the control is removed. Specification of a control, and a coverage signal reaching it, are each insufficient. Unproven controls are recorded as owed, never as proven.
41. Every shared vocabulary — outcome, reason code, lifecycle state — is expressed as frozen data, published as a document, and reconciled by test. Prose alone is not a contract.
42. A throughput figure is meaningless without the context depth it was measured at. Runtime configuration is measured on the target placement, never inherited from another model, card or recipe.
43. No placement decision leaves a catalogued model with fewer healthy instances than its availability floor. Instances that are starting, warming or draining do not count, and a GPU is never swapped away from a model at its floor.
