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

GPU vertices reference the inventory and telemetry defined in
`specs/23_GLOBAL_TELEMETRY_BENCHMARKS.md`. A bounded, display-only `configuration`
projection may carry existing authenticated registration and telemetry facts
with their observation times, as defined below. It does not create another
inventory authority and must never drive placement, scheduling or GPU ownership.

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

The canonical HTTP export is `GET /iw/v1/topology`, returning the versioned
v2 contract (`schemaVersion: 2`). Existing API versioning remains unchanged;
the schema version is the topology payload version, not a claim that `/iw/v2`
exists. The monorepo publishes `schemas/json-schema/topology_v2_graph.json`,
generated bindings and `contracts/topology-v2.example.json`.

### Specification defect corrected 2026-09-22

Previously this text named `contracts/topology-graph.example.json` as though it
implemented the graph model above. Inspection of InferWeave commit `8238290`
showed a library-only v1 export using `node`/`child_gateway` and
`gateway_to_node`/`gateway_to_child_gateway`/`node_to_gpu`, without an HTTP
route or federated composition. Treating that example as canonical would
reintroduce incompatible role vocabularies and imply an API that did not exist.
The existing v1 library and schema remain unchanged for current consumers;
v2 implements the canonical roles and edges above. Consumers must check
`schemaVersion` and must not silently interpret v1 as v2.

### Wire fields and default behavior

The envelope contains `schemaVersion`, `rootId`, `vertices`, `edges`, `sources`
and `truncated`. There is no network-wide freshness timestamp. Names are
camelCase on the wire; timestamps are Unix seconds.

- Vertex: `resourceId`, `kind`, `roles`, `horizon`, `snapshotAt`, `version`;
  optional `epoch`, `label`, `address`, `ownerNodeId`, `status`, `detail`,
  `models`, `counts`, `configuration`. `status` is `live`, `stale`, or `unknown`; it does not
  substitute for completeness. `detail` is a bounded generic explanation,
  never an exception/credential/prompt dump. GPU IDs come from registered
  inventory, never from array indices or a guessed worker-to-GPU ratio.
- Edge: `sourceId`, `targetId`, `kind`; optional `stale`, `cycle` booleans.
  `registered_with` runs child to parent; `routes_to` runs parent to child.
  These inverse relations do not by themselves constitute a cycle. Detect
  cycles separately within registration and routing relations.
- Source: `resourceId`, `snapshotAt`, `version`, optional `epoch`. Sources
  record emitter-specific observations. Vertex counters from two unrelated
  emitters are not comparable. Prefer a resource's own authorized emitter
  to a parent's description; otherwise preserve uncertainty.
- Counts: optional `workers`, `gpus`, `vertices`, `unknown`, `partial`.
  Absent counts are unmeasured, not zero. Aggregates with unknown/partial
  members must remain incomplete; counts never invent measured capacity.

A restarting emitter gives its new in-memory counters a cryptographically
random process `epoch`; counters are ordered only within the same epoch.
An authenticated sequential fetch from a registered peer can replace its
previous epoch and invalidate that cached subtree. Concurrent old responses
must not restore a retired epoch. An offline composer presented with two
epochs for the same source rejects the ambiguity; it must not order epochs by
wall clock. A consumer of an older export without `epoch` cannot infer restart
ordering and must retain uncertainty on a counter rollback.

The local exporter automatically uses existing registration, inventory and
telemetry state. It does not need new operator topology configuration or
probe nodes while handling a browser request. Unknown child gateways remain
visible until their authorized graph is available. Stale registration records
remain visible within the bounded observation window; overflow is explicit.

### Display configuration and serving evidence

The operator's 2026-09-22 map inspection could identify registered nodes but
could not see their reported GPU configuration or distinguish models currently
serving from advertised capabilities. The former text's blanket prohibition on
carrying telemetry projections would force a consumer to make separate requests
or leave these facts invisible. This corrects that specification defect without
creating a second inventory source.

Optional vertex `configuration` is a projection of existing authenticated
registration and telemetry, never arbitrary process arguments, environment,
credentials or private backend addresses. Missing fields mean **unknown**, not
zero, an empty inventory or a default hardware model. The camelCase shape is:

