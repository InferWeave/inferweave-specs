# 54 — Dynamic Model Aliases, negotiated level 2

## Authority, source and compatibility

Feature `IW-ALIAS-001`, tasks `A-T01`–`A-T08`. The operator handoff is retained verbatim in
`INFERWEAVE_DYNAMIC_ALIASES_MASTER_SPEC.md`; the source audit and baselines are in
`docs/alias-implementation-gap-matrix.md`. This specification reconciles that proposal with
D-001/D-002/D-005, invariants 5–8, 11–16, 19–25, 32, 36–43 and specs 40–53.
The handoff is a target, not evidence of deployed support. Implementation acceptance is **owed**.

Protocol `VERSION` remains **1.1.0**, an unreleased additive minor bundle. Handoff version **1.0**,
protocol version **1.1.0**, feature level **2**, object `api_version: inferweave/v1`, event schema
`inferweave.alias-event/v1`, routing policy version and monotonically increasing per-alias revision
are independent version axes. Publishing a revision does not change protocol compatibility.

`dynamic_aliases: "1"` retains spec 45 and `schemas/v1/model/alias.json` exactly. A producer MAY
advertise `dynamic_aliases: "2"` only after passing the level-2 implementation gates. That offer
includes level-1 support. Clients explicitly select level 2 with `InferWeave-Alias-Level: 2` on
native HTTP calls after discovery. No header (including a level-1 consumer) receives the existing
`GET /aliases` array. Explicit level 2 receives the paginated envelope. Unsupported levels fail
with `UNSUPPORTED_ALIAS_LEVEL`; never silently downgrade a policy or write. New management routes
require the header; existing exact-model/OpenAI traffic does not. Unknown feature names remain
ignored per spec 45. New policy members in closed writes are rejected, not silently ignored.
Read-only legacy extension fields retain their existing unknown-field rules.

Level-2 schemas are `schemas/v1/aliases/contract.json` and its small named entry-point schemas.
The schema is normative for shape; semantic validation below is also required. Fixtures are
illustrative, never a claim that a production model, alias, instance or resource is READY.

## Ownership and terminology

Rust in `InferWeave/inferweave` owns durable desired state, published revisions, effective health,
matching, ranking, routing, admission, queues, provisioning, runtime adapters and federation.
The existing Go site gateway may provide typed API consumption, operator forms and authorized
transparent edge relay under the narrow D-002 amendment. No Go alias database, model selector,
scheduler, backend-specific integration, discovery implementation or authoritative inventory is
created. Existing analytics aliases and legacy routing are migration inputs only.

A concrete model is immutable checkpoint/revision identity; a deployment is its immutable runtime
fingerprint; an instance is one owner, placement group and lifecycle generation. Model tags merged
across workers cannot prove any one instance supports a combination of capabilities. An alias is
a stable tenant-visible name of a versioned selection policy. A preview is a snapshot evaluation;
only owner admission grants a reservation. A gateway remains control authority: D-005 direct
client/local-proxy to node is the normal data path; edge byte relay remains compatibility fallback.

## Definition, validation and publication

A `ModelAlias` has `id`, `revision`, `status`, `description`, `visibility`, `owner_scope`, typed
`selection`, `execution`, and bounded metadata. IDs are normalized lowercase ASCII slugs of 1–63
characters. Owner scope is separate from the slug; authenticated tenant plus slug identifies the
record. PRIVATE/TENANT/PUBLIC visibility never bypasses owner/tenant authorization. Public names
and local exact-model names may not collide within a caller's resolution namespace. Creation
rejects canonical IDs, reserved `alias:`/`cap:` syntax and ambiguous existing legacy names.

`selection.type` is MANAGED or DYNAMIC. MANAGED requires nonempty `model_ids_allow`; DYNAMIC
queries typed capabilities, optionally constrained by allowed model families and immutable IDs.
Deny takes precedence. For DYNAMIC selection, omitted or empty `families_allow` and
`model_ids_allow` mean no family/model pinning; an empty `model_ids_deny` has no denials.
MANAGED still requires a nonempty concrete-model allowlist. These selection conveniences do not
apply to `required.allowed_tenants`, `required.trusted_origins` or `required.residency`: an explicit
empty authorization/acceptable-origin set admits nobody. Owner authorization and trust checks
always fail closed independently of selection lists. Family allowlists denote model family
metadata, never substring parsing.
Alias-to-alias targets are prohibited at level 2; model allowlists contain concrete IDs only.
Legacy import detects cycles and depth >4 and rejects them before publication. No recursive runtime
resolution chain is introduced. Weights must be finite, nonnegative, nonempty and sum to 1 within
1e-6; all-zero weights fail. The API returns normalized weights only after explicit validation.

