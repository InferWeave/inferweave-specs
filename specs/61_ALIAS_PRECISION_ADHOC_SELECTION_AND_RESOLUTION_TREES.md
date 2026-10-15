# 61 — Alias Precision, Ad-hoc Selection and Resolution Trees

## Purpose

Feature `IW-ALIAS-001` (extension), tasks `A-T01`, `A-T03`, `A-T05`, `A-T07`. This text is an
**additive amendment of `54_DYNAMIC_MODEL_ALIASES.md`, level 2**. Spec 54 remains the authority on
alias definition, validation, publication, resolution, admission and errors; where this text and
spec 54 disagree, spec 54 wins until this text is accepted and spec 54 is updated to match.
Status: **proposed**. Nothing here is `proven`; see Proof status.

It closes three gaps found while specifying the operator surface for aliases:

1. **Precision is not a selection dimension.** Spec 54 selects on runtime family, modality,
   context, features, privacy, residency and trust. A client cannot say "any 8-bit or better" or
   "no 4-bit"; precision exists only inside the concrete model id (`quant` qualifier of the
   canonical model id, `iw-core` `ModelId`), and spec 54 forbids substring parsing of ids.
2. **There is no form for a selection defined on the fly.** Spec 54 reserves `cap:` (and
   `alias:`) and defines neither. A person asking "what would serve a vision model at 8-bit with
   128k context?" has to publish an alias first.
3. **A resolution has no tree.** Spec 54 returns a flat bounded candidate list. A reader cannot
   see how one selection fans out over models, instances, owners and gateways, nor *why* a branch
   was eliminated, which is the input a provisioning decision needs.

This document defines wire contracts and matching rules only. It adds no scheduler, no gateway
role, no alias database outside Rust (spec 54, Ownership and terminology) and no provisioning
authority. Provisioning stays with the owner under the federated provisioning policy; this text
only makes the *unmet requirements* of a selection a first-class, typed, bounded output.

## Precision

### Facts

A capability profile (spec 54, Resolution step 6) gains the jointly true, separately evidenced
members below. They follow the same evidence rules as every other profile fact: timestamped,
expiring, tied to the profile's `instance_generation`; absence is *unknown* and can never satisfy
a hard requirement.

| Member | Type | Meaning |
|---|---|---|
| `quantization` | token | the canonical `quant` qualifier of the served model id, copied as typed metadata by the producer. A consumer never derives it by parsing an id string. |
| `precision_class` | enum | the class of `quantization` under the frozen table below, or `unknown` |
| `precision_table_version` | integer | the version of the table that produced `precision_class` |

A **token** matches `[a-z0-9._]{1,32}` (the segment alphabet of the canonical model id in
`iw-core` `ModelId`, bounded). Anything else is rejected, not truncated.

`precision_class` is computed by the *producer* and advertised. A consumer **trusts the advertised
class** and never reclassifies a token it received. A consumer that holds the same
`precision_table_version` MAY verify the advertised class; a mismatch makes that candidate
`EXCLUDED` with the frozen reason `precision_unverified`. A consumer with a different table
version does not verify. A producer that does not know a token advertises `unknown`.

### Frozen vocabulary

`precision_class` names **nominal weight bit-width bands**, ordered from highest to lowest:

| Class | Band |
|---|---|
| `full` | 16 bits or more per weight |
| `high` | 8 bits |
| `medium` | 5 to 6 bits |
| `low` | 4 bits |
| `very_low` | 3 bits or fewer |

`full` > `high` > `medium` > `low` > `very_low`. `unknown` is not a band and not an ordinal
position: it **never** satisfies `min_precision_class`, a non-empty `quantization_allow` or a
non-empty `quantization_deny`, and it ranks below every band.

A token is classified by its **nominal base width**, the width its name states. Mixed-precision
or dynamic variants (names ending in `_xl`) are classified by that base width. The classes order
nominal width only: they claim nothing about answer quality, and two tokens in one class are not
interchangeable in quality. Quality remains a measured metric (spec 54 ranking; spec 60
`quality_floor`).

Initial membership (exact tokens, versioned table `schemas/v1/aliases/precision-classes.json`,
**additive**: a token is added in a later table version and never moved between classes):

| Class | Tokens |
|---|---|
| `full` | `fp32`, `bf16`, `fp16` |
| `high` | `q8`, `q8_0`, `q8_k_xl`, `fp8`, `fp8_e4m3fn`, `int8` |
| `medium` | `q6_k`, `q6_k_xl`, `q5_0`, `q5_1`, `q5_k_m` |
| `low` | `q4_0`, `q4_1`, `q4_k_m`, `q4_k_xl`, `mxfp4`, `nvfp4`, `awq` |
| `very_low` | `q3_k_m`, `q2_k` |

