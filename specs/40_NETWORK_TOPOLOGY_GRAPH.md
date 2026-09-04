# 40 — Network Topology Graph and Whole-Network Visualization

Every gateway can emit a typed graph of what it knows: the nodes registered to
it, the gateways beneath it, and the GPU resources those nodes carry. Those
local graphs compose into a view of the whole network, at any moment, without a
central registry that every participant must reach.

This specification defines the graph model, the composition rules, and — most
importantly — what a gateway is **not** allowed to claim about the parts of the
network it cannot see.

## Binding rule

A gateway exports **only what it directly knows**. Absence of a child in an
export is never a claim that no child exists.

This is the rule the rest of the specification exists to protect. A topology
view that silently renders "I cannot see past here" as "nothing is here" is
worse than no view at all: it is confidently wrong at exactly the moment an
operator is using it to decide where capacity went. Every guard, field and test
below follows from it.

## Graph model

A topology export is a set of typed vertices and typed edges. Vertices are keyed
on the stable resource identities of `specs/26_RESOURCE_IDENTITY_REDISCOVERY.md`
— never on an address, a hostname, or an ephemeral worker ID, because all three
change without the underlying resource changing.

Vertex kinds, drawn from the roles in `specs/21_FEDERATION_ROLES.md`:

| Kind | Meaning |
|---|---|
| `gateway` | authenticates clients, issues route tickets |
| `coordinator` | accepts child registrations, holds regional presence |
| `provider` | executes inference |
| `relay` | moves streams/artifacts, holds no scheduling authority |
| `gpu` | one accelerator, owned by exactly one `provider` |
| `aggregate` | a summary standing in for a subtree (see **Scale**) |

Edge kinds:

| Kind | From → To | Meaning |
|---|---|---|
| `registered_with` | provider/coordinator → coordinator/gateway | control-plane parentage |
| `routes_to` | gateway/coordinator → coordinator/provider | this parent may direct work here |
| `hosts_gpu` | provider → gpu | physical ownership |
| `relays_for` | relay → gateway/coordinator | data-plane relay, not authority |

A role set is a property of a vertex, not a separate vertex: spec 21 permits one
process to be several roles at once, and modelling that as multiple vertices
would double-count capacity in every view built on this graph.

GPU vertices carry a reference to the inventory and telemetry defined in
`specs/23_GLOBAL_TELEMETRY_BENCHMARKS.md`. This specification does not restate
those fields and must not fork them; it stores the stable GPU ID and lets the
consumer join. Duplicating telemetry here would create two descriptions of one
device that drift silently.

## Horizon and completeness

Every vertex carries a `horizon` field with exactly one of:

- `complete` — the emitter knows every child of this vertex;
- `partial` — the emitter knows some children and knows that more exist;
- `unknown` — the emitter cannot see this vertex's children at all.

A leaf `provider` with no children is `complete`. A `coordinator` whose own
children have not reported since its last snapshot is `partial`. A gateway
referenced by a peer but never contacted is `unknown`.

**A consumer that renders `unknown` and `complete` identically is
non-conformant.** The count of vertices under an `unknown` vertex is not zero;
it is not known. Any aggregate figure computed across the graph — total GPUs,
total capacity, provider count — must be accompanied by the number of `unknown`
and `partial` vertices it was computed over, or it must not be produced.

## Snapshots are not consistent cuts

There is no global instant at which the network is observed. Each locally
emitted subgraph carries:

- `snapshot_at` — when that emitter observed its own neighbourhood;
- `version` — a monotonic counter per emitter, so a stale export arriving late
  cannot overwrite a newer one.

A composed graph carries **per-subtree** `snapshot_at`, never a single
network-wide timestamp. Presenting one timestamp for the whole graph asserts a
consistent cut that was never taken, and would make a five-minute-old subtree
indistinguishable from a live one.

Composition resolves two exports of the same vertex by `version`, not by arrival
order and not by wall clock, because clocks across a federation are not
comparable.

## Composition

A consumer merges local exports into a network view under the federation rules
of spec 21:

- **Deduplicate** the same physical service reached by several discovery paths.
  Identity is the stable ID; two paths to one provider are one vertex with two
  in-edges, never two vertices.
- **Mark cycles, do not traverse them.** Spec 21 forbids registration/routing
  cycles, but a topology consumer meets networks that violate their own rules.
  A cycle is recorded as an edge annotated `cycle: true` and traversal stops.
  Composition must terminate on adversarial input; a consumer that loops is
  non-conformant.
- **Control-plane only.** Edges describe authority and presence. Nothing in this
  graph may be used to force inference bytes through the root — spec 21 forbids
  it, and a visualization that implies a hierarchy of data flow invites exactly
  that mistake.
- **Parent loss does not erase a child.** A child that outlives its parent
  remains in the graph, with its `registered_with` edge marked stale rather than
  deleted, per spec 21's identity/history rule.

## Redaction

Spec 21 requires clients to express region and GPU preferences *without learning
private node addresses*, and `specs/16_SECURITY_PRIVACY_TRUST.md` governs what
each viewer may see. A topology export is therefore rendered per viewer.

A redacted vertex is **present but opaque**: its kind, its edges, and its
`horizon` remain visible; its address, hostname and operator identity are
replaced by a stable opaque handle that is consistent within one viewer's
session and not correlatable across viewers.

Omitting redacted vertices entirely is non-conformant. It would silently change
the shape of the graph — a viewer would compute a different topology, not a
less-detailed one, and would under-count capacity without being told.

## Scale

Spec 21 requires intermediate coordinators to return compact candidate sets
rather than have global scheduling scan every provider. Topology export obeys
the same constraint: above a configured fan-out, a coordinator emits a single
`aggregate` vertex standing for its subtree, carrying counts and summed
capacity rather than member vertices.

An `aggregate` is explicitly typed so no consumer mistakes a summary for a leaf.
It carries the `horizon` of the subtree it summarises: an aggregate over a
subtree containing `unknown` vertices is itself not `complete`.

## Export contract

The wire format is `contracts/topology-graph.example.json`, versioned with the
protocol of `specs/02_PROTOCOL_AND_API.md`. The dashboard of
`specs/10_DASHBOARD_PORTAL.md` is a consumer of this contract, not the owner of
it: the graph must be equally consumable by the CLI, by an operator's script,
and by a test.

Rendering is deliberately out of scope. What is in scope is that the contract
carries everything a renderer needs — including the completeness and staleness
fields — so that no renderer has to invent them.

## Conformance

Per `specs/38_EXECUTABLE_EVIDENCE_AND_CONFORMANCE.md`, the rules above are
executable or they are decoration. Required, each failing when the control it
covers is removed:

1. An export whose `unknown` vertices are counted as empty fails.
2. A composed graph presenting a single network-wide timestamp fails.
3. Composition over a graph containing a cycle terminates and marks the cycle.
4. Two discovery paths to one provider compose to one vertex.
5. A redacted export contains no private address **and** the same vertex count
   as the unredacted one.
6. An aggregate over a subtree containing `unknown` is not reported `complete`.
7. Resolution of two exports of one vertex follows `version`, not arrival order.

Each test must be run against a deliberately broken fixture as well as the
canonical one, so that a guard which has silently stopped checking is caught.