- `observedAt`: required configuration observation time, Unix seconds.
- `reportedGpuIds`: optional registered identifiers. Legacy labels can remain
  visible as reported labels; they do not prove physical device identity.
- `gpus`: optional records with required `gpuId`, optional device-specific
  `name`, `vendor`, and canonical `CardMemory` (`totalMb`, `usedMb`, in MiB).
- `deployments`: optional records with required `model`, optional `engine`,
  `backend`, `quantization`, `contextTokens`, `gpuModel`, `gpuCount`, `gpuIds`.
  These are reported configuration facts, not confirmed model residency.
- `servedModels`: optional observed serving model identifiers. Omission is
  unknown; an explicit empty array means the observation reported none.
- `servedModelsEvidence`: optional `node-report` or `engine-model-list`.
- `servedModelsObservedAt`: optional time of the serving observation, Unix seconds.

Bound each configuration to 64 GPU records, 64 reported GPU IDs, 64 deployments
and 256 serving models; each deployment has at most 64 GPU IDs. Identifiers and
model names must be nonblank and at most 512 UTF-8 bytes. Other strings have at
most 256 UTF-8 bytes. Integer values must fit JavaScript's exact nonnegative
integer range (at most 9007199254740991); context token counts, reported GPU
counts and total memory are positive when present, and used memory cannot exceed
total. The schemas reuse `CardMemory`; runtime validation also enforces byte
length and cross-field memory limits that ordinary JSON Schema cannot express.
Existing graph, subtree and heartbeat byte limits still apply; optional
configuration that does not fit is omitted safely, never truncated into a false
measurement or allowed to interrupt inference.

Serving colors require a nonstale node and explicit serving evidence observed
within 90 seconds. A newer configuration or transport receipt never refreshes an
older serving observation. A successful engine-answering node telemetry report
may provide `node-report` evidence, but must not be described as independent
residency verification. Failed engine probes, stale or absent reports and
advertised model capabilities alone cannot establish current serving colors.
Gateway models describe routing availability and do not imply local GPU serving;
gateway vertices remain neutral. Text labels and a model legend accompany colors.

Only facts for the exact observed device may populate its name/vendor: a single
node-wide card label does not describe every GPU on a heterogeneous host.
Visible-device telemetry does not prove exclusive process ownership; GPU IDs
are never invented from ordinal, serving endpoint, worker count or card name.
Existing legacy GPU selections and scheduling identity remain unchanged.
A node may report devices visible to its allocation without exclusively owning
them. Omit uncertain ownership edges rather than manufacturing a physical map.

The local exporter uses cached registration, telemetry and device discovery.
Opening or selecting a map node does not query the node or start another probe.
Masked non-operator exports remove **the entire configuration**, preserving
shape and horizon while withholding private hardware/model details. Composition
and held-link forwarding preserve source observation times and evidence labels.

This optional extension retains topology v2 but older strict typed consumers may
reject enriched vertices. Roll out the updated gateway exporter and its parent
held-link CLI together; omission remains decodable by older peers. Existing GPU
workers continue to register and serve without configuration changes or engine
restarts. Additional per-device names from newer workers require a separate
future worker rollout; until then unreported names remain unknown. The current
release does not authorize changes to GPU placement, engines or worker jobs.

### Authentication, privacy and resource bounds

Use existing credentials. An existing operator authorization may reveal the
identities and addresses it permits. Recognized ordinary inference principals
receive opaque private resource identities and no private addresses, hostnames
or operator labels. Anonymous or unrecognized credentials receive `401`.
A caller's forwarding header or traffic pattern grants no topology permission.

Opaque identity handles use a cryptographic keyed derivation (HMAC-SHA256 or
an equivalent existing primitive) with server-owned secret entropy and viewer
scope. A public session ID and a noncryptographic hash are insufficient.
Root identity remains available for authorized composition; topology shape
itself is intentionally visible under the redaction rules above. This does not
claim graph structure is impossible to correlate.

One browser request reads one server-side snapshot. Server-side collectors
only contact already registered, authorized peer endpoints; never follow URLs
advertised in topology, inference headers or labels. Bound response bytes,
concurrency, depth, vertices, edges, sources and deadlines, reusing pooled
connections (D-025). Local v2 documents have at most 2048 vertices, 4096 edges
and 64 sources. A bounded composition may emit typed aggregates and
`truncated: true`; it may not silently advertise a complete network.