Capabilities reuse spec 48 runtime families, not a competing class registry: chat/completions use
`llm`; speech-to-text uses `stt`; rerank uses `reranking`. `system_one` is not a new family by name:
its alias requires the actually registered prediction/other approved family and structured feature
evidence. Unknown families fail closed until a canonical registry extension is negotiated.
Required input/output modalities, context/output ceilings, feature fidelity/confidence, embedding
dimensions, schema digest, privacy, residency, trusted origins and allowed tenants are structured.
Unknown constraints and unsupported semantics fail `INVALID_CAPABILITY`; never silently omit them.

All writes run in Rust under tenant/owner RBAC. Viewer reads; operator drafts/simulates if granted;
administrator publishes/rolls back/shares. Edge authentication is additional. A tenant in a request
body is an assertion to validate against trusted principal claims, never a source of authority.
Native `/inferweave/v1/aliases*` must enter the canonical Rust authentication gate; protecting only
`/v1/*` is insufficient. The source audit found no currently usable Go-to-Rust end-user delegation mechanism. Alias
API/traffic activation therefore remains disabled until A-T02 proves a separate request-bound
edge Ed25519 assertion purpose. Rust must resolve validated `(identity-provider issuer, subject)`
into its own tenant/role grants. The assertion binds method, canonical target, body digest,
preconditions, deadline and nonce; Rust verifies audience/purpose/key trust, expiry and replay
protection. Cross-language positive and hostile vectors are required before rollout. The exact transcript, transport, key trust and PostgreSQL replay contract is
`55_ALIAS_EDGE_DELEGATION.md`; it must receive independent security review before implementation
claims conformance. Forwarding an OIDC token, a shared registration token, arbitrary tenant/role
headers or unsigned caller identity cannot substitute for this gate. Existing service credentials
do not confer end-user publish authority.

POST creation uses `If-None-Match: *`; all mutation calls use an `Idempotency-Key` scoped to actor,
tenant, method and resource. Repeated same key/body returns the original result; changed body is
`IDEMPOTENCY_CONFLICT`. PATCH, publish and rollback require strong `If-Match: "<revision>"` of the
resource. Missing precondition is 428; conflict is 412, with an authorized current revision/diff.
No blind overwrite. PATCH is a complete draft definition replacement, not JSON Merge Patch.

A resource revision increases on every successful mutation. Drafts have revisions and are not
routable. Publish creates a new immutable revision atomically from the named validated draft;
rollback publishes a new revision copied from an earlier published definition. Neither edits old
history. Audit records actor, timestamp, reason, SHA-256 content hash, approval if required and
rollback source. Hash is SHA-256 of the authoritative Rust store's deterministic JSON serialization of the
definition. The immutable revision records that hash; clients treat it as an opaque integrity
token and retrieve the authoritative revision for audit. A serialization change must preserve
verification of previously published hashes. Owner scope/id are
immutable. Disabled is a published desired status; no delete erases history. Empty/impossible
policies fail publication unless owner policy has a separately audited privileged override.
The level-2 API in this revision exposes no bypass field. Crash/restart and concurrent writes must
preserve one current published revision and complete audit atomicity using the existing Rust store.

## Resolution and dispatch

1. Explicit `model_id` or canonical qualified exact ID selects only that model revision.
2. Explicit `alias_id` or `alias:<id>` evaluates only that visible alias.
3. Legacy `model` selects exact named model, then published managed alias, then recognized dynamic
   alias. Import records collisions as warnings and cannot activate an ambiguous new alias.
4. Request requirements intersect/strengthen alias policy. Tenant, license, privacy, trust,
   residency, deny and owner sharing policy cannot be weakened; booleans for federation/cold start
   are logical AND. Conflicting requirements are a safe failure. Client context relaxation must
   be explicit, authorized and traced and cannot go below the alias's floor.
5. Capture immutable alias revision, caller policy fingerprint and bounded catalog snapshot token.
   Catalog revision is an owner snapshot/vector token, not a fictional global atomic cut (spec 40).
