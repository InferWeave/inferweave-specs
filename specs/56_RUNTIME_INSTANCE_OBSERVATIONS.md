# 56 — Generation-bound runtime observations for dynamic aliases

Feature `IW-ALIAS-001`, tasks `A-T01`, `A-T03`, `A-T05`, `A-T08`; master acceptance
3, 5, 6, 11–17, 19, 20, 23. This additive Protocol 1.1.0 producer contract fills the
missing input boundary of spec 54. It does not close any runtime or production gate.

## 1. Source-backed problem and reuse

Inspected Rust source at `728721907c3dced76de1c297de8849aaeb16cc7c` and the working
runtime producer changes present in that checkout on 2026-10-13:

| Existing path / symbol | Meaning and integration obligation |
|---|---|
| `crates/iw-cli/src/engine_set.rs`, `Engines::generation`, `withdraw`, `mark_registered` | In-memory advertisement counter resets at process start. It fences registration withdrawal; it is **not** a durable model-load generation. Preserve drain-before-unload acknowledgement. |
| `crates/iw-cli/src/engine_driver.rs`, `EngineDriver` load/probe/unload | Existing owner-authorized lifecycle and residency accounting; observation publication must follow its success/failure and withdrawal boundaries. No new loader. |
| `crates/iw-cli/src/node_watchdog.rs`, `WatchdogConfig::activation_id` | Existing activation/fence and GPU safety state. An activation ID or HTTP success alone cannot qualify a different process incarnation. |
| `crates/iw-core/src/profile_report.rs`, `ProfileDecisionReport`, `LaunchIdentity` | Bounded profile selection/launch/drift evidence. A selected configuration does not prove live fidelity or current admission capacity. |
| `crates/iw-gateway/src/node_control.rs`, registration handler | Authenticate node identity and registration incarnation before accepting observations. Bind to the current authorized connection. |
| `crates/iw-core/src/adaptive/controller.rs`, placement lifecycle | Existing placement group authority owns GPU-loss invalidation and resource reuse; observations must follow that state. |
| `crates/iw-gateway/src/adaptive/alias_inventory.rs`, `AdaptiveRouter::alias_inventory_snapshot` | Legacy advertisements project UNKNOWN without generation/policy evidence; do not fabricate READY from merged model names. |
| Working `crates/iw-core/src/runtime_family/observation.rs`, `RuntimeInstanceObservation`; `crates/iw-cli/src/entry/node_runtime.rs`, `stamp_observation`, `initial_observation` | Reuse the per-load observation fields below. The inspected working change is not proof of a released producer or registration ingestion. |

The specification gap was consequential: spec 54 required qualified generation-bound profiles
without defining how a node supplies lifecycle facts or how the owner validates qualification.
Treating existing registration age, a healthy endpoint, or a profile filename as that proof would
make stale or unqualified aliases READY. This correction explicitly prohibits those substitutions.

## 2. Negotiation and bounded wire shape

A node offers `iw.runtime-observations/1` in the existing registration `capabilities` array.
The gateway returns the exact supported intersection bound to that registration's `connectionId`.
The optional camelCase registration member `runtimeObservations` contains the snake_case body
in `schemas/v1/requests/runtime-observation-report.json`. It may accompany the initial offer;
a supporting gateway validates it during registration but cannot expose it as eligible supply
until authentication, registration and capability negotiation commit atomically. An unsupported
peer ignores this optional member under existing extension rules and does not acknowledge the
capability. The producer must observe acknowledgement before relying on delivery.

The body is `{schema_version:1, source_id, source_epoch, sequence, observed_at_ms,
expires_at_ms, complete:true, instances:[...]}`. Each item has `observation`, `required_gpu_ids`
and optional `owner_policy_id` and `qualification_id`. IDs are opaque references, not grants.
`source_id` must equal the authenticated registered node identity. The receiving owner supplies
its own gateway identity and authoritative resource-group mapping; nodes cannot provide those
fields. No endpoint, reservation, lease token, tenant allowlist, inferred capacity or owner grant
is accepted in this report. Routing endpoints continue to come from authenticated registration.

`observation` uses the existing singular `RuntimeInstanceObservation` vocabulary:

- `instance_id`, exact `model_id`, immutable `deployment_fingerprint`, nullable `generation`;
- `source_epoch`, `sequence`, `observed_at_ms`, `expires_at_ms`;
- `lifecycle`: UNKNOWN, LOADING, READY, DRAINING, FAILED, UNLOADED;
- `health`: UNKNOWN, HEALTHY, DEGRADED, UNHEALTHY;
- `capabilities`: canonical runtime `family`, input/output modalities, nullable observed
  `limits.context_tokens_per_slot` and `limits.parallel_slots`, confidence advertised or observed.

