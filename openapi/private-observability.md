# Private normalized request telemetry HTTP

This additive contract serves IW-OBS-001/IW-TEL-001/IW-BENCH-002 through
P1-T20/P2-T03. Its machine contract is `contracts/private-observability.json`;
OpenAPI is `openapi/private-observability.yaml`. Event, rollup and failure v1
objects remain unchanged. This surface is internal, default disabled, and is
not a public profile/export API. A DTO's `visibility: internal` is a required
label, never authentication or authorization.

## Routes and authority

| Route | Method | Required server-verified authority |
|---|---|---|
| `/iw/v1/observability/events` | POST | Current registered gateway-role producer |
| `/iw/v1/observability/rollups` | GET | Existing operator admin |
| `/iw/v1/observability/diagnostics` | GET | Existing operator admin |

Use the existing encrypted/authenticated deployment transport; this contract
creates no new plaintext production listener.

POST requires exactly one `X-InferWeave-Node` and exactly one `Authorization:
Bearer <persistent node credential>`. Use the existing
`NodeControl::authenticate_caller(node, credential)` and require its returned
role to be exactly `gateway`; enrollment alone, stale registration, revoked
credentials, worker/upstream roles, inference API keys and browser sessions
are insufficient. Recheck this binding at acceptance, including concurrent
revocation or registration replacement. The authenticated node initially equals
`source_gateway_id`. A different source name requires an explicit operator-owned
source-to-node binding; display names or event claims cannot create that binding.
`attribution.node_id` names the execution resource and is not the producer identity.

The server independently authorizes the source's producer epoch and trusted
lineage against its trusted producer/lineage registry. Registering a node does
not automatically authorize every epoch, ingress owner, parent hop or logical
request ID it submits. Epoch enrollment is an operator binding or an authenticated
producer registration operation in the existing control plane, not an implicit
POST side effect. Trusted foreign-parent lineage requires verified propagated
lineage evidence; absent evidence must be emitted as `local_unlinked` at the
producer or refused, never silently promoted. Local unlinked data remains useful
but cannot deduplicate a fleet request or establish trusted ingress ownership.

Retain at most 16 authorized epochs per source, including current and draining
outboxes. Reconnection/restart may change the current registration while retained
authorized epochs continue to drain under that source's valid current credential.
Persist these permissions and their closed state; an event cannot reopen a retired
epoch. Do not evict a live epoch or silently rebind its identity on overflow:
refuse new enrollment until safe retirement. Retain accepted-event replay and
sealed-window evidence for the full protected aggregate lifetime. Authorization
retirement must not make a previously acknowledged event executable again.

GET accepts exactly one existing admin credential: `X-InferWeave-Admin` OR an
`Authorization: Bearer` value verified by `control.is_admin`. No inference key,
regular user session, service-actor operator claim or node credential grants read
access. Go may use its existing operator adapter with its own configured Rust
admin credential; never forward browser or service-actor identity headers to
manufacture that authority. An in-process local publisher uses a trusted internal
store interface and does not need external HTTP or a fabricated node credential.
It obeys the same durable identity, validation, coverage and window rules.

## Carrier and refusal order

Recognize these exact paths before the generic HTTP request-body allocation.
Enforce 65,536 bytes for POST by declared Content-Length and actual streamed bytes,
including bytes already read with the head, before using the generic 16 MiB
buffer. Never read/allocate that default body and only then apply the event limit.
Retain existing bounded head, read deadline, connection and total-memory budgets.
Reject ambiguous framing, duplicate Content-Length/Transfer-Encoding, and
Content-Length with Transfer-Encoding. No compression or automatic decompression;
nonidentity Content-Encoding is 415. Content-Type is application/json, optionally
charset=utf-8, and bytes must be strict UTF-8. No batch or JSON array is accepted.

Before a first-value header map is constructed, reject case-insensitive duplicate
Authorization, X-InferWeave-Admin, X-InferWeave-Node, X-InferWeave-Service,
X-InferWeave-Actor, X-InferWeave-Actor-Operator and X-InferWeave-Actor-Groups,
even when values are identical. Reject simultaneous admin and bearer credentials
or admin and node identities. Service/actor headers are unsupported here and
refused. A node identity on GET is also refused. Reject duplicate framing/media
headers and comma-combined credentials; do not let proxy normalization select a
credential. POST forbids query parameters; GET forbids bodies. Disabled routes
return 404 without inspecting producer claims. Transport framing/size checks may
precede authentication; detailed payload/identity conflicts require authentication.
Malformed headers/body/query use 400, unauthenticated/unregistered credentials 401,
and authenticated but unauthorized role/source/epoch/lineage or read scope 403.

