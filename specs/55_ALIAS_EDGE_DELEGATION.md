# 55 — Request-bound edge identity for alias operations

Status: contract proposal for independent security review. Feature IW-ALIAS-001, tasks A-T02/A-T06.
No running component is qualified by this document. Spec 54 and OPEN_GATES keep alias activation
disabled until Rust verifier, Go signer, PostgreSQL replay enforcement and cross-language hostile
vectors pass. This separate purpose grants no node registration, lease or arbitrary proxy authority.

## Trust and authorization

Rust configuration maps `(edge_id, key_id)` to a 32-byte Ed25519 public key, enabled/revoked state,
purpose exactly `inferweave.edge-alias-delegation/v1`, accepted audience and accepted IdP issuer(s).
Keys have a validity interval, are independently provisioned and may be revoked immediately. The
same raw key under another protocol purpose is not acceptable. Edge key identity does not grant
administrator authority. Audience is the configured Rust gateway/control authority ID, not a
user-selected URL. Replay state is shared by every replica accepting that audience.

The Go edge first validates its existing authenticated session and IdP issuer/subject. It signs
only those validated identifiers, never caller-supplied identity headers. It strips any inbound
edge assertion and creates a fresh one for each outbound attempt. Rust independently maps exact
`(idp_issuer, subject)` to current owner_scope/role grants in its authoritative grant configuration.
No group snapshot, role, tenant, owner_scope, email or raw OIDC token is carried as delegated
privilege. Missing/revoked grants fail closed. A path/method maps to a Rust capability (read,
preview, draft, publish, rollback or sharing) and body owner_scope must match an applicable grant.
The signed identity is an attribution input; it does not override Rust object authorization.

## HTTP transport

Exactly one `InferWeave-Edge-Assertion` header contains unpadded base64url of a UTF-8 JSON envelope
matching `schemas/v1/aliases/edge-assertion.json`. The entire header is limited to 8192 ASCII bytes.
Reject duplicate JSON keys, unknown fields, duplicate assertion/security/precondition headers,
invalid UTF-8, invalid/padded/noncanonical base64url and control characters. Do not combine duplicate
headers with commas. The edge does not forward its user bearer or registration credential in lieu
of this assertion. Any separate hop credential authenticates the transport only.

The envelope's `version` is integer 1. The `signature` is unpadded base64url of exactly 64 Ed25519
signature bytes. `nonce` is unpadded base64url of exactly 16 cryptographically random bytes, fresh
for every attempt. `body_sha256` is 64 lowercase hexadecimal digits of the exact request entity
bytes before JSON decoding, after HTTP transfer framing; content encoding is identity (reject
Content-Encoding). Native alias management/preview requests are bounded to 1 MiB before parsing.
Empty bodies hash the empty byte string. Signature verification uses strict Ed25519 verification
that rejects noncanonical signatures/points and small-order public keys per the existing trusted
cryptographic implementation; the offline Python reference is for fixtures only.

`method` is the actual uppercase HTTP method. `request_target` is the exact ASCII origin-form
raw path plus optional `?query` sent on the wire, captured before route normalization. It begins
`/inferweave/v1/`; no authority/scheme/fragment, backslash, control characters, repeated slash,
dot path segment, percent-encoded dot/slash/backslash or malformed percent escapes are permitted.
Query parameter order is preserved and signed. Duplicate decoded query keys are rejected.
Canonicalization means rejecting ambiguous forms, not silently rewriting the signed target.

The actual signed header inputs are `If-Match`, `If-None-Match`, `Idempotency-Key`,
`InferWeave-Alias-Level` and `InferWeave-Request-Deadline-Unix-Ms`. Absent optional precondition or
idempotency headers bind the empty string. Present values must already have no leading/trailing
whitespace, no controls, and satisfy spec 54. Alias level is exactly `2`. A strong If-Match retains
its literal double quotes; If-None-Match is `*`. Idempotency key is the exact bounded string.
Deadline header is required canonical positive decimal Unix milliseconds and equals the signed
`deadline_unix_ms` integer. Noncanonical decimal forms (leading zero, plus, exponent) are rejected.
All signed fields must equal the actual request; never verify a detached claimed request instead.

