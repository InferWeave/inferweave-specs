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
  1 MiB is refused before decoding. Unknown versions and unknown kinds fail closed; the
  compatibility rule is same major, any minor.
* **States.** `DESIRED`, `OFFERED`, `RESERVED`, `APPROVED`, `ACTIVATING`, `READY`, `REVOKED`,
  `EXPIRED`, `FAILED`, `RELEASED`. Forward progress is `DESIRED → OFFERED → RESERVED → APPROVED →
  ACTIVATING → READY`; any non-terminal state may move to `REVOKED`, `EXPIRED` (where a lease
  exists) or `FAILED`; those three move only to `RELEASED`; `READY → RELEASED` is also legal;
  `RELEASED` is absorbing and a released reservation is never reactivated.
* **Owner policy modes.** `disabled` (the default; serves nothing), `advertise_only`,
  `approval_required`, `autonomous`. In observe-only operation an activation is refused. In
  `approval_required` a reservation cannot be activated until an operator has approved it.
* **Reservations.** Single-use activation token, monotonic fencing epoch (an older epoch is
  refused), expiring lease, local clients outrank upstream (a not-yet-ready reservation can be
  preempted), every state change is an auditable event.
* **Planner.** `provision_planner` is **eligibility-only, never placement**: it matches an exact
  model repository name, a coarse context ceiling and a coarse slot count against coarse,
  topology-free capacity signals. It cannot know memory headroom, so it never claims a placement
  would succeed. Rejections use a closed, privacy-safe reason vocabulary.

### What that contract cannot express

A request names **one exact model repository string** and a context and slot count. It cannot
express: a model the owner does not hold; a precision (spec 61); where the weights come from or
which immutable revision; whether acquiring them is permitted; how large anything is; what loading
would need; or a profile to be generated. The only model an owner can offer is one it already
advertises. That is the gap this text closes.

## Hosting extension

Negotiated as the additional provisioning **feature `acquisition`** within `iw.provisioning/1`
(beside `approvals`, `leases`, `revocation`). A peer that does not negotiate `acquisition` sees
and sends exactly the delivered contract. All members below are optional additions to existing
messages; a producer that does not negotiate the feature MUST NOT send them and a consumer MUST
reject them from a peer that did not (closed objects: unknown members are rejected, never
ignored).

### Model reference

A **model reference** names an immutable thing to host:

| Member | Meaning |
|---|---|
| `source` | `owner_cache` (already held by the owner or its site artifact cache, spec 27), `inventory` (published on the owner's shared storage) or `huggingface` |
| `repository` | the source-specific repository or path |
| `revision` | an **immutable** revision (a commit hash). A branch or tag name is refused: a floating reference is not a reference |
| `artifacts` | the bounded list of file names the plan would fetch or use; at most 64 entries |
| `quantization` | the spec 61 token of the quantization the artifacts carry |
| `license` | the license identifier as the source states it, or `unknown` |
| `expected_digests` | the per-artifact content digests when the source publishes them |

`huggingface` is one source, not an assumption: an owner states in its capacity signal which
sources it will use (below). The `inventory` and `owner_cache` sources involve no external
network.

### Request additions

`provision.request` gains, when `acquisition` is negotiated:

* `model_ref`: a model reference, **or** `selection_digest`: the digest of a normalized spec 61
  selection the requester evaluated (the owner re-evaluates it; the digest is a binding, not a
  trust input). Exactly one;
* `acquire`: `forbidden` (the default, meaning the delivered contract: serve only what is
  held) or `permitted`;
* `size_budget`: optional upper bounds the requester will accept (`download_bytes`,
  `disk_bytes`, `vram_bytes`), each a number or absent. Absent means **no limit stated**, never
  unlimited: the owner's own policy bound applies.

A request with `acquire: permitted` does **not** authorize acquisition. It authorizes the owner to
*plan*. See Authority.

### Sizing evidence

Every size in a plan is a **sized quantity** with the vocabulary of spec 46 (`Quantity`): a number
in bytes **and** a `basis` of `measured`, `derived`, `estimated`, `declared` or `unknown`, a
`source` and an `observed_at`. Unknown is never zero. A plan that cannot size a required quantity
reports it `unknown`; it is then `UNKNOWN`-fit (below), never `FITS`.

Sources of size evidence, in precedence order. A higher source overrides a lower one; where two
sources disagree the plan reports the **larger** figure for any resource the plan must reserve and
names both:

1. **`owner`**: measured on the owner's own storage or runtime (`measured`).
2. **`inventory`**: file sizes of an artifact already published on the owner's shared storage
   (`measured`, because the file exists).
3. **`huggingface`**: file sizes the repository metadata states for the pinned `revision`
   (`declared`: a third party's statement about bytes this owner has not yet fetched).
4. **`estimate`**: derived from stated inputs such as parameter count and the quantization's
   nominal bit width (`estimated`). An estimate MUST name its inputs. This text fixes **no
   formula and no constant**; the estimator is an implementation matter that must be validated
   against measured sizes before the estimate may drive an automatic decision.

A `declared` or `estimated` figure never satisfies a budget check that a `measured` figure of the
same quantity would fail: the plan uses the larger. After acquisition the owner replaces every
`declared`/`estimated` figure by the `measured` one and re-checks the bounds; exceeding an
approved bound fails the activation (`SIZE_BOUND_EXCEEDED`).

### Offer additions

`provision.offer` gains `hosting_plan`:

| Member | Meaning |
|---|---|
| `model_ref` | the reference the plan is for, echoed with `revision` and resolved `artifacts` |
| `fit` | `FITS`, `FITS_AFTER_EVICTION`, `DOES_NOT_FIT` or `UNKNOWN` |
| `shortfall` | for `DOES_NOT_FIT`: per resource (`disk`, `vram`, `network`, `license`, `source`, `runtime`) the required and the observed available figure, as sized quantities (the `capacity` shape of spec 61 `unmet`) |
| `evicts` | for `FITS_AFTER_EVICTION`: the models the owner would have to unload, as opaque handles; the owner decides, local clients outrank upstream |
| `needs` | sized quantities: `download_bytes`, `disk_bytes`, `vram_bytes` (weights, KV at the requested context, overhead as separate members, spec 46 categories), `egress_hosts` |
| `phases` | the ordered phases and, for each, whether it is required and a duration **estimate** with its basis |
| `profile` | what profile generation will produce: the capability profile facts of spec 54 step 6 and the measured limits the owner will record |

`fit` is the owner's conclusion about **its own resources**, from its own measured reports
(spec 46). `FITS` requires every needed resource `measured` or `derived`; otherwise `UNKNOWN`.
`FITS_AFTER_EVICTION` never evicts anything by itself.

### Phases and states

The delivered state machine is **not changed**: no state is added. Acquisition happens inside
`ACTIVATING`. A heartbeat gains the optional member `phase`, one of `acquiring`, `verifying`,
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
are progress; a `phase` heartbeat with no change in `done` is not.

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
  approver (`license_acknowledged: true` naming the license string approved; `unknown` license
  cannot be acknowledged by default). Approval of a plan does not authorize a different revision,
  an additional artifact or larger bounds.
* **`autonomous`**: acquisition only inside **owner policy caps** set in advance by the owner
  (an allowlist of sources and organizations, per-request and per-period byte caps, an allowlist
  of licenses). A request outside any cap is refused with `SOURCE_NOT_ALLOWED`, never queued for
  silent retry. Autonomous mode MUST NOT acknowledge a license that is `unknown` or not on the
  owner's allowlist.
* A remote requester can never change owner policy, opt-in or caps through any message
  (delivered contract; unchanged).

## Safety

* **Revision pinned, digest verified.** Every artifact is verified against its published digest
  when the source supplies one, and against the digest recorded in the owner's artifact cache
  otherwise; a mismatch is `DIGEST_MISMATCH` and the artifact is discarded (spec 27).
* **Data-only artifact formats.** The owner fetches weight formats that do not execute code on
  load (for example GGUF and safetensors). It never runs repository code, never enables
  remote-code options of a runtime, and never executes a downloaded script. An artifact in a
  format that can execute code on load is refused. The permitted formats are an owner policy
  list; this text does not enumerate a complete one.
* **Bounded egress.** Network access is limited to the sources the owner's policy allows and the
  hosts the plan's `egress_hosts` declared; an unplanned host is refused. Downloads are resumable
  and storage-aware (spec 20).
* **GPU safety is unchanged.** Acquisition and profiling never bypass the GPU watchdog, rescue,
  quarantine, restart-loop protection or Slurm authority (`AGENTS.md`, Required GPU safety).
  Loading follows spec 50's transactional lifecycle and the rebalancer; this text adds no loader.
* **Local priority.** Local clients outrank upstream. A reservation in any phase before `READY`
  may be preempted by a local need; its partial resources are released.
* **Privacy.** A plan's `shortfall` and `evicts` are disclosed only to the requester and only as
  sized quantities and opaque handles: no node identity, no topology, no other tenant's model
  names (spec 61 redaction rules apply).

## Relation to aliases (spec 54, spec 61)

* A spec 61 `unmet` list tells an operator *why a branch is not available now*. It is not an offer
  and not a request. To act on it a requester sends a `provision.request` whose `selection_digest`
  binds the evaluated selection, or whose `model_ref` names a concrete model the selection could
  accept.
* An owner advertises willingness in its capacity signal with an additive member `acquirable`:
  the `sources` it will use, an upper bound on `download_bytes` it would accept, and the license
  identifiers it would accept. It never advertises free disk or topology, only what it is willing
  to plan. `acquirable` marks an alias candidate `PROVISIONABLE` (spec 54 eligibility) **only when**
  the owner is not `disabled`; `PROVISIONABLE` is never `READY`.
* Spec 54 forbids a Go-held alias database, selector or inventory. The Go site gateway MAY render
  the plan, `fit`, `shortfall`, `phases` and progress it receives, and MAY relay a request; it
  does not size, plan, fetch or decide.

## Required tests

All **owed**; none is `proven`. Each must fail if its control is removed.

1. Negotiation: without `acquisition` the delivered messages are unchanged and the new members are
   rejected in both directions; closed-object rejection of unknown members.
2. Authority: `acquire: permitted` alone never starts a fetch; `disabled` and `advertise_only`
   never plan beyond the delivered contract; in `approval_required` no fetch before approval, and
   an approval for revision A does not allow revision B, an extra artifact or larger bounds;
   `autonomous` refuses a source, organization or license outside its caps and an `unknown`
   license; a floating reference is refused.
3. Sizing: precedence and the larger-figure rule; `unknown` never produces `FITS`; measured
   replacement after acquisition re-checks bounds and fails with `SIZE_BOUND_EXCEEDED`; an
   estimate names its inputs.
4. Fit: `FITS`, `FITS_AFTER_EVICTION` and `DOES_NOT_FIT` against owner reports with `shortfall`
   per resource; `FITS_AFTER_EVICTION` evicts nothing.
5. Lifecycle: no state added; `READY` only after validation; each failure reason releases every
   resource including partial downloads; a lease expires on absence of progress, not elapsed
   time; preemption by a local client in each pre-`READY` phase.
6. Safety: digest mismatch discards the artifact; a code-executing format is refused; an
   unplanned egress host is refused; no runtime remote-code option is ever enabled.
7. Privacy: a requester without authorization receives a plan identical to one for a world in
   which the other tenants' models do not exist (modulo handles).
8. Cross-language: the Go console renders a plan and its progress from the schema without
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
* Changing the delivered state machine, envelope or any existing message.
