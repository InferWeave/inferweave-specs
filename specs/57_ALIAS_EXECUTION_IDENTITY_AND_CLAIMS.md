# 57 — Alias inference identity and exclusive execution claims

Feature `IW-ALIAS-001`; tasks A-T01/A-T02/A-T04/A-T05/A-T06/A-T08. Protocol 1.1.0,
negotiated `dynamic_aliases: "2"`. This contract extends specs 54–56; it does not qualify an
implementation or enable traffic. Every operational acceptance below remains **owed**.

## 1. Defect and boundary

Spec 55 authenticates alias administration under `/inferweave/v1/`; its signed purpose and
request targets cannot authorize inference under `/v1/`. Spec 54 required idempotent owner
admission without specifying a shared execution identity across parents. Implementing only a
per-process attempt lock or trusting a raw tenant header at `/v1/chat` would allow cross-tenant
selection and two parents admitting the same logical request. These are specification gaps,
not evidence of an exploited incident. This document supplies the missing boundary.

Rust owns inference authorization, the durable execution claim and existing admission. Go only
validates its existing user session/personal-key identity, signs a separately trusted delegation,
and relays unchanged inference bytes. Neither an operator/admin management grant nor node
registration/shared service credentials imply a tenant `infer` grant. No alias-specific scheduler,
backend transport, model inventory or production Python service is introduced. D-005 direct-first
routing remains normal; the same claim also fences a direct execution permit.

## 2. Authenticated inference principal

A native Rust personal key is validated by the existing key subsystem, then mapped to its stable
principal and **current** tenant `infer` grant in Rust. Revocation, expiry, tenant membership,
allowed runtime/model/alias policy and grant revision are checked before resolution and again
at admission. Key rotation does not create a new principal or idempotency namespace. A submitted
tenant is an assertion to match to a grant, never authority. No grant means no level-2 execution;
raw tenant/role headers, anonymous compatibility or shared registration credentials cannot fill
in a missing principal. Multiple applicable tenant grants require an explicit validated tenant
selection; do not choose a tenant by request order. Management roles alone are insufficient.

The Go edge authenticates its existing supported caller credential locally and delegates only
validated `(idp_issuer, subject)` identifiers. Rust independently maps these to current canonical
principal/tenant `infer` grants. A Go personal key without an independently registered issuer and
subject mapping cannot be delegated. No raw bearer, personal key, session cookie, role snapshot or
unsigned tenant/grant header is forwarded to confer authority. A federation parent has separate
transport/forward permission; authenticated origin identity and operation survive hop changes.
A parent cannot mint a new origin or widen its grant. Existing authenticated federation envelopes
must bind that origin and claim; peers lacking this binding cannot execute level-2 aliases.

## 3. Distinct request-bound inference delegation

Exactly one `InferWeave-Inference-Assertion` header carries unpadded base64url UTF-8 JSON matching
`schemas/v1/aliases/inference-assertion.json`. Trust keys are configured for purpose exactly
`inferweave.edge-inference-delegation/v1`, audience, edge and accepted issuer. A spec55 key/purpose
or management assertion is never accepted by inference, and inference proof cannot publish an
alias. Same raw key bytes do not imply trust in both purposes. Go strips inbound assertions and
all unsigned identity/grant headers; each outbound attempt uses a fresh nonce/signature.

Reuse spec55's strict Ed25519, 8192-byte header limit, duplicate-header/JSON rejection, canonical
base64url, UTF-8, current key/grant validation, timestamp bounds, trusted-time rollback guard and
PostgreSQL nonce consumption rules. The ledger uniqueness remains `(edge_id, nonce)` across keys,
purposes and accepting replicas; consume before any protected execution. Failure never downgrades
to anonymous/shared-token execution. Database unavailability fails closed. Inference body caps use
the existing endpoint's bounded limits (including multipart/audio); never copy spec55's 1 MiB
management cap onto inference blindly. Require identity content encoding. Hash exact entity bytes
before parsing; multipart boundary is part of the signed content type. Duplicate body JSON keys
are rejected on JSON endpoints to prevent alternative interpretations.

Only POST to the exact target allowlist in `contracts/protocol-v1/alias-execution.json` is eligible.
The list includes existing compatibility `/v1/chat`, `/v1/chat/completions`, `/v1/completions`,
`/v1/responses`, `/v1/embeddings`, `/v1/audio/transcriptions`, `/v1/audio/speech` and `/v1/rerank`.
A listed target is **not** a claim that a runtime implements it; unsupported endpoint/runtime
fails explicitly. Queries, percent escapes, repeated/dot path segments, authority and fragments
are forbidden for this v1 purpose. New routes require a reviewed allowlist extension.

