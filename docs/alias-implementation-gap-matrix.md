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
runtime-family views only at this audit baseline; the merged contract follow-up below
records the subsequent narrow alias administration amendment.

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

### Execution boundary follow-up — spec57

| Requirement | Status | Canonical contract / evidence | Remaining implementation proof |
|---|---|---|---|
| Infer identity differs from management purpose | missing at audit; contract specified | specs/57_ALIAS_EXECUTION_IDENTITY_AND_CLAIMS.md; inference-assertion schema; signed hostile fixtures | Native personal keys/current infer grants and separate Go proof at real HTTP boundary (A-T02/A-T06) |
| One execution through multiple parents | missing at audit; contract specified | execution-claim schema; two-parent and admission-race serial vectors | PostgreSQL unique claim/key mapping, owner/node fencing and crash reconciliation (A-T04/A-T05) |
| Ambiguous dispatch and partial stream do not replay | partial contract in spec54; strengthened in spec57 | DISPATCHED-before-send and no-reopen oracle mutations | Real byte-path/direct-permit failure injection, cancellation, deadline and release (A-T04/A-T08) |

These rows describe contract closure only. Offline conformance is not a running alias engine,
production authentication, shared transactional admission or rollout evidence.

## Progress register — 2026-10-13 UTC

The table above preserves the original source audit. This register links merged changes
verified through repository PR metadata and checked-out source on 2026-10-13; a merge
proves source integration, not activation or a passed master acceptance scenario. The
original table remains the dated baseline, while this register describes subsequent
progress. Rust core stacks remain open; the Go console and transport slices have merged
but remain **partial/inactive**. No master acceptance scenario is promoted to `proven`.

