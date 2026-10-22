# Proposed: the spec 56 qualification verifier and a resolvable `qualification_id` — 2026-10-16

**Status:** Proposed — needs owner acceptance. This record decides and authorizes nothing.  
**Decision owner:** InferWeave operator  
**Date:** 2026-10-16  
**Authorizes:** nothing (design proposal only; not implementation, deployment, key issuance, a
verifier run, a schema migration or any change to what a catalog row is called).  
**Relationship:** `discloses` that the evidence boundary of `specs/56_RUNTIME_INSTANCE_OBSERVATIONS.md`
section 4 is undefined; proposes how to define it without amending spec 56, spec 54 or spec 23.
Re-decides nothing. It is not normative specification text: if accepted, the contract below would be
written as a new spec section by a separate change.

Code citations are to `InferWeave/inferweave` at `a54e0398b7faf0842145aab410d358021c618b5f`
(`origin/main` when this record was written), read, not run.

## Context

Spec 56 section 4 (lines 179-196) says an optional `qualification_id` "resolves in the owner's
trusted verifier/evidence store to a bounded spec54 `capability_profile` and its underlying
qualification record", that the owner checks the record binds the same exact model, immutable
deployment, instance generation, producer source epoch, required GPU set, runtime/protocol/build
identities, allowed verifier purpose and freshness, and that "a verification ID or a node-supplied
claim is insufficient". It ends: "This protocol specifies the evidence boundary, not a new verifier
implementation" (lines 188-196). Nothing defines the store, the record, who writes it, how it
expires or is revoked. `OPEN_GATES.md` (the "Spec 56" bullet of the 2026-10-15 latest update) records
the consequence: `qualification_id` stays opaque and nothing becomes `verified`.

What exists today, read at the pinned commit:

* **The reference is carried and never resolved.** `qualification_id: Option<String>` is bounded to
  256 characters by `text(id, 256)` (`crates/iw-core/src/runtime_observation.rs:154`, check at
  `:305-312`), documented "A reference, never a verification. No verifier store resolves it here"
  (`:152`). The producer always sends `None`
  (`crates/iw-cli/src/runtime_observation_report.rs:696`).
* **The consumer never promotes.** A node-attested row keeps confidence `Advertised` and a
  `verification_id` of `unverified-advertisement:<generation>`
  (`crates/iw-gateway/src/adaptive/alias_inventory.rs:719`); a test pins that a request for `verified`
  (the default) selects nothing even with a valid observation (`:1784-1790`). The row still lists
  `owner_canonical_resource_group_identity` among its missing evidence (`:328`, `:1402`).
