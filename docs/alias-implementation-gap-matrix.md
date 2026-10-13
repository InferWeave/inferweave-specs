# Dynamic model aliases: implementation gap matrix

Audit date: 2026-10-12. Baselines: `inferweave-specs` `549e99f`, Rust
`inferweave` `2ad2de78`, Go `inferweave-gateway` `341d220`. This is a source
inventory for the operator's Dynamic Model Aliases v1.0 handoff, not a claim
that a protocol feature or deployed alias is usable. Paths are repository-relative.
`Implemented` means the cited source exists; proof is stated separately.

Protocol v1 already defines `/inferweave/v1/*` in `specs/45_PROTOCOL_V1.md`
and `specs/49_NATIVE_CONTROL_PLANE_ENDPOINTS.md`; the site-gateway-specific
`/iw/v1/*` namespace in `specs/42_SITE_GATEWAY_CONFORMANCE.md` coexists with
it. OpenAI compatibility remains `/v1/*`. Alias endpoints must specify which
surface owns them and how the Go site gateway consumes or relays them.
Protocol `dynamic_aliases: "1"` already has a
meaning (`specs/45_PROTOCOL_V1.md`); a richer contract requires a negotiated
level instead of silently redefining it. The handoff's v1.0, current protocol
1.1.0 (`VERSION`), feature level, schema version and individual alias revision
are distinct version axes. The Go gateway is a conformant site
gateway under D-001. D-002 currently permits its embedded operator UI for
runtime-family views only, so alias administration needs an explicit, narrow
decision amendment before Go UI work.