| Area | Merged source evidence | Current proof boundary |
|---|---|---|
| Audit, level-2 contract and D-002 alias UI amendment | Specs [#248](https://github.com/InferWeave/inferweave-specs/pull/248), [#249](https://github.com/InferWeave/inferweave-specs/pull/249) | Contract artifacts implemented; runtime acceptance remains owed. |
| Signed management query and current grant/UI mode contracts | Specs [#252](https://github.com/InferWeave/inferweave-specs/pull/252), [#253](https://github.com/InferWeave/inferweave-specs/pull/253) | Contract artifacts implemented; production identity, permissions and activation remain owed. |
| Generation-bound runtime producer contract | Specs [#254](https://github.com/InferWeave/inferweave-specs/pull/254) | Contract artifacts implemented; live qualification, owner policy and admission remain partial/inactive. |
| Separate inference identity and exclusive execution claims | Specs [#256](https://github.com/InferWeave/inferweave-specs/pull/256) | Contract artifacts implemented; runtime concurrency, fencing and fault injection remain owed. |
| Existing alias behavior characterization | Rust [#866](https://github.com/InferWeave/inferweave/pull/866), Go [#466](https://github.com/metabolomics-us/inferweave-gateway/pull/466) | Existing behavior tests merged; they do not prove new dynamic alias dispatch. |
| Go typed signed client and management adapter | Go [#468](https://github.com/metabolomics-us/inferweave-gateway/pull/468), [#469](https://github.com/metabolomics-us/inferweave-gateway/pull/469); `cmd/gateway/alias_control_client.go`, `alias_control_handlers.go`, `alias_edge_signer.go` | Partial: client/adapter source merged, default off; live Rust integration and production activation remain owed. |
| Bounded alias list continuation | Specs [#257](https://github.com/InferWeave/inferweave-specs/pull/257); spec54 pagination clarification | Contract artifacts implemented; empty filtered pages retain continuation. Rust API implementation remains open in #872. |
| Alias administration console | Go [#470](https://github.com/metabolomics-us/inferweave-gateway/pull/470), merge `248ac870`; `web/src/console/aliases.ts`, `aliasApi.ts`, `aliasTypes.ts` | Partial: index/detail/editor, simulation, publication/history, candidate evidence and routing/federation reads merged. `off`/`read_only`/`full` and Rust grants constrain controls. Browser fixtures and screenshots establish UI behavior only; live Rust journeys, structured routing timelines, metrics and event resume remain owed. |
| Inference signer and transparent client | Go [#474](https://github.com/metabolomics-us/inferweave-gateway/pull/474), [#476](https://github.com/metabolomics-us/inferweave-gateway/pull/476), latter merge `716dee98`; `cmd/gateway/alias_inference_signer.go`, `alias_inference_client.go` | Partial: unmounted source; shared MIME/header fixtures align parser behavior with Rust and bind exact signed bytes. Specs [#258](https://github.com/InferWeave/inferweave-specs/pull/258) defines this subset. Real authenticated relay, claims, admission and execution remain owed. |
| Owner-to-node permit and consumption protocol | Specs [#259](https://github.com/InferWeave/inferweave-specs/pull/259), merge `e5767173`; spec57 §5.1 | Contract artifacts implemented: protected executable Link request, separately authenticated consume request/ack and durable INTENT → consumption → SPENT → final revalidation order. Runtime implementation and real crash/transport fault injection remain owed. Initial protected JSON does not qualify SSE, multipart, chunking or direct/proxy execution. |
| Operator-local NodeProxy credential API | Rust [#884](https://github.com/InferWeave/inferweave/pull/884), merge `aec7dd33`; `crates/iw-cli/src/link_engine.rs::HttpEngine::with_local_proxy_bearer` | Partial: opt-in builder restricts credential delivery to numeric loopback and isolates it from caller data. Startup wiring, full serving-path verification, admission fencing and live use remain missing. Merge occurred while CI was pending; no CI pass or runtime activation is inferred. |

Spec 54 now makes empty filtered pages with a continuation explicit. The existing
`schemas/v1/aliases/contract.json` list schema already permits zero items and an optional
nonempty `next_cursor`, so this correction adds no schema version or alternate response
shape. Runtime proof is **owed**: an empty intermediate page must reach a later matching
alias, each scan must advance under a bounded budget, and changed authorization/snapshot
must invalidate continuation. Acceptance 20 and 27 and tasks A-T02/A-T06/A-T07/A-T08
retain their existing owed status.

### Open Rust implementation stack

PR state and head references below were checked for this update. Stacked branches must be
rebased/retargeted in dependency order after their base merges. Paths identify actual source
and tests at the cited heads, not code asserted to be on `main`.

| Requirement / task | State and source | Existing component verification entry points | Remaining gate |
|---|---|---|---|
| Typed level-2 contract, A-T01 | partial; [#868](https://github.com/InferWeave/inferweave/pull/868), `8cfb31d8`; `crates/iw-protocol/src/v1/aliases.rs::{AliasDefinition, AliasCandidate, AliasResolution, require_dynamic_aliases}` | `crates/iw-protocol/tests/dynamic_aliases.rs`; `cargo test -p iw-protocol` | Merge, mixed-version live behavior and downstream activation. |
| Durable definitions/revisions/audit, A-T02 | partial; [#869](https://github.com/InferWeave/inferweave/pull/869), `0517fdda`; `crates/iw-storage/src/aliases.rs::{AliasActor, AliasMutation, AliasWrite}` | `crates/iw-storage/tests/aliases.rs`, including live PostgreSQL integration recorded in PR | Production persistence/migration and current authorized identity at mounted endpoints. |
| Management identity/replay, A-T02 | partial; [#870](https://github.com/InferWeave/inferweave/pull/870), `ffbcaec8`; `crates/iw-gateway/src/alias_edge_assertion.rs` and its `tests.rs` | Signed-vector, HTTP and durable replay tests recorded in PR | Actual edge identity mapping, native current grants and live authorization. |
| Pure eligibility/preview, A-T03 | partial; [#871](https://github.com/InferWeave/inferweave/pull/871), `57e9780c`; `crates/iw-core/src/alias_resolution.rs`, `crates/iw-gateway/src/adaptive/alias_inventory.rs::AdaptiveAliasInventory` | Evaluator tests; `alias_inventory_unknown_generation_never_becomes_ready_or_grants_tenant_policy`, `alias_inventory_peer_aggregates_cannot_duplicate_physical_capacity` | Trusted qualification/policy snapshot and owner admission; previews do not reserve capacity. |
| Default-off management API, A-T02/A-T03 | partial; [#872](https://github.com/InferWeave/inferweave/pull/872), `b2a55cb6`; `crates/iw-gateway/src/alias_service.rs::AliasService` and `alias_service/tests.rs` | Alias HTTP/service tests and PostgreSQL evidence in PR | Live authenticated UI/API journeys; returned rows use keyset bounds, but owner-scope revision aggregation still scans under a timeout and needs scale evidence. |
| Exclusive execution claims, A-T04 | partial; [#874](https://github.com/InferWeave/inferweave/pull/874), `5317b10a`; `crates/iw-storage/src/execution_claim.rs` and `execution_claim/tests.rs` | Live storage claim/race/rollback tests recorded in PR | Production caller, owner reservation, node consumption and restart reconciliation. |
| Atomic owner-attempt journal, A-T04 | partial; [#882](https://github.com/InferWeave/inferweave/pull/882), `b5361830`; `crates/iw-storage/src/owner_attempt.rs::{OwnerAttemptBinding, OwnerAttemptState}` | `crates/iw-storage/tests/owner_attempt.rs`; concurrent-parent, immutable binding, retirement, transaction failure and generic-mutation bypass regressions | Authenticate real owner receipts; integrate existing adaptive allocator and durable charges; verify backend stop before release. A journal is not admission. |
| Runtime incarnation lineage, A-T05 | partial; [#875](https://github.com/InferWeave/inferweave/pull/875), `e1342420`; existing controller/runtime adapter and alias inventory | `adaptive_controller`, `node_runtime`, `runtime_adapter`, `alias_inventory` suites; legacy exact-route and receive-time regressions | Full trusted verifier and owner policy. The legacy-journal and future-observation fixes must survive stack integration. |
| Narrow runtime probe qualification, A-T05 | partial; [#878](https://github.com/InferWeave/inferweave/pull/878), `febfc119`; `crates/iw-core/tests/runtime_probe_qualification.rs` | Probe incarnation/freshness tests recorded in PR | Backend probe evidence cannot establish verified tools, privacy, full serving path or READY alias capacity. |
| Authenticated runtime report ingestion, A-T05 | partial; [#879](https://github.com/InferWeave/inferweave/pull/879), `b70287e6`; `crates/iw-gateway/src/node_control/runtime_observations.rs`, `adaptive/alias_observations.rs` | Current-registration, sequence/expiry/tombstone and duplicate-key rejection tests; exact-route compatibility regressions | Trusted independent qualification, current owner policy and physical ownership; node references are not authority. |
| Physical placement binding, A-T05 | partial; [#883](https://github.com/InferWeave/inferweave/pull/883), `970269d0`; runtime observation/alias inventory placement fields | Placement identity, complete GPU set and duplicate-instance regressions recorded in PR | Real allocation loss, atomic multi-GPU invalidation and admission across current owner epochs. |

The Go alias work listed above has merged; no separate open Go alias implementation PR was
present at this audit. Other open Go work is outside this progress register. Existing legacy
Go alias selection still requires characterized shadow parity and controlled migration;
merging typed clients does not remove the duplicated authority identified in the baseline.

### Unmounted source and execution blockers

Additional work exists on the shared Rust implementation branch, but is not represented as
merged or production-ready:

- `alias_inference_assertion.rs` and its tests bind a separate infer-purpose proof to exact
  request bytes; `ebc195f3`/`c750d31d` align transport and correlation semantics with Go #476.
- The strict HTTP parser (`b35ec482`/`25051e19`) rejects duplicate and disguised Unicode
  security fields before legacy map collapse. Socket regressions exist; ingress mounting and
  verification before legacy completions translation remain owed.
- `alias_inference_grants.rs::FileInferenceGrants` (`a11942b7`, `d4e729e1`, `8e5bad6c`)
  reads current native/admission grants through private, pinned, no-follow/nonblocking file
  descriptors. Secure loading is restricted to Linux x86_64 and fails closed elsewhere.
  FIFO/symlink/permission regressions exist. Authenticated identity, trusted clock, replay,
  owner revalidation and candidate disclosure still need integration.

These modules do not satisfy owner-atomic admission. The existing adaptive router must
choose and reserve the same qualified instance under its current accounting authority,
with durable claim/attempt fences and restart reconciliation. No preview selection may be
sent through an unrestricted fallback router. The node must implement negotiated protected
requests, authenticated asynchronous consumption, durable claim-wide start fencing and
final generation/deadline/cancellation checks before invoking a backend. These controls are
**missing/owed**, despite the merged spec57 contract.

A trustworthy runtime verifier must cover the authorized serving path, watchdog/incarnation,
owner policy, credentials and admission fence. The merged local bearer builder is one
prerequisite. Current backend health/probe reports and Farm qualification files do not
establish this verifier; Hive/Farm Apptainer also require equivalent allocation fences.
No production alias flag is enabled by the work in this register.

### Live Farm/Hive incident evidence and limits

These are bounded observations from the supervisor's 2026-10-13 rollout record, separately
attributed from this documentation audit; this change does not rerun SSH probes or deploy.
The local continuity record is `INFERWEAVE_AGENT_HANDOFF.md` in the operator workspace;
PRs below hold the shareable source and rollout evidence.

- **Farm gateway registration repaired:** specs [#250](https://github.com/InferWeave/inferweave-specs/pull/250)
  and Rust [#867](https://github.com/InferWeave/inferweave/pull/867). Deployed source
  `5b4a08cb` permits model-less gateway registration and explicit empty queue-advertisement
  allowlists. Fry topology observed a fresh `node_iw-farm` gateway; Farm workers were absent
  while GPU jobs waited for Slurm priority. This proves gateway visibility, not READY model
  capacity or inference. #867 merged into `feat/farm-throughput`, not `main`; its failed CI
  pipelines lack accessible stage logs, so local tests/live registration do not close CI triage.
- **Hive gateway and providers observed:** a normal parent peer and hot DeepSeek/Qwen
  advertisements were present in the later supervisor observation. Existing worker GPU
  display-name IDs still differed from persistent residency identities, leaving placement
  unresolved. Advertisement presence is not an inference or qualified-alias proof.
  [#876](https://github.com/InferWeave/inferweave/pull/876) fixes synthetic-alias bootstrap
  selection; [#877](https://github.com/InferWeave/inferweave/pull/877) binds allocation-visible
  GPU IDs and fences live-session loss. Both remain open. Combined release `5e775122` is
  staged only; live gateway remains on `2ad2de78`. Activation must coordinate the existing
  pull-cycle desired revision, parent identity and recovery steps, preserve current model
  service, and retain rollback artifacts. Staging tests do not prove production rollout.

### Verification scope and remaining acceptance

This documentation update reruns specs validation/self-test, the spec57 smoke test and
offline conformance. Rust/Go test names and PR links above locate component evidence;
those suites and live deployments are not rerun by this documentation-only change. The
reported CI state is a snapshot, not a substitute for checking current required checks.
Rust [#880](https://github.com/InferWeave/inferweave/pull/880) merged deterministic placement
and frame test repairs; it does not establish the cause of previously inaccessible CI failures.

Master acceptance **1–29 remains owed as full-system acceptance** in
`contracts/dynamic-alias-acceptance.json`. Existing component tests do not close the broader
scenario. Remaining work includes current grants and disclosure enforcement; real owner
and node fencing; qualified runtime/hot-load/rebalance integration; opt-in federation,
shared-capacity leases and preemption; snapshot resume/gap recovery; exact-safe OpenAI
alias traffic and stream/cancellation fidelity; live administration/rollback journeys;
measured routing overhead, load and fault injection; migration/shadow parity and rollout.
`OPEN_GATES.md` remains authoritative for activation. This progress update changes no gate,
contract, feature flag or production state.