* **`deployment_qualification` exists and nothing uses it.** Migration
  `crates/iw-storage/migrations/0002_telemetry_warehouse.up.sql` lines 97-109 create it with primary
  key `(fingerprint, gpu_id, suite_version)`, foreign keys to `deployment_fingerprint(fingerprint)`
  (grammar `dep_[a-z0-9-]{1,64}`) and `gpu_inventory(gpu_id)`, a free-text `result` ("the
  qualification result vocabulary is not frozen yet (invariant 41), so the column is plain text"),
  `evidence_ref` and `measured_at`. A search of `crates/**/*.rs` for `INSERT INTO` or `FROM` against
  `deployment_qualification`, `deployment_fingerprint` and `gpu_inventory` finds no statement; the only
  hits are the migration, its down file and a table-name list in
  `crates/iw-storage/tests/migrations.rs:30`. (`QualificationEvidence` in
  `crates/iw-storage/src/model_intelligence.rs:73` belongs to spec 58 recommendations and is **not**
  this store.)
* **The identity namespaces do not line up.** The producer's `observation.deployment_fingerprint` is
  "the deployment id this node registered with" (`runtime_observation_report.rs:491-500`, `:672`; the
  test fixture is `dep_x`, `:768`): the `dep_` grammar of the table. Spec 50's single-flight
  `deployment_key` is a different object, `sha256:<hex>` over an RFC 8785 canonical manifest
  (`specs/50_TRANSACTIONAL_RUNTIME_LIFECYCLE.md:78-99`). So there are two identity forms, not one: the
  `dep_` id and the spec 50 key. On a dynamic node the `dep_` id is the one spec 64 derives from
  length-prefixed fields (`specs/64_DYNAMIC_NODES_AND_GATEWAY_PROVISIONING.md` section 1 table, section 5
  rule 6); how the `dep_` id of an executor node is formed was not verified for this record. For GPUs, `required_gpu_ids` are node-claimed (`iw-gpu-0` in the producer's tests,
  `runtime_observation_report.rs:769`), cross-checked against the registration's `node.gpu_ids`
  (`alias_inventory.rs:675-679`), while `gpu_inventory.gpu_id` is a free text key and the
  owner-canonical resource-group identity (spec 56 section 4, lines 198-215) is still owed.
* **A database is optional for a gateway.** `inferweave-gateway` takes `--database <url>` or
  `--outbox <dir>` (`crates/iw-gateway/src/cli.rs:60-75`), but the alias engine refuses to start
  without the alias and replay tables (`cli.rs:1837`). Anything that gates `verified` aliases may
  therefore assume Postgres only where the alias engine is on.
* **Two different things are both called qualification.** Spec 23 qualification is a benchmark-suite
  result for a fingerprint on a GPU, "production-qualified only from measured evidence" with raw
  samples stored (`specs/23_GLOBAL_TELEMETRY_BENCHMARKS.md:157-158`); a material fingerprint change triggers requalification
  (`:65`). Spec 56 qualification is a capability attestation for one live incarnation. The table
  models the first.

Constraints that any answer must keep: observed is not verified and cannot be mechanically promoted
(spec 56 lines 181-186); a verification ID alone never upgrades confidence (spec 54 line 131); federation
cannot promote confidence or trust (spec 54 line 140-141); a record for another generation cannot be
copied after reload and may only be requalified "by the approved verifier against the new
incarnation" (spec 56 lines 193-194); invalid or stale references do not fall back to verified
defaults (line 194); an owner rechecks qualifications atomically at admission (spec 57 line 236);
capability claims expire (invariant 16, `specs/00_INVARIANTS.md:23`); no Go inventory or qualification
logic (spec 56 line 226).

## Options

### Option 1 — extend `deployment_qualification`

Add columns for generation, source epoch, verifier, expiry and revocation to the existing table.

* For: no new table; Postgres is already the telemetry store; spec 23's `evidence_ref` already points
  at raw samples.
* Against: the key `(fingerprint, gpu_id, suite_version)` has one GPU per row and no generation, so a
  reload (a new generation of the same fingerprint) collides or must overwrite, which destroys the
  history revocation needs; the foreign keys require rows in `deployment_fingerprint` and
  `gpu_inventory` that nothing writes from registration, and whose id namespaces differ from the
  node-claimed ones; the result column is unfrozen free text; it needs a database on every gateway that
  wants a `verified` alias; a mutable row is not tamper-evident, and records could not be exchanged or
  audited offline. A migration to a table with a different key is a breaking change to an unused table
  and would still leave the signature question open.

### Option 2 — a dedicated, content-addressed, signed record, with the table kept for spec 23

Define a **qualification record**: a closed JSON document, canonicalized (RFC 8785, as spec 50 and
spec 55 already do), whose `qualification_id` is `q1-` plus the lowercase SHA-256 of the canonical
body, signed by a **verifier key** with the same trust shape as spec 55's edge keys (a configured
public key per `(verifier_id, key_id)`, an exact purpose string, a validity interval, an
enabled/revoked state; spec 55 lines 10-12). The owner holds the public keys, never the private
ones. Resolution is a lookup by digest, so a record cannot be altered or substituted without the id
changing. Revocation is a separate signed, append-only list. `deployment_qualification` stays the
spec 23 benchmark-evidence table and a record names its rows through `evidence_ref`; the two are
linked, not merged.

* For: immutable and tamper-evident by construction; verifier identity, purpose and revocation reuse
  a reviewed pattern; the store backing can start as a file directory and move to an append-only table
  without changing the id or the record; no new authority is given to the gateway or the node;
  generation and epoch are first-class.
