# 62 — Federated Provisioning: Hosting Requests, Acquisition, Sizing and Profiling

## Purpose

Feature `IW-ALIAS-001` (extension) and the federated provisioning workstream; tasks `A-T05`,
`P5-T17`. Status: **proposed**. Nothing here is `proven`; see Proof status.

The federated provisioning family (`provision.*`, negotiated as `iw.provisioning/1`) exists in
`InferWeave/inferweave` at commit `de43764a` (`crates/iw-protocol/src/provision.rs`,
`crates/iw-core/src/provisioning.rs`, `provision_planner.rs`, `provision_capacity.rs`,
`crates/iw-gateway/src/provision_controller.rs`, `provision_transport.rs`). The specs repository had **no provisioning specification** before this text
(`docs/federated-provisioning-audit.md` §2.10 records it as missing). This text therefore does two
things, kept apart:

1. **Records the delivered contract** (next section) so there is one reviewable statement of what
   the code already does. It changes nothing.
2. **Extends it additively** so a requester can ask for a model **the owner does not yet host**:
   the request says what it wants and how precisely, the owner answers with what hosting it would
   need (download, disk, memory, profile generation), an operator approves a bounded plan, and the
   owner acquires, verifies, profiles and serves it.

It adds no scheduler, no new gateway role and no authority to install anything on a request
alone. Where this text and `20_NODE_AUTOCONFIG_DISCOVERY.md` (Model fetch), `16_SECURITY_PRIVACY_TRUST.md`, spec 50 or spec 54 disagree, those specifications win.

## The delivered contract (recorded, not changed)

Taken from the code at the commit above. A statement here is a statement about that code; if the
code differs, the code is the fact and this text is the defect.

* **Messages.** A closed family tagged by kind: `capabilities`, `request`, `offer`, `reserve`,
  `approval`, `activate`, `revoke`, `heartbeat`. Every message is enveloped (id, idempotency key,
  actor origin token, provenance hop list bounded at 8, expiry, trace id). A message larger than
  1 MiB is refused before decoding (`MAX_PROVISION_BYTES` in the protocol crate; the transport
  enforces its own duplicate `MAX_PROVISION_BODY`). Unknown versions and unknown kinds fail closed; the
  compatibility rule is same major, any minor.
* **States.** `DESIRED`, `OFFERED`, `RESERVED`, `APPROVED`, `ACTIVATING`, `READY`, `REVOKED`,
  `EXPIRED`, `FAILED`, `RELEASED`. Forward progress is `DESIRED → OFFERED → RESERVED → APPROVED →
  ACTIVATING → READY`; any non-terminal state may move to `REVOKED` or `FAILED`; `EXPIRED` is
  reachable only from `RESERVED`, `APPROVED`, `ACTIVATING` and `READY` (a `DESIRED` or `OFFERED`
  request cannot expire); `REVOKED`, `EXPIRED` and `FAILED` move only to `RELEASED`; `READY → RELEASED` is also legal;
  `RELEASED` is absorbing and a released reservation is never reactivated.
* **Owner policy modes.** `disabled` (the default; serves nothing), `advertise_only`,
  `approval_required`, `autonomous`. In observe-only operation an activation is refused. In
  `approval_required` a reservation cannot be activated until an operator has approved it. Before
  any mode applies, `emergency_stop` beats every mode and a parent `allowlist` is applied (an
  empty allowlist admits nobody). **Gap:** `autonomous` + `activate` is refused today
  (`Refusal::AutonomousUnavailable`); autonomous acquisition therefore needs an activation path
  that does not exist. `emergency_stop` and the parent allowlist apply to the plan, to
  acquisition and to every phase of this extension.
* **Reservations.** Single-use activation token, monotonic fencing epoch (an older epoch is
  refused), lease, local clients outrank upstream (a not-yet-ready reservation can be
  preempted), every state change is an auditable event.
* **Lease (delivered, non-conforming).** `lease_expires_at = now + DEFAULT_LEASE_TTL` (300 s) and
  only `tick(now)` expires it; the transport's heartbeat handler is a no-op and nothing renews
  it. The delivered lease is therefore **elapsed-time**, which invariant 37 forbids. The
  extension changes this (progress-based expiry, below); that is a semantic change to delivered
  behaviour, not an additive one, and is recorded in `OPEN_GATES.md`.