6. Evaluate individual model/instance/generation/deployment/owner/resource-group tuples. Each
   candidate includes one jointly satisfiable `capability_profile`, timestamped expiring evidence,
   verification ID, policy evidence and resource ownership. Capability-profile `instance_generation` is required and must match the candidate instance
   generation. Provenance `source_generation` remains the source/owner stream epoch and can differ
   from the instance generation; never compare these separate identities. Required profile
   `confidence` records qualification of runtime/modality/limit/policy facts; requirements may
   specify `profile_confidence` as advertised/probed/verified. Alias omission defaults to verified;
   request omission inherits the alias minimum. Explicit request minimums can only strengthen it; unknown/degraded/disabled never satisfy a hard qualified profile.
   A nonempty verification ID alone does not upgrade confidence. A profile may also carry
   `max_output_tokens`, `embedding_dimensions`, `output_schema_digest`, `privacy`, `residency`
   and `trusted_origin`. These facts are jointly true for that profile and share its evidence
   expiry; absence is unknown and cannot satisfy a corresponding hard requirement. Profile
   `privacy` is a set of guarantees; `residency` and `trusted_origin` are single observed labels
   matched against request acceptable sets. Owner policy authorizes disclosure per receiving
   principal; never publish tenant allowlists or private policy details upstream. Omit a protected
   claim and mark the required match unqualified rather than fabricate compatibility. Advertised/unknown is not verified;
   degraded/disabled/stale evidence cannot satisfy a verified requirement. Probed/advertised
   confidence is accepted only when the hard policy explicitly permits it. Federation cannot
   promote confidence or trust.
7. Hard-filter runtime, modalities, features/fidelity, ceilings, policy, reachability, owner opt-in,
   READY health and current generation. Classify ELIGIBLE, QUEUEABLE, COLD_START_POSSIBLE,
   PROVISIONABLE or EXCLUDED with frozen reasons. Only READY may be ELIGIBLE; busy, cold, unloaded,
   warming, draining and lost placements provide no immediately available route.
8. Rank eligible instances using a versioned deterministic policy. Scores are normalized per
   candidate set with contributions, units, metric freshness/sample counts and missing evidence
   treatment. Optional candidate `metric_evidence` maps at most 16 bounded metric names to
   `{value, unit, sample_size, confidence, provenance}`. Provenance carries observed/expiry times,
   source identity/generation, build/protocol and verification ID. Names such as `latency_p50`,
   `latency_p95`, `throughput` and `quality` identify measured quantities; `factors` remains the
   normalized scoring contribution. Evidence is visible only within authorized tenant/workload
   scope; omitted evidence is unknown, never an invented zero or a measured percentile.
   Low-confidence quality cannot beat qualified evidence without separately permitted
   exploration. Stable instance identity breaks ties. Smallest sufficient resources is a bias
   only after hard constraints and qualified quality floors. No fixed-slot scheduler is added.
9. Admit through the existing owner router with idempotency key, alias/catalog revision, instance
   generation, deadline and scoped lease. Revalidate policy, generation, readiness and measured
   resources atomically. Cache eligibility hints only; never cache entitlement. Multiple parents
   must not double-admit a retry. Bounded pre-stream races may try the next compatible candidate;
   `max_admission_attempts` is 1–8 and total queue deadline 1–300000 ms, further capped by owner.
10. With no READY target, existing authorized queue/demand/rebalancer flows may provision only when
    both caller and alias/owner permit. Preview and simulation never enqueue, reserve, change demand,
    allocate, load/unload, start jobs or consume a lease. Preserve valid affinity; incompatible
    stateful migration fails clearly. After first response byte, no hidden replay or substitution.
11. Cancellation, timeout and completion release reservations. Lease expiry follows absence of
    observable progress (invariant 37); a request deadline cancels work and releases its lease,
    but is not a wall-clock reservation reclamation policy.

Preview response includes alias/catalog/policy revision, evaluated/expiry times, status, bounded
redacted candidates and `admission_reserved: false`. `selected` is optional and must reference an
included ELIGIBLE READY candidate with matching generation/profile. Expiry is after evaluation
and no later than any selected evidence expiry. A response with no suitable ready candidate cannot
be READY. DEGRADED has at least one ready eligible instance with separately explained degradation;
QUEUE_ONLY, PROVISIONABLE, UNAVAILABLE and DISABLED cannot claim an immediately ready selection.

## Runtime, GPU and federation integration

