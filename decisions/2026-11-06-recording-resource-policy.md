# Bounded recorder resources and outcome uncertainty

**Status:** Source policy accepted in the operator's 2026-11-06 repair request;
production/shared-filesystem qualification remains unsatisfied.

**Amends:** The implementation detail of the 2026-09-28 buffered gateway
recording decision and spec22. Durable ingest, alias authority, GPU placement,
deployment substrate and production rollout gates are unchanged.

An observed quota incident exposed unbounded retained file growth and ordinary
serving/storage coupling. Its unlogged exit cause remains unproven. Event-count
bounds alone did not specify an encoded-byte/file budget or independent stable
identity provisioning. The selected configurable defaults in
[recording-outcomes-v1.json](../contracts/recording-outcomes-v1.json) are policy
ceilings, not measured machine capacity. They cannot justify larger model,
concurrency, queue or rollout claims. Canonical count bounds are enforced as
ceilings (8192 queued, 128 per batch); configuration may lower them, never raise
them. Reject zero, inconsistent or oversized limits before channel allocation;
explicit discard disables recording without treating zero budgets as a mode.

Ordinary recording uses bounded one-use managed sealing entropy and encoded
reservations without waiting on storage or shared entropy I/O. Existing stable
identity is preprovisioned outside recording storage; unsupported implicit
identity configurations need migration, never a replacement identity. File
budgets preserve historical/uncertain bytes; private namespace/reference checks
and target filesystem writer exclusion must be qualified. No automatic deletion
of acknowledged data is authorized.

A sink can commit and then lose its acknowledgement or terminate. Calling all
unacknowledged work lost is false accounting. Known queued casualties, known
permanent loss and unresolved in-flight outcomes therefore remain distinct in
[frozen vocabulary and its document](../docs/contracts/recording-outcomes-v1.md).
Only unresolved events retry; their reservations remain held. PostgreSQL semantic
receipts commit with supported rows, rejecting mismatched and unproven legacy
semantics. This introduces no PostgreSQL response capture.

Required proof is exact-source local/real-engine negatives plus independent
review. Current evidence and remaining obligations are recorded in
[the repair evidence](../evidence/bounded-recording-2026-11-06/README.md).
Component tests do not open the production, remote-lock or migration gate.

The fixed entropy reservoir has8191 queued objects and one preparing/sending
object (8192 maximum), independent of a lowered event queue. Its prepared gauge
is not a readiness guarantee. This avoids coupling small event-count policies
to a rendezvous-only entropy channel while preserving a finite software bound.