Parse JSON with recursive duplicate-key refusal, finite exact safe-integer
semantics, valid Unicode scalars and bounded nesting/work. Preserve the frozen
v1 mathematical-integer spellings (1, 1.0 and 1e0) without binary-float rounding.
Validate the entire closed event schema and semantic rules before persistence.
No server clock, trusted coverage, principal counts, public eligibility or public
publication grants are accepted inputs. `observed_at` is producer evidence; only
the server's own clock controls retention, eligibility and sealing. Frozen event
shape forbids prompt/completion/token content, raw request/response bodies, free
error text, secrets and arbitrary runtime settings. Token counts with provenance
remain permitted. Do not include submitted JSON or credential values in errors.

## Durable ingest and publisher lifecycle

| HTTP | Code or successful status | Meaning |
|---|---|---|
| 201 | accepted | Valid immutable event and dedupe identity durably committed |
| 200 | replay | Same identity and normalized body already durably accepted; no count change |
| 400 | INVALID_REQUEST | Malformed carrier, schema, query or semantic input |
| 401 | UNAUTHENTICATED | Missing/invalid credential or unavailable current registration |
| 403 | FORBIDDEN | Authenticated identity lacks route/source/epoch/lineage authority |
| 404 | FEATURE_DISABLED | Private API disabled |
| 405 | METHOD_NOT_ALLOWED | Unsupported method |
| 409 | REPLAY_CONFLICT | Same event/terminal fact identity with changed facts |
| 409 | WINDOW_SEALED | Event would modify a sealed window |
| 410 | WINDOW_EXPIRED | Event would recreate data outside retained diagnostic/aggregate horizons |
| 410 | CURSOR_EXPIRED | Snapshot expired or was invalidated; restart the query |
| 413 | PAYLOAD_TOO_LARGE | Carrier exceeds route bound |
| 415 | UNSUPPORTED_MEDIA_TYPE | Unsupported media type or content encoding |
| 429 | BUSY | Bounded admission/queue capacity exhausted; nothing accepted |
| 503 | UNAVAILABLE | Required store or service temporarily unavailable; no durable acknowledgement |

The API error codes above are transport codes in a separate envelope, never new
inference outcome reason codes. Events retain the existing frozen reason taxonomy.
Every response has `Cache-Control: private, no-store`; 429/503 additionally carry
`Retry-After` in integer seconds 1..60 matching `retry_after_seconds`. Other error
codes carry null retry_after_seconds. Errors contain no free-form submitted data.

A 201/200 is durable acceptance, never enqueue-only, HTTP success before commit,
or permission to publish. Commit-before-response failure is retried with exactly
the same identity/body. The producer durably records its immutable event_id,
producer_epoch, sequence and normalized body before attempting transmission, and
retains them until a matching 201/200 acknowledgement identifies the same
source/epoch/event. Restart/reconnect cannot regenerate the ID or rewrite the
persisted body. Within an authorized, unsealed and unexpired window, retained
identical replay is a no-op. Existing spec23 late-ingest policy still applies:
beyond a seal or retained horizon, reject with WINDOW_SEALED/WINDOW_EXPIRED,
even if identity evidence remains; never recreate a protected window.
Dedupe/revision/watermark
checks and write must share a transaction or equivalent serializable fence.
Normal epoch closure/sealing follows a drained publisher outbox and independently
verified capture checkpoint, so lost-ACK retries can resolve before close; this
does not invent a fixed lateness allowance or permit reopening a sealed window.

The initial publisher outbox is bounded by both 1,024 events and 64 MiB of event
payload, with bounded metadata and one worker per configured producer. Its
persistent filesystem/store has its own configured total allocation cap. It must
not block inference admission or token delivery on disk, HTTP or queue pressure.
Capture overflow/write failure therefore loses telemetry explicitly: increment
independently maintained loss counters with source, counter epoch and window;
if counters cannot be persisted, coverage becomes unknown. There is no silent
oldest-event eviction, identity rewrite or unbounded retry goroutine/task. Retry
429/503 and ambiguous transport failure with paced bounded backoff, respecting
Retry-After; keep the item in the bounded outbox. Terminal schema/auth/conflict/
sealed/expired refusal is counted and quarantined or retired under bounded policy,
not retried tightly. Outbox retirement after terminal refusal is explicit loss,
not successful delivery. Operator intervention for bad credentials is required.
These numerical bounds are initial policy choices, not measured throughput claims.

