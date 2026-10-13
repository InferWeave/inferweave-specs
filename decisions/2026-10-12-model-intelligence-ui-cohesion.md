# Existing embedded model-intelligence UI and Rust analytics ownership

Date: 2026-10-12. Status: adopted from explicit operator implementation/merge
instructions; independent implementation review and runtime proof remain owed.

The operator supplied the full Model Intelligence & UI Cohesion v1.0 kit and
instructed preservation of the current `metabolomics-us/inferweave-gateway` UI
through full analytics implementation and merge. The source is preserved unchanged
in `docs/specs/model-intelligence-kit/MASTER_SPEC.md`; spec 58 is its canonical
normalization. The kit explicitly states: **Do not replace the existing UI.**
Its repository hint is resolved to `InferWeave/inferweave-specs`.

D-002 previously permitted runtime-family and alias views only. Following that
text literally would forbid the requested analytics on existing pages and could
cause an unwanted replacement frontend. This is an explicit scoped amendment,
not an assertion that the previous exception already covered analytics.

Authorize model-intelligence presentation, existing-page cohesion and optional
system/light/dark parity inside the current embedded Go/TypeScript operator UI.
Preserve current routes, workflows, permissions and default palette; do not create
a second frontend, new app shell or standalone Go browser product. New general
web products remain Next.js + TypeScript. Rust owns all metric normalization,
accounting, storage/aggregation, capacity, evaluation, recommendation and policy;
Go only adapts authorized reads and TypeScript renders results.

New analytics reads require explicit principal authorization. Tenant filters and
`x-inferweave-tenant` do not grant tenant rights. Until verified grants exist,
private tenant/user analytics remain unsupported. Shared operational reports use
redacted aggregate allowlists; privileged reports require operator authorization.
Reuse existing PgStore/facts/events/benchmarks with additive nullable records.
Do not fabricate historical fields or add a metrics storage service.

Rejected: replacement frontend (violates requested workflow preservation);
Go/frontend analytics ownership (duplicates Rust authority); treating existing
tenant headers as identity (unverified grants); inferred historical usage (false
evidence); automatically activating recommendations (unrequested authority).

Implementation and merge are authorized within this scope. This decision grants
no production rollout, hardware qualification, cross-tenant access or model
promotion. Tests, runtime measurements and independent review are separately owed
under OPEN_GATES and the model-intelligence acceptance contract.
