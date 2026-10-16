# 59 — Exact-model HTTP JSON over Held Link

## Scope and defect

Feature IDs: `IW-CORE-001`, `IW-DP-001`, `IW-DP-002`; task `P1-T18`.

The source audit at engine commit `8e5bad6c82ab781451b0b8a8d7a5655dc67a4136` of `inferweave`'s `iw-core/src/control_connection.rs` and
`iw-gateway/src/{server,node_link}.rs` (Held Link response in `server.rs:1815`,
request/Token/End in `control_connection.rs:953`, and request caps in
`link_chunking.rs:43`) found that the legacy Request carried a
payload without its original HTTP target, Token carried strings without an HTTP
head, and End could not distinguish success from a failed backend stream. Routing
`POST /v1/completions` through that chat-oriented path could rewrite the endpoint
and lose backend status/content type. Prior specifications did not define this
OpenAI HTTP transport boundary. An implementer following the old text could
repeat that loss. This contract repairs the omission; it does not assert live
production conformance.

`link_http_json: "1"` names `iw.link-http-json/1`. This is a bounded transport for
existing exact-model JSON chat and completions requests. It creates no alias
resolver, admission authority, backend endpoint, or arbitrary HTTP proxy. Existing
Rust admission and exact model identity checks still apply. It cannot authorize
level-2 alias execution: `meta.http` together with `meta.native`,
`ownerExecutionPermit`, or `executable` is invalid. Spec57 protected execution
requires its own permit and fenced path; composition is unsupported in version 1.

## Negotiation and revocation

Use the existing spec45 native Link v1 Hello/ack envelope and authentication.
The historical `native_link_*` names remain unchanged on the wire. Registration
must offer and return `iw.link-http-json/1`, and the actual authenticated socket's
Hello and its matching bound ack must include it. An HTTP-only peer may offer
this capability without `iw.link-native-request/1`; either request capability is
sufficient for the common handshake. Native response proof still requires native
request support. Owner permits retain spec57's independent requirements.

The gateway intersects current authenticated registration capabilities, Hello
offers, and local support. It checks credential validity, registration freshness,
registration `connectionId`, unpredictable per-dial `link_incarnation_id`, and
same-socket ack. A node ID, process session, old ack, protocol version, or HTTP
capability in an unrelated registration cannot enable this mode. Selection,
validation of that held Link binding, and enqueue are one atomic transition.
Replacement, re-registration, credential expiry, withdrawal, staleness and socket
close revoke new dispatch. No metadata is sent until the binding succeeds.

Old peers receive unchanged metadata-free legacy chat requests. New peers talking
to old peers omit this extension for legacy chat. `/v1/completions` requiring exact
HTTP transport must use an eligible existing HTTP route or another eligible exact
placement, or return HTTP 503 `FEATURE_UNSUPPORTED` with `retryable:false` before
dispatch. Never strip the HTTP target and silently send it as chat. Receiving an
unnegotiated `meta.http` request fails before backend execution.

### System One targets

`/v1/systemone` and `/v1/systemone/batch` carry a System One (Laya) decision request and a batch of
them. They are `POST` with a strict JSON object body (the rules below apply unchanged, including a
non-empty `model` string that must equal the selected deployment when one is selected). `stream`
exists only on the chat target: `stream:true` on any other target, these two included, returns HTTP
400 `stream_unsupported` before dispatch, and a non-boolean `stream` is invalid. A node that has not
negotiated `iw.link-http-json/1` for the bound link gets no System One HTTP-mode request: the
gateway returns HTTP 503 `FEATURE_UNSUPPORTED`, `retryable:false`, before dispatch (never rewriting the
target). `/v1/systemone?x`, `/v1/systemone/other` and `/v1/systemone/batch/` are refused like every
other inexpressible target.

Separately, the legacy (metadata-free) frame path has no `meta.http`. A sender on that path marks a
System One batch with the optional boolean `meta.systemone_batch: true` (schema
`link-request-meta.json`); the key is omitted when not set, an old receiver ignores it, and it is
mutually independent of `meta.http` (the HTTP target already says batch or not). The reference
receiver additionally classifies an unmarked legacy System One frame from the body's `model`. That
body-based fallback is implementation behaviour, not specified here: whether a gateway may use the
legacy path for System One when HTTP mode is not negotiated, rather than answering 503, is left open
(`OPEN_GATES.md`).

## Request bytes and limits

The closed `schemas/v1/requests/link-http-request.json` describes the logical
Request after existing negotiated chunk reassembly. Its `meta.http` contains:

```json
{"version":1,"method":"POST","target":"/v1/completions","content_type":"application/json","payload_bytes":41}
```

`payload_bytes` is the actual UTF-8 byte length of the unchanged Request.payload;
the number above is illustrative. Only exact `/v1/chat/completions`, `/v1/completions`,
`/v1/systemone` and `/v1/systemone/batch` targets are legal. No query, fragment, percent-encoded alternative,
absolute URL, alternate method, arbitrary headers or destination is expressible.
The backend origin comes only from authenticated deployment configuration.
The existing `/v1/completions` API remains non-streaming: `stream:true` MUST return
HTTP400 with JSON error code `stream_unsupported` before backend dispatch, even
when `iw.link-http-json/1` is negotiated. `stream:false` or an omitted stream flag
retains non-streaming JSON completion behavior. This transport adds no new legacy
completions streaming support; SSE preservation applies to supported chat streams.
Request content type is `application/json`, optionally a single `charset=utf-8`
parameter (ASCII case-insensitive, SP/HTAB around separators and optional quoted
`utf-8`). Preserve the original valid MIME string, including casing and spacing.
Control bytes except MIME separator HTAB are forbidden. The body must be a JSON
object; reject duplicate object keys at any depth, invalid UTF-8/unpaired surrogate,
non-finite numbers and trailing data. Validation never reparses/reserializes the
forwarded bytes. Exact `model` and deployment selection are not substituted.