| Requirement | State | Source evidence | Planned change / proof owed |
|---|---|---|---|
| Versioned alias object and compatibility | partial | Specs `schemas/v1/model/alias.json` requires only `alias_id`, allows arbitrary `constraints`; Rust `crates/iw-protocol/src/v1/model.rs` has first-class `Alias`; specs `specs/45_PROTOCOL_V1.md` declares `dynamic_aliases: "1"`. | Add negotiated typed managed/dynamic alias definition, immutable revision and owner scope without breaking level 1 fixtures; classify compatibility and update changelog, compatibility matrix and release manifest; schema round-trip and mixed-version tests. |
| Exact model and legacy-name precedence | partial / conflicting | Rust `crates/iw-gateway/src/adaptive.rs` has snapshot/operator/peer alias lookup; `crates/iw-gateway/src/cli.rs` reads `IW_MODEL_ALIASES`; Go `internal/registry/registry.go` implements exact → registered alias → partial group. | Characterize both existing paths; define explicit exact/`alias:`/legacy precedence and reject collisions. Keep exact requests exact. |
| Alias CRUD, publication, rollback, CAS and audit | missing | Specs `openapi/inferweave-v1.yaml` exposes only `GET /aliases`; Rust logical route updates in `crates/iw-gateway/src/adaptive/logical.rs` are in-memory; Go has no canonical alias write API. | Rust authoritative persisted drafts/revisions, validation, RBAC, optimistic preconditions, publish-as-new-revision rollback and audit; Go typed forms only. |
| Capability fidelity and hard constraints | partial | Specs `schemas/v1/model/capabilities.json` distinguishes native/translated/emulated/unsupported/unknown; `specs/00_INVARIANTS.md` makes context, modality, privacy, license and exact deployment hard; Rust logical capability routes exist in `crates/iw-core/src/logical_route.rs`. | Typed request constraints and verified confidence; prove no unknown/stale feature satisfies a hard verified requirement. |
| Context-size aliases | partial | Specs `specs/03_NODE_BOOTSTRAP_DEPLOYMENTS.md` and task `P1-T13A` require alias intent below a deployment ceiling; Rust logical route tests exist. | Characterize production context aliases; preserve ceilings and no silent downgrade. |
| Dynamic candidate evaluation and ranking | partial | Rust `crates/iw-gateway/src/adaptive/logical.rs` supports operator routes, fallbacks and `cap:` queries; `crates/iw-gateway/tests/logical_routes.rs` covers part of this path. | Reuse this router, add typed hard filtering, deterministic weighted policy version, safe metric confidence, bounded candidate explanations and tenant filtering. |
| Side-effect-free resolve/simulate | missing | Specs `specs/02_PROTOCOL_AND_API.md` mentions route preview but defines no alias purity contract; native OpenAPI has no alias resolve route. | Read-only snapshot preview with revision/freshness, no admission, demand, lease, loading or queue effects; state-before/after tests. |
| Admission, retries, stream safety and affinity | partial | Existing Rust adaptive router/admission in `crates/iw-gateway/src/adaptive.rs` and HTTP dispatch in `crates/iw-gateway/src/server.rs`; specs `specs/00_INVARIANTS.md` requires bounded queues, cancellation release and exact hard constraints. | Revalidate alias selection at owner admission, bound pre-stream retries, preserve idempotency/affinity/cancellation and prohibit post-stream replay. |
| Runtime READY generation and hot loading | partial | Rust logical replacement is pending/event-driven in `crates/iw-gateway/src/adaptive/logical.rs`; it observes Serving/timeout but does not itself initiate placement. Existing demand queue handles on-demand requests. | Connect alias demand through existing runtime/rebalancer paths; prove unloaded targets never advertise READY and failed generation is removed. |
| Per-GPU and multi-GPU accounting | partial | Canonical specs `specs/43_GPU_PLACEMENT_HOT_SWAP.md` and protocol GPU-memory contracts exist; current readiness is tracked independently of alias definition. | Consume existing placement-group and memory facts; require atomic invalidation on required GPU loss and no alias-specific rebalancer. |
| Federation envelopes, leases and de-duplication | partial | Specs `specs/45_PROTOCOL_V1.md` requires provenance/TTL/loop rejection; Rust `crates/iw-gateway/src/adaptive.rs` federates current catalog, while logical aliases are added to HTTP model listings separately. | Publish conservative co-occurring alias profiles jointly satisfiable by an eligible target, with context bounds enforced by routing, owner/resource-group identity, expiry/sequence/tombstones; reuse owner lease admission and test several parents. |
| Error reasons and explanations | partial | Specs `contracts/protocol-v1/error-taxonomy.json` has generic reasons; `schemas/v1/errors/error.json` requires code/message/retryability; Rust logical route responses expose some status. | Freeze alias candidate and terminal reason vocabularies, map HTTP/retry semantics, redact unauthorized candidates and provide request trace. |
| Event snapshot/delta consistency | partial | Specs `specs/45_PROTOCOL_V1.md` requires per-source ordering and snapshot recovery, but no alias event namespace; `specs/40_NETWORK_TOPOLOGY_GRAPH.md` rejects a fictional global snapshot cut. | Alias events, cursors, tombstones and gap recovery with per-source generations; bounded browser invalidation. |
| OpenAI compatibility and `/v1/models` | partial / conflicting | Rust `crates/iw-gateway/src/server.rs` lists aliases and rewrites explicit alias bodies; Go `internal/catalog/catalog.go` filters noncanonical legacy aliases, with tests under `cmd/gateway/model_aliases_test.go`. | Characterize both routes; expose authorized published aliases while preserving exact models, SSE/tool/multimodal bytes, status and cancellation. |
| Go gateway alias engine / persistence | duplicated / conflicting | Go `internal/registry/registry.go` routes by worker aliases; `cmd/gateway/legacy_names.go` reads startup `models.json`; `iw.mi_models.aliases` is analytics metadata. | Preserve legacy behavior during shadow parity, then make canonical Rust resolution/admission authoritative for new alias traffic; no second Go alias DB or ranking engine. |
| Go administration and observability UI | missing | Existing Go console and model graph have registered alias edges, but no authoritative alias create/validate/preview/publish/history or routing explorer. | Typed Rust API client; index/detail/editor/simulation/routing/federation views with stale, error, permission and responsive states; UI conformance/visual QA. |
| Authentication and tenant privacy | partial | Canonical specs impose redacted public telemetry and strict content access; current Go edge and Rust gateway each have authentication paths. | Rust-side tenant-scoped CRUD/resolve authorization and explanation redaction; Go forwards validated caller identity via existing mechanism. |
| Migration, flags, shadow parity and rollback | missing | Startup alias files and Go `models.json` currently supply names; no durable published revision or shadow comparison. | Inventory deployed mappings, import only verified compatible definitions, compare shadow decisions, gate traffic by `alias_engine_v1`, retain exact path and rollback. |
| Metrics, traces, load and full acceptance | partial | Existing logical-route and registry tests cover narrow behavior; protocol conformance currently validates a basic alias schema fixture. | Add property/conformance/integration/UI/load/security cases from acceptance IDs 1–29, measure baseline and p95 overhead, collect traces/screenshots; mark each proof `proven` or `owed`. |