Six of these tokens (`fp16`, `q8_k_xl`, `fp8_e4m3fn`, `q4_k_m`, `q4_k_xl`, `mxfp4`) are
**observed**: they are the distinct `quant` qualifiers the reference lab gateway listed on
2026-10-15, reproduced in `evidence/alias-precision-tokens-2026-10-15/`. Every other token in the
table is **unobserved** there; its band is a classification of its nominal width by the authors
of this change. `fp8`, `int8` and `awq` occur in the reference implementation's deployment
vocabulary; `awq` is listed as 4-bit by its nominal weight width. A token not in the table is
`unknown`, which is intentional and safe: it is hidden from precision-constrained selections
until a later table version classifies it.

### Requirements and preferences

`required` and the request requirements gain:

| Member | Type | Meaning |
|---|---|---|
| `min_precision_class` | band (never `unknown`) | the candidate's `precision_class` is at or above this band |
| `quantization_allow` | set of tokens, 1..16 | the candidate's `quantization` is a member |
| `quantization_deny` | set of tokens, 0..16 | the candidate's `quantization` is not a member; deny wins |

Rules:

* `quantization_allow` and `quantization_deny` match **the token alone**, independent of class.
  Only `min_precision_class` depends on the class. A token outside the table is accepted in an
  allow or deny set.
* Fail closed on absence: when any of the three members is set, a candidate with an absent or
  `unknown` `quantization` (or, for `min_precision_class`, an `unknown` class) is `EXCLUDED`.
  Absent is never treated as "not in the deny set".
* Spec 54 step 4 applies: a request may only *strengthen* (raise `min_precision_class`, shrink
  `quantization_allow`, grow `quantization_deny`); weakening is a safe failure.
* **Conflict** is evaluated against the table version pinned in the alias revision (or, for an
  ad-hoc selection, in the request) and fails `INVALID_CAPABILITY`: an allow set that is empty
  after removing the deny set; an allow set none of whose tokens can meet `min_precision_class`
  under that version (tokens of class `unknown` count as unable). A token classified in a later
  table version never changes the validity of an already-published revision.
* `preferred` gains the member `precision`, a weight like the others (spec 54: finite,
  nonnegative, normalized to sum 1 within 1e-6 with the others). Its score is the candidate's
  class ordinal only; ties within a class are not broken by token. It ranks after all hard
  constraints and never admits a candidate a hard requirement excluded.
* With none of the new members present, behaviour is exactly spec 54.

## Ad-hoc selection

An **ad-hoc selection** is an anonymous `selection` supplied inline with a *simulate* or *resolve*
call on the native API. It is evaluated as if it were a published `DYNAMIC` alias with these fixed
properties:

* it has **no id, no revision and no publication**; the response reports `alias: null` and
  `adhoc: true`; it is never stored, never listed, never advertised and never appears in
  `/v1/models`;
* `selection.type` is `DYNAMIC` only. `MANAGED` requires a stored allowlist and is not an ad-hoc
  form. Alias-to-alias targets remain prohibited (spec 54 Definition): an ad-hoc selection cannot
  name an alias.

**Routes and permission.** The inline `selection` is accepted **only** on
`POST /inferweave/v1/aliases/resolve` and `/inferweave/v1/aliases/simulate` with the explicit
`InferWeave-Alias-Level: 2` header, never on `/v1/*` and never on a dispatch route. It requires
the same grant as spec 54 requires for that route (`can_preview` for resolve; the simulate grant
for simulate). The request schemas `schemas/v1/aliases/resolve-request.json` and
`simulate-request.json` gain the optional member `selection`; they stay closed, and a call
carrying both `alias_id` and `selection` is rejected.

**Authority floor.** An ad-hoc selection has no alias to strengthen, so its floor is the caller's
own authority, never "unrestricted":

* an omitted `allowed_tenants`, `trusted_origins`, `residency` or `privacy` member defaults to the
  caller's own tenant and policy floor; an explicit empty set admits nobody (spec 54);
* the evaluation is the *intersection* of the caller's authority and the selection, never more
  (spec 54 step 4: tenant, license, privacy, trust, residency, deny and owner sharing policy
  cannot be weakened).

**Evaluate-only.** An ad-hoc selection MUST NOT dispatch inference, enqueue, reserve, change
demand, allocate, load, unload, start a job or consume a lease, and the response **mints no
spec 57 execution permit, claim or binding**. Its `selected` member is informational: it cannot
be supplied back as `alias_id`, and a client that wants to route by it must publish an alias
through the spec 54 definition and publication flow. Spec 54 Resolution step 10 already states
that preview and simulation do none of these things; this text states it for the ad-hoc form so
no implementation can treat "unpublished" as "unrestricted".