`sampling: all_terminal` declares capture intent. Accepted rows do not prove the
eligible population, and accepted_events cannot be copied into expected_events.
Trusted independent source capture checkpoints must establish expected terminal
count, counter epoch, source/window coverage and recording loss. This initial
HTTP version accepts no caller-supplied coverage checkpoint; absent a separately
verified internal/control-plane path, coverage remains unknown/partial. Trace
sampling/drop counters stay separate from all-terminal population counters.

## Operator reads and consistency

Both GET routes require canonical whole-second UTC `start` and `end`, a positive
half-open interval. Diagnostics span at most 7 days; rollups at most 90 days and
require resolution_seconds=300/3600/86400. Reject unknown/duplicate scalar query
parameters, malformed percent encoding, and query strings over 8 KiB before
normalization. Optional exact filters are source_gateway_id, model_id, cluster_id,
runtime_instance_id, gpu_resource_id (one value per filter, ASCII 1..128 bytes).
Additional exact enum filters are dataset (production/controlled/unknown),
observation_kind (ingress_terminal/attempt_terminal/hop_terminal), and
lineage_scope (trusted/local_unlinked), using the frozen event vocabularies.
Each is explicitly nullable in normalized query state and bound into the cursor.
Reliability consumers select production + trusted + ingress_terminal to avoid
mixing controlled traffic, attempts or hops into request outcomes. Diagnostics
match lineage_scope against event.lineage.scope. No selector grants authority.
Unknown attribution does not match a supplied filter. Return only rows wholly
inside the selected window; diagnostics use observed_at in [start,end). Never
split a rollup or prorate counts. Keep internal source/configuration/runtime/GPU
and dataset/kind/lineage dimensions intact; this is not a public serializer.

limit defaults to 25, range 1..100. Each nested frozen object retains its 64 KiB
bound; total response bytes are at most 16 MiB, including envelopes. Stop before
the byte or item bound and emit a continuation; never cut a row/pair. Query work,
scan budgets, connections and snapshot storage are bounded independently of the
page limit; overflow is BUSY/UNAVAILABLE, never an unbounded full-history scan.

A first page establishes snapshot_id, server as_of and expires_at (at most 300
seconds later), normalized query including filters and limit, query_health,
items and nullable next_cursor. The server captures stable read state for all
pages: accepted events/replacements/seals arriving later cannot appear mid-query.
Order diagnostics by (observed_at, source_gateway_id, producer_epoch, event_id)
and rollups by (window_start, source_gateway_id, producer_epoch, rollup_id).
An authenticated opaque cursor at most 1,024 bytes binds the operator authority,
endpoint, complete normalized query/limit, snapshot identity/version, last sort
key and expiry. Send all original query parameters alongside a cursor. Reject
tampering or changed filters/limit/endpoint with 400; reauthenticate every page.
Expired or invalidated snapshots return 410 without silently restarting. Diagnostic items must satisfy as_of minus 7 days < observed_at <= as_of;
aggregate items must satisfy as_of minus 90 days < window_end <= as_of,
retaining the exact parent/companion together. The cutoff is exclusive and
the server snapshot clock is authoritative. A bounded historical query may
return no retained rows with explicit retention health; its small width does
not authorize expired or future items. Do not
keep rows beyond retention to serve a cursor: invalidate that snapshot. Offset
pagination or a high-water timestamp alone cannot pin mutable rollup revisions.

Each rollup item is {parent, failure, failure_availability}; the companion is
validated against that exact parent fingerprint and read from the same committed
snapshot. Missing/unsupported/mismatched/corrupt companion becomes failure=null
and failure_availability=unavailable with query health reason
`failure_companion_unavailable`, never zero counts or
a mismatched pair. Invalid parent/event DTOs are withheld with `invalid_record`; expose partial or
unavailable query health rather than serializing corrupt warehouse JSON. A page
validator checks nested event semantics, full parent/companion conservation,
bounds, exact filters and window membership before emitting it. Empty items do
not prove zero traffic. Query health describes read availability; parent coverage
separately describes capture completeness. Unavailable reads carry no items or
cursor; storage failure may instead return 503. No read creates principal counts,
public eligibility, or per-published-cell privacy evidence.

## Enablement and retention

Production collection stays disabled until the durable publisher/store plus the
parent/failure generator, atomic 5m/1h/1d replacement/sealing/pruning and persisted
late-ingest watermark fence are implemented and tested together. Starting a
private API, passing fixtures or accepting diagnostics alone cannot satisfy this
gate. Only new-family diagnostics/aggregates use 7/90 days; legacy 730/365-day
records and shared backups are unchanged. No retroactive purge is authorized.
All runtime AC-PRIVATEOBS-01..06 proofs remain owed until separately recorded.