## Exact transcript

Start with these literal 36 ASCII bytes including the final zero byte:

`inferweave.edge-alias-delegation/v1\0`

Then append the following fields in exactly this order. For each field append its UTF-8 byte length
as an unsigned 32-bit big-endian integer, followed by its bytes. Length counts bytes, not Unicode
characters. All integer fields are canonical unsigned decimal ASCII without leading zeroes.
There are no separators, JSON encodings, terminators, optional-field presence bytes or final newline.
The fixed domain selects version 1; the envelope version must equal 1 before verification. JSON
field order/whitespace do not affect the signature. Signature itself is excluded.

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
12. `if_match`
13. `if_none_match`
14. `idempotency_key`
15. `alias_level`
16. `deadline_unix_ms`

Sign these bytes directly with Ed25519 (not Ed25519ph; no additional digest/signature wrapper).
Golden vectors publish the exact transcript hexadecimal bytes, public key, detached signature and
transport envelope. The fixture private seed is public test data and never a deployment credential.

## Time and durable replay protection

Use Rust's trusted current time (prefer database time for shared admission). Integers are bounded
to the JSON interoperable range <= 9007199254740991. Require all of:

- `issued_at_unix_ms <= now + 5000` (bounded future clock skew).
- `issued_at_unix_ms < expires_at_unix_ms <= issued_at_unix_ms + 30000`.
- `now < expires_at_unix_ms`; expiration has no extra grace period.
- `now < deadline_unix_ms <= issued_at_unix_ms + 300000`.
- The configured signing key is currently enabled, purpose/audience/issuer-matched and within its
  validity interval; revoked key or revoked principal grants fail immediately.

Rust PostgreSQL owns a replay ledger with a uniqueness constraint on `(edge_id, nonce)` across
all keys/replicas accepting that edge. After signature, request binding, time and principal/capability
validation, atomically INSERT the nonce and expiry before invoking any protected operation. A
conflict rejects the replay. Commit this consumption in its own transaction; an operation failure
must not roll it back. A dropped response or retry uses a fresh nonce plus the same operation
Idempotency-Key, whose separate canonical store prevents duplicate mutations. All replicas share
this ledger; process-local replay caches cannot authorize a request.

If PostgreSQL is unavailable, do not execute the operation; return 503 and `BACKEND_UNHEALTHY` in
a redacted alias error. Delete replay rows only after their stored expiry plus 5000 ms according to
trusted database time. Size/retention bounds and per-edge admission limits must prevent storage
abuse. A clock rollback must not allow deleted nonce reacceptance; the trusted verifier rejects an
assertion issued more than 35000 ms before its monotonic trusted-time high-water mark. Time-source
regression that cannot be bounded fails closed until repaired.

Replay/security audit/rate-limit writes are permitted for read-only preview authentication. The
preview purity guarantee forbids mutations of alias desired state, routing demand, queues, model
lifecycle, capacity or leases; it does not disable replay protection or audit.

Signature/key/audience/request-binding/replay failures return redacted 403 `POLICY_DENIED` without
revealing key/grant existence. A valid principal denied tenant ownership returns redacted
`TENANT_DENIED` only if disclosure policy allows it. No failed assertion can fall back to an
anonymous or shared-token alias principal. Do not log the assertion, session token or raw subject
in public telemetry. Audit stores protected principal attribution and correlation metadata only.

## Required proof

A-T02/A-T06 must replay `conformance/alias-edge-delegation-vectors.json` byte-for-byte in Rust and
Go. Include Unicode subject byte-length coverage, changed body/method/target/preconditions/deadline,
wrong audience/purpose, revoked key/grant, expired assertion, future timestamp, duplicate
headers/JSON/query keys, malformed base64 and Ed25519, nonce replay/concurrent replicas, failed
operation consumption, fresh-nonce idempotent retry and unavailable replay database. Offline
transcript/signature fixtures are contract proof only; authentication, grants and durable replay
remain owed until exercised against the actual HTTP and PostgreSQL boundary.
