# Live benchmark workbench: grants, fencing and existing-site rollout

Status: Accepted for implementation by the operator on 2026-10-26. Deployment
is authorized only to the existing bench.metabolomics.us site after validation;
implementation authorization is not evidence of completed production gates.

Feature IDs: IW-BENCH-003, IW-UI-001, IW-BENCH-002.

## Problem and evidence

The merged conductor provided durable leaves and a private status projection,
but no live driver server. Browser sessions were deliberately viewer-only.
Inspection found that gateway operator holds did not fence direct node
admission, and an existing engine drain could proceed after a timeout. Reusing
either as an atomic benchmark-idle proof would permit serving interference.

## Decision

Reuse the existing Rust gateway, registry PostgreSQL store, node admission and
runtime executor. Next.js/TypeScript remains the sole browser application;
shared InferWeave design tokens, stylesheets and components apply to benchmark
and other application surfaces. The operator corrected an intermediate UC Davis
palette request: retain the existing light neutral/green/orange InferWeave theme.
No additional identity provider, role authority, scheduler, or arbitrary shell
execution surface is introduced.

Grants are keyed by the verified OIDC issuer and subject. Roles are viewer,
requester, reviewer and admin. New users are viewers. An explicit local operator
command bootstraps the first administrator once, with audit; it cannot be
repeated to restore revoked privileges. Further mutations require a current
persisted administrator grant, a recent signed authentication time on a verified access token, optimistic
revision and idempotency key. Grant changes and audit rows commit atomically.
Cognito groups, email, browser role fields, and existing generic frontend
operator headers are never benchmark authorization. The operator-selected initial account must resolve to a verified stable identity
before a grant is written; its email is not an authorization key.

Provider access credentials stay in encrypted HttpOnly browser sessions and
travel only server-to-server to an operator-configured gateway. Rust verifies
the bearer signature, issuer, audience, token-use and expiry. Role reads are
uncached; revocation takes effect without waiting for the browser cookie to
expire. Same-origin checks protect browser mutation endpoints. All reads and
writes are bounded; unavailable role storage removes elevated authority.

Benchmark lease ownership is distinct from operator holds, cordons and swap
drains. Gateway acquisition is atomic with routing admission and checks complete
fresh idle telemetry, current registration, model floors and owner priority.
Node acquisition is atomic with direct admission. Each fence persists before
acknowledgement and replays before new work. Expiry does not reopen capacity.
A distinct node-issued credential permits only lease-owned inference, retaining
normal context/resource admission. Restoration uses a separate bounded canary
capability when the work credential has expired. It cannot authorize management.

The first live adapter executes leaves only against an already resident exact
deployment. It refuses model switching until the existing runtime executor has
an explicit lease-owned handoff; no parallel executor may claim its state.
Successful return requires current exact deployment attestation and a real
credentialed, admitted inference probe at the node and gateway boundaries.
Verification errors leave fences in place. Engine/scratch cleanup is limited to
objects proven to belong to the lease; completed journals survive cleanup.

## Protected operations

Hive allocation24781153 and its current benchmark mode remain protected. Do not
release the allocation, resume DeepSeek, or take over its current engines.
Beast remains drained until a new operator instruction makes it eligible.
No DNS or Cognito/AWS mutation is implied by existing-site deployment approval.

## Evidence obligations

Required: signed-access-token route tests; PostgreSQL grant/audit rollback and
CAS tests; immediate revocation and cross-issuer refusal; bootstrap one-shot;
gateway/node acquire-versus-admission races; duplicate/stale owners; restart
replay; failed/ambiguous restoration; full authorized canary probes; bounded
supervised Rust leaf execution; private export/aggregate projection; desktop and
narrow visual checks; isolated campaign completion/cancellation/preemption;
existing-site smoke and rollback. A resident-only test does not prove runtime
switching, and fixtures never establish measured fabric capacity.