* **Activation (delivered).** `activate()` moves `APPROVED → ACTIVATING → READY` in one
  synchronous call with no work between. The extension requires that `READY` is no longer
  emitted by `activate()` itself (controller change, below).
* **Wire shape (delivered).** `provision.*` bodies use `#[serde(flatten)]` without
  `deny_unknown_fields`; `ProvisionCapacity` documents that unknown fields are ignored. A
  delivered consumer therefore **drops** unplanned members rather than rejecting them.
  `ProvisionFeature` is a closed enum (`approvals`, `leases`, `revocation`) and
  `Capabilities.features` is a `Vec<ProvisionFeature>`: a peer that sends `"acquisition"` makes
  serde fail the whole `capabilities` message on a delivered consumer.
* **Capacity signal (delivered).** `provision_capacity.available_vram` is `Derived`, summed from
  advertised per-model `vram_bytes`: it is loaded-model size, not free memory. `fit` MUST NOT
  read it.
* **Planner.** `provision_planner` is **eligibility-only, never placement**: it matches the model repository name exactly
  or followed by a `-` qualifier boundary (`model_name == req.model || starts_with(req.model + "-")`,
  never a bare prefix; so `qwen3-27b` matches `qwen3-27b-q4_k_m` without any precision decision), a coarse context ceiling and a coarse slot count against coarse,
  topology-free capacity signals. It cannot know memory headroom, so it never claims a placement
  would succeed. Rejections use a closed, privacy-safe reason vocabulary.

### What that contract cannot express

A request names **one exact model repository string** and a context and slot count. It cannot
express: a model the owner does not hold; a precision (spec 61); where the weights come from or
which immutable revision; whether acquiring them is permitted; how large anything is; what loading
would need; or a profile to be generated. The only model an owner can offer is one it already
advertises. That is the gap this text closes.

## Hosting extension

Negotiated as the additional provisioning **feature `acquisition`**, carried by a new major (`iw.provisioning/2`, `schema_version` major 2; the delivered transport refuses a different major with `IncompatibleVersion`, so a delivered peer never receives it; `model` stays a required request field)
(beside `approvals`, `leases`, `revocation`). Because the delivered `ProvisionFeature` enum is closed
(see above), negotiation is **not** additive on delivered consumers. Two things are therefore
required of the controller task: (a) unknown feature names in `capabilities` are skipped, not
fatal; (b) the major-2 token above is the negotiation. A negotiation test against the delivered decoder is owed. A producer
that did not negotiate the feature MUST NOT send the members below; the **new** consumer rule is
that such members from a non-negotiating peer are rejected (a closed-object rule that does not
exist today and is owed). A delivered consumer drops them silently.

### Model reference

A **model reference** names an immutable thing to host:

| Member | Meaning |
|---|---|
| `source` | `owner_cache` (already held by the owner or its site artifact cache, spec 27), `inventory` (published on the owner's shared storage) or `huggingface` |
| `repository` | the source-specific repository or path |
| `revision` | an **immutable** revision: 40 or 64 lowercase hex characters. Anything else (branch, tag, short hash) is refused: a floating reference is not a reference |
| `artifacts` | the bounded list of file names the plan would fetch or use; at most 64 entries |
| `quantization` | the spec 61 token of the quantization the artifacts carry |
| `license` | informational only. The owner fetches the license from the pinned revision itself and normalizes it to an identifier set; the approver acknowledges the **owner-fetched** value, never the requester's. A gated or terms-accepting repository needs a separate operator action (authentication or acceptance of source terms) which a request never performs |
| `expected_digests` | the per-artifact content digests when the source publishes them |
| `repository_id` | the source's immutable repository id when it supplies one; organization allowlists bind to it, not to a renamable owner name |

Bounds: at most 64 artifacts, 256 characters per name or host, 32 `egress_hosts`, 16 `shortfall`
entries, 64 `evicts` handles, 16 `phases`. A plan that would exceed 1 MiB is refused with
`PLAN_TOO_LARGE`. Planning is itself rate-limited per requester: plan-only is a free resource
probe otherwise.

`huggingface` is one source, not an assumption: an owner states in its capacity signal which
sources it will use (below). The `inventory` and `owner_cache` sources involve no external
network.

### Request additions

`provision.request` gains, when `acquisition` is negotiated:

* `model_ref`: a model reference, **or** `selection_digest`: the digest of a normalized spec 61
  selection the requester evaluated (the owner re-evaluates it; the digest is a binding, not a
  trust input). Exactly one. A `selection_digest` alone never authorizes acquisition: the owner re-evaluates
  it to candidates and must present a pinned `model_ref` for approval; when re-evaluation yields
  several candidates the plan lists them and the approval names one. `acquire: forbidden` with a
  `selection_digest` is a plain evaluation (no plan of acquisition); `acquire: permitted`
  without either member is rejected;
* `acquire`: `forbidden` (the default, meaning the delivered contract: serve only what is
  held) or `permitted`;
* `size_budget`: optional upper bounds the requester will accept (`download_bytes`,
  `disk_bytes`, `vram_bytes`), each a number or absent. Absent means **no limit stated**, never
  unlimited: the owner's own policy bound applies, and an owner with no policy bound **denies**.
  `size_budget.vram_bytes` is the requester's acceptance bound; the delivered
  `budget_vram_bytes` remains the approval budget field and is the one an approval binds. The
  size check is made on the sum over the owner-resolved artifact list, not the stated figure.

A request with `acquire: permitted` does **not** authorize acquisition. It authorizes the owner to
*plan*. See Authority.

### Sizing evidence

Every size in a plan is a **sized quantity** with the vocabulary of spec 46 (`Quantity`): a number
in bytes **and** a `basis` of `measured`, `derived`, `estimated`, `declared` or `unknown`, a
`source` and an `observed_at`. Unknown is never zero. A plan that cannot size a required quantity
reports it `unknown`; it is then `UNKNOWN`-fit (below), never `FITS`.

Sources of size evidence. For any resource the plan must reserve, the plan uses the **largest**
figure among all sources that sized it and names every figure; a lower-precedence source never
reduces a figure. Precedence orders only which `basis` and `source` label is reported:

1. **`owner`**: measured on the owner's own storage or runtime (`measured`).
2. **`inventory`**: file sizes of an artifact already published on the owner's shared storage
   (`measured` only when the owner stat'ed the file, with `observed_at` and a maximum age; a
   listing alone is `derived`).
3. **`huggingface`**: file sizes the repository metadata states for the pinned `revision`
   (`declared`: a third party's statement about bytes this owner has not yet fetched).
4. **`estimate`**: derived from stated inputs such as parameter count and the quantization's
   nominal bit width (`estimated`). An estimate MUST name its inputs. This text fixes **no
   formula and no constant**; the estimator is an implementation matter that must be validated
   against measured sizes before the estimate may drive an automatic decision.

After acquisition the owner replaces every `declared`/`estimated` figure by the `measured` one
and re-checks the bounds **before `loading`**, for disk and for VRAM; exceeding an approved
bound fails the activation (`SIZE_BOUND_EXCEEDED`).

### Offer additions

`provision.offer` gains `hosting_plan`:

| Member | Meaning |
|---|---|
| `model_ref` | the reference the plan is for, echoed with `revision` and resolved `artifacts` |
| `fit` | `FITS`, `FITS_AFTER_EVICTION`, `DOES_NOT_FIT` or `UNKNOWN` |
| `shortfall` | for `DOES_NOT_FIT`: per resource (`disk`, `vram`, `network`, `license`, `source`, `runtime`) the required figure and a boolean or coarse bucket of what is available, never the observed free disk, VRAM or bandwidth (an exact figure would let a requester probe the owner; it may be shown to an authorized operator only) |
| `evicts` | for `FITS_AFTER_EVICTION`: the models the owner would have to unload, as opaque handles to the owner's operator only (the requester receives only the redacted verdict); the owner decides, local clients outrank upstream. The distinction `FITS` versus `FITS_AFTER_EVICTION` itself reveals other tenants' load; a requester without authorization receives the plan as if no other tenant's model existed (spec 61 rule) |
| `needs` | sized quantities: `download_bytes`, `disk_bytes`, `vram_bytes` (weights, KV at the requested context, overhead as separate members, spec 46 categories), `egress_hosts` |
| `phases` | the ordered phases and, for each, whether it is required and a duration **estimate** with its basis |
| `profile` | what profile generation will produce: the capability profile facts of spec 54 step 6 and the measured limits the owner will record |

`fit` is the owner's conclusion about **its own resources**, from its own measured reports
(spec 46). A not-yet-loaded model's VRAM need is by construction an estimate (KV at the
requested context plus overhead), and spec 46 §2.1 makes arithmetic over an estimate
`estimated`. Therefore **`FITS` is not reachable for an unprofiled model**: before profiling
`fit` is `UNKNOWN` unless the owner applies an explicit conservative upper bound with a measured
safety margin, in which case the bound is reported as `derived` and named as a bound. `fit` is the conjunction over every resource: it is `FITS` or `FITS_AFTER_EVICTION` only when every resource is, and both appear only under the conservative-bound clause or after profiling. A `declared` (Hugging Face) download size can never reach `FITS` alone; it counts as `UNKNOWN` until measured or bounded by the larger-figure rule. The plan's
`egress_hosts` and `phases` are shown to the requester only to the extent the owner's policy
allows; the owner's network policy is not otherwise disclosed.
`FITS_AFTER_EVICTION` never evicts anything by itself.

### Phases and states

No state is added to the delivered machine. Acquisition happens inside `ACTIVATING`, which
requires a controller change: today `activate()` is synchronous (see above), so `ACTIVATING`
must become an interval the controller holds while phases run. A heartbeat gains the optional member `phase`, one of `acquiring`, `verifying`,
`profiling`, `loading`, `validating`, with `done` and `total` sized quantities for the current
phase. The owner's internal runtime lifecycle (spec 50: `DOWNLOADING`, `LOADING`, `WARMING`,
`VALIDATING`) is the implementation of these phases and remains the authority on loading.

