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

`precision_class` is computed by the *producer* from the table in the producer's own build and
advertised; a consumer MAY recompute it and MUST treat a mismatch with the advertised class as
`unknown`. A producer that does not know a token advertises `unknown`.

### Frozen vocabulary

`precision_class`, ordered from highest to lowest precision:

`full` > `high` > `medium` > `low` > `very_low` > `unknown`

`unknown` is not an ordinal position. It sorts below every class for ranking and **never**
satisfies `min_precision_class`, `quantization_allow` or any other hard precision requirement.

Initial membership (exact tokens, versioned table `schemas/v1/aliases/precision-classes.json`,
additive: a token is added in a later table version, never moved between classes):

| Class | Tokens |
|---|---|
| `full` | `fp16`, `bf16`, `fp32` |
| `high` | `q8`, `q8_0`, `q8_k_xl`, `fp8_e4m3fn` |
| `medium` | `q6_k`, `q6_k_xl`, `q5_k_m` |
| `low` | `q4_k_m`, `q4_k_xl`, `mxfp4`, `nvfp4` |
| `very_low` | `q3_k_m`, `q2_k` |

The tokens `q8_k_xl`, `q4_k_m`, `q4_k_xl`, `mxfp4`, `fp8_e4m3fn` and `fp16` are the
quantizations of served models the reference lab gateway listed in its `/v1/models` and
`/v1/workers` answers on 2026-10-14 (observed by the author of this change). The remaining tokens are table entries included
so common quantizations do not fall to `unknown`; each is **unobserved** in that fleet and its
class is a classification by the table's authors, not a measurement. The classes order
*nominal* precision only. They claim nothing about answer quality; quality remains a measured
metric (spec 54 ranking, spec 60 `quality_floor`).

### Requirements and preferences

`required` and the request requirements gain:

| Member | Type | Meaning |
|---|---|---|
| `min_precision_class` | precision class (not `unknown`) | candidate profile's class must be at or above this |
| `quantization_allow` | set of tokens, 1..16 | profile `quantization` must be a member |
| `quantization_deny` | set of tokens, 0..16 | profile `quantization` must not be a member; deny wins |

Rules, all inherited from spec 54 step 4 and stated here for the new members:

* A request may only *strengthen*: raise `min_precision_class`, shrink `quantization_allow`,
  grow `quantization_deny`. A request that would weaken the alias is a safe failure.
* Conflicting members (for example `min_precision_class: high` with an allowlist of only
  `q4_k_m`) fail validation with `INVALID_CAPABILITY`; they are never reconciled by ignoring one.
* An unknown quantization token in an *allow* or *deny* set is accepted (tokens are an open
  vocabulary) but an unknown `precision_class` value is rejected.
* `preferred` gains the member `precision`, a weight like the others. It ranks candidates after
  all hard constraints; it never admits a candidate a hard requirement excluded.
* With none of the new members present, behaviour is exactly spec 54.

## Ad-hoc selection

An **ad-hoc selection** is an anonymous `selection` supplied inline with a *preview*, *simulate*
or *resolve* call on the native API. It is evaluated as if it were a published `DYNAMIC` alias
with these fixed properties:

* it has **no id, no revision and no publication**; the response reports
  `alias: null` and `adhoc: true`; it is never stored, never listed, never advertised and never
  appears in `/v1/models`;
* it is subject to every constraint of a published alias: caller authorization, tenant, privacy,
  residency, trust and owner sharing policy cannot be weakened (spec 54 step 4); an ad-hoc
  selection has the *intersection* of the caller's authority and the selection, never more;
* `selection.type` is `DYNAMIC` only. `MANAGED` requires a stored allowlist and is not an
  ad-hoc form;
* alias-to-alias targets remain prohibited (spec 54 Definition). An ad-hoc selection cannot name
  an alias.

Ad-hoc selection is **evaluate-only**. It MUST NOT dispatch inference, enqueue, reserve, change
demand, allocate, load, unload, start a job or consume a lease. Spec 54 Resolution step 10
already states that preview and simulation never do these; this text states the same for the
ad-hoc form so no implementation can treat "unpublished" as "unrestricted".

The model-name syntax `cap:` stays **reserved and undefined** on the OpenAI-compatible edge.
This text deliberately does not turn a model name into a policy language: a policy hidden in a
string is not validated, versioned or audited. A client or UI MAY offer a text convenience
("qwen 27b q8 vision") but converts it to a structured ad-hoc selection before the call and shows
the structured form it produced. That conversion is **client-side and non-normative**; the wire
form is the structured `selection`.

The ad-hoc selection uses the same capability vocabulary as `60_CAPABILITY_ROUTING_AND_MISSION_
EVENTS.md` where the concepts coincide (capability id, modality, minimum context, minimum quality
metric), so one request shape does not exist in two dialects. Where spec 60 expresses a client's
need and spec 54 expresses a published policy, an implementation maps between them without
changing a constraint's meaning.

## Resolution tree

A preview, simulate or resolve response carries `resolution_tree` beside the flat bounded
candidate list of spec 54. The tree is a *rendering of the evaluation that already happened*; it
adds no new evaluation and no new authority.

Levels, root to leaf, fixed:

1. `selection`: the alias revision, or `adhoc: true` with the normalized selection;
2. `model`: one node per concrete model id that met the selection's model-level constraints;
3. `instance`: one node per instance of that model, with its `instance_state`, `eligibility` and
   frozen reason codes (spec 54 Additional frozen vocabularies);
4. `owner`: the owner gateway and, for federated candidates, the bounded **path vector** the
   advertisement carried (spec 54, Runtime, GPU and federation integration), never more hops than
   the advertisement's own bound.

Rules:

* The tree is **bounded**: at most 64 `model` nodes and 256 `instance` nodes per response, further
  capped by owner policy. When a bound truncates, the response sets `truncated: true` and counts
  the omitted nodes; it never presents a truncated tree as complete.
* Every node carries the evidence expiry of the facts it rests on; the tree expires no later than
  the earliest expiry of any *selected* candidate (spec 54 Preview response).
* **Redaction is per tenant and per principal** exactly as for candidates: an owner or path
  element the caller is not authorized to see is replaced by an opaque stable handle, never
  omitted in a way that changes counts. Private policy details, tenant allowlists and protected
  claims are never placed in a node.
* A node never contradicts the flat candidate list; a candidate appears in the tree if and only
  if it appears in the list, or is counted in `truncated`.
* Level 2 forbids alias recursion, so the tree has the fixed four levels. It is a view over
  federation fan-out, not a way to nest aliases.

### Unmet requirements

When a `model` or `selection` node has no READY ELIGIBLE descendant, it carries `unmet`: a list of
at most 16 typed entries explaining why the branch is not available *now*:

| Member | Meaning |
|---|---|
| `requirement` | frozen token naming the constraint (`runtime_family`, `input_modality`, `output_modality`, `feature`, `min_context_tokens`, `min_output_tokens`, `min_precision_class`, `quantization`, `privacy`, `residency`, `trusted_origin`, `tenant`, `health`, `capacity`) |
| `required` | the bound value the selection demanded, as the contract already types it |
| `observed` | the best value any evaluated candidate showed, or absent when none was observed |
| `scope` | `model`, `instance` or `owner`: where the shortfall was found |
| `count` | how many evaluated candidates this entry eliminated |

`unmet` reports shortfalls; it never reports a *remedy*, a price, a duration or a promise. A
reader MUST NOT treat `PROVISIONABLE` or an `unmet` list as an offer. They tell an operator which
constraint stopped each branch. Turning that into a request to host is a separate act under the
owner's provisioning policy (the `provision.*` message family and its approval modes) and is not
specified here.

A `capacity` entry reports a *measured* shortfall only: free memory the owner's report (spec 46)
showed against the memory the candidate's published profile needs, with spec 46's rule that
unknown is never zero. Where the owner reports no figure, the entry is absent, not zero.

## Compatibility

* Additive within the unreleased level-2 bundle (spec 54: protocol `VERSION` 1.1.0). No new
  version axis. A producer advertising `dynamic_aliases: "2"` MUST either implement this text or
  reject the new members as `INVALID_CAPABILITY` (spec 54: closed writes reject unknown policy
  members, never silently ignore them). A level-1 consumer is unaffected.
* A producer that does not advertise `precision_class` makes every precision requirement fail
  closed (`unknown` never satisfies). This is the safe direction: absent precision data hides a
  candidate; it never admits one.
* Producers and consumers with different precision-class tables interoperate through the
  advertised class; a consumer never reclassifies a token it received.

## Security and privacy

* An ad-hoc selection is not a way around authorization (above). It is evaluated under the
  caller's grant like any alias and fails closed on missing grants.
* The tree and `unmet` entries disclose *shortfalls*, not capacity: `observed` is bounded to the
  caller's authorized view. An implementation MUST NOT let `unmet` entries be diffed across
  principals to enumerate private instances; counts are over the caller's authorized candidate
  set.
* Preview, simulate and resolve with an ad-hoc selection are rate-limited and audited like alias
  previews (spec 54 Events, errors, cache and telemetry). The audit record stores the normalized
  selection digest, not the free text a UI converted from.
* The client-side text convenience never reaches the server and is never a trust input.

## Required tests

All are **owed**; none is `proven`.

1. Precision: `min_precision_class` and `quantization_allow/deny` admit and exclude the expected
   candidates; `unknown` never satisfies; an unknown token in an allow set is accepted; an
   unknown class value is rejected; a conflicting pair fails `INVALID_CAPABILITY`; a request that
   weakens the alias is a safe failure. Each test fails if the control is removed.
2. Ad-hoc: an ad-hoc selection can never return a candidate the caller's grant excludes; it never
   dispatches, enqueues, reserves or changes demand (counters unchanged); `adhoc: true`,
   `alias: null`; an ad-hoc selection naming an alias is rejected; `MANAGED` ad-hoc is rejected.
3. Tree: the four fixed levels; the 64/256 bounds with `truncated` and omitted counts; the tree
   and the flat list never disagree; redaction keeps counts and uses stable handles; the tree
   never outlives the earliest selected evidence expiry; a federated candidate carries a path
   vector no longer than its advertisement's.
4. Unmet: each `requirement` token is produced by at least one fixture; a branch with no
   candidate never claims READY; `capacity` appears only with a reported measured shortfall;
   `unmet` is identical for two callers with identical authority and differs only by redaction
   for callers without.
5. Cross-language: the Go console renders the tree and `unmet` from the schema without
   deriving any of them (spec 54 Ownership: Go consumes, never decides).
6. Table: `precision-classes.json` is additive across versions; a token never changes class.

## Proof status

Everything in this specification is **proposed** and **owed**: no schema, fixture, producer,
consumer or test exists. In particular the precision-class table is a classification, the
`capacity` shortfall depends on owner reporting that is not yet universal, and the tree bounds
(64 models, 256 instances, 16 `unmet` entries, 16 allowed tokens) are *design limits chosen for
bounded responses*, not measurements; each is to be confirmed against a measured response size
before acceptance.

## Out of scope

* Hosting requests, offers, approval, download and profile generation: they belong to the
  federated provisioning contract and are the subject of a separate change.
* Alias-to-alias composition (prohibited by spec 54 at level 2).
* Dispatching by ad-hoc selection.
* Changing any ranking weight default.