Reuse existing frame/chunk bounds: at most 1,048,576 encoded JSON bytes per frame
(excludes four-byte frame prefix), and the configured `IW_LINK_MAX_REQUEST_BYTES`
reassembly ceiling (default 33,554,432 payload bytes). A peer without separately
negotiated chunking can accept only a single fitting frame. Enforce the recipient's
actual configured limit before backend start, and reject oversize explicitly;
this feature does not raise or silently lower existing limits. Schema integer
limits use the interoperable safe integer range; byte/frame caps require semantic
checks. JSON escaping counts toward encoded frame length. Chunk reconstruction
must preserve bytes and identical metadata using the existing chunk contract.

## Authoritative response head and body

Only requests sent in negotiated HTTP mode use these response fields. The first
Token has `seq:0`, `payload:""`, and the required closed `response_head`:

```json
{"kind":"token","request_id":"r1","seq":0,"payload":"","response_head":{"status":429,"content_type":"application/json","headers":{"retry-after":"2","x-inferweave-request-id":"r1"}}}
```

The head comes from the backend HTTP response. Accept final statuses 200–299 and
400–599; reject redirects and informational responses. Content type is either
`application/json` or `text/event-stream` with the same optional UTF-8 parameter
grammar as above. Preserve its original valid value. `headers` is optional and
closed: `x-inferweave-request-id` is a bounded visible ASCII opaque correlation
value; `retry-after` is decimal seconds on 429/503 only. Validate the entire
header value, including its last byte; no CR, LF, HTAB, NUL, DEL or other control
byte is allowed. JSON Schema patterns use a strict end assertion because `$`
can match before a final LF. The semantic verifier independently uses full-string
matching before committing the head. No cookies, credentials,
internal addresses, candidate identities or arbitrary header forwarding. Correlation
headers confer no caller authority. Existing independently negotiated queue_ms and
queue_hops may occur on this first token under their prior semantics.

Every following Token has the next sequential `seq`, contains only the unchanged
body fragment in `payload`, and omits `response_head` and first-token queue fields.
Split at UTF-8 scalar boundaries; incremental decoding must buffer an incomplete
scalar across network reads and reject invalid bytes, never substitute U+FFFD.
No newline insertion, JSON rewriting, synthesized SSE envelope or `[DONE]` marker.
Do not infer HTTP status from JSON `code`, `error`, or other body content. Status204
must have zero body bytes. Nonempty bodies and streams otherwise remain opaque.
Each encoded frame obeys the existing frame limit; no new aggregate response cap
or unbounded buffering is introduced. Head Token consumes existing stream credit;
receiver replenishment must permit body progress even though head payload is empty.

A second head, body before head, repeated/out-of-order sequence, wrong request ID,
invalid MIME/status/header, oversized frame, duplicate keys in the control frame,
normal End before head, or response proof from another mode is a protocol failure.
Before any HTTP head is committed, return 502 `invalid_upstream_response`. After
commit, terminate as an explicit failed stream. HTTP status cannot be changed after
commit, even before the first body byte. Do not inject an error into backend body.

## Terminal failure, cancellation and backpressure

Normal End (without `failure`) succeeds only after a valid head and complete body.
A backend transport failure sends End.failure with a frozen code in
`contracts/protocol-v1/link-http-json.json` and `retryable:false`. Before the head,
`BACKEND_TIMEOUT` maps to504, other non-cancellation failures to502. After the head,
all failures terminate the response incompletely and record the machine-readable
failure in request telemetry. Never send normal End after an I/O/decode failure.
Socket loss without End is failure; a terminal request rejects further frames.
Backend HTTP4xx/5xx is an ordinary authoritative head/body/End, not End.failure.

Cancellation uses the existing Cancel frame and cancels backend I/O; deadline,
client disconnect and terminal cleanup release existing resources exactly once.
Cancel/heartbeat control must keep progressing when body credits are exhausted.
The transport must not retry/replay any accepted request, including a lost response
head: absence of output is not proof the backend did not execute. Only existing
pre-dispatch admission refusal may select another eligible exact placement under
its current bounded rules. There is no resume semantics in this version.

## Evidence and activation

Closed schemas, golden/hostile vectors and the offline state-machine oracle in
`conformance/link_http_json.py` are specification evidence. Run
`python3 -m unittest discover -s tests/smoke -p 'test_link_http_json.py'` and
`python3 scripts/validate_specs.py --self-test`. The System One targets' vectors (accepted, not-negotiated 503, stream refusal, refused targets) are in
the same file. Production Rust/Go mixed-version,
real backend exact path/status/MIME/bytes, cancellation, credit exhaustion, socket
loss and no-replay tests remain **owed**. Spec57 and alias rollout gates remain
blocked. Independent review is required before implementation activation.