Start the transcript with literal UTF-8 `inferweave.edge-inference-delegation/v1` followed by one
zero byte. Append each following value as u32 big-endian UTF-8 byte length then bytes. Integer
values use canonical positive decimal ASCII. No separators/final newline; signature is excluded.
The version is exactly integer 1, selected by the domain. The ordered fields are:

1. `edge_id`
2. `key_id`
3. `audience`
4. `idp_issuer`
5. `subject`
6. `issued_at_unix_ms`
7. `expires_at_unix_ms`
8. `nonce`
9. `method`
10. `request_target`
11. `body_sha256`
12. `content_type`
13. `alias_level`
14. `session_id`
15. `timeout_ms`
16. `capabilities`
17. `min_context`
18. `prefer_family`
19. `queue`
20. `tenant_selector`
21. `operation_id`
22. `idempotency_key`
23. `request_fingerprint`
24. `deadline_unix_ms`

Bind actual `Content-Type`, `InferWeave-Alias-Level`, `x-inferweave-session`,
`x-inferweave-timeout-ms`, `x-inferweave-capabilities`, `x-inferweave-min-context`,
`x-inferweave-prefer-family`, `x-inferweave-queue`, `x-inferweave-tenant`,
`InferWeave-Operation-Id`, `Idempotency-Key` and `InferWeave-Request-Deadline-Unix-Ms`.
These map respectively to content_type, alias_level, session_id, timeout_ms, capabilities,
min_context, prefer_family, queue, tenant_selector, operation_id, idempotency_key and
deadline_unix_ms. Absent optional values bind empty strings; alias level is exactly `2`.
Headers are singular, bounded, control-free with no surrounding whitespace; reject ambiguous
or noncanonical forms. Existing semantic parsing still validates every accepted value and
rejects unknown capabilities. The tenant selector must match a current Rust grant; signing a
requested tenant does not grant it. Session reuse cannot weaken requirements or force unauthorized
placement. Header and body constraints combine by strengthening; contradictory selectors or
unimplementable combinations fail explicitly, never take a last-value-wins shortcut.
`timeout_ms`, if present, must be canonical positive decimal within owner endpoint limits;
ingress computes an absolute deadline once, capped by the signed deadline and owner/alias bounds.
Retries retain that effective deadline and cannot reset timeout. The signed absolute deadline
is required even when the legacy timeout header is absent.
All accepted semantic controls belong in this fingerprint. Unknown inference semantic headers
must be rejected or added to the contract before being honored; never accept an unbound control.
The assertion fields must match the actual request, not a detached self-declared request.

`request_fingerprint` is lowercase SHA-256 of the same length-prefix encoding with domain
`inferweave.alias-request-fingerprint/v1\0` and fields, in order: `method`, `request_target`,
`body_sha256`, `content_type`, `alias_level`, `session_id`, `timeout_ms`, `capabilities`,
`min_context`, `prefer_family`, `queue`, `tenant_selector`. Body digest is lowercase
SHA-256 hex of exact entity bytes. Nonce, signature, parent/edge, attempt correlation and transport
are excluded so attempts converge. Deadline is separately signed: retries may shorten the stored
deadline, never extend it. Content-identical intentional new requests are **not** deduplicated by
fingerprint; fingerprint detects changed work under an existing operation/key.

## 4. Canonical identity, idempotency and durable authority

`ExecutionIdentity` has `tenant_id`, `principal_id`, `grant_revision`, `operation_id`, canonical
`request_id`, optional `idempotency_key`, `request_fingerprint`, and `deadline_unix_ms`.
Principal/tenant/grant values come only from Rust authorization. Origin is the canonical principal,
not a mutable key ID or parent/edge identity. Operation ID is opaque high-entropy random identity,
with at least 128 random bits when generated; it is not a content hash. A native unkeyed ingress
generates it; the Go edge generates it once per inbound request and retains it across its bounded
outbound attempts. Client-provided operation IDs are namespaced by authenticated origin and never
confer authority. A retry retains the original operation/request IDs even with fresh proof nonce.
An unkeyed request after an ambiguous disconnected attempt must not be automatically retried as a
fresh operation or on another parent. A user intentionally starting new work is a new operation.