Generation is opaque durable entropy identifying one actual process/container/model-load
incarnation. Persist before launch. Process replacement/reload/model or deployment change creates
a new generation. Re-registration, health refresh and a verified no-op adoption of the same live
incarnation preserve it. A legacy journal with no lineage retains null generation and cannot be
READY for alias selection. The producer's journal epoch is separately durable; missing/replaced
journal identity creates a new epoch and requires full resynchronization. Never derive generation
from model name, endpoint, wall-clock, registration ID, GPU inventory revision or engine-set counter.

Version 1 uses **full snapshots only**, at most 256 items, with unique instance IDs. Runtime report
encoded size is at most 256 KiB (262144 actual UTF-8 transport bytes, including whitespace);
check this bound before JSON decoding, never after reserializing a parsed object. A registration
ingester must bound the raw member span or apply an equally strict whole-body cap before decoding.
Existing stricter registration/body limits still apply. IDs and
arrays are bounded by schema, numeric values by the interoperable unsigned 53-bit integer range.
An oversized report must fail explicitly, never truncate into a complete snapshot. An owner may
impose tighter negotiated operational limits. TTL is positive and at most 60000 ms; 10000 ms is
the current producer's configured default, not a measured freshness SLO. Future-dated or expired
reports cannot establish current facts. Receiver trusted time and connection freshness cap validity;
clock disagreement fails closed with diagnostic status rather than extending expiry.

## 3. Ordering, invalidation and event projection

Envelope sequence increases within source epoch; an item's sequence is no greater than envelope
sequence, its epoch matches, and its observation time is no later than envelope observation time.
An item's expiry may be earlier or later than the envelope; effective validity is their minimum.
Envelope monotonicity does **not** replace per-item ordering. The owner retains the highest
accepted item sequence and canonical full item content for each source epoch/instance/generation,
including items omitted from subsequent snapshots. An item below that fence is rejected; equal
item sequence is allowed only with identical full item content and unchanged expiry. Any change
to lifecycle, health, GPU references, policy/qualification references or timestamps requires a
strictly newer item sequence. Reject the entire conflicting snapshot atomically. For example,
DRAINING item sequence 2 cannot be replaced by old READY item sequence 1 carried inside a newer
envelope sequence 3. Unchanged older items may be carried forward only while their original
expiry remains valid. Retain item fences alongside tombstones through the authenticated epoch
lifetime, with the same restart/resynchronization obligations below.
Expiry never grants lease reclamation authority and does not replace progress-based leases.

Only the current authenticated registration incarnation may submit. On an epoch transition the
owner atomically invalidates the prior source snapshot, establishes a new source baseline through
registration, and accepts only a complete snapshot. Old-incarnation deliveries cannot switch the
source epoch back. Persist retired-epoch/replay fences or reconstruct them by requiring a fresh
registration after owner restart; never restore READY facts from an unauthenticated cache.

Same epoch/sequence with identical canonical content is an idempotent replay with unchanged
expiry; same sequence with different content is a conflict. Lower sequence is rejected. A gap in
this full-snapshot protocol may be repaired by a newer authenticated complete snapshot; no delta
can cross a gap. For the current authenticated registration, after disconnect, expiration, malformed/conflicting replacement report or loss of
negotiation, mark affected facts unqualified until a valid current snapshot is accepted. Processing
and invalidation are atomic with the owner catalog revision. Rejection of an unauthenticated
or retired-connection replay must not invalidate a legitimate successor registration.

An item with UNLOADED lifecycle is a tombstone for its instance/generation; it invalidates the
route irrespective of health. Omission from a newer complete snapshot also removes previously
observed instances. FAILED/DRAINING/unhealthy and absent required GPUs immediately invalidate
eligibility. A tombstoned generation cannot return as READY, even at a later sequence; a true
reload needs a new generation. Keep tombstone knowledge for the current epoch or until an
owner-authenticated epoch reset invalidates all old facts. Empty complete snapshots are valid.
Producer heartbeat without the optional report clears level-2 observation eligibility on
re-registration; legacy exact-model registration behavior remains governed by its existing contract.