`READY` is entered only when `validating` succeeded: the model loaded, answered a validation
request, and its profile facts were recorded with the confidence spec 54 assigns (`verified` only
by the owner's own qualification). A model that has been fetched but not profiled and validated is
not `READY` and is not advertised as available.

A failure moves the reservation to `FAILED` with one of the closed reasons
`DOWNLOAD_FAILED`, `DIGEST_MISMATCH`, `LICENSE_NOT_ACCEPTED`, `INSUFFICIENT_DISK`,
`INSUFFICIENT_VRAM`, `SIZE_BOUND_EXCEEDED`, `SOURCE_NOT_ALLOWED`, `PROFILE_FAILED`,
`VALIDATION_FAILED`, then `RELEASED`. Release removes every resource the reservation held,
including partial downloads not retained in the content-addressed cache (invariant 37).

Lease: following invariant 37, a lease expires on **absence of observable progress**, never on
elapsed time alone. Bytes acquired, a profiling step completed or a validation request answered
are progress; a `phase` heartbeat with no change in `done` is not. Spec 50 allows accepted
progress to sustain an arbitrarily long load, so invariant 37 is kept; to stop a trickle
download from holding disk and bandwidth indefinitely the owner policy MAY set a minimum rate or
per-phase cap, and this text states that none exists unless the owner sets one.
A `READY` lease is sustained by a heartbeat whose state changes (or by an explicit owner exemption); the delivered `tick` also expires `READY`, so this is owed. `READY` and its advertisement are one event with the spec 54 advertisement generation, so an
alias never sees `READY` before the profile facts are recorded.

## Authority

* **Never from a name.** Acquisition is never started because a model name or a `selection_digest`
  appeared in a remote request (`20_NODE_AUTOCONFIG_DISCOVERY.md`, Model fetch). A request is a
  request to *plan*.
* **`disabled` and `advertise_only`**: no acquisition, no plan beyond what the delivered contract
  already produces.
* **`approval_required`**: acquisition requires an operator's `approval`, which binds, in addition
  to the delivered request digest, budget, policy revision and fencing epoch: the **pinned
  `revision`**, the **artifact list**, `acquire: permitted`, the approved `download_bytes`,
  `disk_bytes` and `vram_bytes` bounds, and an explicit **license acknowledgement** by the
  approver (`license_acknowledged: true` naming the owner-fetched normalized license identifier
  approved, bound to the pinned revision; `unknown` cannot be acknowledged by default). It also
  binds the `source`, `repository` (and `repository_id`), the `expected_digests` set,
  `quantization` and the `egress_hosts` list. If the source publishes no per-artifact digest
  and the owner's cache holds none (a first fetch), the operator must approve the digests the
  owner computed; without that the result is `UNVERIFIED` and the model stays not `READY`.
  Approval of a plan does not authorize a different revision, source, host, additional artifact
  or larger bounds.
* **`autonomous`**: acquisition only inside **owner policy caps** set in advance by the owner
  (an allowlist of sources and organizations, per-request and per-period byte caps, an allowlist
  of licenses). Period counters are durable, per requester as well as global, charged at the
  start of acquisition and never refunded until the bytes are actually removed, including after
  a restart. This mode needs the activation path the delivered contract lacks (see above). A request outside any cap is refused with `SOURCE_NOT_ALLOWED`, never queued for
  silent retry. Autonomous mode MUST NOT acknowledge a license that is `unknown` or not on the
  owner's allowlist.
* A remote requester can never change owner policy, opt-in or caps through any message
  (delivered contract; unchanged).

## Safety

* **Revision pinned, digest verified.** Every artifact is verified against its published digest
  when the source supplies one, and against the digest recorded in the owner's artifact cache
  otherwise (see Authority for a first fetch with neither); a mismatch is `DIGEST_MISMATCH` and the artifact is discarded (spec 27).
* **Data-only artifact formats.** The owner fetches weight formats that do not execute code on
  load (for example GGUF and safetensors). It never runs repository code, never enables
  remote-code options of a runtime, and never executes a downloaded script. An artifact in a
  format that can execute code on load is refused. The default policy is deny: only `.gguf` and `.safetensors` weights are permitted; `.bin`,
  `.pt`, `.pkl` and `.py` are refused unless the owner explicitly allows them. Headers are parsed
  with bounded sizes. Companion files (tokenizer, chat template) can carry executable-ish
  template code and are fetched only if listed in `artifacts`, verified, and rendered only by
  the runtime's sandboxed template engine.
* **Bounded egress.** Network access is limited to the sources the owner's policy allows and the
  hosts the plan's `egress_hosts` declared; an unplanned host is refused, including a host reached by redirect or mirror (the host is
  pinned after redirect against `egress_hosts`). Downloads are resumable
  and storage-aware (spec 20).