Rust's shared PostgreSQL claim authority enforces unique `(tenant_id, principal_id, operation_id)`.
A supplied idempotency key has a second unique mapping scoped by `(tenant_id, principal_id, method,
request_target, idempotency_key)` to the original operation and request IDs. Create mapping and
claim atomically. The optional key choice is immutable for an existing operation: adding,
changing or removing its key returns `IDEMPOTENCY_CONFLICT`. If an existing key and an existing
operation name different claims, reject the contradictory pair. A rejected key change must not
appear successfully attached to the operation. Concurrent same-key requests with different new
proposed operation IDs converge on
one original operation. A conflict in fingerprint returns `IDEMPOTENCY_CONFLICT` without revealing
the stored payload. Reusing an operation with changed method/target/body/semantic headers is also
a conflict. A different valid principal or tenant cannot read or attach to the original operation.
Bound key lengths, per-tenant occupancy and retention; preserve conflict/tombstone knowledge for
the entire advertised retry horizon. After retirement, reject a retired operation/key rather than
silently recreating it. Compact tombstones retain the retired identities after result eviction.
A bounded ledger that cannot preserve this denial must reject new claims; deleting a tombstone
is not permission to accept that old identity again. A future archival/namespace migration must
prove equivalent retirement denial before removing these fences. The authority must publish/enforce an explicit finite retry horizon before
activation; its duration is a deployment setting, not an invented performance number.

All parents capable of selecting different owners for one operation must converge on this same
claim authority **before** owner choice. Parent IDs are attribution only. A process-local mutex,
per-parent database or independent owner stores cannot establish that uniqueness. Authority
unreachable means no new admission/dispatch. Existing admitted work keeps owner progress/cleanup
semantics; authority outage is not permission to start a competing operation.

## 5. Claim state, fencing and admission

The closed claim shape is `schemas/v1/aliases/execution-claim.json`. State vocabulary:
`CLAIMED`, `RESERVED`, `DISPATCHED`, `TERMINAL`. Claim fields include `claim_id`, identity,
`holder_id`, monotonic `fencing_token`, `last_progress_at`, `ownership_lease`, `attempt_count`,
`response_started`, `reservation_pending`, `dispatch_consumed` and optional
selection/reservation/execution-binding/terminal evidence. These are protected
internal records, never an unredacted public API or bearer credential.

Every mutation uses PostgreSQL compare-and-swap on current holder/fence/state. The existing owner
admission/reservation and node execution boundary also fence stale holders; a database fence that
the node ignores is insufficient. Selection carries alias ID/revision, catalog revision,
`routing_policy_version`, exact `model_id`, immutable `deployment_key`, `instance_id`,
`instance_generation`, `capability_profile_id`, `policy_evidence_id`, `resource_owner_id`,
`resource_group_id` and `requirement_fingerprint`. The profile reference equals the selected
spec54 `capability_profile.profile_id`; resource owner equals its `owner_gateway_id`. Requirement
fingerprint identifies the persisted immutable normalized hard-requirement record in the core,
versioned with routing_policy_version; it is not a grant or a replacement for the required facts.
Recheck spec56 qualifications/current generation,
current grant/policy, resources, cancellation and deadline atomically at owner admission. Do not
pass only a selected model name into an unconstrained legacy router or let its fallback widen the
eligible set. Exact ID precedence from spec54 stays exact across all attempts.

| From | To | Required evidence |
|---|---|---|
| `CLAIMED` | `RESERVED` | Current fence, live grants, hard-eligible instance/generation/profile/policy, atomic owner reservation bound to this claim |
| `RESERVED` | `CLAIMED` | No dispatch occurred; owner confirms nonexecution and releases/fences reservation and every outstanding unspent permit; bounded compatible fallback remains |
| `RESERVED` | `DISPATCHED` | Durably commit dispatch intent with current fence **before** sending inference bytes or issuing a direct permit |
| `CLAIMED` | `TERMINAL` | Cancel, deadline, denial, unavailable capacity or exhausted bounded attempts; no active reservation |
| `RESERVED` | `TERMINAL` | Owner reconciliation and confirmed release/nonexecution; cancel/deadline/denial; no unspent permit |
| `DISPATCHED` | `TERMINAL` | Completion, cancellation, partial failure or ambiguous outcome recorded; cleanup remains owner reconciled |

