# Audit part: Go gateway authority + existing UI + API/SDK/CI

Read-only audit, 2026-10-16. Repos: inferweave-gateway @ fb5310d (2026-10-15), inferweave @ 7171259 (apps/web last touched a142f83), inferweave-specs.
Status vocabulary: complete / partial / broken / missing / duplicated / unknown (unknown != missing).
Paths are relative to /home/user/inferweave-gateway unless prefixed `iw:` (/home/user/inferweave).
Method: static read of package docs, signatures and wiring in cmd/gateway; no tests or builds run.

## 1. Authority classification (requirement: 02-ARCHITECTURE.md:2 "Go gateway only UI, edge auth and transparent relay, no independent model routing/placement")

AGENTS.md/CONTRACT.md describe the gateway as itself the placement, pool and Slurm-acquire authority (AGENTS.md "Scope boundaries"; R1..R14). That is the root conflict with the unified requirement.

| Package | Last SHA | Class | Evidence |
|---|---|---|---|
| internal/placement | 70716b4 | **duplicated authority** | `Solve(d Demand, nodes []Node, size Sizer)` placement.go:126 derives workers/slots/ctx/cards from live Slurm node state; doc :1-7 says "turns demand into a resource shape". Rust owns placement (spec 43 "second scheduler or rebalancer" forbidden, 43:28). |
| internal/capacityplan | 70716b4 | **duplicated authority** | `Planner.Plan` capacityplan.go:228 writes desired replicas into pool; `SlurmNodes` capacityplan/nodes.go:19 shells `sinfo`. Wired: cmd/gateway/main.go:217-224, 2508-2531, 3294-3295; HTTP `POST/GET/DELETE /v1/capacity/demand` cmd/gateway/demand.go:68,173-194,290. Nil when SlurmAcquirer (main.go:2538-2545 comment), so partly dormant. |
| internal/scaling | 70716b4 | **duplicated authority (shadow only)** | Pure retune/add-worker decision, controller.go:1-15; `FitFromPlacement` fit.go:9. Wired shadow-only behind `IW_SCALING_SHADOW=1`, never submits (cmd/gateway/scaling_shadow.go:3-12); exposed `GET /v1/capacity/scaling`. Risk low today; must not be promoted. |
| internal/pool | 70716b4 | **duplicated authority** | Desired-vs-observed reconcile, acquires and releases Slurm jobs: `Reconcile` pool.go:221; only caller `warmFloorOnce` cmd/gateway/main.go:3274-3299; `SetDesired` main.go:858. |
| internal/lifecycle | 70716b4 | **duplicated authority** | Warmup/Release/ReapIdle (lifecycle.go:157,306,339); `Reapable = Tier==burst` :149. Public `POST/GET/DELETE /v1/warmup`. Decides idle release of Slurm jobs. |
| internal/acquire (adjacent) | e0aeb79 | duplicated authority | Calls `scale/request-capacity.sh`; AGENTS.md "shells out to inferweave-slurm". Not in the asked list but the actuator for pool/lifecycle. |
| internal/capacity | 70716b4 | duplicated authority (data) | Checked-in per-model footprint record capacity.json; `Footprint.Plan` used by planWarmupRequest cmd/gateway/capacity_admission.go:48-62; refuses warmups. Sizing authority belongs to Rust ledger (03-RESOURCE-LEDGER). |
| internal/cardvram | 70716b4 | duplicated authority (data) | Remembers per-node card VRAM from worker reports to feed placement (cardvram.go:1-20); cmd/gateway/main.go:143. Exists only to serve Go placement. |
| internal/runtimefamily | 5603018 | **duplicated authority (classification)** | `Classifier.Classify(modality,id)` runtimefamily.go:55 maps model id to family and builds VRAM-by-component and "placement-selection reason" (doc :1-6). Used by native (/inferweave/v1/models, /runtimes) and main.go:1463. Rust spec 48 is authority; should be a relay of Rust's family. |
| internal/gpumemory | 70716b4 | **transparent relay / decoder** | Doc types.go:6-15: decoder, validator, de-duplicating merge; "never computes safe-schedulable capacity... only ever makes it LESS certain". Matches spec 46 (no second calculation). Reuse as is. |
| internal/registry | ec2b3b7 | transparent store (partial authority) | Liveness/TTL worker table (doc.go:1-20), `capacity.go`, `drain.go`, `gpu_count.go`. It is the gateway's "only source of truth for who can serve model X" (doc.go:3-8) which is a competing source of truth to Rust, not a relay. Classify: state mirror, consolidate under Rust. |
| internal/proxy | a059441 | **mixed: relay + duplicated routing** | Relay: SSE streaming, X-Request-Id, `retargetModel` retarget.go:32. Duplicated: worker choice `RegistryPicker.Pick` proxy.go:1028, `PickAvailable*` picker_available.go:132-174, best-fit packing `selectPacked` picker_pack.go:58 ("pack the most loaded worker with free slot"), capability filter `eligibleWorkers` picker_available.go:398, affinity :92-130, local slot reservations :288, and 429 vs warmup logic. Independent routing in the data path. |
| internal/link | c83c429 | **transparent relay** | Outbound-dialled worker link transport (acceptor/frame/chunk/http_json); spec 59/63 data path. No model choice. Reuse. |
| internal/nodecontrol | 4261be8 | admin + partial duplicate | Enrolment/approval/proof/telemetry (approval.go:38-500, admission.go). Admin: tokenless-node approve/reject. Duplicate risk: `foldAliases` admission.go:412 folds alias workers and `ChildReport` budgets (admission.go:344); admission budgets are a local admission authority. |
| internal/native | e6405ef | admin/read projection with duplicated derivation | Doc native.go:1-12: "read-only projection of catalogue and runtime-family registry; performs no inference, never schedules". Derives family/selection_reason locally via runtimefamily. Also jobs/pipeline dispatch (dispatch.go, jobs.go, pipeline.go; 1903 LOC) which is a second durable-job layer (spec 51/52 Rust). |
| internal/catalog | c1c1943 | derived view | `Model.State` hot/warm/cold derived from registry (R9); alias folding. Not requested but part of the same set. |