* Against: new schema, new key management, a verifier tool to write; a file-backed store must be
  shared by replicas (spec 54's cursor keyring, `IW_ALIAS_CURSOR_KEYS`, is the precedent); content
  addressing means any edit is a new id (intended).

### Option 3 — an online verifier service the gateway calls

The gateway asks a verifier endpoint "is this incarnation qualified?" at admission.

* For: freshest answer, no store to replicate.
* Against: puts a network call and a new availability dependency on the admission path (spec 57 line
  236 requires an atomic recheck there), needs its own authentication, cannot be audited after the
  fact, and a compromised endpoint can promote anything. Rejected for the first version; it remains a
  legitimate later transport for Option 2 records.

### Option 4 — leave `qualification_id` opaque

Safe, and the status quo; nothing can ever be `verified`, so every alias that requires the default
`verified` confidence stays unselectable for registered instances. This is the cost the operator is
already paying.

## Recommended option

**Option 2**, with the store starting as a read-only, operator-managed directory and moving to an
append-only table only when a gateway has one.

The sketch below is a proposal for later spec text, not a contract. Every number is deliberately left
to the owner's policy because none has been measured (`ADR_TEMPLATE.md`, "Measured basis").

**Record body (closed, versioned).** `record_version`; `owner_gateway_id`; `verifier_id`, `key_id`,
`purpose` (`inferweave.runtime-qualification/v1`); `issued_at`, `not_before`, `expires_at`;
**binding:** `node_id`, `instance_id`, `model_id`, `deployment_fingerprint` (the `dep_` id the
observation carries), `deployment_key` (spec 50, when the manifest is known; the owner recomputes it
from the manifest and never trusts the stated value, spec 50 line 92), `generation`, `source_epoch`,
`required_gpu_ids` (node-claimed, as observed), `resource_group_id` (owner-canonical, once it exists),
`runtime_family`, `runtime_build` and `protocol_version`; **claims:** a list of
`{feature, fidelity, confidence, sample_size, suite_version, evidence_ref}` where `confidence` is
`probed` or `verified` and `evidence_ref` names a spec 23 sample set or a digest of raw samples;
`limits` actually measured. No prompt, no completion, no tenant, policy or allowlist content, and no
credential appears in a record (spec 23 privacy; spec 54 lines 135-137).

**Who may write evidence.** Only a verifier holding a private key whose public half the owner's
operator configured, for the purpose above and inside its validity interval. The gateway holds public
keys and reads records; it never writes or signs one. A node writes nothing and a node-supplied claim
carries no weight (spec 56 line 192). The operator, not the verifier, adds and revokes keys. The
reference verifier is an out-of-band tool run by the operator against one live incarnation: it reads
the owner's accepted observation for that instance (an operator route the owner would add), drives
the probes whose results it signs, and emits a record. It must run on a host that is not the node
under test and must not receive the node's credentials. Key material is read from a `0600` file, never
from argv.

**Expiry.** `expires_at` is required, the owner's policy sets a maximum lifetime, and the effective
validity is the minimum of the record, the observation item (spec 56 line 136: item and envelope
expiries combine by minimum) and the owner policy. A record is void when the generation is
tombstoned, the epoch is retired, the instance reloads, the model, deployment or runtime build
changes, or the policy revision changes (spec 56 section 3, lines 132-175, and the policy-change rule at line 202). **Epoch tension for the owner:** spec
56 binds the record to the source epoch, and spec 56 section 2.1 (lines 106-120) has a producer rotate
its epoch at a registration before 256 distinct generations and on a resync, while generations stay
live. Read literally, each rotation voids every record of that node. This record recommends keeping
the literal rule (conservative, no spec change) and making requalification cheap by automation; the
alternative, binding to the generation and node and treating the epoch as informational, needs an
amendment of spec 56 and trusts the node's claim that an unchanged generation is the same
incarnation. See the open questions.

**Revocation.** A signed, append-only revocation entry names a `qualification_id`, or a verifier key
with an effective time. Revoking a key voids every record it signed unless the operator re-attests it.
The owner consults the revocation list on every resolution. A revocation takes effect at the next
resolution and at the next admission recheck.

**How the gateway verifies (every observation item that carries an id, and again at admission per
spec 57 line 236).**

1. Look the id up in the store (bounded size and count; unknown or oversized is a miss).
2. Recompute the SHA-256 of the canonical body; reject on mismatch with the id.
3. Verify the signature with a key valid at `issued_at`, with the exact purpose, not revoked.
4. Match every binding field against the held item and registration, and the owner-computed
   `deployment_key` and owner-canonical resource group; any difference is a mismatch, never a partial
   match.
5. Check freshness against the owner's trusted time; a record dated in the future, or a disagreeing
   clock, fails closed (spec 56 lines 72-74).
6. Take the claim set, cap each claim's confidence at the owner's hard policy, and build the
   capability profile. Cache the result under `(qualification_id, item sequence)` for no longer than
   the minimum validity.
7. On any failure the row keeps its unqualified state with a frozen reason code; it never falls back
   to verified defaults (spec 56 line 194).

**Failure modes and what they do.** Store unreadable or absent: every row stays unqualified, nothing
already serving is withdrawn by this check alone, but a request that requires `verified` stops
matching (the spec 54 rule for stale evidence). Replicas with different stores: a row verifies on one
and not another, so the store must be shared or identical across replicas, as the cursor keyring is.
Verifier key compromised: revoke the key; every record it signed is void at the next resolution, which
is the intended blast radius. Reload races: a record names the old generation and fails the binding
check, correctly. Duplicate or colliding ids: impossible for a content-addressed id unless SHA-256
breaks. Verifier signs a record for a node that is draining or unhealthy: the observation lifecycle
and health still gate eligibility (spec 56 lines 213-217: "necessary but insufficient").

**Privacy.** Records are owner-local evidence. They are not federated: a peer receives only the
redacted projection the owner chooses, and a downstream's `verified` is advertised to the upstream
(spec 54 line 140). Raw node and GPU ids appear in records and are operator-only, never in UI-reader
projections (spec 56 line 174). No tenant allowlist or policy detail is in a record. Sample
sets referenced by `evidence_ref` stay in the owner's warehouse under spec 23's prompt-body rule.

**Incremental rollout (each step gated; none opens a production gate).**

1. Accept this record for design; write the spec section and the schemas, with hostile vectors
   (wrong generation, wrong epoch, wrong GPU set, replayed record on a reload, expired, future-dated,
   revoked key, wrong purpose, digest mismatch, oversized).
2. **Shadow mode** in the Rust gateway behind a flag: resolve and verify every presented id and report
   counters and reasons, changing no row.
3. Reference verifier tool; run it on the lab gateway's nodes (`OPEN_GATES.md`, lab deployment bullet),
   claims limited to what a probe can measure: limits and modalities. Rows may reach `probed` only where
   a hard policy permits it (spec 54 lines 139-140).
4. `verified` for that closed claim set, once the owner-canonical resource-group identity exists.
5. Feature-fidelity claims (tools, JSON constraints, vision), each separately qualified; privacy,
   residency, trust and licence remain owner-policy evidence (spec 56 lines 181-186), never a probe
   result.
6. An append-only table behind the same ids for gateways with Postgres.

## Consequences

* Positive: a catalog row can become `verified` only through evidence that is immutable, signed by a
  key the operator controls, bound to one incarnation and revocable. The existing opaque field gains
  meaning without a wire change: `qualification_id` and its 256-character bound are already in the
  schema and the Rust type.
* Negative: a key-management duty for the operator; requalification after every reload and, under the
  literal epoch rule, after every epoch rotation; one more store to keep identical across replicas.
* The mismatch between the two deployment identity forms (the `dep_` id, spec 64 derived on dynamic
  nodes, and the spec 50 `deployment_key`) becomes visible: a record carries both the observed id and the owner-computed key.
  Whether they should be unified is not decided here.
* `deployment_qualification` is not changed. Its unfrozen `result` column is not resolved by this
  record (invariant 41 remains open for it).

## What implementation would follow

Spec 56 section 4 text and schemas for the record, the revocation entry and the verifier-key
configuration; vectors in `conformance/`; a Rust resolver in `iw-core` (pure verification) with the
gateway adapter behind a flag; the reference verifier; later an append-only migration. Tasks would
fall under `A-T05` and `A-T08`. Nothing here changes the task graph.

## Open questions for the owner

1. **Epoch binding.** Keep the literal rule (a rotation voids records) or amend spec 56 to bind the
   generation and node, with the epoch informational?
2. **Maximum record lifetime** and the freshness the lab can live with. No figure is proposed because
   none is measured.
3. **Who runs the verifier** and where its signing key lives; may the lab use a single operator key?
4. **Which identity is canonical for a record**: the observed `dep_` id, the spec 50 `deployment_key`,
   or both as proposed.
5. **First claim set.** Limits and modalities only, or does the lab need tool-calling fidelity first?
6. **Is the owner-canonical resource-group identity a prerequisite** for any `verified`, as proposed, or
   may `probed` ship before it?

## Not authorized

Any implementation, schema or migration, key creation or distribution, running a verifier against any
node, shadow or enforcing resolution on any gateway, any change to what a catalog row reports, any
deployment, and any production traffic.