Use existing runtime facts and spec 50 transactional lifecycle, load single-flight, measured peak
reservations, caches, rebalancer, hysteresis/cooldown and availability floors. Weights, runtime
startup overhead, KV/cache, fragmentation, reservations and actual free headroom remain distinct.
Losing one required GPU invalidates the entire atomic placement group/generation; unused surviving
GPUs may enter existing smaller-model placement after owner revalidation. No alias-specific
scheduler or Go Slurm/Kubernetes/Docker integration is permitted.

Owner-authorized advertisements use bounded valid capability profiles; never union vision/tools/
context from disjoint instances into an impossible capability claim. Stable owner/resource-group
identity deduplicates shared physical supply advertised to several parents. Availability, offer,
reservation and READY endpoint are different states. `allocation_entitlement: false` is mandatory.
Profiles are conservative current facts; WARM/PROVISIONABLE are not READY. Signed/authenticated
links bind provenance, generation, monotonic sequence, expiry, bounded path vectors and tombstones.
Reject cycles/replays/stale offers; local owner demand outranks upstream and revokes/preempts
permitted loans with immediate route invalidation. Upstream demand is advisory, not authority to
install, provision, execute code or open a tunnel. All admission remains owner atomic and idempotent.

## Native API and compatible edge transport

Paths below are relative to `/inferweave/v1`, following specs 45/49 and native OpenAPI. `/iw/v1`
site-gateway topology endpoints coexist; alias policy does not move there. Request IDs use the
existing `{request_id}` route parameter. OpenAPI operations reference the standalone schemas.

| Method/path | Meaning | Body / response |
|---|---|---|
| GET `/aliases` | Visible definitions; level 1 unchanged, level 2 paginated | list |
| POST `/aliases` | Create draft, idempotent and absent precondition | draft-write / detail |
| GET `/aliases/{id}` | Current draft/published/effective state | detail |
| PATCH `/aliases/{id}` | Complete draft replacement with CAS | draft-write / detail |
| POST `/aliases/{id}/validate` | Read-only stored draft validation | draft_revision / validation |
| POST `/aliases/{id}/publish` | Atomic immutable publication | publish / detail |
| POST `/aliases/{id}/rollback` | Publish copy of prior revision | rollback / detail |
| POST `/aliases/resolve` | Read-only live candidate preview | resolve-request / resolution |
| POST `/aliases/simulate` | Read-only hypothetical definition preview | simulate-request / resolution |
| GET `/aliases/{id}/history` | Tenant-scoped audit pagination | history |
| GET `/catalog/models` | Authorized concrete models and instance profiles | catalog |
| GET `/requests/{request_id}/routing` | Existing causal routing explanation | existing route, extended typed trace |
| GET `/events` | Existing resumable source stream, alias events negotiated | event envelope |
| GET `/federation/alias-advertisements` | Authorized conservative envelopes | advertisement page |

Lists use opaque cursors bound to principal, filters and snapshot, limit 1–100 (default 50).
Expired cursor returns 410 and requires new snapshot; malformed cursor returns 400. Filters are
server-side: `query` (case-insensitive alias ID/description), `runtime_family`, `owner_scope`,
`status` (effective health), `visibility`, `route_kind` and `family` (structured model family).
Filters are conjunctive; omitted filters are unrestricted only within the authorized view.
An unsupported or malformed filter returns 400, never an unfiltered page.
The server applies authorization before filtering/counts; cursor tampering cannot widen access.
Every response identifies authoritative observed time/revision. Never expose forbidden model IDs,
internal addresses, peer secrets, lease tokens or cross-tenant metrics in catalog/preview/errors.
Dry-run limits and candidate cap (256) are enforced in Rust; truncated output is explicitly flagged.

`/v1/models` retains OpenAI list shape and includes permitted published aliases plus exact models.
Expose aliases only when their semantics can be honored; do not advertise richer level-2 policy
through an older parent that can only reinterpret it as a level-1 hint. Exact request identity is
preserved. Authorized execution may include `x-inferweave-request-id`, `x-inferweave-alias`,
`x-inferweave-alias-revision`, `x-inferweave-resolved-model` and routing-policy metadata. Headers
must be redacted by principal policy. Go compatibility relay preserves status, bytes, SSE chunk
order/tool JSON, multimodal/audio content types, caller deadline, cancellation, backpressure and
idempotency. It never resolves or re-scores aliases from a UI cache.

## Events, errors, cache and telemetry