The model-name syntax `cap:` stays **reserved and undefined** on the OpenAI-compatible edge. A
policy hidden in a string is not validated, versioned or audited. A client or UI MAY offer a text
convenience ("qwen 27b q8 vision") but converts it to a structured ad-hoc selection before the
call and shows the structured form it produced. That conversion is **client-side and
non-normative**; the wire form is the structured `selection`.

### Relation to spec 60

Spec 60 expresses *a client's need*; spec 54 expresses *a published policy*. Where concepts
coincide an implementation maps them as below without changing a constraint's meaning. The
mapping is a requirement on implementations, not a claim that the two schemas are one dialect.

| Spec 60 member | Spec 54 / 61 member |
|---|---|
| `modality` | `required.input_modalities` |
| `min_context_tokens` | `required.min_context_tokens` |
| `capability` | a `required.features` entry (feature and fidelity as spec 54 defines) |
| `quality_floor` | a qualified quality requirement over the named metric; no ranking-only reading |
| `open_weight_only` | **no equivalent**: owner policy, not a selection member; an implementation MUST NOT silently drop it when mapping |
| `deadline`, `affinity` | request-level (spec 54 admission), not selection members |

## Resolution tree

A resolve or simulate response carries `resolution_tree` beside the flat bounded candidate list
of spec 54. The tree is a *rendering of the evaluation that already happened*; it adds no new
evaluation and no new authority. Level 2 forbids alias recursion, so the tree has exactly four
levels and is a view over federation fan-out, not a way to nest aliases.

Levels, root to leaf:

1. `selection`: the alias revision, or `adhoc: true` with the normalized selection;
2. `model`: one node per concrete model id that met every **model-level** constraint (runtime
   family, modalities, ceilings, precision, model allow/deny) for the caller;
3. `instance`: one node per instance of that model, with its `instance_state`, `eligibility` and
   the frozen reason codes of spec 54 (Additional frozen vocabularies);
4. `owner`: the owner gateway and, for a federated candidate, the bounded **path vector** its
   advertisement carried (spec 54, Runtime, GPU and federation integration), never longer than
   that advertisement's own bound.

A model that failed a model-level constraint has **no `model` node**; the shortfall appears as an
`unmet` entry on the `selection` node (below).

Rules:

* **Bounds.** At most 64 `model` nodes and at most the candidate cap of spec 54 (256) `instance`
  nodes per response, further capped by owner policy. When a bound truncates, the response sets
  `truncated: true` and the count of omitted nodes; a truncated tree is never presented as
  complete.
* **Counts and redaction.** Every count, `observed` value and omitted-node count is computed
  **only over candidates the caller is authorized to see**. Where an owner or path element is
  visible but its identifying detail is not, it is replaced by an opaque **handle derived per
  principal and per response** (keyed with a server secret and the catalog snapshot token) and
  stable only within that one response. A handle is never stable across callers or across
  responses, so two principals cannot correlate or enumerate private owners or instances. Private
  policy details, tenant allowlists and protected claims are never placed in a node.
* **Expiry.** Every node carries the evidence expiry of the facts it rests on. The tree expires no
  later than the earliest expiry of any *selected* candidate; when nothing is selected, no later
  than the earliest expiry of any node in the tree, and in no case later than a fixed maximum TTL
  set by the owner.
* **Consistency.** A candidate appears in the tree if and only if it appears in the flat list or
  is counted in `truncated`. A node never contradicts the list.

### Unmet requirements

A `selection` or `model` node with no READY, ELIGIBLE descendant carries `unmet`: a list of typed
entries explaining why the branch is not available *now*:

| Member | Meaning |
|---|---|
| `requirement` | frozen token (below) |
| `required` | the bound value the selection demanded, as the contract already types it |
| `observed` | the best value any **authorized** evaluated candidate showed; absent when none was observed |
| `scope` | `selection` (no model qualified), `model` (a model qualified but no instance did), `instance` or `owner`: where the shortfall was found |
| `count` | how many **authorized** evaluated candidates this entry eliminated |

`requirement` tokens: `runtime_family`, `input_modality`, `output_modality`, `feature`,
`min_context_tokens`, `min_output_tokens`, `min_precision_class`, `quantization`, `health`,
`capacity`.

**Authorization-caused eliminations are never reported.** There are deliberately no `tenant`,
`privacy`, `residency` or `trusted_origin` tokens. A candidate eliminated because the caller is
not entitled to see or use it is **indistinguishable from absence**: it contributes to no entry,
no `count`, no `observed` and no `truncated` figure (spec 54 Errors: authorization redacts reason
detail when disclosure itself would leak). A request whose *own* privacy, residency or trust
requirement removed every visible candidate reports that as `feature` or `health` only where the
visible evidence shows it, and otherwise as an empty `unmet` with the node's status; it never
reveals that a private candidate exists.