Other independent-authority findings in cmd/gateway:
- Admission queue/priority/fairshare: cmd/gateway/admission*.go (many files) is a local scheduler for who gets a slot. Rust has `/iw/v1/admission` (iw: crates/iw-gateway). Duplicated authority, status partial (Go still serving traffic; Rust parity unproven).
- Alias resolution: NOT duplicated. Aliases are relayed to Rust through signed edge client (alias_control_client.go, alias_control_handlers.go:117-123, `IW_ALIAS_CONTROL_URL` :57-62, last SHA 8bc3015). alias_inference_client.go:21 states "deliberately not wired into production route setup". UI aliasTree.ts:1-4 "No eligibility, ranking, fit or availability is derived". Status: complete relay; decision reuse. Residual: `legacy_names.go` rename table (loadModelNames :34, `legacyNamePicker.Pick` :136) is a local name->canonical resolver, classified duplicated (static, legacy), keep until Rust parity.
- Rebalancing/hot-swap: no Go rebalancer found (spec 43 hot-swap). gpumemory deliberately avoids it. Status: absent in Go (good). `iw-drain` and `drain.go` in cmd/gateway are operator drain and not a rebalancer: unknown depth, not audited.

Summary decision: relay = link, gpumemory, alias client; admin = nodecontrol approvals, keys/oidc/apikey; duplicated = placement, capacityplan, scaling, pool, lifecycle, acquire, capacity, cardvram, runtimefamily, proxy picker, admission. Do not delete until Rust parity (02-ARCHITECTURE.md:2 "Do not remove Go behavior until Rust parity proven"); gate behind a flag and make read-only.

Risk: HIGH. Two live control loops (Go `warmFloorOnce` + `/v1/capacity/demand` + `/v1/warmup`, and Rust rebalancer) can both acquire/release GPUs. Go reconcile runs always (main.go:863-869 "Safe to run always").

## 2. Existing UI inventory