No other state transitions are permitted. `TERMINAL` is immutable for execution and cannot reopen.
Accounting/cleanup evidence may append without changing the execution outcome. A fresh nonce or
expired ownership lease cannot reopen `DISPATCHED`/`TERMINAL` as new work. A retry observes original
status/result (where retained and authorized); it never reserves a second seat. Stream attachment
or resume is unsupported unless a separately negotiated protocol proves it. Do not cache/replay
sensitive response content as a side effect of this contract.

`ownership_lease` contains `lease_id`, `generation`, `expires_at_unix_ms`. This coordinates claim
holders, **not GPU reservation expiry**. CLAIMED takeover after holder expiry can increment the
fence only before any owner reservation exists. RESERVED takeover requires owner reconciliation,
fencing and confirmed release/nonexecution first. An owner reservation progressing normally is
not reclaimed due to elapsed wall time or database/holder lease expiry (invariant 37). Before calling owner admission, durably record the selected owner/instance, incremented attempt
and `reservation_pending=true` while still CLAIMED. An ambiguous
reservation acquisition must be reconciled by claim ID before retry. The owner reservation API
must be idempotent by `(claim_id, admission_attempt)`, where `admission_attempt` is the durable
positive `attempt_count` captured when starting that attempt. Every acquisition, response, release,
reconciliation and direct permit binds that attempt, holder fence, selected owner and exact
instance/generation. The claim authority never increments the attempt while reservation outcome
is unresolved. A response for attempt 1 cannot complete attempt 2, even at the same holder/fence
and owner; equality of generation alone is insufficient. Same-owner compatible fallback after
confirmed release starts a new attempt and may create a new reservation.

Owners atomically retain retirement tombstones/high-water fences for completed/released attempts.
A delayed acquisition for a retired attempt must return the retired outcome and never create a
new reservation. Retirement must be owner-confirmed before the authority increments the attempt;
if acknowledgement is lost, reconcile the same attempt rather than issuing a new one. Persist
these fences through restart for the same horizon as the claim. With no authority/retirement
proof, an owner refuses new acquisition. A holder change cannot resurrect an old attempt.
Until confirmed, retain the claim and block takeover/admission elsewhere. A request deadline
initiates cancellation; resources are released when the owner confirms stop, not by pretending
unreachable work has stopped.

DISPATCHED is durable **before transmission**, even when zero response bytes have arrived. A
crash after that commit but before send is conservatively ambiguous. Do not automatically replay
nondeterministic inference/tool operations on another model. Direct/relay execution uses the same immutable `execution_binding` below and is exclusive by
**claim ID**, not permit ID. Permits may be reissued for delivery, but two permit IDs, direct plus
relay attempts, or reconnects cannot authorize two executions. Bind claim ID, holder fence,
admission attempt, tenant/principal, exact selected owner/instance/generation, reservation and
deadline in the existing authenticated permit transport. `schemas/v1/aliases/execution-permit.json`
describes these protected fields; it defines no new unauthenticated bearer format.

The node recomputes the executable fingerprint from actual method, target, Content-Type, every
accepted semantic header and exact executable entity bytes. It compares the immutable binding
and current claim/attempt/selection through the authenticated owner authority before spending.
The shared claim authority atomically records `dispatch_consumed=true` once per claim; the node
also persists a one-execution fence by claim so reconnect cannot repeat an already consumed
execution. If consumption acknowledgement is lost, reconcile or fail without replay; neither
side may treat uncertainty as unspent. A new permit/fence/transport does not reset consumption.
Releasing an unused reservation revokes all unspent permits for its retired attempt. No stale
holder may issue/spend a permit. Generic HTTP retry logic cannot bypass this boundary.

### Original request versus executable payload

Rust may replace an alias reference with its admitted exact model and serialize the inference
body for the selected backend. Consequently the original client entity digest and node-visible
digest are generally different. Preserve the original `request_fingerprint` as operation identity;
never replace it with the materialized body's fingerprint during retry lookup.

Before committing DISPATCHED, Rust stores immutable `execution_binding` containing the original
`request_fingerprint`, `executable_request_fingerprint`, `executable_body_sha256`, selected
`model_id`, and `transformation_version`. The only initial version is
`inferweave.alias-materialization/v1`. Both fingerprints use the same spec57 field/domain framing,
applied respectively to original and executable requests. The existing trusted Rust adapter must
validate that the transformation selects the admitted exact model and preserves every other
request value/constraint, method, target, Content-Type and semantic header. Re-serialization may
change JSON whitespace/member order; it cannot change prompt, tools, generation parameters or
hard constraints. Exact identity materialization may use the same version with unchanged model.
A runtime needing another transformation or changed semantic headers must define and qualify it
before use; unsupported body formats fail explicitly. Go must not perform this transformation.