* **GPU safety is unchanged.** Acquisition and profiling never bypass the GPU watchdog, rescue,
  quarantine, restart-loop protection or Slurm authority (`AGENTS.md`, Required GPU safety).
  Loading follows spec 50's transactional lifecycle and the rebalancer; this text adds no loader.
* **Local priority.** Local clients outrank upstream. A reservation in any phase before `READY`
  may be preempted by a local need; its partial resources are released.
* **Privacy.** A plan's `shortfall` and `evicts` are disclosed to the requester only as required
  figures, coarse availability and redacted verdicts (see Offer additions): no node identity, no
  topology, no free-resource figures, no other tenant's model names (spec 61 redaction rules
  apply).
* **Approval digest.** The owner recomputes the request digest over `model_ref`, `acquire` and `size_budget`; a requester-supplied digest is never trusted.
* **Spec 41.** Inter-gateway capacity requests (spec 41) are a different mechanism; this text
  does not alter grants.

## Relation to aliases (spec 54, spec 61)

* A spec 61 `unmet` list tells an operator *why a branch is not available now*. It is not an offer
  and not a request. To act on it a requester sends a `provision.request` whose `selection_digest`
  binds the evaluated selection, or whose `model_ref` names a concrete model the selection could
  accept.
* An owner advertises willingness in its capacity signal with an additive member `acquirable`:
  the `sources` it will use, an upper bound on `download_bytes` it would accept, and the license
  identifiers it would accept. It never advertises free disk or topology, only what it is willing
  to plan. `acquirable` marks an alias candidate `PROVISIONABLE` (spec 54 eligibility) **only when**
  the owner is not `disabled` and the signal is fresh (by `sequence`/`observed_at`, as the planner
  treats stale offers); `PROVISIONABLE` is never `READY`.