Frozen vocabulary is `contracts/protocol-v1/dynamic-aliases.json`; tables below are reconciled
against schemas by `guard_dynamic_alias_contracts`, including deliberately corrupted self-tests.
Reason retryability is a classification, not permission to replay an operation; retries still obey
idempotency, deadline and pre-stream constraints. A partial stream cannot change an already sent
HTTP status; emit a protocol-compatible terminal diagnostic and record the reason. Capacity is
503, caller/rate/FairShare limitation 429. Authorization redacts reason detail when disclosure itself
would reveal a hidden object (including existence). All errors have code/message/retryable and a
correlation ID; retry-after is optional and measured.

| Reason | Retryable | HTTP before stream |
|---|---|---|
| `ALIAS_NOT_FOUND` | false | 404 |
| `ALIAS_DISABLED` | false | 400 |
| `ALIAS_CYCLE` | false | 400 |
| `ALIAS_DEPTH_EXCEEDED` | false | 400 |
| `ALIAS_NAMESPACE_CONFLICT` | false | 409 |
| `INVALID_CAPABILITY` | false | 400 |
| `FEATURE_UNVERIFIED` | false | 400 |
| `CONTEXT_TOO_SMALL` | false | 400 |
| `MODALITY_UNSUPPORTED` | false | 400 |
| `POLICY_DENIED` | false | 403 |
| `TENANT_DENIED` | false | 403 |
| `TRUST_DENIED` | false | 403 |
| `RESIDENCY_DENIED` | false | 403 |
| `NO_READY_INSTANCE` | true | 503 |
| `NO_ADMISSION_CAPACITY` | true | 503 |
| `QUEUE_DEADLINE` | true | 503 |
| `PROVISIONING_UNAVAILABLE` | true | 503 |
| `COLD_START_DISALLOWED` | false | 400 |
| `STALE_ADVERTISEMENT` | true | 503 |
| `FEDERATION_UNAVAILABLE` | true | 503 |
| `LEASE_CONFLICT` | true | 503 |
| `MODEL_DRAINING` | true | 503 |
| `MODEL_PREEMPTED` | true | 503 |
| `INSTANCE_GENERATION_STALE` | true | 503 |
| `BACKEND_UNHEALTHY` | true | 503 |
| `BACKEND_UNREACHABLE` | true | 503 |
| `UPSTREAM_RATE_LIMITED` | true | 429 |
| `RETRY_BUDGET_EXHAUSTED` | true | 503 |
| `PARTIAL_STREAM_FAILURE` | false | 400 |
| `CLIENT_CANCELLED` | false | 400 |
| `REVISION_CONFLICT` | false | 412 |
| `PRECONDITION_REQUIRED` | false | 428 |
| `IDEMPOTENCY_CONFLICT` | false | 409 |
| `UNSUPPORTED_ALIAS_LEVEL` | false | 400 |

Health: `READY`, `DEGRADED`, `QUEUE_ONLY`, `PROVISIONABLE`, `UNAVAILABLE`, `DISABLED`.

Events: `alias.created`, `alias.published`, `alias.disabled`, `alias.state_changed`, `alias.resolved`, `request.candidate_excluded`, `request.admission_failed`, `request.routed`, `request.fallback`, `request.completed`, `deployment.ready`, `deployment.draining`, `deployment.lost`, `offer.updated`, `offer.revoked`, `lease.preempted`, `capacity.changed`.


A subscription starts with authorized versioned full snapshot, followed by monotonic per-source
sequence deltas, heartbeat and opaque resumable cursor. De-duplicate by source/generation/event ID.
Sequence gaps or expired cursor force snapshot recovery; until recovered, state is visibly stale
and unverified READY supply is not advertised. Generation changes and tombstones prevent stale
resurrection. The existing event envelope remains transport authority; the alias event payload
adds the negotiated typed metadata. Bounded retention/sampling and per-tenant cardinality prevent
telemetry from blocking admission. Request trace metadata carries no prompt/output bodies.

Compiled policies cache by immutable revision. Candidate hints key alias/catalog revision,
principal-policy scope and requirement fingerprint. Negative TTL is short and invalidated on
ready/health/capacity/deployment/offer change. Capacity is always revalidated by owner at admission.