The node validates the **executable** fingerprint, including its body digest and selected model;
the owner authenticates the binding back to the original claim/alias revision and selection.
Comparing only the original body digest, accepting either digest opportunistically, or trusting
an unsigned rewritten model loses this binding. The fixture transformation is a bounded JSON
example, not a production adapter or authorization proof. No materialization may create a new
logical operation, weaken constraints or reopen an ambiguous dispatch. Legacy exact routes retain their prior contract;
this strict execution path is required before level-2 alias traffic is activated.

## 6. Existing router reuse, bounded fallback and diagnostics

Claim once, then use the existing queue/admission/rebalancer with canonical request ID. Every
admission attempt increments durable `attempt_count`, capped by the alias's 1–8 budget and owner
limits across all parents/takeovers. Total deadline is the minimum of caller, alias queue bound
and owner deadline; a retry cannot reset it. Queue admission holds no phantom GPU entitlement.
Only proved pre-dispatch nonexecution permits compatible fallback; if there is doubt, reconcile
instead. Queue/provision policy remains owner authorized and existing demand is deduplicated.
A preview never creates a claim, queue, reservation or model load.

Additive reasons in spec54's frozen error vocabulary:

| Reason | Retryable | HTTP before stream | Meaning |
|---|---|---|---|
| `EXECUTION_IN_PROGRESS` | true | 409 | Existing operation; retry only with same identity to observe status, never start new work |
| `EXECUTION_OUTCOME_UNKNOWN` | false | 409 | Dispatch might have happened; reconcile, no automatic inference replay |
| `EXECUTION_RESULT_UNAVAILABLE` | false | 409 | Original terminal result is not retained/resumable; do not infer again |

Partial output remains `PARTIAL_STREAM_FAILURE`; committed HTTP status cannot change. Use the
existing protocol-compatible terminal error/trace and preserve tool JSON/chunk sequence. Completion,
cancel and timeout arrange fenced owner cleanup, with pending reconciliation explicit. Never
report a released resource before owner evidence. Request IDs link redacted claim/attempt traces,
selected alias revision, exclusions, reservation and owner outcomes. Hide raw issuer/subject,
private candidates, internal endpoints, bearer/lease tokens and cross-tenant telemetry. Go displays
Rust explanations and preserves response bytes, status, authorized metadata and cancellation.

## 7. Evidence and activation gates

`conformance/alias-execution-vectors.json` and `conformance/alias_execution.py` provide reproducible
signature/fingerprint known answers and an offline serial claim transition oracle. They do not
implement production authentication, distributed transactions, fencing, routing or persistence.
Runtime acceptance remains owed: native personal-key revocation/current grants, HTTP signature
binding and separate purposes, shared nonce consumption, simultaneous two-parent/key races,
crash between reservation acquisition and persistence, stale holder/node fencing, direct-permit
one-use, GPU loss, admission-race fallback, queue/cancel/deadline cleanup, partial streams and
ambiguous pre-response dispatch, exact-ID compatibility, authorization redaction and measured load.
Cross-language consumers must replay the same transcript vectors. Independent security review,
actual shared PostgreSQL and owner/node fault injection are required before enabling traffic.

### Independent review corrections

Review of draft PR #256 found three contract defects. The first serial oracle returned an
existing operation without rejecting a newly supplied idempotency key; A/key1 → A/key2 → B/key2
could misleadingly acknowledge a key change and then create separate work. Key choice is now
immutable, with regression coverage for added/removed/changed and contradictory existing keys.
Second, owner idempotency by claim alone could confuse a delayed attempt-1 response with a
same-owner attempt-2 fallback. Acquisition/release/reconcile now bind durable attempt/selection,
and owner retirement fences reject delayed old acquisitions. Third, body-only permit binding
omitted semantic headers and confused original alias payload with Rust's exact-model payload.
The materialization record binds both fingerprints; claim-level consumption covers multiple
permits and direct/relay delivery. Offline fixes do not close the corresponding implementation
gates in OPEN_GATES.