### 2a. Gateway web/ (embedded, esbuild TS, no framework). Last SHA d20be9a (2026-10-15). Delivered as committed dist cmd/gateway/web/dist (Makefile web-build; bundle parity CI).
- Pages (console.html:33-145 sections): overview, models, aliases, model-performance, model-detail, model-diagnosis, usage(+user/key/model), keys, cluster/hardware, topology, model-map, gpu-memory, activity, traffic, model-responses, gateway/{id}, routing, nodes. Portal: quickstart/keys/usage (portal/*.ts).
- Nav: left rail `#nav` with hash routing, groups, collapse, skip link, aria-current, arrow-key tree (web/src/shared/nav.ts:12-129). Operator-only Routing/Nodes (console.html:25-26).
- Design tokens: CSS variables in web/src/shared/theme.css:4-64+ (--bg, --panel, --accent #022851, --gold, --ok, --warn, --focus, --chart-1..6, outcome colors); 1507 lines; dark mode via theme.ts (44 lines). Status complete. Decision reuse (spec 58: extend, never replace).
- API client: web/src/shared/api.ts (226 LOC): `getJSON` with cache, in-flight dedupe, timeout, AuthError/HTTPError, `poll`, `panelPoll`, `preserveView`, `setPanelState`, `panelProvenance`, pause/visibility. Same-origin cookies; hand-written types per page (not generated). Status complete for gateway endpoints; no generated Rust types (partial vs requirement "UI only calls Rust typed APIs").
- Event stream: web/src/console/stream.ts: SSE `GET /console/api/stream`, probe-then-EventSource, backoff 1s..30s, heartbeat staleness watchdog, drops counted (stream.ts:1-80). Events: `request`, `admission`, `heartbeat` only. Alias control also registers `/console/api/events` (alias_control_handlers.go:119) relayed from Rust. Status partial; no resource/deployment/lease events.
- Endpoints consumed (grep of getJSON/fetch): /console/api/{me, fleet, cluster, topology, gpu-memory, model-graph, model-status, model-stats, models, queue, saturation, usage, ladder, measurements, activity, traffic, traffic/models, traffic/classification, model-inflight(+history), model-diagnostics/*, gateway/{id}, nodes/pending, autoscaler, livetest, aliases*, alias-capabilities, federation/alias-advertisements, requests/{id}/routing, web-vitals, stream}; mutations POST /v1/routing/enable|disable, /v1/node/approve|reject, /keys.

Feature matrix against 07-UI-OBSERVABILITY.md:3 (grep/read of web/src; "present" = a page or panel reads it):

| Required view | Status | Evidence / gap | Decision |
|---|---|---|---|
| Fleet GPU/VRAM utilization | partial | gpuMemory.ts:1-40 (physical total/used/free, logical, safeSchedulable, pressure); hardware.ts:50-54 VRAM in use | extend |
| Fleet CPU utilization / RAM | partial | Only inventory: hardwareModel.ts:109-110 `cpu`, `cpu_threads`, `mem_bytes` (:465); no utilization, allocatable/reserved/free | extend |
| Unified memory (APU/Apple) | missing | zero matches for "unified" in web/src and internal Go (grep) | new (after Rust ledger API) |
| Allocatable/reserved/free breakdown | partial | gpuMemory shows logical reservations vs physical separately (gpuMemory.ts:9-12); no CPU/RAM | extend |
| Per-node topology | partial | topology.ts (graph of nodes/GPUs, staleness via graphTree.ts), hardwareTree.ts, model-map | reuse |
| NUMA | missing | no "numa" match in web/src or gateway Go | new |
| Runtime profile / execution mode | partial | runtime family shown (graphTree.ts, models.ts, catalogViews.ts); "execution mode" no match | extend |
| Deployment stages | missing | no staging/stage UI; model-status.ts shows per-model status only | new |
| Federation approvals | partial | nodes.ts:1-20 pending/approved tokenless nodes, approve/reject/revoke -> /v1/node/*; this is node-enrolment, not spec 62 hosting-request approval | extend (Rust: iw: provision_operator.rs `/iw/v1/provision/operator/approvals|approve|reject|policy|status`) |
| Federation leases | missing | no lease UI ("lease" hits are substrings of "release") | new |
| Slurm wait reasons | missing | no match for pending reason/squeue in web/src; autoscaler panel exists (`/console/api/autoscaler`, autoscaler_status.go) | new, source from Rust |
| Placement/fallback decision history | partial | routing explain `GET /console/api/routing/explain` (main.go:1523), requests/{id}/routing (alias relay), modelDiagnosis.ts, aliasTree.ts unmet reasons, admission decisions in stream. No history of placement decisions; Rust has `/iw/v1/profiles/decisions` (unconsumed by Go) | extend |
| Benchmark evidence | missing | no "benchmark" in web/src; livetest.ts and measurements.ts only; apps/web has /benchmarks | new/consolidate |
| Throughput / TTFT | partial | livetest.ts (ttft), model-stats, measurements, prefill/decode tps in stream events | extend |
| Input/output/cached tokens | partial | models.ts, gatewayDetail.ts ("cached"), usage pages, stream prompt/completion tokens | extend |
| Queue time / queue metrics | complete | queue.ts, saturation.ts, model_diagnostics.ts queue, admission events | reuse |
| Stale/disconnected state | complete/partial | stale handling across ~20 files (api.ts, gpuMemory.ts "Unknown, unsupported, stale... are words, never 0", graphTree ageWords/staleSuffix, stream.ts watchdog, fleet/topology disconnected) | reuse |
| Privacy redaction | partial | gpuMemory.ts/hardwareModel.ts redact notes; modelDiagnosis.ts; textContent-only rendering (aliasTree.ts:1-4). No central redaction policy module. | extend |
| Accessibility | partial | skip link, aria-current, focus mgmt (nav.ts), docs/accessibility/console.md, web/tools/accessibility-check.mjs (WCAG 2.2 AA via Playwright + optional axe) | reuse |
| Responsive | partial | gpu-memory-check 320px/1280px screenshots (gpu-memory-check.mjs:195-200), layout-check.mjs | reuse |
| Screenshot regression | partial/weak | screenshots are written to /tmp or SCREENSHOT_DIR (gpu-memory-check.mjs:195; navigation-usage-check.mjs:104-125); no baseline images or diff (grep toMatchSnapshot none) | extend |

### 2b. inferweave apps/web (Next.js 16/React 19, public dashboard). Last SHA a142f83.
- Routes: / capacity orchestration models gpus nodes system-one watchdog benchmarks explorer contributions status docs about connect play (components/shell/routes.ts:12-27; app/*/page.tsx).
- Tokens: `presentation/tokens.ts` minimal (canvas/ink/muted/accent/danger) vs gateway's much richer theme.css: tokens are NOT shared across the two UIs. Decision: consolidate toward gateway theme.css values (spec 58: extend the existing gateway UI, no second frontend).
- API client: client/api.ts is generated-typed (`API_OPERATIONS` from iw: generated/typescript/index.ts, 1290 lines; @inferweave/bindings tarball). Paths: /v1/models, /api/v1/nodes, /api/v1/deployments, /api/v1/routes/preview, /api/v1/benchmarks/profiles, /api/v1/snapshots, /iw/v1/topology, /v1/systemone*, /iw/v1/routes*, /v1/admin/routes*. No auth by default (client/api.ts header: no token supplied while security gate BLOCKED).
- Fixtures drive most pages (client/*-fixtures.ts, 17 files): many pages are fixture-backed. Status of live wiring: unknown per page; `server-data.ts` and `server/orchestration.ts` fetch live data for some.
- Freshness: presentation/freshness.ts STALE_AFTER_MS 30000, `fresh|stale|unknown` (spec 10 invariant 13). Privacy: presentation/policy.ts + denylist.ts (empty list) + docs/presentation-policy.md.
- Tests: vitest, 17 test files in tests/ (shell.smoke, dashboard, capacity, gpus, nodes, benchmarks, watchdog, system-one, orchestration, client-contract, presentation-policy...). jsdom component tests; no screenshot tests. CI: iw: .woodpecker/rust.yaml:277-289 `web` step (tsc + vitest).
- Present in apps/web but absent in gateway UI: benchmarks page, orchestration page, watchdog, contributions, system-one. Absent in both: NUMA, unified memory, Slurm wait reasons, leases, deployment stages.
- Decision: the two UIs overlap (nodes, gpus, capacity, models). Per spec 58 and 07-UI-OBSERVABILITY.md:1 "Extend current gateway UI, never replace", build new views in gateway web/ consuming Rust typed APIs through the gateway read adapter; apps/web stays the public surface. Reuse apps/web `API_OPERATIONS` generated types as the contract source for the gateway TS (currently hand-copied wire types, e.g. gpuMemory.ts:15-40).

## 3. API surface, SDKs, CI, tests

### 3a. Gateway endpoints vs Rust typed APIs
- Go-only console API: ~40 `/console/api/*` routes (main.go mux list). These are Go-composed views (cluster, fleet, model-status, ladder, traffic, saturation) built from the Go registry. Status: partial-duplicate; they should become adapters over Rust.
- Rust routes in iw: crates/iw-gateway/src include `/iw/v1/{admission,autoscaler,demand,federation/*,gpu-memory,model-intelligence,occupancy,profiles,profiles/decisions,provision,provision/operator/*,routes,routes/events,topology}` and `/inferweave/v1/{aliases*,alias-capabilities,capacity,catalog/models,events,events/stream,features,health,heartbeat,jobs,models,protocol,registration,requests/,topology,federation/alias-advertisements}`.
- Gateway consumes from Rust today: aliases, alias-capabilities, catalog/models, requests/{id}/routing, federation/alias-advertisements, events (alias_control_handlers.go:119 via signed edge client, SHA 8bc3015, 84a6dd8). gpu-memory protocol decoded (gpumemory, console `GET /console/api/gpu-memory`).
- NOT consumed by gateway (grep for iw/v1/provision|profiles|federation|occupancy|demand in cmd, internal, web/src: no hits): provision/operator approvals, profiles/decisions, occupancy, demand, federation snapshot/enrollments. These are the sources for the missing UI views. Status: missing in gateway; Rust side exists (status of Rust handlers: partial/unknown, not audited here).
- Gateway serves a Go version of protocol endpoints too: `/inferweave/v1/{protocol,capabilities,models,runtimes,jobs}` (internal/native) and `/iw/v1/{capacity,dashboard,topology,warmup,workers,autoscaler/status}` duplicates `/v1/*` aliases. Duplicated authority against Rust `/inferweave/v1/*`.

### 3b. SDKs
- No SDK repos or dirs found (find across /home/user depth 3; no hits outside vendored google-cloud-sdk). Specs 01_REPOSITORIES_AND_OWNERSHIP.md contains no sdk entry. Generated clients exist only as iw: generated/typescript (bindings 0.1.0; README says generated by `cargo run -p schema-gen`, CI rejects drift) and iw: generated/rust. Gateway has no generated client (hand-written types). Status: SDKs unknown (not in checked-out repos), generated bindings complete for the OpenAPI subset (no /iw/v1/provision, /profiles, /occupancy in API_OPERATIONS list read at index.ts operations table: partial).

### 3c. CI and test layout
- Gateway: .woodpecker.yml (138 lines) steps: checkout, gates (ops/ci/woodpecker-gates.sh: gofmt -s, vet, report-failure self-test, release self-tests, go build, go test -count=1 -timeout 10m, -race 20m), release (CGO off, publishes dist/inferweave-gateway), bundle-parity (ops/ci/woodpecker-bundle-parity.sh:39-75: npm ci, `npm run check`, `npm run build`, fail if committed dist differs). Makefile: fmt vet test build. TeamCity deleted 2026-09-24 (gates.sh header).
- Go tests: 469 *_test.go files (excluding vendor), table-driven, no network (AGENTS.md); acceptance/ (10 files) cross-package; per-package tests.
- Web tests: web/tools/*.mjs, 41 Playwright (Chrome) scripts, run by hand (`node tools/accessibility-check.mjs`, docs/accessibility/console.md:80). Not in .woodpecker.yml or bundle-parity (grep: only tsc + build). Status of UI behaviour tests in CI: **missing** (they exist, un-gated). Go tests reference web fixtures (cmd/gateway/gpu_memory_golden_test.go:16-21 writes/reads web/tools/gpu-memory-fixture.json), so contract fixture sharing is real.
- apps/web: vitest 17 files; CI in Rust pipeline .woodpecker/rust.yaml:289 `web`.
- Rust conformance: iw: conformance/, crates/conformance; spec fixtures in inferweave-specs/{conformance,fixtures,contracts}. Gateway has golden fixtures captured from running Rust gateway (nodecontrol doc :5-9; commit 54c5b42 "Rust contract example ... decodes and validates here").

## 4. Decisions and risks

| Item | Decision | Risk |
|---|---|---|
| Go placement/capacityplan/pool/lifecycle/acquire/scaling | consolidate: flag off by default, then remove after Rust parity; keep scaling shadow read-only | High: dual actuators on Slurm |
| proxy picker | extend proxy to honor Rust-issued route decision (iw: `/iw/v1/routes`) and keep picker as fallback during shadow/canary | High: data path, live traffic |
| runtimefamily/native/capacity record | consolidate onto Rust spec 48/45 responses | Medium |
| gpumemory, link, alias client | reuse | Low |
| nodecontrol approvals | reuse UI; extend to provision approvals/leases from Rust | Medium (two approval notions: node enrolment vs spec 62 hosting) |
| Gateway web theme/nav/api/stream | reuse; add pages as new sections via nav.ts groups (data-sections pattern) | Low |
| apps/web tokens | consolidate to gateway theme.css tokens | Low |
| New views (CPU/RAM/unified, NUMA, stages, leases, wait reasons, benchmark evidence, decision history) | new, on Rust typed APIs only; add event kinds to SSE via Rust events stream | Medium: Rust API availability unverified |
| Playwright web/tools | extend: add baseline screenshot diff and wire into CI; currently un-gated | Medium |
| SDKs | unknown: confirm with owner whether external SDK repos exist | Low |

Open unknowns: Rust handler completeness behind the listed `/iw/v1/*` routes; whether Fry/prod runs with `IW_SCALING_SHADOW`, `-keep-warm` or planner enabled (deployment flags in deploy/ not audited); dist/ vs src parity at HEAD (not run).