Required bounded metrics: alias_resolution_total, alias_resolution_duration_seconds,
alias_candidate_filter_total, alias_admission_attempts_total, alias_route_selected_total,
alias_fallback_total, alias_queue_wait_seconds, alias_cold_start_seconds, alias_active_requests,
alias_eligible_instances, alias_ready_seats, alias_federation_offers,
alias_stale_advertisements_total, alias_lease_conflicts_total, alias_revision_published_total,
alias_resolution_cache_hits_total and alias_resolution_stale_rejects_total. Metric labels exclude
secrets and uncapped identifiers. Policy-approved per-request trace links edge, owner and instance,
filter/rank contributions, retry history and completion. Measure p95 overhead before activation;
no invented latency target or unmeasured performance claim is a release gate pass.

## Administration, migration and release gates

Existing Go navigation gains Models > Aliases, index and filters, effective states/snapshot age,
candidate tree, configuration draft/editor, required-vs-preferred controls, validation/preview,
impact/diff, publish/history/rollback, Routing Explorer, read-only workload simulation, federation
profiles/provenance and model/runtime/GPU crosslinks. Show actual measured metrics with sample size
or explicit unknown. Core API owns all counts, policy outcomes and ranking. Presets populate
constraints only. Existing family registration determines which workload presets are available.
A test inference is a separately labeled action, never a side effect of simulation.

Design loading, empty, unauthorized, offline/stale, partial, failure, disabled and conflict states.
Preserve keyboard access/ARIA, non-color status labels, contrast, desktop/tablet responsive layout,
server pagination, throttled event invalidation with backoff and stale badges. Protected publish,
disable, rollback and sharing actions require confirmation in the product and Rust authorization.
Screenshots/keyboard/accessibility traces are required across index, editor/detail, routing,
federation, tablet and failure states. The CLI agent's authorization to implement these screens
is not a reason to remove user-facing operation confirmations.

Inventory existing Rust operator/static/logical aliases and Go worker/model aliases; characterize
exact names before import. Shadow compare eligibility/decisions before any traffic switch. Feature
flag `alias_engine_v1` and read-only UI flag default off until parity/security gates pass. No
migration marks a hard capability verified without evidence. Preserve legacy exact behavior and
mixed-version links. Remove Go duplicate selection only after parity and rollback window; never
remove active production behavior merely because the target contract differs.

Phase A contracts/audit precede B Rust shadow preview, C owner admission/runtime/federation,
D Go consumer/UI, E measured tenant-scoped canary rollout and F verified cleanup. Expired/unavailable
providers, GPU loss, multi-parent contention, preemption and partial stream failures are mandatory
failure tests. Enablement requires automated acceptance evidence, independently reviewed changes,
measured baseline/canary traces and tested feature-flag rollback; compilation is insufficient.

`contracts/dynamic-alias-acceptance.json` maps all 29 master acceptance IDs to canonical lanes,
required evidence and **owed** runtime status. Local contract/schema tests prove only artifact
consistency. Runtime tests, security enforcement, UI journeys and live rollout remain owed until
recorded with repository commit, exact command and result. `OPEN_GATES.md` records these omissions.

## Additional frozen vocabularies

| Vocabulary | Values |
|---|---|
| `confidence` | `advertised`, `probed`, `verified`, `degraded`, `disabled`, `unknown` |
| `fidelity` | `native`, `translated`, `emulated`, `unsupported`, `unknown` |
| `visibility` | `PRIVATE`, `TENANT`, `PUBLIC` |
| `desired_status` | `ACTIVE`, `DISABLED` |
| `selection_type` | `MANAGED`, `DYNAMIC` |
| `fallback_policy` | `NONE`, `COMPATIBLE_ONLY` |
| `eligibility` | `ELIGIBLE`, `QUEUEABLE`, `COLD_START_POSSIBLE`, `PROVISIONABLE`, `EXCLUDED` |
| `route_kind` | `LOCAL`, `FEDERATED` |
| `instance_state` | `READY`, `BUSY`, `COLD`, `PROVISIONABLE`, `DRAINING`, `LOST`, `UNHEALTHY`, `UNKNOWN` |
| `advertised_availability` | `READY`, `WARM`, `PROVISIONABLE`, `UNAVAILABLE` |
| `trace_stage` | `resolve`, `filter`, `rank`, `admission`, `queue`, `provision`, `route`, `stream`, `complete`, `fallback`, `error`, `cancel` |
| `preview_warning` | `PREVIEW_ONLY_REVALIDATE_ON_DISPATCH`, `CANDIDATES_TRUNCATED`, `METRICS_UNAVAILABLE` |