## Baseline verification

- `python3 scripts/validate_specs.py` on specs `549e99f`: **passed**, 100 features,
  159 canonical tasks, DAG valid. This validates the existing registry, not the
  proposed alias contract.
- Rust focused baseline: `cargo test -p iw-gateway --test logical_routes
  --test logical_routes_http` on `2ad2de78`: **passed**, 22 logical-route and
  5 HTTP tests. Existing `iw-core` emitted an unrelated `ts-rs` cfg warning.
- Go focused baseline: `go test ./cmd/gateway ./internal/registry
  ./internal/catalog` on `341d220`: **passed**, all three packages.
- Existing canonical aliases task `P5-T22` is `owed`; no row here should be read
  as a completed v1.0 handoff acceptance test.

## Implementation order and authority

1. Freeze a compatibility-preserving protocol contract in this repository,
   including reasons, schemas, fixtures, conformance, and an explicit D-002 Go
   UI exception scoped to the existing site gateway. Keep preview read-only.
2. Add Rust persistence and typed preview around the current logical route
   machinery, then integrate admission, runtime facts and federation under
   existing owner authority. Shadow compare before traffic activation.
3. Add Go typed client, transparent relay and administration views against
   Rust APIs. Remove duplicate selection only after parity proof.
4. Run acceptance tests and measured rollout gates; update each row with PR,
   test and observed deployment evidence or retain `owed` with a reason.

The operator's handoff is a proposed target. Existing decisions/invariants and
live incident evidence remain explicit in this matrix; any changed boundary
must be amended canonically before implementation relies on it.

## Contract audit follow-up (level 2)

- Rust `crates/iw-gateway/src/adaptive/logical.rs:424` builds a model-level candidate projection;
  merged worker capabilities lose per-instance joint feature evidence and lifecycle generation.
  Level-2 schema therefore binds every candidate to instance/generation/deployment/owner facts.
- Rust `crates/iw-gateway/src/client_auth.rs:123` gates existing client routes without native
  `/inferweave/v1` alias coverage. Native alias auth is missing until implementation proves it.
- Go `cmd/gateway/admission_identity.go:140` strips admission identity and the proxy replaces
  authorization. A validated caller-identity mechanism must survive edge relay before writes or
  tenant-scoped alias routing are enabled. A shared service token cannot establish end-user scope.

Spec 54 / IW-ALIAS-001 adds the level-2 contract; schemas and offline fixtures are artifact evidence
only. All implementation scenarios remain owed in `contracts/dynamic-alias-acceptance.json`.

## Runtime producer follow-up — spec 56

The first contract omitted the bounded authenticated producer input needed by A-T05.
`specs/56_RUNTIME_INSTANCE_OBSERVATIONS.md` records source symbols and distinguishes
per-load generation from registration/engine-set counters. The optional report, ordering and
negative conformance artifacts are **implemented as contracts only**; live producer delivery,
qualification, owner-policy binding and admission remain **missing/owed**. The working Rust
`RuntimeInstanceObservation` is a partial producer, not an existing READY alias pathway.
Master acceptance 3, 5, 6, 11–17, 19, 20 and 23 now link to this contract; none is marked proven.