* Spec 54 forbids a Go-held alias database, selector or inventory. The Go site gateway MAY render
  the plan, `fit`, `shortfall`, `phases` and progress it receives, and MAY relay a request; it
  does not size, plan, fetch or decide.

## Required tests

All **owed**; none is `proven`. Each must fail if its control is removed.

1. Negotiation: without `acquisition` the delivered messages are unchanged and the new members are
   rejected by a new consumer; an unknown feature name does not fail `capabilities`; the
   delivered decoder is exercised against a message carrying the new members.
2. Authority: `acquire: permitted` alone never starts a fetch; `disabled` and `advertise_only`
   never plan beyond the delivered contract; in `approval_required` no fetch before approval, and
   an approval for revision A does not allow revision B, an extra artifact or larger bounds;
   `autonomous` refuses a source, organization or license outside its caps and an `unknown`
   license; a floating reference or short hash is refused; `selection_digest` alone never
   acquires; a gated repository is never accepted by a request; `emergency_stop` and the parent
   allowlist stop a plan, an acquisition and each phase; period caps survive a restart.
3. Sizing: the largest-figure rule; `FITS` unreachable for an unprofiled model; `unknown` never produces `FITS`; measured
   replacement after acquisition re-checks bounds and fails with `SIZE_BOUND_EXCEEDED`; an
  estimate names its inputs; the VRAM re-check precedes `loading`; the budget is checked over
   the resolved artifact list.
4. Fit: `FITS`, `FITS_AFTER_EVICTION` and `DOES_NOT_FIT` against owner reports with `shortfall`
   per resource; `FITS_AFTER_EVICTION` evicts nothing.
5. Lifecycle: no state added; `READY` only after validation; each failure reason releases every
   resource including partial downloads; a lease expires on absence of progress, not elapsed
   time (with the delivered elapsed-time lease shown failing the same test); `activate()` no
   longer emits `READY`; preemption by a local client in each pre-`READY` phase.
6. Safety: digest mismatch discards the artifact; a code-executing format is refused; an
   unplanned egress host is refused; no runtime remote-code option is ever enabled; `.bin`/`.pkl` refused by default; a redirect to
   an unplanned host is refused; an unverifiable first fetch is `UNVERIFIED`, not `READY`.
7. Privacy: a requester without authorization receives a plan identical to one for a world in
   which the other tenants' models do not exist (modulo handles).
8. Privacy of the plan: `shortfall` carries no observed free figure; repeated requests cannot
   probe free disk or VRAM; planning is rate-limited.
9. Cross-language: the Go console renders a plan and its progress from the schema without
   deriving `fit` or any size.

## Proof status

Everything in this specification is **proposed** and **owed**: no schema, fixture, sender,
consumer or test of the *extension* exists. The section "The delivered contract" is a record of
code at commit `de43764a`; the tests the code carries prove the code against itself, not this
text, and this change does not run them. The size-estimate method, the phase duration estimates
and every byte bound are deliberately **left unspecified** here, because none has been measured:
they are owed measurements and an estimator validated against measured sizes. Nothing in this
text opens a production gate.

## Out of scope

* The estimator, the download client, the profile generator and the runtime loaders.
* Pricing, quota between tenants and cross-site billing.
* Aliases that compose other aliases (prohibited by spec 54).
* Adding a state to the delivered machine, or changing the delivered envelope. (The lease
  semantics, `activate()` timing, feature negotiation and the closed-object rule do change; they
  are named above and owed.)

## Ownership

The controller changes (progress-based lease, asynchronous `ACTIVATING`, feature negotiation,
autonomous activation path) belong to `A-T05`; the planner, sizing and hosting-plan work belongs
to `P5-T17`.