The dashboard in `specs/10_DASHBOARD_PORTAL.md` is a consumer, not the owner,
of this contract. CLI and scripts consume the same versioned payload.

Rendering is deliberately out of scope. What is in scope is that the contract
carries everything a renderer needs — including the completeness and staleness
fields — so that no renderer has to invent them.

## Gateway inventory over an established link

The 2026-09-22 console rollout exposed a transport gap: Hive was registered
and serving over its outbound link, but its descendants remained unknown
because the parent could not dial the local topology HTTP endpoint. An exposed
HTTP contract alone did not make inventory available behind that held link.

A gateway-role peer may attach canonical v2 `topology` to the existing
heartbeat `status`. The frame remains `kind: heartbeat`; this is an optional
additive member, not a new connection, frame kind, credential or operator setting.
Ordinary node roles omit it. Older receivers ignore the optional field and old
heartbeats lacking it decode unchanged. The published `node_status.json` schema
references `TopologyV2Graph` without duplicating its resource vocabulary.

The sender reads its own `/iw/v1/topology` using existing **local** gateway
administrative authority (`IW_ADMIN_SECRET`), never the parent's enrollment
credential or `--admin-secret-file`. Derive the port from the configured backend
and pin this administrative HTTP read to literal `127.0.0.1`; do not dial the
advertised hostname, consult proxies, follow redirects or silently downgrade an
HTTPS backend. Missing local authority or unsupported local access leaves the
inventory unknown while inference continues.

Observation runs asynchronously to the heartbeat/inference loop, with a total
read deadline of two seconds, at most 512 KiB of topology data, pooled local HTTP
connections and a nominal 30-second refresh interval. Each held-link session owns
its cache across reconnects; one session must not inherit another endpoint's
graph. Failed reads do not renew its local cache age. After 90 seconds without a
successful local observation, omit topology until observation succeeds again.
These are conservative resource bounds, not measured fleet performance claims.

Parse and validate the typed v2 graph, remove unnecessary private addresses,
and ensure both the topology payload and **complete encoded heartbeat** fit their
budgets. The existing frame limit is 1 MiB. If other status fields leave too
little room, omit topology and preserve the ordinary heartbeat; never truncate
JSON or rewrite source epochs/versions to fit a changing frame budget.
Malformed, invalid or oversized optional metadata must not terminate a serving
link. Receiver authorization remains tied to the current authenticated
**gateway-role** connection, not to IDs or role claims inside the graph.

This extension is sent on the held link only. Plain HTTP heartbeats retain their
existing small status payload: the site gateway's 64 KiB HTTP body limit is not
raised to accommodate inventory. A deployment with no held link continues to
use authorized HTTP topology discovery where available; lack of reachability
is represented as unknown.

Retransmission does not change graph `snapshotAt`, `epoch` or `version`, and a
receiver replay does not renew observation freshness. Disconnect, expiry or
failed observation leaves previous inventory stale/unknown rather than claiming
an empty fleet. Existing per-viewer redaction applies after authenticated
receipt. This scoped transport extension does not approve unrelated deployment,
scheduling, capacity-controller or fleet-operation gates.

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
8. Configuration wire/schema serialization preserves reported GPU/deployment
   facts, omits unknown fields, and rejects malformed or over-budget enrichment.
9. Masked exports remove configuration, and cloned/composed graphs do not share
   mutable nested configuration state.
10. Fresh engine-answering reports, explicit empty reports, failed probes and
    stale reports remain distinct; advertised capability does not become current
    serving evidence and configuration refresh does not renew serving freshness.
11. Multi-GPU and multi-model rendering preserves reported identity, accessible
    model labels and legend, node expansion and unknown fields without claiming
    exclusive ownership or independently verified residency.

Each test must be run against a deliberately broken fixture as well as the
canonical one, so that a guard which has silently stopped checking is caught.

Automatic gateway identity is generated once beside the deployment's existing
state (outbox deployment directory, or node catalog sibling) and reused after
restart. Addresses/hostnames are not identity. If that store is unavailable,
use a distinct random process identity, explicitly mark the root partial, and
do not claim cross-restart history continuity. An explicit existing gateway ID
continues to take precedence.