`schemas/v1/events/runtime-observation-event.json` and its fixture describe the **internal owner
projection** `runtime.observations.snapshot`, containing the accepted report. This does not add a
public HTTP endpoint or make raw node/GPU IDs visible to UI readers. Existing owner event storage
provides cursor/resume, retention and redaction. Alias/catalog projections emit spec54 events only
after owner validation. A consumer losing its event cursor requests the existing authoritative
snapshot; event replay never reinstates expired facts or increases admission counters.

## 4. Qualification and owner policy

Observed health/limits mean the named probe measured those properties. The producer vocabulary
`observed` is not spec54 `verified`, and cannot be mechanically promoted to it. In particular a
health endpoint, text completion or launch profile does not verify tool fidelity, JSON constraints,
image understanding, privacy, residency, license or tenant authorization. Unsupported or absent
facts remain unknown. Probe adapters must state which limits they actually measured; launch
configuration ceilings remain advertised until observed.

An optional `qualification_id` resolves in the owner's trusted verifier/evidence store to a
bounded spec54 `capability_profile` and its underlying qualification record. The owner independently
checks that the record binds the same exact model, immutable deployment, instance generation, producer source epoch,
required GPU set, runtime/protocol/build identities, allowed verifier purpose and freshness. Every
feature retains its own fidelity/confidence/provenance. A verification ID or a node-supplied claim
is insufficient. A record for another generation cannot be copied after reload. It may only be
requalified by the approved verifier against the new incarnation. Invalid/stale references do not
fall back to verified defaults. This protocol specifies the evidence boundary, not a new verifier
implementation or a claim that any verifier is operationally qualified.

`owner_policy_id` likewise references independently authorized owner policy. Missing, revoked or
foreign policy denies alias eligibility and tenant disclosure. Node enrollment or model execution
proof does not authorize tenant, privacy or federation policy. The owner binds the policy to its
registered node, placement group and allowed tenants; the node cannot edit those grants. The
profile `policy_evidence_id` must identify the resolved policy evidence. Policy changes invalidate
snapshots and caches even if the node report sequence is unchanged.

The owner constructs spec54 instance identity/profile only after those checks. `required_gpu_ids`
are producer claims cross-checked against owner placement inventory. The owner canonicalizes all
co-allocated GPUs into a stable owner/resource-group identity shared across parents; changing a
node's spelling or reporting through a second parent must not create additional supply. Overlapping
resource groups use the existing common resource ledger. Losing one required GPU invalidates the
whole placement and generation. Remaining GPUs become candidates for the existing rebalancer only
after owner revalidation, never by splitting the failed instance into phantom capacity.

READY lifecycle plus healthy current generation is **necessary but insufficient** for a READY
alias candidate: policy, qualified jointly satisfiable capabilities, reachable current instance,
placement and available owner admission must all pass. `parallel_slots` describes an observed
runtime limit, not free seats. Neither report, qualification, advertisement nor preview grants
allocation entitlement. Only existing atomic owner admission establishes entitlement, rechecking
policy, lifecycle generation, physical resources, idempotency, deadline and active reservations.

## 5. Compatibility, acceptance and proof

Old nodes without observations continue existing exact-model behavior; their level-2 alias facts
remain UNKNOWN. Old gateways ignoring the member cannot acknowledge support or advertise qualified
level-2 supply from it. Unknown report versions/closed fields fail validation on supporting peers;
no interpretation as version 1, downgrade to a permissive policy or synthetic generation is allowed.
No additional Go inventory, qualification logic or scheduler is authorized. Go may transport typed
reports unchanged through an authorized existing path and display redacted Rust projections.

`conformance/runtime_observations.py` exercises the schemas and bounded reference acceptance rules
against positive/negative vectors. It cannot prove actual registration authentication, persistence,
GPU-loss propagation, verifier trust or owner admission. Required producer/ingestion/mixed-version
integration evidence remains **owed** under A-T05 and the open gate. The exact source commit, test
commands, failure injection and live traces must accompany any future claim of runtime proof.

### Contract review corrections

Independent review of PR #254 found that the first offline reference checked only envelope
sequence, so a new envelope could resurrect an older READY item after DRAINING. It also checked
JSON shape without checking encoded byte length, allowing a schema-valid 334441-byte report
through the specified 256 KiB limit. The item sequence/content fence and predecode byte bound
above correct specification defects; implementers must not reproduce the earlier permissive
interpretation. Hostile vectors include stale-item replay, same-sequence item conflict, retained
fences across omission, oversized content and oversized JSON whitespace. Their offline success
remains distinct from producer/owner implementation proof.