`unmet` is bounded by 16 entries per node. When more would apply, the node sets
`unmet_truncated: true` and the omitted count, keeping the entries that eliminated the most
authorized candidates first (ties by token order). Truncation is never silent.

`unmet` reports shortfalls; it never reports a *remedy*, a price, a duration or a promise. A
reader MUST NOT treat `PROVISIONABLE` or an `unmet` list as an offer. Turning an `unmet` list into
a request to host is a separate act under the owner's provisioning policy (the `provision.*`
message family and its approval modes) and is not specified here.

A `capacity` entry reports a *measured* shortfall only: free memory the owner's report (spec 46)
showed against the memory the candidate's published profile needs, with spec 46's rule that
unknown is never zero. Where the owner reports no figure, the entry is absent, not zero.

## Compatibility

* Additive within the unreleased level-2 bundle (spec 54: protocol `VERSION` 1.1.0); no new
  version axis. **On acceptance of this text** a producer advertising `dynamic_aliases: "2"` MUST
  either implement it or reject the new members as `INVALID_CAPABILITY` (spec 54: closed writes
  reject unknown policy members, never silently ignore them). Until accepted, nothing here binds
  an implementation. A level-1 consumer is unaffected.
* A producer that does not advertise `precision_class` makes every precision requirement fail
  closed (`unknown` never satisfies). Absent precision data hides a candidate; it never admits
  one.
* Producers and consumers with different table versions interoperate through the advertised class
  (above).

## Security and privacy

* An ad-hoc selection is not a way around authorization (above). It is evaluated under the
  caller's grant like any alias and fails closed on missing grants.
* The tree and `unmet` entries disclose *shortfalls over the caller's authorized view*, never
  capacity beyond it. Entries, counts, `observed` values and handles MUST NOT allow two
  principals, or one principal across calls, to diff private instances or owners.
* Resolve and simulate with an ad-hoc selection are rate-limited and audited like alias previews
  (spec 54 Events, errors, cache and telemetry). The audit record stores the **bounded normalized
  selection** (it is not secret) and its digest; it does not store the free text a UI converted
  from, which never reaches the server.
* The client-side text convenience is never a trust input.

## Required tests

All are **owed**; none is `proven`. Each must fail if its control is removed.

1. Precision: `min_precision_class` and `quantization_allow/deny` admit and exclude the expected
   candidates; allow/deny match on the token alone; absent or `unknown` quantization is excluded
   whenever any precision member is set; a token outside the table is accepted in a set; an
   unknown band value is rejected; a token outside `[a-z0-9._]{1,32}` is rejected; each conflict
   rule above fails `INVALID_CAPABILITY`; a request that weakens the alias is a safe failure;
   a class mismatch under an identical `precision_table_version` yields `precision_unverified`.
2. Ad-hoc: only the two routes accept `selection`, with the level-2 header and the right grant;
   `alias_id` with `selection` is rejected; omitted authority members default to the caller's
   floor; no candidate outside the caller's grant is returned; no dispatch, enqueue, reservation,
   demand change or permit/claim/binding is produced (counters unchanged); `adhoc: true`,
   `alias: null`; naming an alias or `MANAGED` is rejected; `selected` cannot be used as
   `alias_id`.
3. Tree: the four fixed levels; the 64/256 bounds with `truncated` and omitted counts; the tree
   and the flat list never disagree; handles differ between principals and between responses;
   no count or `observed` includes an unauthorized candidate; expiry with and without a
   selected candidate; a path vector never longer than its advertisement's.
4. Unmet: each token is produced by at least one fixture; there is no authorization-caused
   token; two callers differing only in authorization to a private instance receive identical
   `unmet`; `unmet_truncated` is set and counts omissions; a branch with no candidate never
   claims READY; `capacity` appears only with a reported measured shortfall.
5. Cross-language: the Go console renders the tree and `unmet` from the schema without deriving
   any of them (spec 54 Ownership: Go consumes, never decides).
6. Table: `precision-classes.json` is additive across versions; a token never changes class; a
   published revision's validity never changes with a later table version.

## Proof status

Everything in this specification is **proposed** and **owed**: no schema, fixture, producer,
consumer or test exists. The precision-class table is a classification of nominal width; the
`capacity` shortfall depends on owner reporting that is not yet universal; and the tree bounds
(64 models, 16 `unmet` entries per node, 16 allowed tokens, 32-character tokens) are *design
limits chosen for bounded responses*, not measurements, each to be confirmed against a measured
response size before acceptance (the 256-instance bound is the existing spec 54 candidate cap).

## Out of scope

* Hosting requests, offers, approval, download and profile generation: they belong to the
  federated provisioning contract and are the subject of a separate change.
* Alias-to-alias composition (prohibited by spec 54 at level 2).
* Dispatching by ad-hoc selection.
* Changing any ranking weight default.
